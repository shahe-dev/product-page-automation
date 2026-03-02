"""
Prompt management service for PDP Automation v.3

Handles:
- Version-controlled prompt templates
- Field-specific prompt retrieval with template-aware defaults
- Template variable substitution
- Database-backed prompts with file fallback
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Prompt as PromptDB

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """Prompt template with metadata."""

    field_name: str
    template_type: str
    content: str
    character_limit: Optional[int] = None
    version: int = 1


class PromptManager:
    """Service for managing version-controlled prompts."""

    def __init__(self):
        """Initialize prompt manager with default prompts."""
        self.default_prompts = self.get_default_prompts()
        logger.info("PromptManager initialized with %d default prompts", len(self.default_prompts))

    async def get_prompt(
        self,
        field_name: str,
        template_type: str,
        variant: str = "standard",
        db: Optional[AsyncSession] = None
    ) -> PromptTemplate:
        """
        Get active prompt for a field/template combination.

        Lookup order:
        1. Database (if db session provided)
        2. Template-specific default (key: "{template_type}:{field_name}")
        3. Generic default (key: "{field_name}")
        4. Auto-generated generic fallback

        Args:
            field_name: Name of content field
            template_type: Template type (aggregators, opr, etc.)
            variant: Content variant (standard, luxury)
            db: Optional database session for querying prompts

        Returns:
            PromptTemplate for the field
        """
        # Try database lookup if session provided
        if db:
            try:
                query = select(PromptDB).where(
                    PromptDB.name == field_name,
                    PromptDB.template_type == template_type,
                    PromptDB.content_variant == variant,
                    PromptDB.is_active == True
                )
                result = await db.execute(query)
                prompt_db = result.scalar_one_or_none()

                if prompt_db:
                    logger.debug(
                        "Loaded prompt from database: %s (template=%s, variant=%s, version=%d)",
                        field_name, template_type, variant, prompt_db.version
                    )
                    return PromptTemplate(
                        field_name=field_name,
                        template_type=template_type,
                        content=prompt_db.content,
                        character_limit=prompt_db.character_limit,
                        version=prompt_db.version
                    )
            except Exception as e:
                logger.warning("Database prompt lookup failed, falling back to defaults: %s", e)

        # Fall back to default prompts -- template-specific key first
        template_key = f"{template_type}:{field_name}"

        if template_key in self.default_prompts:
            prompt_dict = self.default_prompts[template_key]
        elif field_name in self.default_prompts:
            prompt_dict = self.default_prompts[field_name]
        else:
            logger.warning(
                "No default prompt for field '%s' (template=%s), using generic",
                field_name, template_type
            )
            return self._get_generic_prompt(field_name, template_type)

        logger.debug(
            "Using default prompt: %s (template=%s, variant=%s)",
            field_name, template_type, variant
        )

        return PromptTemplate(
            field_name=field_name,
            template_type=template_type,
            content=prompt_dict["content"],
            character_limit=prompt_dict.get("character_limit"),
            version=prompt_dict.get("version", 1)
        )

    def format_prompt(
        self,
        template: PromptTemplate,
        data: dict
    ) -> str:
        """
        Format prompt template with actual data.

        Supports alias resolution so prompts can use either legacy placeholder
        names (e.g. {starting_price}) or new data keys (e.g. {price_min}).

        Args:
            template: Prompt template with placeholders
            data: Project data dictionary

        Returns:
            Formatted prompt string

        Placeholders (original + aliases):
            {project_name}, {developer}, {location}, {emirate},
            {starting_price}, {handover_date}, {amenities}, {property_types},
            {payment_plan}, {description}, {price_range}, {community},
            {sub_community}, {bedrooms}, {floor_plan_count}, {unit_types},
            {sqft_range}, {key_features}, {total_units}, {floors},
            {launch_date}, {currency}, {price_per_sqft}
        """
        prompt = template.content

        # Resolve location with fallback chain: location -> community -> sub_community -> emirate
        location = (
            data.get("location")
            or data.get("community")
            or data.get("sub_community")
            or data.get("emirate")
            or "Dubai"
        )

        # Resolve starting_price with fallback: starting_price -> price_min
        starting_price_raw = data.get("starting_price") or data.get("price_min")

        # Resolve property_types with fallback: property_types -> bedrooms
        property_types_raw = data.get("property_types") or data.get("bedrooms")
        if isinstance(property_types_raw, list):
            property_types = self._format_list(property_types_raw)
        elif property_types_raw:
            property_types = str(property_types_raw)
        else:
            property_types = "Not specified"

        # Format payment_plan: if dict, format as human-readable string
        payment_plan_raw = data.get("payment_plan", "Available on request")
        if isinstance(payment_plan_raw, dict):
            parts = []
            for key, val in payment_plan_raw.items():
                label = key.replace("_", " ").title()
                parts.append(f"{val} {label}")
            payment_plan = ", ".join(parts) if parts else "Available on request"
        else:
            payment_plan = payment_plan_raw or "Available on request"

        # Build price_range from price_min/price_max
        price_min = data.get("price_min")
        price_max = data.get("price_max")
        if price_min and price_max:
            price_range = f"{self._format_price(price_min)} - {self._format_price(price_max)}"
        elif price_min:
            price_range = f"From {self._format_price(price_min)}"
        elif price_max:
            price_range = f"Up to {self._format_price(price_max)}"
        else:
            price_range = "Price on request"

        # Floor plan summary values
        fp_summary = data.get("floor_plan_summary", {})

        # Prepare formatted values
        replacements = {
            # Core fields
            "project_name": data.get("project_name") or "Unknown Project",
            "developer": data.get("developer") or "Unknown Developer",
            "location": location,
            "emirate": data.get("emirate") or "Dubai",
            "starting_price": self._format_price(starting_price_raw),
            "handover_date": data.get("handover_date") or "TBA",
            "amenities": self._format_list(data.get("amenities", [])),
            "property_types": property_types,
            "payment_plan": payment_plan,
            "description": data.get("description") or "",
            # New direct pass-through fields
            "community": data.get("community") or data.get("location") or "",
            "sub_community": data.get("sub_community") or "",
            "bedrooms": self._format_list(data.get("bedrooms", [])),
            "key_features": self._format_list(data.get("key_features", [])),
            "total_units": str(data.get("total_units") or "N/A"),
            "floors": str(data.get("floors") or "N/A"),
            "launch_date": data.get("launch_date") or "TBA",
            "currency": data.get("currency") or "AED",
            "price_per_sqft": self._format_price(data.get("price_per_sqft")),
            # Computed fields
            "price_range": price_range,
            # Floor plan summary fields
            "floor_plan_count": str(fp_summary.get("count", 0)),
            "unit_types": self._format_list(fp_summary.get("unit_types", [])),
            "sqft_range": fp_summary.get("sqft_range", "N/A"),
        }

        # Add character limit if present
        if template.character_limit:
            replacements["character_limit"] = str(template.character_limit)

        # Replace all placeholders in a single pass to avoid corruption
        # when replacement values contain '{' or '}' characters.
        def _replacer(match: re.Match) -> str:
            key = match.group(1)
            val = replacements.get(key)
            if val is not None:
                return str(val)
            logger.warning("Unresolved placeholder in prompt: {%s}", key)
            return "N/A"

        formatted = re.sub(r'\{(\w+)\}', _replacer, prompt)

        # Auto-inject image descriptions as universal visual context
        image_desc = data.get("image_descriptions", "")
        if image_desc:
            formatted += (
                "\n\nVisual context from property brochure images:\n"
                + image_desc
            )

        return formatted

    def get_default_prompts(self) -> dict:
        """
        Get all default prompt templates.

        Returns:
            Dictionary keyed by field_name for generic prompts.
            Template-specific prompts keyed as "{template_type}:{field_name}".
            Lookup checks template-specific key first, then generic fallback.
        """
        generic = self._get_generic_field_prompts()

        agg_overrides = self._get_aggregators_prompts()
        opr_overrides = self._get_opr_prompts()
        mpp_overrides = self._get_mpp_prompts()
        adop_overrides = self._get_adop_prompts()
        adre_overrides = self._get_adre_prompts()
        commercial_overrides = self._get_commercial_prompts()

        merged = dict(generic)
        for template_type, overrides in [
            ("aggregators", agg_overrides),
            ("opr", opr_overrides),
            ("mpp", mpp_overrides),
            ("adop", adop_overrides),
            ("adre", adre_overrides),
            ("commercial", commercial_overrides),
        ]:
            for field_name, prompt_data in overrides.items():
                merged[f"{template_type}:{field_name}"] = prompt_data

        return merged

    # ------------------------------------------------------------------
    # Generic field prompts (fallback for any template)
    # ------------------------------------------------------------------

    def _get_generic_field_prompts(self) -> dict:
        """Generic prompts that work as fallback for any template type."""
        return {
            "meta_title": {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 60,
                "version": 1,
            },
            "meta_description": {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 160,
                "version": 1,
            },
            "h1": {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 70,
                "version": 1,
            },
            "url_slug": {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": None,
                "version": 1,
            },
            "image_alt": {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 125,
                "version": 1,
            },
        }

    # ------------------------------------------------------------------
    # AGGREGATORS prompts -- SEO-focused, searchability, 24+ domains
    # ------------------------------------------------------------------

    def _get_aggregators_prompts(self) -> dict:
        """Aggregator-specific prompts. SEO-focused for property listing sites."""
        prompts = {}

        # -- Hero --
        prompts["hero_h1"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 70,
            "version": 1,
        }
        prompts["hero_subtitle"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 150,
            "version": 1,
        }
        for i in range(1, 4):
            stat_focus = {
                1: "rental yield or ROI potential for the area",
                2: "capital appreciation or price growth trend",
                3: "Golden Visa eligibility or visa benefit",
            }.get(i, "key investment metric")
            prompts[f"hero_investment_stat_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }

        # -- About --
        prompts["about_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 80,
            "version": 1,
        }
        prompts["about_paragraph"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 650,
            "version": 1,
        }
        for i in range(1, 6):
            prompts[f"selling_point_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 100,
                "version": 1,
            }

        # -- Amenities --
        prompts["amenities_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 50,
            "version": 1,
        }
        for i in range(1, 7):
            prompts[f"amenity_{i}_title"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 40,
                "version": 1,
            }
            prompts[f"amenity_{i}_description"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 100,
                "version": 1,
            }

        # -- Payment Plan --
        prompts["payment_plan_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 60,
            "version": 1,
        }
        prompts["payment_plan_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 200,
            "version": 1,
        }

        # -- Location --
        prompts["location_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 70,
            "version": 1,
        }
        prompts["location_overview_paragraph"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 700,
            "version": 1,
        }

        # -- Economic Appeal --
        prompts["economic_appeal_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 60,
            "version": 1,
        }
        prompts["economic_appeal_paragraph"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 650,
            "version": 1,
        }

        # -- Key Features --
        for i in range(1, 4):
            feature_focus = {
                1: "location advantage or connectivity",
                2: "project design, quality, or amenities",
                3: "investment value or developer reputation",
            }.get(i, "project feature")
            prompts[f"key_feature_{i}_title"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 50,
                "version": 1,
            }
            prompts[f"key_feature_{i}_description"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 180,
                "version": 1,
            }

        # -- Social Facilities --
        prompts["social_facilities_intro"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 250,
            "version": 1,
        }
        for i in range(1, 4):
            prompts[f"social_facility_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }

        # -- Education & Medicine --
        prompts["education_medicine_intro"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 250,
            "version": 1,
        }
        for i in range(1, 4):
            prompts[f"education_facility_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }

        # -- Culture --
        prompts["culture_intro"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 250,
            "version": 1,
        }
        for i in range(1, 4):
            prompts[f"culture_facility_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }

        # -- Developer --
        prompts["developer_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 50,
            "version": 1,
        }
        prompts["developer_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 400,
            "version": 1,
        }

        # -- FAQ (10 Q&A) --
        for i in range(1, 11):
            prompts[f"faq_{i}_question"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }
            prompts[f"faq_{i}_answer"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 200,
                "version": 1,
            }

        return prompts

    @staticmethod
    def _faq_topic_aggregators(n: int) -> str:
        """Return the FAQ topic for aggregator FAQ question number n."""
        topics = {
            1: "Location and connectivity",
            2: "Price and payment plan",
            3: "Property types and sizes",
            4: "Handover date and construction status",
            5: "Developer track record",
            6: "Amenities and facilities",
            7: "ROI and investment potential",
            8: "Golden Visa eligibility",
            9: "Nearby schools and healthcare",
            10: "Community and lifestyle",
        }
        return topics.get(n, "General project information")

    # ------------------------------------------------------------------
    # OPR prompts -- Investment-focused, neutral factual tone
    # Per reference/company/prompts/prompt  opr.md
    # ------------------------------------------------------------------

    def _get_opr_prompts(self) -> dict:
        """OPR-specific prompts. Investment-focused, neutral factual tone."""
        prompts = {}

        # -- Hero --
        prompts["hero_subheading"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 150,
            "version": 1,
        }

        # -- Overview --
        prompts["overview_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 50,
            "version": 1,
        }
        prompts["overview_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 500,
            "version": 1,
        }

        # -- Location Access --
        prompts["location_access_h3"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        for i in range(1, 9):
            prompts[f"location_access_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 60,
                "version": 1,
            }

        # -- Amenities --
        prompts["amenities_h3"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        prompts["amenities_intro"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 200,
            "version": 1,
        }
        for i in range(1, 15):
            prompts[f"amenity_bullet_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 30,
                "version": 1,
            }

        # -- Property Types --
        prompts["property_types_h3"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 200,
            "version": 1,
        }

        # -- Payment Plan --
        prompts["payment_plan_h3"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        prompts["payment_plan_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 200,
            "version": 1,
        }

        # -- Investment Opportunities --
        prompts["investment_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        prompts["investment_intro"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 200,
            "version": 1,
        }
        for i in range(1, 7):
            topic = {
                1: "ROI potential percentage based on district median",
                2: "Average annual rent estimate for the area",
                3: "District rental yield data",
                4: "Golden Visa eligibility (if price >= AED 2M: eligible for 10-year UAE Golden Visa)",
                5: "Capital appreciation potential based on area development pipeline",
                6: "Comparison to similar projects in the district",
            }.get(i, "Capital appreciation context")
            prompts[f"investment_bullet_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 100,
                "version": 1,
            }

        # -- About the Area --
        prompts["area_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        prompts["area_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 400,
            "version": 1,
        }

        # -- Lifestyle, Healthcare, Education --
        prompts["lifestyle_h3"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        prompts["lifestyle_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 200,
            "version": 1,
        }
        for i in range(1, 5):
            prompts[f"lifestyle_bullet_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 60,
                "version": 1,
            }

        prompts["healthcare_h3"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        prompts["healthcare_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 200,
            "version": 1,
        }
        for i in range(1, 4):
            prompts[f"healthcare_bullet_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 60,
                "version": 1,
            }

        prompts["education_h3"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        prompts["education_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 200,
            "version": 1,
        }
        for i in range(1, 4):
            prompts[f"education_bullet_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 60,
                "version": 1,
            }

        # -- Developer --
        prompts["developer_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        prompts["developer_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 300,
            "version": 1,
        }

        # -- FAQ (14 Q&A) --
        prompts["faq_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        for i in range(1, 15):
            topic = self._faq_topic_opr(i)
            prompts[f"faq_{i}_question"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 100,
                "version": 1,
            }
            prompts[f"faq_{i}_answer"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 200,
                "version": 1,
            }

        return prompts

    @staticmethod
    def _faq_topic_opr(n: int) -> str:
        """Return the FAQ topic for OPR FAQ question number n."""
        topics = {
            1: "Starting price",
            2: "Location and area",
            3: "Payment plan structure",
            4: "Handover date",
            5: "Property types and sizes",
            6: "Developer information",
            7: "ROI and investment potential",
            8: "Rental yield estimates",
            9: "Golden Visa eligibility",
            10: "Amenities and facilities",
            11: "Construction status",
            12: "Nearby schools and healthcare",
            13: "Community lifestyle and recreation",
            14: "Service charges and maintenance",
        }
        return topics.get(n, "General project information")

    # ------------------------------------------------------------------
    # MPP prompts -- Balanced buyer/investor, comprehensive pages
    # ------------------------------------------------------------------

    def _get_mpp_prompts(self) -> dict:
        """MPP-specific prompts. Balanced for buyers and investors."""
        prompts = {}

        # -- Hero --
        prompts["hero_h1"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 70,
            "version": 1,
        }
        prompts["hero_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 450,
            "version": 1,
        }

        # -- Overview --
        prompts["overview_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 800,
            "version": 1,
        }

        # -- Payment Plan --
        prompts["payment_plan_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 250,
            "version": 1,
        }

        # -- Key Points --
        for i in range(1, 3):
            focus = "unique project feature or lifestyle benefit" if i == 1 else "investment value or location advantage"
            prompts[f"key_point_{i}_title"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 60,
                "version": 1,
            }
            prompts[f"key_point_{i}_description"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 350,
                "version": 1,
            }

        # -- Amenities --
        prompts["amenities_paragraph"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 450,
            "version": 1,
        }

        # -- Location --
        prompts["location_title"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 50,
            "version": 1,
        }
        prompts["location_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 600,
            "version": 1,
        }

        # -- Developer --
        prompts["developer_name_title"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 50,
            "version": 1,
        }
        prompts["developer_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 550,
            "version": 1,
        }

        # -- Image Alt --
        prompts["image_alt_tag"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 125,
            "version": 1,
        }

        # -- FAQ (6 Q&A) --
        prompts["faq_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        for i in range(1, 7):
            topic = self._faq_topic_mpp(i)
            prompts[f"faq_{i}_question"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }
            prompts[f"faq_{i}_answer"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 200,
                "version": 1,
            }

        return prompts

    @staticmethod
    def _faq_topic_mpp(n: int) -> str:
        """Return the FAQ topic for MPP FAQ question number n."""
        topics = {
            1: "Price and payment plan",
            2: "Location and connectivity",
            3: "Property types and sizes available",
            4: "Amenities and facilities",
            5: "Handover date and developer",
            6: "Developer information and handover",
        }
        return topics.get(n, "General project information")

    # ------------------------------------------------------------------
    # ADOP prompts -- Abu Dhabi off-plan, new development features
    # ------------------------------------------------------------------

    def _get_adop_prompts(self) -> dict:
        """ADOP-specific prompts for abudhabioffplan.ae. New development focus."""
        prompts = {}

        # -- Hero --
        prompts["hero_h1"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 60,
            "version": 1,
        }
        prompts["hero_subtitle"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 80,
            "version": 1,
        }
        prompts["image_alt_tag"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 125,
            "version": 1,
        }

        # -- About (3 paragraphs) --
        prompts["about_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 50,
            "version": 1,
        }
        prompts["about_paragraph_1"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 370,
            "version": 1,
        }
        prompts["about_paragraph_2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 370,
            "version": 1,
        }
        prompts["about_paragraph_3"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 370,
            "version": 1,
        }

        # -- Key Benefits --
        prompts["key_benefits_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 50,
            "version": 1,
        }
        prompts["key_benefits_paragraph_1"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 450,
            "version": 1,
        }
        prompts["key_benefits_paragraph_2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 500,
            "version": 1,
        }

        # -- Area Infrastructure --
        prompts["area_infrastructure_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 50,
            "version": 1,
        }
        prompts["infrastructure_paragraph_1"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 250,
            "version": 1,
        }
        prompts["infrastructure_paragraph_2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 350,
            "version": 1,
        }
        prompts["infrastructure_paragraph_3"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 250,
            "version": 1,
        }

        # -- Location --
        prompts["location_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 50,
            "version": 1,
        }
        prompts["location_drive_time_summary"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        prompts["location_overview"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 200,
            "version": 1,
        }
        prompts["location_key_attractions"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        prompts["location_major_destinations"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }

        # -- Investment --
        prompts["investment_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 50,
            "version": 1,
        }
        prompts["investment_paragraph_1"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 320,
            "version": 1,
        }
        prompts["investment_paragraph_2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 320,
            "version": 1,
        }
        prompts["investment_paragraph_3"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 320,
            "version": 1,
        }
        prompts["investment_paragraph_4"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 300,
            "version": 1,
        }

        # -- Developer --
        prompts["developer_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 50,
            "version": 1,
        }
        prompts["developer_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 500,
            "version": 1,
        }

        # -- FAQ (12 Q&A) --
        prompts["faq_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        for i in range(1, 13):
            topic = self._faq_topic_adop(i)
            prompts[f"faq_{i}_question"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }
            prompts[f"faq_{i}_answer"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 200,
                "version": 1,
            }

        return prompts

    @staticmethod
    def _faq_topic_adop(n: int) -> str:
        """Return the FAQ topic for ADOP FAQ question number n."""
        topics = {
            1: "Starting price and value proposition",
            2: "Location and area in Abu Dhabi",
            3: "Payment plan structure",
            4: "Handover date and construction status",
            5: "Property types and unit sizes",
            6: "Area infrastructure and connectivity",
            7: "Developer track record in Abu Dhabi",
            8: "Investment potential and visa eligibility",
            9: "Community amenities and lifestyle",
            10: "Rental yield potential",
            11: "Registration and ownership process",
            12: "Nearby schools and healthcare",
        }
        return topics.get(n, "General project information")

    # ------------------------------------------------------------------
    # ADRE prompts -- Abu Dhabi ready/secondary market
    # ------------------------------------------------------------------

    def _get_adre_prompts(self) -> dict:
        """ADRE-specific prompts for secondary-market-portal.com. Ready property market."""
        prompts = {}

        # -- Hero --
        prompts["hero_marketing_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 60,
            "version": 1,
        }

        # -- About --
        prompts["about_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 60,
            "version": 1,
        }
        prompts["about_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 900,
            "version": 1,
        }

        # -- Amenities (3 items with H3 subheads + amenities list) --
        prompts["amenities_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 50,
            "version": 1,
        }
        for i in range(1, 4):
            prompts[f"amenity_{i}_h3"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 50,
                "version": 1,
            }
            prompts[f"amenity_{i}_description"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 250,
                "version": 1,
            }
        prompts["amenities_list"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }

        # -- Developer --
        prompts["developer_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 300,
            "version": 1,
        }

        # -- Economic Appeal --
        prompts["economic_appeal_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 60,
            "version": 1,
        }
        prompts["economic_appeal_intro"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 600,
            "version": 1,
        }
        prompts["economic_stats_roi"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": None,
            "version": 1,
        }
        prompts["rental_appeal"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 250,
            "version": 1,
        }
        prompts["resale_appeal"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 250,
            "version": 1,
        }
        prompts["enduser_appeal"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 250,
            "version": 1,
        }

        # -- Payment Plan --
        prompts["payment_plan_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 70,
            "version": 1,
        }

        # -- Location --
        prompts["location_overview"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 700,
            "version": 1,
        }

        # -- Area Card --
        prompts["area_card_style"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 30,
            "version": 1,
        }
        prompts["area_card_focal_point"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 60,
            "version": 1,
        }
        prompts["area_card_accessibility"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 80,
            "version": 1,
        }
        for i in range(1, 5):
            prompts[f"area_card_shopping_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }
        for i in range(1, 7):
            prompts[f"area_card_entertainment_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }

        # -- Healthcare --
        for i in range(1, 3):
            prompts[f"healthcare_facility_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }

        # -- Education --
        prompts["education_nurseries"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 80,
            "version": 1,
        }
        prompts["education_international_schools"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 80,
            "version": 1,
        }
        prompts["education_secondary_schools"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 80,
            "version": 1,
        }
        prompts["education_universities"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 80,
            "version": 1,
        }

        # -- FAQ (12 Q&A) --
        for i in range(1, 13):
            topic = self._faq_topic_adre(i)
            prompts[f"faq_{i}_question"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }
            prompts[f"faq_{i}_answer"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 200,
                "version": 1,
            }

        return prompts

    @staticmethod
    def _faq_topic_adre(n: int) -> str:
        """Return the FAQ topic for ADRE FAQ question number n."""
        topics = {
            1: "Starting price and property types",
            2: "Location and community in Abu Dhabi",
            3: "Rental yield and tenant demand",
            4: "Resale value and price trends",
            5: "Amenities and facilities available",
            6: "Developer and build quality",
            7: "End-user lifestyle and family suitability",
            8: "Service charges and ownership costs",
            9: "Community living and daily convenience",
            10: "Pet-friendliness and outdoor spaces",
            11: "Registration and transfer fees",
            12: "Maintenance and property management",
        }
        return topics.get(n, "General property information")

    # ------------------------------------------------------------------
    # COMMERCIAL prompts -- B2B professional, office/retail focus
    # ------------------------------------------------------------------

    def _get_commercial_prompts(self) -> dict:
        """Commercial-specific prompts for commercial-portal.com. B2B professional tone."""
        prompts = {}

        # -- Hero --
        prompts["hero_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 80,
            "version": 1,
        }
        for i in range(1, 4):
            feature_focus = {
                1: "location or business connectivity advantage",
                2: "commercial specifications or building quality",
                3: "investment returns or financial incentives",
            }.get(i, "commercial advantage")
            prompts[f"hero_feature_{i}_title"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 30,
                "version": 1,
            }
            prompts[f"hero_feature_{i}_description"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 60,
                "version": 1,
            }

        # -- About --
        prompts["about_h2"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 50,
            "version": 1,
        }
        prompts["about_h3"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 80,
            "version": 1,
        }
        prompts["about_paragraph"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 200,
            "version": 1,
        }

        # -- Payment Plan --
        prompts["payment_plan_headline"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 60,
            "version": 1,
        }
        prompts["payment_plan_title"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 30,
            "version": 1,
        }
        prompts["payment_plan_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 150,
            "version": 1,
        }

        # -- Advantages (3 items) --
        for i in range(1, 4):
            focus = {
                1: "location and business connectivity advantage",
                2: "commercial specifications and building quality",
                3: "investment returns and financial incentives",
            }.get(i, "commercial advantage")
            prompts[f"advantage_{i}_title"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }
            prompts[f"advantage_{i}_description"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 200,
                "version": 1,
            }

        # -- Amenities (5 items) --
        for i in range(1, 6):
            prompts[f"amenity_{i}_title"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }
            prompts[f"amenity_{i}_description"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 200,
                "version": 1,
            }

        # -- Developer --
        prompts["developer_h3"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 60,
            "version": 1,
        }
        prompts["developer_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 250,
            "version": 1,
        }

        # -- Location --
        prompts["location_h3"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 80,
            "version": 1,
        }
        prompts["location_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 400,
            "version": 1,
        }

        # -- Social Facilities --
        prompts["social_facilities_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 300,
            "version": 1,
        }
        for i in range(1, 4):
            prompts[f"social_facility_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }

        # -- Education & Medicine --
        prompts["education_medicine_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 300,
            "version": 1,
        }
        for i in range(1, 4):
            prompts[f"education_nearby_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }

        # -- Culture --
        prompts["culture_description"] = {
            "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

            "character_limit": 300,
            "version": 1,
        }
        for i in range(1, 4):
            prompts[f"culture_nearby_{i}"] = {
                "content": "[Prompt not included in public repository -- configure via database or seed_prompts.py]",

                "character_limit": 80,
                "version": 1,
            }

        return prompts

    # ------------------------------------------------------------------
    # Fallback generic prompt for unknown fields
    # ------------------------------------------------------------------

    def _get_generic_prompt(
        self,
        field_name: str,
        template_type: str
    ) -> PromptTemplate:
        """
        Generate a generic prompt for fields with no defined prompt.

        Args:
            field_name: Field name
            template_type: Template type

        Returns:
            Generic PromptTemplate
        """
        content = (
            f'Generate content for the field "{field_name}" for this Dubai real estate project.\n\n'
            f"Project: {{project_name}}\nDeveloper: {{developer}}\nLocation: {{location}}\n"
            f"Price: {{starting_price}}\n\n"
            f"Requirements:\n- Professional and informative\n- Follow brand guidelines\n"
            f"- No prohibited marketing terms\n- Clear and concise\n\n"
            f'Return ONLY the content for "{field_name}", nothing else.'
        )

        return PromptTemplate(
            field_name=field_name,
            template_type=template_type,
            content=content,
            character_limit=None,
            version=1
        )

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    def _format_price(self, price: Optional[float | int]) -> str:
        """Format price for display."""
        if price is None:
            return "Price on request"

        price = float(price)

        if price >= 1000000:
            return f"AED {price/1000000:.1f}M"
        elif price >= 1000:
            return f"AED {price/1000:.0f}K"
        else:
            return f"AED {price:,.0f}"

    def _format_list(self, items: list) -> str:
        """Format a list of items for display in prompts."""
        if not items:
            return "Not specified"

        if len(items) <= 3:
            return ", ".join(str(item) for item in items)
        else:
            first_three = ", ".join(str(item) for item in items[:3])
            return f"{first_three}, and {len(items) - 3} more"


# Singleton instance (thread-safe)
_prompt_manager_instance: Optional[PromptManager] = None
_prompt_manager_lock = __import__("threading").Lock()


def get_prompt_manager() -> PromptManager:
    """
    Get or create singleton PromptManager instance (thread-safe).

    Returns:
        PromptManager instance
    """
    global _prompt_manager_instance
    if _prompt_manager_instance is None:
        with _prompt_manager_lock:
            if _prompt_manager_instance is None:
                _prompt_manager_instance = PromptManager()
    return _prompt_manager_instance
