"""
Comprehensive unit tests for Anthropic client and token counter.

Tests cover:
- AnthropicService initialization and configuration
- Message creation with default and custom parameters
- Vision completion with base64 encoding
- Retry logic (RateLimitError, APITimeoutError, APIError with 5xx)
- No retry behavior (AuthenticationError, BadRequestError, 4xx errors)
- Session usage tracking and cost calculation
- Token estimation and cost formatting utilities
"""

import asyncio
import base64
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import httpx
from anthropic import APIError, APITimeoutError, AuthenticationError, BadRequestError, RateLimitError
from anthropic.types import Message, Usage

from app.integrations.anthropic_client import AnthropicService
from app.utils.token_counter import (
    COST_PER_INPUT_TOKEN,
    COST_PER_OUTPUT_TOKEN,
    calculate_cost,
    estimate_image_tokens,
    estimate_text_tokens,
    format_cost,
)


# Helper functions for creating mock exceptions

def create_mock_response(status_code: int, content: str = "Error"):
    """Create a mock httpx.Response for exception initialization."""
    return httpx.Response(
        status_code=status_code,
        content=content.encode(),
        request=httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    )


def create_rate_limit_error(message: str = "Rate limited"):
    """Create a properly initialized RateLimitError."""
    response = create_mock_response(429, message)
    return RateLimitError(message, response=response, body={"error": {"message": message}})


def create_authentication_error(message: str = "Invalid API key"):
    """Create a properly initialized AuthenticationError."""
    response = create_mock_response(401, message)
    return AuthenticationError(message, response=response, body={"error": {"message": message}})


def create_bad_request_error(message: str = "Invalid parameters"):
    """Create a properly initialized BadRequestError."""
    response = create_mock_response(400, message)
    return BadRequestError(message, response=response, body={"error": {"message": message}})


def create_api_error(status_code: int, message: str = "API Error"):
    """Create a properly initialized APIError with custom status code."""
    response = create_mock_response(status_code, message)
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    error = APIError(message, request=request, body={"error": {"message": message}})
    error.status_code = status_code
    return error


def create_timeout_error(message: str = "Timeout"):
    """Create a properly initialized APITimeoutError."""
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return APITimeoutError(request=request)


# Test fixtures

@pytest.fixture
def mock_settings():
    """Mock application settings."""
    settings = MagicMock()
    settings.ANTHROPIC_API_KEY = "test-api-key"
    settings.ANTHROPIC_MODEL = "claude-sonnet-4-5-20250514"
    settings.ANTHROPIC_MAX_TOKENS = 4096
    settings.ANTHROPIC_TEMPERATURE = 0.0
    settings.ANTHROPIC_TIMEOUT = 300
    return settings


@pytest.fixture
def mock_message_response():
    """Create a mock Message response from Anthropic API."""
    message = Mock(spec=Message)
    message.usage = Mock(spec=Usage)
    message.usage.input_tokens = 100
    message.usage.output_tokens = 50
    message.content = [{"type": "text", "text": "Test response"}]
    message.id = "msg_test123"
    message.model = "claude-sonnet-4-5-20250514"
    message.role = "assistant"
    message.stop_reason = "end_turn"
    return message


@pytest.fixture
def anthropic_service(mock_settings):
    """Create AnthropicService instance with mocked settings."""
    with patch("app.integrations.anthropic_client.get_settings", return_value=mock_settings):
        with patch("app.integrations.anthropic_client.anthropic.AsyncAnthropic") as mock_client:
            service = AnthropicService()
            service.client = AsyncMock()
            return service


# AnthropicService Tests

class TestAnthropicServiceInitialization:
    """Test service initialization and configuration."""

    def test_init_with_settings(self, mock_settings):
        """Test that service initializes with correct settings."""
        with patch("app.integrations.anthropic_client.get_settings", return_value=mock_settings):
            with patch("app.integrations.anthropic_client.anthropic.AsyncAnthropic") as mock_client_class:
                mock_client_instance = AsyncMock()
                mock_client_class.return_value = mock_client_instance

                service = AnthropicService()

                # Verify client was created with correct parameters
                mock_client_class.assert_called_once_with(
                    api_key="test-api-key",
                    timeout=300,
                )

                # Verify settings are stored
                assert service.settings == mock_settings

                # Verify session stats initialized
                assert service._session_stats["total_input_tokens"] == 0
                assert service._session_stats["total_output_tokens"] == 0
                assert service._session_stats["total_cost"] == 0.0
                assert service._session_stats["request_count"] == 0


