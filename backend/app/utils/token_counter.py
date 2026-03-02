"""
Token estimation and cost calculation utilities.

Provides helpers for:
- Estimating token usage before API calls
- Calculating API costs based on token usage
- Formatting cost information for display
"""

import os
from decimal import Decimal

# Anthropic Claude API pricing.
# Override via environment variables if model or pricing changes.
# Defaults: Claude Sonnet 4.5 as of January 2025
# Source: https://www.anthropic.com/pricing
COST_PER_INPUT_TOKEN = Decimal(
    os.environ.get("ANTHROPIC_COST_PER_INPUT_TOKEN", "0.000003")
)  # Default: $3 per million input tokens
COST_PER_OUTPUT_TOKEN = Decimal(
    os.environ.get("ANTHROPIC_COST_PER_OUTPUT_TOKEN", "0.000015")
)  # Default: $15 per million output tokens


def estimate_text_tokens(text: str) -> int:
    """
    Estimate token count for text content.

    Uses rough approximation of 4 characters per token.
    For accurate counts, use the actual API response.

    Args:
        text: Text content to estimate

    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return len(text) // 4


def estimate_image_tokens(width: int, height: int) -> int:
    """
    Estimate token count for image content.

    Based on Anthropic's documentation:
    - Images are resized to fit within 1568x1568 px square
    - Token count = (width * height) / 750

    Args:
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        Estimated token count
    """
    # Resize to fit within max dimensions while preserving aspect ratio
    max_dimension = 1568
    if width > max_dimension or height > max_dimension:
        scale = min(max_dimension / width, max_dimension / height)
        width = int(width * scale)
        height = int(height * scale)

    # Calculate tokens
    tokens = (width * height) / 750
    return int(tokens)


def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """
    Calculate API call cost in USD.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD
    """
    input_cost = Decimal(input_tokens) * COST_PER_INPUT_TOKEN
    output_cost = Decimal(output_tokens) * COST_PER_OUTPUT_TOKEN
    total_cost = input_cost + output_cost
    return float(total_cost)


def format_cost(input_tokens: int, output_tokens: int) -> str:
    """
    Format cost calculation as readable string.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Formatted cost string (e.g., "$0.0450 (10000 in + 2000 out)")
    """
    cost = calculate_cost(input_tokens, output_tokens)
    return f"${cost:.4f} ({input_tokens} in + {output_tokens} out)"
