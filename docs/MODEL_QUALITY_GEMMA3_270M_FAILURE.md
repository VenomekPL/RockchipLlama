# Model Quality Assessment - Gemma3-270m

**Date:** October 20, 2025  
**Model:** google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm  
**Status:** ❌ **FAILED - UNUSABLE**

## Performance Metrics

- **Speed:** 29.80 tokens/sec (excellent)
- **Memory:** 602 MB (efficient)
- **TTFT:** 85.67ms (very fast)

## Quality Assessment: ❌ FAILED

Despite excellent performance metrics, **output quality is completely broken**.

### Critical Issues

1. **Repetition Loop**
   - Model gets stuck repeating the same phrase endlessly
   - Example: Repeats "artificial intelligence and machine learning are revolutionizing..." 20+ times

2. **Degradation into Word Salad**
   - Coherent text breaks down into nonsensical fragments
   - "Machine Learning Machine Learning Machine Machine Machine..."
   - Capitalization becomes random

3. **Zero Task Completion**
   - Cannot complete simple prompts
   - No coherent responses in any test
   - 0/10 tests produced usable output

### Example Output (Test 1)

**Prompt:** "Artificial intelligence and machine learning are revolutionizing how we approach complex problems, but their impact on"

**Output:** Repeats the input 20+ times, then degrades to:
```
machine learning are not only for artificial intelligence are not only for artificial 
intelligence and machine learning but also for artificial intelligence are not only 
for machine learning is not only for artificial intelligence is also for machine learning 
is not only for artificial intelligence is not only for artificial intelligence is also 
is machine learning and artificial problems are also and machine are are not only but 
also Artificial intelligence is also Artificial intelligence Artificial and machine 
learning Artificial and Machine learning are also Artificial and Machine learning are 
Artificial and Machine Learning Artificial Machine Learning Machine Learning Machine 
Learning Machine Learning Machine Learning Machine Learning Machine Learning Machine 
Learning Machine Machine Machine Machine Machine Machine Machine Machine Machine
```

## Root Cause Analysis

**Likely Issues:**
1. **Poor model conversion** - Quantization errors in w8a8 process
2. **Broken sampling parameters** - Repeat penalty not working
3. **Model architecture incompatibility** - Gemma-3-270m may not be well-suited for RK3588 NPU
4. **Training issues** - Base model may have quality problems

## Attempted Solutions

✅ Tried user's optimized parameters:
- top_k: 20
- top_p: 0.95
- temperature: 0.6
- repeat_penalty: 0.9

❌ Result: No improvement, still produces garbage output

## Recommendation

**DO NOT USE THIS MODEL**

- Speed metrics are meaningless when output is unusable
- Wasting NPU cycles on repetitive garbage
- Better to use slower models with coherent output

## Comparison with Working Models

| Model | Speed | Quality | Verdict |
|-------|-------|---------|---------|
| **Gemma3-270m** | 29.80 tok/s | ❌ BROKEN | **REMOVE** |
| **Qwen3-0.6B** | 15.59 tok/s | ✅ EXCELLENT | **USE THIS** |
| **Gemma3-1B** | 13.50 tok/s | ✅ GOOD | **USE THIS** |

## Action Taken

**Model Status:** REMOVED  
**Date:** October 20, 2025  
**Reason:** Produces completely unusable output despite good performance metrics

---

## Lessons Learned

1. **Speed ≠ Quality**: Fast token generation is worthless if tokens are garbage
2. **Always test quality**: Benchmark metrics must include output validation
3. **Model conversion matters**: Some models don't convert well to NPU w8a8
4. **Trust benchmarks**: Real-world testing reveals issues metrics can't show

## Alternative Recommendations

For users seeking fast inference:
1. **Stick with Qwen3-0.6B** - 15.59 tok/s with excellent quality
2. **Use Gemma3-1B** - 13.50 tok/s with good quality (reconvert to 16K)
3. **Wait for better 270m models** - This specific conversion is broken
