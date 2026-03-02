# Agent Brief: QA-ANTHROPIC-001

**Agent ID:** QA-ANTHROPIC-001
**Agent Name:** Anthropic Integration QA
**Type:** QA
**Phase:** 5 - Integrations
**Paired Dev Agent:** DEV-ANTHROPIC-001

---

## Validation Checklist

- [ ] API key loaded from Secret Manager
- [ ] Claude Sonnet 4.5 text requests work
- [ ] Claude Sonnet 4.5 vision requests work
- [ ] Token counting accurate (input_tokens, output_tokens)
- [ ] Cost tracking accurate ($3/MTok input, $15/MTok output)
- [ ] Rate limit retry works (RateLimitError)
- [ ] Server error retry works (APIError)
- [ ] Timeout handling works (APITimeoutError)
- [ ] Model selection works (future-proof for Haiku/Opus)
- [ ] Temperature control works
- [ ] System prompt as separate parameter (not in messages)

---

## Test Cases

1. Simple message completion
2. Multi-turn conversation
3. System prompt injection (separate parameter)
4. Vision with base64 image
5. Vision with multiple images
6. Token pre-counting for images (pixels/750)
7. Handle rate limit (mock RateLimitError)
8. Handle server error (mock APIError)
9. Timeout scenario (APITimeoutError)
10. Cost calculation verification
11. Different model selection
12. Max tokens enforcement
13. Media type detection for images

---

## Token Counting Tests

- Short prompt accurate
- Long prompt accurate
- Image tokens estimated (pixels/750)
- Multilingual token count
- Response usage tracking (response.usage)

---

## Cost Tracking Tests

- Claude Sonnet 4.5 input pricing correct ($3/MTok)
- Claude Sonnet 4.5 output pricing correct ($15/MTok)
- Vision pricing correct
- Aggregate cost matches per job

---

## Anthropic-Specific Tests

- System message NOT in messages array (separate parameter)
- Vision uses image source object (not data URL)
- Response accessed via content[0].text (not choices[0])
- JSON output via prompt instruction (no response_format)

---

## Security Tests

- API key not logged
- API key not exposed in errors
- Requests use HTTPS
- AsyncAnthropic client properly initialized

---

**Begin review.**
