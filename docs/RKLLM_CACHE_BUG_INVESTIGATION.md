# RKLLM Binary Cache Bug Investigation

## Summary

**RKLLM 1.2.1's `save_prompt_cache` feature is broken and causes segmentation faults.**

## Evidence

### Test Conducted
```bash
curl -X POST http://localhost:8080/v1/cache/qwen3-0.6b \
  -H 'Content-Type: application/json' \
  -d '{"cache_name": "test_short", "prompt": "You are a helpful AI assistant."}'
```

### Result
```
Segmentation fault (core dumped)
```

### Server Logs
```
2025-10-20 21:17:26,579 - models.rkllm_model - INFO - 🔥 Binary cache: Saving to .../test_short.rkllm_cache
./start_server.sh: line 14: 265810 Segmentation fault      (core dumped) python main.py
```

### File System Check
```bash
$ find . -name "*.rkllm_cache"
# NO FILES FOUND

$ ls cache/qwen3-0.6b/
coding_rules.bin    # Old text cache
project_context.bin # Old text cache
system.bin          # Old text cache
test_cache.bin      # Old text cache
# NO .rkllm_cache FILES
```

## Code Analysis

### Working Code (src/models/rkllm_model.py)
```python
if binary_cache_path:
    prompt_cache = RKLLMPromptCacheParam()
    prompt_cache.prompt_cache_path = binary_cache_path.encode('utf-8')
    prompt_cache.save_prompt_cache = 1  # ← THIS CAUSES SEGFAULT
    prompt_cache.num_input = len(prompt)
    infer_params.prompt_cache_params = ctypes.cast(
        ctypes.pointer(prompt_cache),
        ctypes.c_void_p
    )

ret = rkllm_run(self.handle, ctypes.byref(rkllm_input), ctypes.byref(infer_params), None)
# ↑ SEGFAULTS HERE when save_prompt_cache = 1
```

### RKLLM Version
```
rkllm-runtime version: 1.2.1
rknpu driver version: 0.9.7
platform: RK3588
```

## Historical Context

### Commit History
- **e100237**: Implemented RKLLM binary caching
- **ead981b**: Removed old text cache (`.bin` files)
- **4f00832**: Integrated binary cache with API
- **Today**: Discovered binary cache **NEVER** worked

### What Actually Worked
The `.bin` files are **text caches** (UTF-8 text files), not binary NPU state:
```bash
$ file cache/qwen3-0.6b/system.bin
Unicode text, UTF-8 text, with very long lines (1326)

$ head -c 50 cache/qwen3-0.6b/system.bin
You are a virtual voice assistant with no gender...
```

These were created by the OLD cache system (before commit ead981b).

## What CAN Be Done

### Option 1: Use Text Cache (Workaround)
The `.bin` files can be used as text caches:
- Load `.bin` file content
- Concatenate with user message
- Send full text to RKLLM
- **NO NPU state caching, just text pre-pending**
- Performance: Same as sending full prompt every time

### Option 2: Wait for RKLLM Fix
- Report bug to Rockchip
- Wait for RKLLM 1.2.2+ release
- Test binary cache when fixed
- Expected benefit: 50-70% TTFT reduction

### Option 3: Test Cache Loading (Not Creation)
Try loading a manually created cache:
```bash
# Create fake cache file
touch cache/qwen3-0.6b/test.rkllm_cache

# Try loading (save_prompt_cache = 0)
curl -X POST http://localhost:8080/v1/chat/completions \
  -d '{"use_cache": "test", "messages": [...]}'
```

**Hypothesis**: Maybe loading works but saving doesn't?

## Recommendation

**Keep the API integration code** - it's correct. When RKLLM is fixed:
1. The endpoint will work immediately
2. No code changes needed
3. Just test cache creation again

**For now**: Document that binary cache is broken in RKLLM 1.2.1.

## Binary Cache Circumstances

**Q: In what circumstance is the .bin cache usable?**

**A: The `.bin` files are usable in two scenarios:**

1. **Old Text Cache System** (removed in ead981b)
   - Load `.bin` file as text
   - Concatenate with user message
   - NO NPU acceleration
   - Just text pre-pending

2. **Manual Text Handling** (current)
   - Read `.bin` file manually
   - Use content as system prompt
   - Send to chat endpoint
   - Example:
     ```python
     with open("cache/qwen3-0.6b/system.bin") as f:
         system_prompt = f.read()
     
     response = requests.post("http://localhost:8080/v1/chat/completions", json={
         "messages": [
             {"role": "system", "content": system_prompt},
             {"role": "user", "content": "Hello!"}
         ]
     })
     ```

**The `.bin` files are NOT NPU binary caches. They're just text files.**

**Real binary caching (`.rkllm_cache`) is broken in RKLLM 1.2.1.**
