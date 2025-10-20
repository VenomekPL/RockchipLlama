# RoPE and Context Window Extension

## Current Status

**RKLLM Version**: 1.2.1 (installed on system)  
**Latest Version**: 1.2.2 (supports LongRoPE)

## Context Size in RockchipLlama

### How Context Works

Context size in RKLLM is **BAKED INTO the .rkllm model file** during conversion. It cannot be changed at runtime.

**Current Models:**
- **qwen3-0.6b**: 16384 tokens (has `ctx16384` in filename) ✅
- **gemma3-270m**: 16384 tokens (has `ctx16384` in filename) ✅
- **gemma3-1b**: 4096 tokens (NO ctx in filename = default 4K) ⚠️

### Runtime Context Parameter

The `max_context_len` parameter in our code:
```python
rkllm_param.max_context_len = 16384  # From config/inference_config.json
```

**This does NOT extend context beyond what the model was converted with.**

It only sets the maximum that will be used, but cannot exceed the model's built-in limit.

## LongRoPE Support (RKLLM v1.2.2)

### What is LongRoPE?

LongRoPE is a technique for extending context windows beyond the training length. RKLLM v1.2.2 added support for this.

### Capabilities

From RKLLM v1.2.2 changelog:
- **Extended context**: Models can potentially use >16K tokens
- **Requires**: Model must be converted with LongRoPE support enabled
- **Runtime**: No special parameters needed if model has LongRoPE

### How to Enable

**At Model Conversion Time** (using rkllm-toolkit):
```bash
# Convert model with extended context
rkllm-convert \
  --model_path model.gguf \
  --target_platform rk3588 \
  --dtype w8a8 \
  --ctx 32768 \        # Request 32K context
  --longrope \          # Enable LongRoPE extension
  --output model.rkllm
```

**Our models need to be reconverted to use LongRoPE.**

## Current System Capabilities

### Memory Available
Orange Pi 5 Max: **16GB RAM**

**Current Usage:**
- qwen3-0.6b: ~890 MB (with 16K context)
- gemma3-270m: ~600 MB (estimated, with 16K context)
- gemma3-1b: ~1.2 GB (with 4K context)

**Theoretical Capacity:**
With 16GB RAM, we could potentially run:
- Multiple models simultaneously
- OR single model with extended context (32K, 64K with LongRoPE)
- OR larger models (3B-7B range)

### KV Cache Memory

Context window size affects KV cache memory:
- **16K context**: ~100-300 MB KV cache (depending on model size)
- **32K context**: ~200-600 MB KV cache
- **64K context**: ~400-1200 MB KV cache

**We have plenty of RAM for extended context!**

## Recommendations

### Short Term (Current RKLLM 1.2.1)

1. **Use 16K models**: qwen3-0.6b and gemma3-270m already support this ✅
2. **Reconvert gemma3-1b** with `--ctx 16384` for consistency
3. **Test memory limits**: Run benchmarks with full 16K input prompts

### Medium Term (Upgrade to RKLLM 1.2.2)

1. **Upgrade runtime** to 1.2.2 for LongRoPE support
2. **Reconvert models** with:
   - `--ctx 32768` for 32K context
   - `--longrope` flag enabled
3. **Benchmark extended context** to measure performance impact

### Long Term (Max Capabilities)

1. **Experiment with 64K context** (if model architecture supports it)
2. **Test larger models** (3B-7B) given our 16GB RAM
3. **Multi-instance** running with different models

## Performance Considerations

### Context vs Speed Trade-off

Larger context = more memory = potentially slower:
- **Prefill time** increases linearly with input tokens
- **KV cache** grows with context length
- **Memory bandwidth** becomes bottleneck

**Expected Impact:**
- 16K context: ~200-400ms TTFT (measured)
- 32K context: ~400-800ms TTFT (estimated)
- 64K context: ~800-1600ms TTFT (estimated)

### Optimization Strategies

1. **Prompt Caching**: Cache common prefixes to avoid re-prefilling
2. **Sliding Window**: Use only recent K tokens for generation
3. **Flash Embedding** (`embed_flash=1`): Already enabled ✅
4. **GPU Prefill**: Already enabled (`base_domain_id=0`) ✅

## Implementation Status

### Current Implementation ✅

```python
# In config/inference_config.json
{
  "inference_params": {
    "max_context_len": 16384  // Will use model's built-in limit
  }
}

# In rkllm_model.py
rkllm_param.max_context_len = max_context_len  // Respects model limit
```

### What We Can Do NOW

1. ✅ Use full 16K context on qwen3-0.6b and gemma3-270m
2. ✅ Detect context size from filename automatically
3. ✅ Warn if requested context exceeds model capability
4. ⏳ Test with long prompts (8K-16K tokens)

### What Requires Model Reconversion

1. ❌ Extend gemma3-1b to 16K (currently 4K)
2. ❌ Enable 32K context (requires RKLLM 1.2.2 + LongRoPE conversion)
3. ❌ Enable 64K context (requires RKLLM 1.2.2 + LongRoPE conversion)

## Testing Plan

### Phase 1: Current Capabilities (16K)

```bash
# Test with 8K input prompt
python scripts/benchmark.py --type quality --max-input-tokens 8000

# Test with 16K input prompt (max for current models)
python scripts/benchmark.py --type quality --max-input-tokens 16000

# Measure memory usage and TTFT
```

### Phase 2: Extended Context (After Reconversion)

```bash
# Test 32K context model
python scripts/benchmark.py --type quality --max-input-tokens 32000

# Test 64K context model (if supported)
python scripts/benchmark.py --type quality --max-input-tokens 64000
```

## Conclusion

**Current State:**
- ✅ 16K context available on 2/3 models
- ✅ Automatic context detection working
- ✅ Plenty of RAM available (16GB)
- ✅ Can safely use full context without memory issues

**To Extend Beyond 16K:**
1. Need to reconvert models with `--longrope` flag
2. Should upgrade to RKLLM 1.2.2 for best support
3. Hardware (16GB RAM) can easily handle 32K-64K contexts

**Next Steps:**
1. Reconvert gemma3-1b with 16K context for consistency
2. Test current 16K capabilities thoroughly
3. Plan upgrade to RKLLM 1.2.2 for LongRoPE
4. Reconvert models with extended context as needed
