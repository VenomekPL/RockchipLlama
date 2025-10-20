# Current Model Status

**Last Updated:** October 20, 2025

## Working Models ✅

### Qwen3-0.6B (RECOMMENDED)
**File:** `Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm`
- **Friendly Name:** `qwen3-0.6b`
- **Performance:** 15.59 tokens/sec
- **Context:** 16K (16384 tokens)
- **Memory:** 890 MB
- **TTFT:** ~200ms
- **Quality:** ✅ EXCELLENT - Coherent, accurate, follows instructions
- **Status:** PRODUCTION READY
- **Benchmark:** `benchmarks/benchmark_report_qwen3_0.6b.md`

### Gemma3-1B
**File:** `gemma-3-1b-it_w8a8.rkllm`
- **Friendly Name:** `gemma3-1b`
- **Performance:** 13.50 tokens/sec
- **Context:** 4K (4096 tokens) ⚠️
- **Memory:** 1243 MB
- **TTFT:** ~150ms
- **Quality:** ✅ GOOD - Coherent responses, verbose style
- **Status:** USABLE (needs 16K reconversion)
- **Benchmark:** `benchmarks/benchmark_report_gemma3_1b.md`
- **Note:** Hit 4K context limit in 2/10 tests, needs reconversion with --ctx 16384

## Removed Models ❌

### Gemma3-270m (REMOVED)
**File:** ~~`google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm`~~ (deleted)
- **Friendly Name:** ~~`gemma3-270m`~~
- **Performance:** 29.80 tokens/sec (meaningless)
- **Context:** 16K (16384 tokens)
- **Memory:** 602 MB
- **TTFT:** 85ms
- **Quality:** ❌ COMPLETELY BROKEN
- **Status:** REMOVED FROM PRODUCTION
- **Reason:** 
  - Infinite repetition loops
  - Degrades into word salad
  - 0/10 tests produced usable output
  - Poor w8a8 quantization/conversion
- **Documentation:** `docs/MODEL_QUALITY_GEMMA3_270M_FAILURE.md`
- **Benchmarks:** Moved to `benchmarks/removed/`

## Model Selection Guide

### For Production Use
**USE:** `qwen3-0.6b`
- Best balance of quality and speed
- Reliable, coherent output
- Full 16K context support
- Proven in all benchmark tests

### For Experimentation
**USE:** `gemma3-1b`
- Good quality output
- Verbose responses (3x more tokens than Qwen3)
- Needs reconversion for full 16K context
- Currently limited to 4K context

### Avoid
**DO NOT USE:** ~~`gemma3-270m`~~
- Model removed from repository
- Produces garbage output despite fast speed
- Not suitable for RK3588 NPU w8a8 conversion

## Recommendations

### Immediate Actions
1. ✅ Use `qwen3-0.6b` for all production workloads
2. ⏳ Reconvert `gemma3-1b` with `--ctx 16384` for consistency
3. ❌ Do not attempt to use gemma3-270m

### Future Model Additions
When adding new models:
1. Always run quality benchmarks, not just performance metrics
2. Validate output coherence on multiple test cases
3. Check for repetition loops and degradation
4. Test with the actual inference parameters you'll use in production
5. Document quality issues immediately if found

## Summary

| Model | Speed | Context | Memory | Quality | Status |
|-------|-------|---------|--------|---------|--------|
| **qwen3-0.6b** | 15.59 tok/s | 16K | 890 MB | ✅ Excellent | **RECOMMENDED** |
| **gemma3-1b** | 13.50 tok/s | 4K | 1243 MB | ✅ Good | Usable (needs fix) |
| ~~gemma3-270m~~ | ~~29.80 tok/s~~ | ~~16K~~ | ~~602 MB~~ | ❌ Broken | **REMOVED** |

**Bottom Line:** Speed means nothing if the output is garbage. Quality > Speed.
