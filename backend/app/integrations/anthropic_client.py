"""
Centralized Anthropic API client for Claude integration.

Provides:
- Async API client with configuration from settings
- Retry logic with exponential backoff
- Token usage and cost tracking
- Convenience methods for common operations
- Session-level usage statistics
"""

import asyncio
import base64
import logging
import random
from typing import Optional

import anthropic
from anthropic.types import Message

from app.config.settings import get_settings
from app.utils.token_counter import calculate_cost

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0  # seconds
RETRY_DELAY_MAX = 15.0  # seconds
JITTER_MAX = 0.5  # max jitter in seconds


class AnthropicService:
    """
    Centralized service for Anthropic API interactions.

    Features:
    - Async client with timeout configuration
    - Exponential backoff retry with jitter
    - Token usage and cost tracking per request and session
    - Convenience methods for common patterns (messages, vision)
    - Error handling with specific retry logic
    """

    def __init__(self):
        """Initialize Anthropic service with settings."""
        self.settings = get_settings()
        self.client = anthropic.AsyncAnthropic(
            api_key=self.settings.ANTHROPIC_API_KEY,
            timeout=self.settings.ANTHROPIC_TIMEOUT,
        )

        # Session-level tracking
        self._session_stats = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "request_count": 0,
        }

        logger.info(
            "AnthropicService initialized (model: %s, timeout: %ds)",
            self.settings.ANTHROPIC_MODEL,
            self.settings.ANTHROPIC_TIMEOUT
        )

    async def messages_create(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Message:
        """
        Create a message with retry logic and usage tracking.

        Args:
            messages: List of message dicts with "role" and "content"
            system: Optional system prompt
            model: Model identifier (defaults to settings)
            max_tokens: Max tokens to generate (defaults to settings)
            temperature: Sampling temperature (defaults to settings)

        Returns:
            Message response from API

        Raises:
            anthropic.AuthenticationError: Invalid API key
            anthropic.BadRequestError: Invalid request parameters
            Exception: After all retries exhausted
        """
        # Apply defaults from settings
        model = model or self.settings.ANTHROPIC_MODEL
        max_tokens = max_tokens or self.settings.ANTHROPIC_MAX_TOKENS
        temperature = temperature if temperature is not None else self.settings.ANTHROPIC_TEMPERATURE

        async def _api_call():
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }
            if system:
                kwargs["system"] = system

            return await self.client.messages.create(**kwargs)

        # Call with retry logic
        response = await self._call_with_retry(_api_call)

        # Track usage
        self._track_usage(response.usage.input_tokens, response.usage.output_tokens)

        # Log request
        cost = calculate_cost(response.usage.input_tokens, response.usage.output_tokens)
        logger.info(
            "API call complete: %d input, %d output tokens, $%.4f",
            response.usage.input_tokens,
            response.usage.output_tokens,
            cost
        )

        return response

    async def vision_completion(
        self,
        image_bytes: bytes,
        prompt: str,
        media_type: str = "image/jpeg",
        model: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> Message:
        """
        Convenience method for vision-based completions.

        Args:
            image_bytes: Image data as bytes
            prompt: Text prompt for the image
            media_type: MIME type (image/jpeg, image/png, image/gif, image/webp)
            model: Model identifier (defaults to settings)
            max_tokens: Max tokens to generate (defaults to settings)

        Returns:
            Message response from API
        """
        # Encode image to base64
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Build message with image content block
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ]

        return await self.messages_create(
            messages=messages,
            model=model,
            max_tokens=max_tokens
        )

    async def _call_with_retry(self, func, max_retries: int = MAX_RETRIES):
        """
        Call async function with exponential backoff retry logic.

        Retries on:
        - RateLimitError (exponential backoff with jitter)
        - APITimeoutError (fixed delay)
        - APIError with 5xx status (server errors)

        Does NOT retry on:
        - AuthenticationError (bad API key)
        - BadRequestError (invalid parameters)
        - APIError with 4xx status (client errors)

        Args:
            func: Async function to call
            max_retries: Maximum number of retry attempts

        Returns:
            Result from successful function call

        Raises:
            Exception: After all retries exhausted or on non-retryable error
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await func()

            except anthropic.AuthenticationError as e:
                # Don't retry auth errors
                logger.error("Authentication error: %s", e)
                raise

            except anthropic.BadRequestError as e:
                # Don't retry bad request errors
                logger.error("Bad request error: %s", e)
                raise

            except anthropic.RateLimitError as e:
                last_exception = e
                # Extract retry_after from error or use exponential backoff
                retry_after = getattr(e, "retry_after", None) or (RETRY_DELAY_BASE * (2 ** attempt))
                jitter = random.uniform(0, JITTER_MAX)
                delay = min(float(retry_after) + jitter, RETRY_DELAY_MAX)

                logger.warning(
                    "Rate limit hit (attempt %d/%d), retrying in %.1fs",
                    attempt + 1, max_retries, delay
                )

                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)

            except anthropic.APITimeoutError as e:
                last_exception = e
                delay = RETRY_DELAY_BASE * (2 ** attempt)

                logger.warning(
                    "API timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1, max_retries, delay
                )

                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)

            except anthropic.APIError as e:
                last_exception = e

                # Check if it's a server error (5xx) - retry
                # Client errors (4xx) - don't retry
                status_code = getattr(e, "status_code", None)
                if status_code and 400 <= status_code < 500:
                    logger.error("Client error (status %d): %s", status_code, e)
                    raise

                logger.warning(
                    "API error (attempt %d/%d): %s",
                    attempt + 1, max_retries, e
                )

                if attempt < max_retries - 1:
                    delay = RETRY_DELAY_BASE * (2 ** attempt)
                    await asyncio.sleep(delay)

        # All retries exhausted
        logger.error("All retry attempts exhausted")
        raise last_exception or Exception("Unknown error during API call")

    def _track_usage(self, input_tokens: int, output_tokens: int):
        """
        Track token usage for session statistics.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        self._session_stats["total_input_tokens"] += input_tokens
        self._session_stats["total_output_tokens"] += output_tokens
        self._session_stats["total_cost"] += calculate_cost(input_tokens, output_tokens)
        self._session_stats["request_count"] += 1

    def get_session_usage(self) -> dict:
        """
        Get cumulative session usage statistics.

        Returns:
            Dict with total_input_tokens, total_output_tokens, total_cost, request_count
        """
        return self._session_stats.copy()

    async def close(self):
        """Close the Anthropic client and log final stats."""
        stats = self.get_session_usage()
        logger.info(
            "AnthropicService shutting down - Total: %d requests, %d tokens, $%.4f",
            stats["request_count"],
            stats["total_input_tokens"] + stats["total_output_tokens"],
            stats["total_cost"]
        )
        await self.client.close()


# Singleton instance for application-wide use
anthropic_service = AnthropicService()
