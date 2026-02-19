# Feature: Pause/Resume Inference Callback

## Overview

The pause/resume inference feature allows the server to interrupt an ongoing inference, modify the context (e.g., inject new tokens, edit output, perform KV cache surgery), and then resume generation. This is essential for advanced use cases like guided generation, output filtering, dynamic prompt injection, and function calling mid-stream.

## Current Status

**Disabled** — Code scaffolding exists but the functionality is disabled due to crashes.

In `src/models/rkllm_model.py`:

```python
# In the callback function (approximately line 251-253):
# return 1 # DISABLED to debug crash
pass
```

The RKLLM callback mechanism supports returning `1` to pause inference, but this caused crashes in practice and was disabled.

### Related RKLLM API

```c
// From rkllm.h (line 252-256):
// Callback return values:
// - 0: Continue inference normally
// - 1: Pause inference. User can modify/intervene in the result,
//       then call rkllm_run with updated content to resume.

typedef int(*LLMResultCallback)(RKLLMResult* result, void* userdata, LLMCallState state);
```

### KV Cache Control (Companion Feature)

```c
// Clear part or all of the KV cache
// start_pos/end_pos: only valid when keep_history == 0 and generation
//                    has been paused by returning 1 in the callback
int rkllm_clear_kv_cache(LLMHandle handle, int keep_system_prompt,
                          int* start_pos, int* end_pos);

// Get current KV cache size (per-batch)
int rkllm_get_kv_cache_size(LLMHandle handle, int* cache_sizes);
```

## rknn-llm Reference

The rknn-llm C API (v1.2.1+) documents the pause mechanism:

1. **Pause**: Return `1` from the `LLMResultCallback` to suspend inference.
2. **Modify**: While paused, optionally clear/modify KV cache via `rkllm_clear_kv_cache()`.
3. **Resume**: Call `rkllm_run()` again with updated input to continue generation.

### Reference from `rkllm.h`

```c
// Pause inference by returning 1 from callback
int my_callback(RKLLMResult* result, void* userdata, LLMCallState state) {
    if (should_pause(result->text)) {
        return 1;  // Pause inference
    }
    return 0;  // Continue normally
}

// After pausing, optionally manipulate KV cache
int start_pos[] = {10};  // Clear from position 10
int end_pos[] = {20};    // Clear to position 20
rkllm_clear_kv_cache(handle, 0, start_pos, end_pos);

// Resume with new input
RKLLMInput new_input;
new_input.input_type = RKLLM_INPUT_PROMPT;
new_input.prompt_input = "Continue with this context...";
rkllm_run(handle, &new_input, &infer_params, userdata);
```

## Implementation Plan

### Step 1: Investigate and Fix the Crash

The first priority is understanding why returning `1` from the callback causes a crash:

1. Enable RKLLM debug logging: `export RKLLM_LOG_LEVEL=1`
2. Test with a simple synchronous (non-async) inference to isolate the issue.
3. Check if the crash is related to:
   - Thread safety (callback running on a different thread).
   - Memory access after pause (result pointer becoming invalid).
   - Async mode incompatibility with pause.
   - KV cache state corruption.
4. Test with `is_async = False` to see if synchronous mode handles pause correctly.

### Step 2: Implement Safe Pause Mechanism

Once the crash is resolved, implement a thread-safe pause mechanism:

```python
class RKLLMModel:
    def __init__(self):
        self._pause_requested = threading.Event()
        self._pause_condition = None  # Callable that decides when to pause

    def _callback(self, result, userdata, state):
        if state == RKLLM_RUN_NORMAL:
            token = result.contents.text.decode('utf-8')
            # Check pause condition
            if self._pause_condition and self._pause_condition(token, self._accumulated_text):
                self._pause_requested.set()
                return 1  # Pause inference
        return 0  # Continue

    async def generate_with_pause(self, prompt, pause_condition=None):
        self._pause_condition = pause_condition
        self._pause_requested.clear()

        # Start inference
        await self._run_inference(prompt)

        if self._pause_requested.is_set():
            # Inference was paused - return partial result and control
            return {
                "status": "paused",
                "partial_output": self._accumulated_text,
                "can_resume": True
            }
```

