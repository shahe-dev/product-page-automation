"""
AI-powered content generation service for PDP Automation v.3

Handles:
- Multi-field content generation using Anthropic Claude
- Brand context integration
- Character limit enforcement
- Token usage and cost tracking
- Template-specific content generation
"""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.integrations.anthropic_client import anthropic_service
from app.services.prompt_manager import PromptManager
from app.services.template_fields import get_fields_for_template
from app.utils.token_counter import calculate_cost

logger = logging.getLogger(__name__)

# Rate limit configuration
MAX_RETRIES = 3  # For character limit retries only
RETRY_DELAY_BASE = 1.0  # Base retry delay in seconds
RETRY_DELAY_MAX = 15.0  # Maximum retry delay in seconds

# Re-export token cost constants for backward compatibility
from app.utils.token_counter import (
    COST_PER_INPUT_TOKEN,
    COST_PER_OUTPUT_TOKEN,
)


@dataclass
class GeneratedField:
    """Result of generating a single content field."""

    field_name: str
    content: str
    character_count: int
    within_limit: bool
    template_type: str
    token_usage: dict  # {"input": N, "output": N}
    generation_cost: float
    prompt_version: Optional[str] = None


@dataclass
class ContentOutput:
    """Complete content generation result for a project."""

    fields: dict[str, GeneratedField]
    template_type: str
    total_token_usage: dict  # {"input": N, "output": N}
    total_cost: float
    errors: list[str] = field(default_factory=list)


