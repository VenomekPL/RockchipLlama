# CRITICAL BUG FIX - RKLLMPromptCacheParam Structure

## Issue

Binary cache creation was **FAILING with segfault** due to incorrect structure definition.

## Root Cause

Our `RKLLMPromptCacheParam` structure had:
1. **Wrong field order**
2. **Extra field that doesn't exist**

### Our (Wrong) Structure
```python
class RKLLMPromptCacheParam(ctypes.Structure):
    _fields_ = [
        ("prompt_cache_path", ctypes.c_char_p),  # WRONG: This should be second
        ("save_prompt_cache", ctypes.c_int),     # WRONG: This should be first
        ("num_input", ctypes.c_int)              # WRONG: This field doesn't exist!
    ]
```

### Official RKLLM Structure (from rkllm.h)
```c
typedef struct {
    int save_prompt_cache;          // FIRST field
    const char* prompt_cache_path;  // SECOND field
} RKLLMPromptCacheParam;
```

## Fix

Corrected to match official header:

```python
class RKLLMPromptCacheParam(ctypes.Structure):
    _fields_ = [
        ("save_prompt_cache", ctypes.c_int),     # 1=save, 0=load (FIRST!)
        ("prompt_cache_path", ctypes.c_char_p)   # Path to cache file (SECOND!)
    ]
```

## Results

### Before Fix
- ❌ Segmentation fault when creating cache
- ❌ No `.rkllm_cache` files created
- ❌ TTFT: ~1775ms (no caching possible)

### After Fix
- ✅ Cache creation successful: `system.rkllm_cache` (33 MB)
- ✅ Cache loading successful
- ✅ TTFT: **75.2ms** (23.5x faster!)

## Performance Comparison

### Test: 1326-char system prompt + "Hello, how are you?"

| Method | TTFT | Improvement |
|--------|------|-------------|
| Without cache | 1775ms | baseline |
| With cache | 75.2ms | **95.8% faster** |

**Speedup: 23.5x**

## How to Use

### Create Cache
```bash
curl -X POST http://localhost:8080/v1/cache/qwen3-0.6b \
  -H 'Content-Type: application/json' \
  -d '{
    "cache_name": "system",
    "prompt": "You are a helpful AI assistant..."
  }'
```

Response:
```json
{
  "object": "cache.created",
  "cache_name": "system",
  "size_mb": 32.42,
  "ttft_ms": 669.98,
  "message": "Binary cache generated successfully"
}
```

### Use Cache
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -d '{
    "use_cache": "system",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

Response includes cache confirmation:
```json
{
  "usage": {
    "cache_hit": true,
    "cached_prompts": ["system"]
  }
}
```

## Lessons Learned

1. **Always match official C structures exactly**
   - Field order matters in ctypes!
   - Don't add extra fields
   
2. **Check official examples**
   - `/external/rknn-llm/examples/` has working code
   - Compare with official headers in `rkllm-runtime/`

3. **Structure mismatch causes memory corruption**
   - Segfaults
   - Silent failures
   - Unpredictable behavior

## References

- Official header: `/external/rknn-llm/rkllm-runtime/Linux/librkllm_api/include/rkllm.h`
- Working example: `/external/rknn-llm/examples/rkllm_server_demo/rkllm_server/gradio_server.py`
- C++ example: `/external/rknn-llm/examples/rkllm_api_demo/deploy/src/llm_demo.cpp`
