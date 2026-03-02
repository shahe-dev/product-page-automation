# Agent Brief: DEV-ANTHROPIC-001

**Agent ID:** DEV-ANTHROPIC-001
**Agent Name:** Anthropic Integration Agent
**Type:** Development
**Phase:** 5 - Integrations
**Context Budget:** 55,000 tokens

---

## Mission

Implement Anthropic Claude API client with model selection, token management, cost tracking, and retry logic.

---

## Documentation to Read

### Primary
1. `docs/05-integrations/ANTHROPIC_API_INTEGRATION.md` - Claude API patterns

### Secondary
1. `docs/02-modules/CONTENT_GENERATION.md` - Content generation needs

---

## Dependencies

**Upstream:** DEV-CONFIG-001
**Downstream:** DEV-IMGCLASS-001, DEV-WATERMARK-001, DEV-FLOORPLAN-001, DEV-STRUCT-001, DEV-CONTENT-001

---

## Outputs

### `backend/app/integrations/anthropic_client.py`
### `backend/app/utils/token_counter.py`

---

## Acceptance Criteria

1. **Client Setup:**
   - API key from Secret Manager
   - Request timeout configuration
   - AsyncAnthropic client initialization

2. **Model Support:**
   - Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) for all tasks
   - Model selection per request (future-proof for Haiku/Opus)

3. **Messages API:**
   - Single message
   - Multi-turn conversation
   - System prompt injection (separate parameter)
   - Temperature control
   - Max tokens limit

4. **Vision Requests:**
   - Base64 image input (source.type: "base64")
   - Multiple images per request
   - Media type detection

5. **Token Management:**
   - Pre-estimate tokens for images (pixels/750)
   - Warn on approaching limits
   - Track usage per request via response.usage

6. **Cost Tracking:**
   - Log tokens used (input_tokens, output_tokens)
   - Calculate cost per request ($3/MTok input, $15/MTok output)
   - Aggregate cost per job

7. **Error Handling:**
   - Retry on rate limit (RateLimitError)
   - Retry on server error (APIError)
   - Exponential backoff
   - Timeout handling (APITimeoutError)

---

## Usage Example

```python
client = AnthropicClient()

# Text generation
response = await client.messages_create(
    messages=[{"role": "user", "content": "..."}],
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    system="You are a helpful assistant."
)

# Vision analysis
response = await client.vision_completion(
    image_bytes=image_data,
    prompt="Classify this image",
    model="claude-sonnet-4-5-20250929"
)
```

---

## Key Differences from OpenAI

| Feature | OpenAI | Anthropic |
|---------|--------|-----------|
| System message | In messages array | Separate `system` parameter |
| Vision format | image_url with data URL | image source object with base64 |
| Response access | choices[0].message.content | content[0].text |
| JSON mode | response_format parameter | Instruct in prompt |

---

## QA Pair: QA-ANTHROPIC-001

---

**Begin execution.**