### Step 3: Implement Stop Sequence via Pause

Use the pause mechanism to implement proper stop sequences:

```python
def stop_sequence_checker(token, accumulated_text):
    """Returns True if any stop sequence is found in accumulated text."""
    for stop in stop_sequences:
        if stop in accumulated_text:
            return True
    return False

# Use as pause condition
result = await model.generate_with_pause(prompt, pause_condition=stop_sequence_checker)
```

### Step 4: Expose KV Cache Control API

Add KV cache management methods to the RKLLM wrapper:

```python
def clear_kv_cache(self, keep_system_prompt=True, start_pos=None, end_pos=None):
    """Clear part or all of the KV cache."""
    c_start = (ctypes.c_int * len(start_pos))(*start_pos) if start_pos else None
    c_end = (ctypes.c_int * len(end_pos))(*end_pos) if end_pos else None
    return self._clear_kv_cache(self.handle, int(keep_system_prompt), c_start, c_end)

def get_kv_cache_size(self):
    """Get current KV cache size per batch."""
    sizes = (ctypes.c_int * self.n_batch)()
    self._get_kv_cache_size(self.handle, sizes)
    return list(sizes)
```

### Step 5: Add Admin Endpoints for KV Cache

Expose KV cache control via API endpoints:

```python
@router.get("/v1/cache/kv/size")
async def get_kv_cache_size():
    sizes = model_instance.get_kv_cache_size()
    return {"kv_cache_sizes": sizes}

@router.post("/v1/cache/kv/clear")
async def clear_kv_cache(keep_system_prompt: bool = True):
    model_instance.clear_kv_cache(keep_system_prompt=keep_system_prompt)
    return {"status": "cleared"}
```

## Goals

1. Working pause/resume mechanism that doesn't crash.
2. Stop sequence implementation using pause callback.
3. KV cache size monitoring and manual clearing.
4. Foundation for advanced features (guided generation, output filtering).

## Definition of Done

- [ ] Root cause of callback pause crash identified and documented.
- [ ] Returning `1` from callback successfully pauses inference without crash.
- [ ] Inference can be resumed after pause with new input.
- [ ] KV cache can be partially cleared while inference is paused.
- [ ] `rkllm_get_kv_cache_size()` bound and exposed via API.
- [ ] `rkllm_clear_kv_cache()` bound and exposed via API.
- [ ] Stop sequences work via pause mechanism (not just post-processing).
- [ ] Thread safety verified under concurrent requests.
- [ ] No memory leaks from pause/resume cycles.

## Test Approach

### Unit Tests

- Test callback returns `1` and inference pauses (mock RKLLM).
- Test KV cache size retrieval.
- Test KV cache clearing (full and partial range).
- Test stop sequence detection via pause condition.

### Integration Tests

- Pause inference mid-generation and verify partial output.
- Resume after pause and verify continuation is coherent.
- Clear KV cache range and verify output changes.
- Test concurrent pause/resume with multiple requests.

### Stress Tests

- Rapid pause/resume cycles to detect memory leaks.
- Pause at various points in generation (early, middle, near end).
- Test pause with different `n_batch` values.

### Manual Testing

```bash
# Test KV cache monitoring
curl http://localhost:8080/v1/cache/kv/size

# Test KV cache clearing
curl -X POST http://localhost:8080/v1/cache/kv/clear

# Test with debug logging
export RKLLM_LOG_LEVEL=1
./start_server.sh
# Send a request and observe pause/resume in logs
```

## References

- RKLLM Callback API: `external/rknn-llm/rkllm-runtime/Linux/librkllm_api/include/rkllm.h` (lines 246-257)
- KV Cache API: `external/rknn-llm/rkllm-runtime/Linux/librkllm_api/include/rkllm.h` (lines 338-364)
- Disabled pause code: `src/models/rkllm_model.py` (lines ~251-253)
- RKLLM SDK Documentation: `external/rknn-llm/doc/Rockchip_RKLLM_SDK_EN_1.2.3.pdf`