class TestMessagesCreate:
    """Test messages_create method with various configurations."""

    @pytest.mark.asyncio
    async def test_messages_create_with_defaults(self, anthropic_service, mock_message_response):
        """Test message creation with default settings."""
        anthropic_service.client.messages.create = AsyncMock(return_value=mock_message_response)

        messages = [{"role": "user", "content": "Hello"}]
        response = await anthropic_service.messages_create(messages=messages)

        # Verify API was called with default settings
        anthropic_service.client.messages.create.assert_called_once()
        call_kwargs = anthropic_service.client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-sonnet-4-5-20250514"
        assert call_kwargs["max_tokens"] == 4096
        assert call_kwargs["temperature"] == 0.0
        assert call_kwargs["messages"] == messages
        assert "system" not in call_kwargs

        # Verify response
        assert response == mock_message_response

        # Verify usage tracking
        stats = anthropic_service.get_session_usage()
        assert stats["total_input_tokens"] == 100
        assert stats["total_output_tokens"] == 50
        assert stats["request_count"] == 1

    @pytest.mark.asyncio
    async def test_messages_create_with_custom_parameters(self, anthropic_service, mock_message_response):
        """Test message creation with custom model, max_tokens, and temperature."""
        anthropic_service.client.messages.create = AsyncMock(return_value=mock_message_response)

        messages = [{"role": "user", "content": "Custom test"}]
        response = await anthropic_service.messages_create(
            messages=messages,
            model="claude-opus-4-5-20251101",
            max_tokens=8192,
            temperature=0.7
        )

        # Verify API was called with custom parameters
        call_kwargs = anthropic_service.client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-opus-4-5-20251101"
        assert call_kwargs["max_tokens"] == 8192
        assert call_kwargs["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_messages_create_with_system_prompt(self, anthropic_service, mock_message_response):
        """Test message creation with system prompt."""
        anthropic_service.client.messages.create = AsyncMock(return_value=mock_message_response)

        messages = [{"role": "user", "content": "Hello"}]
        system_prompt = "You are a helpful assistant."

        await anthropic_service.messages_create(messages=messages, system=system_prompt)

        # Verify system prompt was included
        call_kwargs = anthropic_service.client.messages.create.call_args.kwargs
        assert call_kwargs["system"] == system_prompt

    @pytest.mark.asyncio
    async def test_messages_create_with_zero_temperature(self, anthropic_service, mock_message_response):
        """Test that temperature=0.0 is correctly passed (not treated as falsy)."""
        anthropic_service.client.messages.create = AsyncMock(return_value=mock_message_response)

        messages = [{"role": "user", "content": "Test"}]
        await anthropic_service.messages_create(messages=messages, temperature=0.0)

        call_kwargs = anthropic_service.client.messages.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.0


class TestVisionCompletion:
    """Test vision_completion method."""

    @pytest.mark.asyncio
    async def test_vision_completion_base64_encoding(self, anthropic_service, mock_message_response):
        """Test that image bytes are correctly base64 encoded."""
        anthropic_service.client.messages.create = AsyncMock(return_value=mock_message_response)

        image_bytes = b"fake_image_data"
        prompt = "Describe this image"
        media_type = "image/jpeg"

        response = await anthropic_service.vision_completion(
            image_bytes=image_bytes,
            prompt=prompt,
            media_type=media_type
        )

        # Verify base64 encoding
        expected_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Verify message structure
        call_kwargs = anthropic_service.client.messages.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert len(messages[0]["content"]) == 2

        # Verify image content block
        image_block = messages[0]["content"][0]
        assert image_block["type"] == "image"
        assert image_block["source"]["type"] == "base64"
        assert image_block["source"]["media_type"] == media_type
        assert image_block["source"]["data"] == expected_b64

        # Verify text content block
        text_block = messages[0]["content"][1]
        assert text_block["type"] == "text"
        assert text_block["text"] == prompt

        assert response == mock_message_response

    @pytest.mark.asyncio
    async def test_vision_completion_with_custom_params(self, anthropic_service, mock_message_response):
        """Test vision completion with custom model and max_tokens."""
        anthropic_service.client.messages.create = AsyncMock(return_value=mock_message_response)

        await anthropic_service.vision_completion(
            image_bytes=b"image",
            prompt="Test",
            media_type="image/png",
            model="claude-opus-4-5-20251101",
            max_tokens=2048
        )

        call_kwargs = anthropic_service.client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-opus-4-5-20251101"
        assert call_kwargs["max_tokens"] == 2048


class TestRetryLogic:
    """Test retry behavior for different error types."""

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit_error(self, anthropic_service, mock_message_response):
        """Test exponential backoff retry on RateLimitError."""
        # First call raises RateLimitError, second succeeds
        anthropic_service.client.messages.create = AsyncMock(
            side_effect=[create_rate_limit_error(), mock_message_response]
        )

        messages = [{"role": "user", "content": "Test"}]

        with patch("app.integrations.anthropic_client.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            response = await anthropic_service.messages_create(messages=messages)

            # Verify retry happened
            assert anthropic_service.client.messages.create.call_count == 2
            mock_sleep.assert_called_once()

            # Verify delay was applied (base delay + jitter)
            delay_arg = mock_sleep.call_args[0][0]
            assert 1.0 <= delay_arg <= 1.5  # RETRY_DELAY_BASE + JITTER_MAX

            assert response == mock_message_response

    @pytest.mark.asyncio
    async def test_retry_on_timeout_error(self, anthropic_service, mock_message_response):
        """Test retry on APITimeoutError."""
        anthropic_service.client.messages.create = AsyncMock(
            side_effect=[create_timeout_error(), mock_message_response]
        )

        messages = [{"role": "user", "content": "Test"}]

        with patch("app.integrations.anthropic_client.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            response = await anthropic_service.messages_create(messages=messages)

            assert anthropic_service.client.messages.create.call_count == 2
            mock_sleep.assert_called_once()
            assert response == mock_message_response

    @pytest.mark.asyncio
    async def test_retry_on_5xx_api_error(self, anthropic_service, mock_message_response):
        """Test retry on APIError with 5xx status code."""
        anthropic_service.client.messages.create = AsyncMock(
            side_effect=[create_api_error(500, "Server error"), mock_message_response]
        )

        messages = [{"role": "user", "content": "Test"}]

        with patch("app.integrations.anthropic_client.asyncio.sleep", new_callable=AsyncMock):
            response = await anthropic_service.messages_create(messages=messages)

            assert anthropic_service.client.messages.create.call_count == 2
            assert response == mock_message_response

    @pytest.mark.asyncio
    async def test_no_retry_on_authentication_error(self, anthropic_service):
        """Test that AuthenticationError is not retried."""
        anthropic_service.client.messages.create = AsyncMock(
            side_effect=create_authentication_error()
        )

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(AuthenticationError):
            await anthropic_service.messages_create(messages=messages)

        # Should only be called once (no retry)
        assert anthropic_service.client.messages.create.call_count == 1

    @pytest.mark.asyncio
    async def test_no_retry_on_bad_request_error(self, anthropic_service):
        """Test that BadRequestError is not retried."""
        anthropic_service.client.messages.create = AsyncMock(
            side_effect=create_bad_request_error()
        )

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(BadRequestError):
            await anthropic_service.messages_create(messages=messages)

        assert anthropic_service.client.messages.create.call_count == 1

    @pytest.mark.asyncio
    async def test_no_retry_on_4xx_api_error(self, anthropic_service):
        """Test that APIError with 4xx status is not retried."""
        anthropic_service.client.messages.create = AsyncMock(
            side_effect=create_api_error(400, "Client error")
        )

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(APIError) as exc_info:
            await anthropic_service.messages_create(messages=messages)

        assert exc_info.value.status_code == 400
        assert anthropic_service.client.messages.create.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self, anthropic_service):
        """Test that retry logic gives up after max attempts."""
        anthropic_service.client.messages.create = AsyncMock(
            side_effect=[create_rate_limit_error() for _ in range(3)]
        )

        messages = [{"role": "user", "content": "Test"}]

        with patch("app.integrations.anthropic_client.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RateLimitError):
                await anthropic_service.messages_create(messages=messages)

            # Should attempt 3 times (MAX_RETRIES)
            assert anthropic_service.client.messages.create.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self, anthropic_service, mock_message_response):
        """Test that retry delays follow exponential backoff."""
        anthropic_service.client.messages.create = AsyncMock(
            side_effect=[
                create_rate_limit_error(),
                create_rate_limit_error(),
                mock_message_response
            ]
        )

        messages = [{"role": "user", "content": "Test"}]

        with patch("app.integrations.anthropic_client.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await anthropic_service.messages_create(messages=messages)

            # Should have 2 sleep calls (after first two failures)
            assert mock_sleep.call_count == 2

            # Verify exponential backoff pattern
            delays = [call[0][0] for call in mock_sleep.call_args_list]
            # First delay: 1.0 * (2^0) + jitter = 1.0 to 1.5
            assert 1.0 <= delays[0] <= 1.5
            # Second delay: 1.0 * (2^1) + jitter = 2.0 to 2.5
            assert 2.0 <= delays[1] <= 2.5


class TestSessionUsageTracking:
    """Test session-level usage tracking."""

    @pytest.mark.asyncio
    async def test_get_session_usage_initial_state(self, anthropic_service):
        """Test that session usage starts at zero."""
        stats = anthropic_service.get_session_usage()

        assert stats["total_input_tokens"] == 0
        assert stats["total_output_tokens"] == 0
        assert stats["total_cost"] == 0.0
        assert stats["request_count"] == 0

    @pytest.mark.asyncio
    async def test_session_usage_tracking_single_request(self, anthropic_service, mock_message_response):
        """Test usage tracking for a single request."""
        anthropic_service.client.messages.create = AsyncMock(return_value=mock_message_response)

        messages = [{"role": "user", "content": "Test"}]
        await anthropic_service.messages_create(messages=messages)

        stats = anthropic_service.get_session_usage()
        assert stats["total_input_tokens"] == 100
        assert stats["total_output_tokens"] == 50
        assert stats["request_count"] == 1

        # Verify cost calculation
        expected_cost = calculate_cost(100, 50)
        assert stats["total_cost"] == expected_cost

    @pytest.mark.asyncio
    async def test_session_usage_tracking_multiple_requests(self, anthropic_service):
        """Test cumulative usage tracking across multiple requests."""
        # Create different responses
        response1 = Mock(spec=Message)
        response1.usage = Mock(input_tokens=100, output_tokens=50)

        response2 = Mock(spec=Message)
        response2.usage = Mock(input_tokens=200, output_tokens=100)

        anthropic_service.client.messages.create = AsyncMock(
            side_effect=[response1, response2]
        )

        messages = [{"role": "user", "content": "Test"}]
        await anthropic_service.messages_create(messages=messages)
        await anthropic_service.messages_create(messages=messages)

        stats = anthropic_service.get_session_usage()
        assert stats["total_input_tokens"] == 300
        assert stats["total_output_tokens"] == 150
        assert stats["request_count"] == 2

        expected_cost = calculate_cost(300, 150)
        assert stats["total_cost"] == expected_cost

    @pytest.mark.asyncio
    async def test_session_usage_returns_copy(self, anthropic_service):
        """Test that get_session_usage returns a copy, not reference."""
        stats1 = anthropic_service.get_session_usage()
        stats1["total_input_tokens"] = 999

        stats2 = anthropic_service.get_session_usage()
        assert stats2["total_input_tokens"] == 0


class TestCloseMethod:
    """Test close method and cleanup."""

    @pytest.mark.asyncio
    async def test_close_method(self, anthropic_service, mock_message_response):
        """Test that close method shuts down client and logs stats."""
        anthropic_service.client.messages.create = AsyncMock(return_value=mock_message_response)
        anthropic_service.client.close = AsyncMock()

        # Make a request to populate stats
        messages = [{"role": "user", "content": "Test"}]
        await anthropic_service.messages_create(messages=messages)

        # Close the service
        await anthropic_service.close()

        # Verify client was closed
        anthropic_service.client.close.assert_called_once()


# Token Counter Tests

class TestEstimateTextTokens:
    """Test text token estimation."""

    def test_estimate_text_tokens_basic(self):
        """Test basic text token estimation."""
        text = "Hello world"  # 11 characters
        tokens = estimate_text_tokens(text)
        assert tokens == 11 // 4  # 2 tokens

    def test_estimate_text_tokens_longer(self):
        """Test with longer text."""
        text = "A" * 1000  # 1000 characters
        tokens = estimate_text_tokens(text)
        assert tokens == 250

    def test_estimate_text_tokens_empty(self):
        """Test with empty string."""
        assert estimate_text_tokens("") == 0

    def test_estimate_text_tokens_none(self):
        """Test with None."""
        assert estimate_text_tokens(None) == 0


class TestEstimateImageTokens:
    """Test image token estimation."""

    def test_estimate_image_tokens_small(self):
        """Test token estimation for small image."""
        tokens = estimate_image_tokens(800, 600)
        expected = int((800 * 600) / 750)
        assert tokens == expected

    def test_estimate_image_tokens_large_width(self):
        """Test that large images are resized (width exceeds max)."""
        tokens = estimate_image_tokens(2000, 1000)

        # Should be scaled down to fit 1568px max
        scale = 1568 / 2000
        scaled_width = int(2000 * scale)
        scaled_height = int(1000 * scale)
        expected = int((scaled_width * scaled_height) / 750)

        assert tokens == expected

    def test_estimate_image_tokens_large_height(self):
        """Test that large images are resized (height exceeds max)."""
        tokens = estimate_image_tokens(1000, 2000)

        # Should be scaled down to fit 1568px max
        scale = 1568 / 2000
        scaled_width = int(1000 * scale)
        scaled_height = int(2000 * scale)
        expected = int((scaled_width * scaled_height) / 750)

        assert tokens == expected

    def test_estimate_image_tokens_exact_max(self):
        """Test with image exactly at max dimension."""
        tokens = estimate_image_tokens(1568, 1568)
        expected = int((1568 * 1568) / 750)
        assert tokens == expected

    def test_estimate_image_tokens_aspect_ratio_preserved(self):
        """Test that aspect ratio is preserved during resize."""
        # 3000x1500 should scale to 1568x784
        tokens = estimate_image_tokens(3000, 1500)

        scale = 1568 / 3000
        scaled_width = int(3000 * scale)
        scaled_height = int(1500 * scale)
        expected = int((scaled_width * scaled_height) / 750)

        assert tokens == expected
        # Verify aspect ratio preserved (approximately)
        assert abs((3000/1500) - (scaled_width/scaled_height)) < 0.01


class TestCalculateCost:
    """Test cost calculation."""

    def test_calculate_cost_basic(self):
        """Test basic cost calculation."""
        cost = calculate_cost(1000, 500)

        input_cost = Decimal(1000) * COST_PER_INPUT_TOKEN
        output_cost = Decimal(500) * COST_PER_OUTPUT_TOKEN
        expected = float(input_cost + output_cost)

        assert cost == expected

    def test_calculate_cost_zero_tokens(self):
        """Test cost with zero tokens."""
        cost = calculate_cost(0, 0)
        assert cost == 0.0

    def test_calculate_cost_only_input(self):
        """Test cost with only input tokens."""
        cost = calculate_cost(1000, 0)
        expected = float(Decimal(1000) * COST_PER_INPUT_TOKEN)
        assert cost == expected

    def test_calculate_cost_only_output(self):
        """Test cost with only output tokens."""
        cost = calculate_cost(0, 1000)
        expected = float(Decimal(1000) * COST_PER_OUTPUT_TOKEN)
        assert cost == expected

    def test_calculate_cost_precision(self):
        """Test that cost calculation maintains precision."""
        # 1M input + 1M output should equal exact pricing
        cost = calculate_cost(1_000_000, 1_000_000)
        expected = 3.0 + 15.0  # $3 + $15 per million
        assert abs(cost - expected) < 0.0001


class TestFormatCost:
    """Test cost formatting."""

    def test_format_cost_basic(self):
        """Test basic cost formatting."""
        formatted = format_cost(1000, 500)

        cost = calculate_cost(1000, 500)
        expected = f"${cost:.4f} (1000 in + 500 out)"

        assert formatted == expected

    def test_format_cost_zero(self):
        """Test formatting with zero cost."""
        formatted = format_cost(0, 0)
        assert formatted == "$0.0000 (0 in + 0 out)"

    def test_format_cost_large_numbers(self):
        """Test formatting with large token counts."""
        formatted = format_cost(1_000_000, 500_000)

        cost = calculate_cost(1_000_000, 500_000)
        expected = f"${cost:.4f} (1000000 in + 500000 out)"

        assert formatted == expected

    def test_format_cost_decimal_precision(self):
        """Test that format includes 4 decimal places."""
        formatted = format_cost(100, 50)
        # Extract dollar amount
        dollar_part = formatted.split(" ")[0]
        # Check format: $0.0000
        assert dollar_part.startswith("$")
        assert len(dollar_part.split(".")[1]) == 4
