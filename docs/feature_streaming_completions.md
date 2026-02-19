# Feature: Streaming Text Completions

## Overview

Streaming text completions allows the `/v1/completions` endpoint to return tokens incrementally via Server-Sent Events (SSE), matching the behavior already implemented for `/v1/chat/completions`. This provides real-time response delivery for text completion use cases, reducing perceived latency for end users.

## Current Status

**Stub Only** — The streaming path explicitly raises a 501 error.

In `src/api/openai_routes.py`:

```python
if request.stream:
    raise HTTPException(
        status_code=501,
        detail="Streaming not yet implemented for text completions..."
    )
```

**What already works:**
- Non-streaming text completions (`POST /v1/completions` with `stream: false`) work correctly.
- Streaming chat completions (`POST /v1/chat/completions` with `stream: true`) work correctly with full SSE support.
- The underlying RKLLM inference engine supports streaming via the callback mechanism regardless of whether chat or text completion is being performed.

## rknn-llm Reference

The rknn-llm server demo (`flask_server.py`) implements streaming for all inference types using the same callback pattern:

```python
# From flask_server.py - streaming generate function
def generate():
    model_thread = threading.Thread(target=rkllm_model.run, args=(role, enable_thinking, input_prompt))
    model_thread.start()

    model_thread_finished = False
    while not model_thread_finished:
        while len(global_text) > 0:
            rkllm_output = global_text.pop(0)
            rkllm_responses["choices"].append({
                "delta": {"role": "assistant", "content": rkllm_output[-1]},
                "finish_reason": "stop" if global_state == 1 else None,
            })
            yield f"{json.dumps(rkllm_responses)}\n\n"
        model_thread.join(timeout=0.005)
        model_thread_finished = not model_thread.is_alive()

return Response(generate(), content_type='text/plain')
```

## Implementation Plan

### Step 1: Reuse Existing Streaming Infrastructure

The streaming chat completion in `openai_routes.py` already has a complete SSE streaming implementation. The text completion streaming can reuse the same pattern:

```python
# Existing chat streaming pattern (in openai_routes.py):
async def stream_response(prompt, model, request_id, ...):
    # 1. Acquire batch semaphore
    # 2. Start inference with streaming callback
    # 3. Yield SSE chunks as tokens arrive
    # 4. Yield final chunk with usage stats
    # 5. Yield [DONE] sentinel
```

### Step 2: Implement Streaming for `/v1/completions`

Replace the 501 stub with a streaming generator:

```python
@router.post("/v1/completions")
async def create_completion(request: CompletionRequest):
    if request.stream:
        return StreamingResponse(
            stream_text_completion(request),
            media_type="text/event-stream"
        )
    # ... existing non-streaming logic ...

async def stream_text_completion(request):
    request_id = f"cmpl-{uuid4().hex[:12]}"
    prompt = request.prompt

    async for token in model_instance.generate_stream(prompt, ...):
        chunk = {
            "id": request_id,
            "object": "text_completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "text": token,
                "logprobs": None,
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(chunk)}\n\n"

    # Final chunk with finish_reason
    final_chunk = {
        "id": request_id,
        "object": "text_completion",
        "choices": [{"index": 0, "text": "", "finish_reason": "stop"}],
        "usage": { ... }
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"
```

### Step 3: Ensure SSE Format Consistency

The text completion SSE format differs slightly from chat completion:

| Field | Chat Completion | Text Completion |
|-------|----------------|-----------------|
| object | `chat.completion.chunk` | `text_completion` |
| choices[].delta | `{"content": "token"}` | N/A |
| choices[].text | N/A | `"token"` |

### Step 4: Add Stop Sequence Support in Streaming

Ensure stop sequences work correctly in streaming mode by checking each accumulated token against the stop list.

## Goals

1. Full SSE streaming support for `/v1/completions` endpoint.
2. Response format matches OpenAI text completion streaming specification.
3. Stop sequences work correctly in streaming mode.
4. Usage statistics included in the final streaming chunk.
5. Performance parity with streaming chat completions.

## Definition of Done

- [ ] `POST /v1/completions` with `stream: true` returns SSE chunks.
- [ ] Each chunk has `object: "text_completion"` and `choices[].text` field.
- [ ] Final chunk includes `finish_reason: "stop"` (or `"length"`).
- [ ] Usage statistics (prompt_tokens, completion_tokens) in final chunk.
- [ ] Stop sequences correctly terminate streaming.
- [ ] `max_tokens` limit correctly terminates streaming.
- [ ] `[DONE]` sentinel sent at end of stream.
- [ ] Error handling during streaming (model errors, timeouts).
- [ ] Compatible with OpenAI Python client's streaming mode.

## Test Approach

### Unit Tests

- Test SSE chunk format matches OpenAI spec.
- Test stop sequence detection in streaming tokens.
- Test `max_tokens` limit in streaming mode.

### Integration Tests

- Stream a text completion and verify all chunks arrive.
- Verify final chunk has correct finish_reason and usage stats.
- Compare streaming vs non-streaming output for the same prompt (should be identical content).
- Test with OpenAI Python client in streaming mode.

### Manual Testing

```bash
# Test streaming text completion
curl -X POST http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-0.6b",
    "prompt": "Once upon a time",
    "max_tokens": 50,
    "stream": true
  }'

# Test with Python OpenAI client
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8080/v1", api_key="not-needed")
stream = client.completions.create(
    model="qwen3-0.6b",
    prompt="The quick brown fox",
    max_tokens=50,
    stream=True
)
for chunk in stream:
    print(chunk.choices[0].text, end="", flush=True)
```

## References

- [OpenAI Completions API - Streaming](https://platform.openai.com/docs/api-reference/completions/create#completions-create-stream)
- Existing chat streaming implementation: `src/api/openai_routes.py` (streaming chat completions section)
- RKLLM callback pattern: `src/models/rkllm_model.py` (`streaming_callback` function)
- rknn-llm streaming example: `external/rknn-llm/examples/rkllm_server_demo/rkllm_server/flask_server.py` (lines ~530-560)