class ContentGenerator:
    """Service for AI-powered content generation."""

    # Prohibited brand terms (always banned regardless of context)
    PROHIBITED_TERMS = [
        "world-class",
        "prime location",
        "state-of-the-art",
        "unrivaled",
        "prestigious",
    ]

    # Context-dependent terms: flag but do not auto-reject
    FLAGGED_TERMS = [
        "exclusive",
        "luxury",
    ]

    def __init__(self, db: Optional[AsyncSession] = None):
        """Initialize content generator with Anthropic client and brand context.

        Args:
            db: Optional database session for prompt lookups.
                When provided, prompts are read from the database.
                When None, falls back to hardcoded defaults.
        """
        self.settings = get_settings()
        self.client = anthropic_service
        self.brand_context = self._load_brand_context()
        self.prompt_manager = PromptManager()
        self.db = db

        logger.info("ContentGenerator initialized with model: %s", self.settings.ANTHROPIC_MODEL)

    @staticmethod
    def _needs_rich_context(field_name: str, char_limit: Optional[int]) -> bool:
        """Determine if a field needs Tier 2 (rich) context with full extracted text.

        Fields qualifying for rich context:
        - Have a character limit > 300 (paragraph-length fields)
        - Contain keywords indicating descriptive content
        """
        if char_limit and char_limit > 300:
            return True
        rich_keywords = ("paragraph", "description", "about", "overview")
        return any(kw in field_name for kw in rich_keywords)

    async def generate_all(
        self,
        base_context: dict,
        rich_context: dict,
        template_type: str,
        content_variant: str = "standard",
        progress_callback: Optional[callable] = None
    ) -> ContentOutput:
        """
        Generate all content fields for a project using tiered context.

        Uses a two-tier context system:
        - Tier 1 (base_context): All 19 StructuredProject fields + floor plan
          summary + image manifest metadata. Used for short-form fields.
        - Tier 2 (rich_context): Tier 1 + full extracted PDF text. Used for
          paragraph/description fields (char_limit > 300 or name contains
          "paragraph", "description", "about", "overview").

        Args:
            base_context: Tier 1 context dict (structured fields + summaries)
            rich_context: Tier 2 context dict (Tier 1 + extracted_text)
            template_type: Template type (aggregators, opr, mpp, etc.)
            content_variant: Content style variant (standard, luxury)
            progress_callback: Optional async callback(message: str) for progress updates

        Returns:
            ContentOutput with all generated fields
        """
        logger.info(
            "Generating content for project: %s (template: %s, variant: %s)",
            base_context.get("project_name", "Unknown"),
            template_type,
            content_variant
        )

        # Log context availability
        null_keys = [k for k, v in base_context.items() if v is None]
        logger.info(
            "Context summary: %d base keys, %d null fields, rich text %d chars",
            len(base_context),
            len(null_keys),
            len(rich_context.get("extracted_text", "")),
        )
        if null_keys:
            logger.info("Null context fields: %s", ", ".join(null_keys))

        template_fields = get_fields_for_template(template_type)
        fields_to_generate = list(template_fields.keys())
        generated_fields = {}
        errors = []
        total_input_tokens = 0
        total_output_tokens = 0

        for i, field_name in enumerate(fields_to_generate):
            # Report progress for UI visibility
            if progress_callback:
                fraction = (i + 1) / len(fields_to_generate)
                await progress_callback(
                    f"Generating: {field_name} ({i + 1}/{len(fields_to_generate)})",
                    fraction,
                )

            try:
                field_def = template_fields.get(field_name)
                character_limit = field_def.char_limit if field_def else None

                # Select context tier based on field characteristics
                use_rich = self._needs_rich_context(field_name, character_limit)
                context = rich_context if use_rich else base_context
                tier_label = "Tier 2 (rich)" if use_rich else "Tier 1 (base)"
                logger.debug(
                    "Generating %s with %s context", field_name, tier_label
                )

                generated = await self.generate_field(
                    field_name=field_name,
                    structured_data=context,
                    template_type=template_type,
                    content_variant=content_variant,
                    character_limit=character_limit
                )
                generated_fields[field_name] = generated
                total_input_tokens += generated.token_usage["input"]
                total_output_tokens += generated.token_usage["output"]

            except Exception as e:
                logger.error("Failed to generate field '%s': %s", field_name, e)
                errors.append(f"Failed to generate {field_name}: {str(e)}")

        # Calculate total cost
        total_cost = calculate_cost(total_input_tokens, total_output_tokens)

        return ContentOutput(
            fields=generated_fields,
            template_type=template_type,
            total_token_usage={
                "input": total_input_tokens,
                "output": total_output_tokens
            },
            total_cost=total_cost,
            errors=errors
        )

    async def generate_field(
        self,
        field_name: str,
        structured_data: dict,
        template_type: str,
        content_variant: str = "standard",
        character_limit: Optional[int] = None
    ) -> GeneratedField:
        """
        Generate a single content field.

        Args:
            field_name: Name of field to generate (meta_title, meta_description, etc.)
            structured_data: Extracted project data
            template_type: Template type
            content_variant: Content style variant
            character_limit: Optional character limit override

        Returns:
            GeneratedField with content and metadata

        Raises:
            ValueError: If field_name is invalid or generation fails
        """
        template_fields = get_fields_for_template(template_type)
        if field_name not in template_fields:
            raise ValueError(f"Unknown field '{field_name}' for template '{template_type}'")

        # Get field-specific prompt (from database or file fallback)
        prompt_template = await self.prompt_manager.get_prompt(
            field_name=field_name,
            template_type=template_type,
            variant=content_variant,
            db=self.db
        )

        # Format prompt with actual data
        original_message = self.prompt_manager.format_prompt(
            template=prompt_template,
            data=structured_data
        )

        # Build system message with brand context
        system_message = self._build_system_message(template_type)

        # Use the character_limit passed from caller (already extracted from FieldDef)
        # Fallback to field_def.char_limit if character_limit wasn't provided
        field_def = template_fields.get(field_name)
        limit = character_limit or (field_def.char_limit if field_def else None)
        current_message = original_message

        for attempt in range(MAX_RETRIES):
            try:
                response = await self.client.messages_create(
                    messages=[{"role": "user", "content": current_message}],
                    system=system_message
                )

                content = response.content[0].text.strip()
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens

                generation_cost = calculate_cost(input_tokens, output_tokens)

                char_count = len(content)
                within_limit = limit is None or char_count <= limit

                # Retry with stricter prompt if content exceeds character limit
                if not within_limit and attempt < MAX_RETRIES - 1:
                    logger.warning(
                        "Field '%s' over limit (%d/%d chars), retrying with stricter prompt",
                        field_name, char_count, limit
                    )
                    current_message = (
                        original_message
                        + f"\n\nCRITICAL: Response MUST be {limit} characters or fewer. "
                        f"Previous attempt was {char_count} characters. Be more concise."
                    )
                    await asyncio.sleep(1.0)
                    continue

                if not within_limit:
                    logger.warning(
                        "Field '%s' still over limit after retries: %d/%d chars",
                        field_name, char_count, limit
                    )

                logger.info(
                    "Generated field '%s': %d chars, %d tokens (cost: $%.4f)",
                    field_name, char_count, output_tokens, generation_cost
                )

                return GeneratedField(
                    field_name=field_name,
                    content=content,
                    character_count=char_count,
                    within_limit=within_limit,
                    template_type=template_type,
                    token_usage={"input": input_tokens, "output": output_tokens},
                    generation_cost=generation_cost,
                    prompt_version=f"v{prompt_template.version}"
                )

            except Exception as e:
                # Non-retryable errors should propagate immediately
                import anthropic as _anthropic_mod
                if isinstance(e, (_anthropic_mod.AuthenticationError, _anthropic_mod.BadRequestError)):
                    raise ValueError(
                        f"Content generation failed for {field_name} (non-retryable): {e}"
                    ) from e

                # API retry logic is handled by centralized client
                # This catches business logic issues (character limits, parsing, etc.)
                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        "Error generating field '%s' (attempt %d/%d): %s",
                        field_name, attempt + 1, MAX_RETRIES, e
                    )
                    await asyncio.sleep(1.0)
                else:
                    raise ValueError(
                        f"Content generation failed for {field_name} after {MAX_RETRIES} attempts: {e}"
                    ) from e

    def _load_brand_context(self) -> str:
        """
        Load brand context from file with fallback to default.

        TODO: This performs synchronous file I/O which blocks the event loop if
        called during an async request. Preload the singleton during app startup
        via asyncio.to_thread(get_content_generator) in main.py.

        Returns:
            Brand context string for system prompt
        """
        # Get project root (backend/app/services/content_generator.py -> ../../.. = project root)
        project_root = Path(__file__).parent.parent.parent.parent
        brand_context_path = project_root / "reference/company/brand-guidelines/brand-context-prompt.md"

        if brand_context_path.exists():
            try:
                with open(brand_context_path, "r", encoding="utf-8") as f:
                    context = f.read()
                    logger.info("Loaded brand context from: %s", brand_context_path)
                    return context
            except Exception as e:
                logger.warning("Failed to load brand context file: %s", e)

        # Fallback to embedded default
        logger.warning("Brand context file not found, using embedded defaults")
        return self._get_default_brand_context()

    def _get_default_brand_context(self) -> str:
        """Get default brand context if file is not available."""
        return """
You are a professional real estate content writer for the company.

BRAND VOICE:
- Expert advisor, not salesperson
- Informative and trustworthy
- Clear and concise
- Professional but approachable

TERMINOLOGY:
- Use "apartment" not "flat"
- Use "developer" not "builder"
- Use "handover" not "completion"
- Use "payment plan" not "installment plan"

PROHIBITED TERMS (avoid generic marketing fluff):
- "world-class"
- "prime location" (be specific instead)
- "state-of-the-art" (describe actual features)
- "unrivaled"
- "prestigious" (unless factually accurate)
- "exclusive" (unless factually accurate)

STYLE GUIDELINES:
- Lead with facts: price, location, developer, handover
- Use specific details over vague claims
- Include numbers and data points
- Write for Dubai property market audience
- SEO-optimized but natural language
- Active voice preferred
"""

    def _build_system_message(self, template_type: str) -> str:
        """
        Build system message with brand context and template type description.

        Per-field prompt content is now in PromptManager defaults and the database.
        The system message provides brand context and template-level context only.

        Args:
            template_type: Template type (aggregators, opr, mpp, etc.)

        Returns:
            Complete system message for Claude
        """
        template_descriptions = {
            "aggregators": "Content for third-party property listing aggregator websites. Focus on SEO, searchability, and clear property information for comparison shoppers.",
            "opr": "Content for off-plan-portal.com, the Off-Plan Real Estate website. Emphasize investment potential, ROI data, payment plan structure, and factual property analysis for investors.",
            "mpp": "Content for main-portal.com, the Brand Portal main site. Balanced approach for both end-user buyers and investors with comprehensive project information.",
            "adop": "Content for abudhabioffplan.ae, Abu Dhabi off-plan developments. Focus on new project features, area infrastructure, and investment benefits specific to Abu Dhabi market.",
            "adre": "Content for secondary-market-portal.com, Abu Dhabi ready/secondary market. Cover economic appeal for rental, resale, and end-user segments with location-categorized information.",
            "commercial": "Content for cre.main-portal.com, commercial real estate (office/retail). Professional B2B tone with economic indicators, project passport data, and business-focused amenities.",
        }

        template_context = template_descriptions.get(
            template_type,
            "General real estate content for Dubai/UAE property market."
        )

        return f"""{self.brand_context}

TEMPLATE TYPE: {template_type.upper()}
TEMPLATE CONTEXT: {template_context}

ACCURACY REQUIREMENTS (non-negotiable):
- Use ONLY facts provided in the project data below. Do not invent, assume, or hallucinate any information.
- Project name, developer name, community, emirate: Use the EXACT values provided. Never alter spelling or substitute similar names.
- Prices: Use the exact price figures provided. If no price data is given, write "Price on request" -- never fabricate a number.
- Amenities: Mention ONLY amenities listed in the provided data. If no amenities are listed, do not invent them.
- Developer info: Use only the developer name provided. Do not add developer history, portfolio size, or reputation claims unless explicitly in the data.
- Payment plans: Use the exact payment structure provided. Do not fabricate percentages or milestones.
- Handover dates: Use the exact date provided. If not provided, write "TBA".
- Bedroom types, unit counts, floors: Use only the values provided. Do not estimate.
- If any required information is missing from the data, write "TBA" (To Be Announced) rather than inventing a plausible value.
- EXCEPTION: Location access (distances/drive times) and investment analysis (ROI, rental yields) may use general market knowledge when project-specific data is not provided.

Generate content that follows these brand guidelines strictly. Return ONLY the requested content, no additional commentary or formatting."""


def get_content_generator(db: Optional[AsyncSession] = None) -> ContentGenerator:
    """
    Create a ContentGenerator instance.

    Args:
        db: Optional database session for prompt lookups.
            When provided, prompts are read from the database.
            When None, falls back to hardcoded defaults.

    Returns:
        ContentGenerator instance
    """
    return ContentGenerator(db=db)
