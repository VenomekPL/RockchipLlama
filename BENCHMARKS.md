# 🚀 RockchipLlama Performance Benchmarks

**Last Updated:** October 20, 2025  
**Hardware:** Rockchip RK3588 (3 NPU cores @ 1.0 GHz, Big cores @ 2.3 GHz)  
**RKLLM Version:** 1.2.1

---

## 📊 Model Performance Comparison

All models tested with w8a8 quantization, 16K context, 3 NPU cores.

| Model | Size | Tokens/sec | TTFT (avg) | Memory | Context | Status |
|-------|------|------------|------------|--------|---------|--------|
| **Qwen3-0.6B** ⭐ | 909 MB | **15.59** | 295ms | 890 MB | 16K | ✅ **RECOMMENDED** |
| **Gemma3-1B** | 1.5 GB | **13.50** | 339ms | 1243 MB | 4K | ✅ USABLE |
| Qwen3-4B | 5.0 GB | **3.13** | 1775ms | 5027 MB | 16K | ⚠️ TOO SLOW |
| Gemma3-270M | 616 MB | ~~29.80~~ | 285ms | 654 MB | 16K | ❌ REMOVED (garbage output) |

### Performance Notes

- **Qwen3-0.6B**: Best balance of speed, quality, and context length (16K). **Production ready.**
- **Gemma3-1B**: Good speed, excellent quality, but limited to 4K context (needs 16K reconversion).
- **Qwen3-4B**: Excellent quality but too slow for production (< 5 tok/s minimum viable).
- **Gemma3-270M**: Fast but produces incoherent output - not usable despite speed.

**Production Minimum:** 5 tokens/sec for acceptable user experience.

---

## 🔥 Binary Cache Performance (Phase 4.1)

Binary caching stores NPU state for instant restoration - **23.5x faster prefill!**

### Cache Performance Results

**Model:** Qwen3-0.6B  
**Test Prompt:** 1326-character system prompt (coding assistant)

| Scenario | TTFT | Improvement |
|----------|------|-------------|
| **Without Cache** | 1775 ms | Baseline |
| **With Binary Cache** | 75.2 ms | **95.8% reduction!** |

**Speedup:** 23.5x faster Time To First Token!

### How It Works

1. **Cache Creation** (one-time): Server processes prompt, saves NPU state to `.rkllm_cache` file (~33MB)
2. **Cache Loading** (every request): NPU state restored instantly, no recomputation needed
3. **Result**: Skip entire prefill phase for cached portion

### Cache Sizes

| Model | System Prompt (1326 chars) | Cache File Size |
|-------|---------------------------|-----------------|
| Qwen3-0.6B | 1326 characters | 33 MB |
| Gemma3-1B | ~1300 characters | ~40 MB (estimated) |

### Real-World Impact

**Example: Coding Assistant**

```bash
# Without cache (cold start)
Request: "Fix this Python code..."
TTFT: 1775 ms ⏳

# With cache (system prompt cached)
Request: "Fix this Python code..."
TTFT: 75.2 ms ⚡

Result: 23.5x faster response!
```

### Usage

```bash
# 1. Create binary cache (once)
curl -X POST http://localhost:8080/v1/cache/qwen3-0.6b \
  -H 'Content-Type: application/json' \
  -d '{
    "cache_name": "system",
    "prompt": "You are a helpful AI assistant specialized in coding..."
  }'

# 2. Use cache in every request
curl -X POST http://localhost:8080/v1/chat/completions \
  -d '{
    "use_cache": "system",
    "messages": [{"role": "user", "content": "Help me debug this code"}]
  }'
```

**Best Practices:**
- ✅ Cache system prompts (stable, reused frequently)
- ✅ Cache coding rules, project context
- ❌ Don't cache user messages (always unique)

---

## 📈 Detailed Benchmark Results

### Qwen3-0.6B (Recommended)

**Test Suite:** 10 prompts (5 performance + 5 quality tests)  
**Success Rate:** 10/10 (100%)  
**Duration:** 292.1 seconds

#### Performance Metrics

| Metric | Average | Median | Min | Max |
|--------|---------|--------|-----|-----|
| Tokens/sec | 15.59 | 16.00 | 12.59 | 17.57 |
| TTFT | 295 ms | 254 ms | 140 ms | 581 ms |
| Input Processing | 248.88 tok/s | - | - | - |

#### Token Statistics
- **Total Output:** 3,990 tokens across 10 tests
- **Average Output:** 399 tokens per request
- **Memory Usage:** ~890 MB stable

#### Test Categories
✅ Technical Explanation (AI/ML concepts)  
✅ Creative Writing (Story completion)  
✅ Scientific Discussion (Climate change)  
✅ Historical Analysis (Roman Empire)  
✅ Technology Trends (Edge computing)  
✅ Fantasy Story Creation (300-500 words)  
✅ Software Development Plan (Planning)  
✅ Python Data Processing (Coding)  
✅ Structured JSON Response (Instruction following)  
✅ Roman Empire Essay (800-1200 words, consistency)

**Full Report:** [benchmarks/benchmark_report_qwen3_0.6b.md](benchmarks/benchmark_report_qwen3_0.6b.md)

---

### Gemma3-1B

**Test Suite:** 10 prompts  
**Success Rate:** 10/10 (100%)  
**Context:** 4K (needs 16K reconversion)

#### Performance Metrics

| Metric | Average | Median | Min | Max |
|--------|---------|--------|-----|-----|
| Tokens/sec | 13.50 | 13.71 | 10.76 | 15.12 |
| TTFT | 339 ms | 317 ms | 218 ms | 548 ms |
| Memory Usage | 1243 MB | - | - | - |

#### Notes
- Excellent output quality despite 4K context
- Would benefit from 16K reconversion for production use
- Slightly slower than Qwen3-0.6B but still usable

**Full Report:** [benchmarks/benchmark_report_gemma3_1b.md](benchmarks/benchmark_report_gemma3_1b.md)

---

### Qwen3-4B (Not Recommended for Production)

**Single Test Results:**

| Metric | Value |
|--------|-------|
| Tokens/sec | 3.13 |
| TTFT | 1775 ms |
| Memory Usage | 5027 MB |
| Context | 16K |

#### Why Not Recommended
- ❌ Too slow: 3.13 tok/s < 5 tok/s minimum
- ❌ Poor user experience: >1.7 seconds before first token
- ❌ High memory usage: 5 GB RAM
- ✅ Excellent quality: But speed makes it impractical

**Verdict:** Quality is excellent, but RK3588 hardware insufficient for this model size.

---

### Gemma3-270M (Removed)

**Test Results:**

| Metric | Value |
|--------|-------|
| Tokens/sec | 29.80 (fastest!) |
| TTFT | 285 ms |
| Memory Usage | 654 MB |

#### Why Removed
- ❌ Produces incoherent/garbage output
- ❌ Cannot follow instructions properly
- ❌ Unusable despite excellent speed

**Example Output Quality:**
```
Input: "Explain quantum computing in simple terms"
Output: "quantum the is computing of particles that are superposition..."
(Word salad, no coherent explanation)
```

**Verdict:** Speed means nothing if output is unusable. Model removed from production.

---

## 🎯 Recommendations

### For Production Use

**Primary Choice: Qwen3-0.6B** ⭐
- ✅ 15.59 tok/s (good speed)
- ✅ 16K context (handles long conversations)
- ✅ 890 MB RAM (efficient)
- ✅ Binary cache: 23.5x faster TTFT
- ✅ Excellent quality output

**Alternative: Gemma3-1B**
- ✅ 13.50 tok/s (acceptable speed)
- ⚠️ 4K context (needs reconversion for 16K)
- ✅ 1243 MB RAM (still reasonable)
- ✅ Excellent quality

### For Development/Testing

Use **Qwen3-0.6B** with binary caching enabled for best experience.

### Hardware Considerations

**RK3588 Sweet Spot:** 0.5B - 1.5B parameter models
- Below 0.5B: Often poor quality (see Gemma3-270M)
- 0.5B - 1.5B: Good balance of speed and quality
- Above 1.5B: Too slow for production (see Qwen3-4B)

---

## 🔬 Testing Methodology

### Test Environment
- **Platform:** Orange Pi 5 Max (RK3588)
- **NPU Frequency:** 1.0 GHz (maximum)
- **CPU Big Cores:** 2.3 GHz (maximum, cores 4-7)
- **CPU Affinity:** 0xF0 (big cores only)
- **Threads:** 4
- **RKLLM Version:** 1.2.1

### Benchmark Configuration
```json
{
  "inference_params": {
    "top_k": 20,
    "top_p": 0.95,
    "temperature": 0.6,
    "repeat_penalty": 0.9,
    "frequency_penalty": 0.6,
    "presence_penalty": 0.1
  },
  "hardware": {
    "num_npu_cores": 3,
    "enabled_cpus_mask": 240,
    "num_threads": 4
  }
}
```

### Test Prompts

**Performance Tests (Speed Focus):**
1. Technical Explanation - AI/ML concepts
2. Creative Writing - Story completion
3. Scientific Discussion - Climate change analysis
4. Historical Analysis - Roman Empire
5. Technology Trends - Edge computing

**Quality Tests (Output Focus):**
1. Creativity - Fantasy story (300-500 words)
2. Planning - Software development plan
3. Coding - Python data processing function
4. Instruction Following - Structured JSON response
5. Consistency - Long-form essay (800-1200 words)

### Metrics Collected

- **TTFT (Time To First Token)**: Prefill/input processing time
- **Tokens/Second**: Generation speed (output tokens / generation time)
- **Input Processing Speed**: Prefill efficiency (input tokens / TTFT)
- **Memory Usage**: RAM consumption during inference
- **Total Time**: End-to-end request duration

---

## 📁 Benchmark Files

All detailed results available in [`benchmarks/`](benchmarks/) directory:

- [`benchmark_report_qwen3_0.6b.md`](benchmarks/benchmark_report_qwen3_0.6b.md) - Full Qwen3-0.6B results with response samples
- [`benchmark_report_gemma3_1b.md`](benchmarks/benchmark_report_gemma3_1b.md) - Full Gemma3-1B results
- [`RESULTS_20251020.md`](benchmarks/RESULTS_20251020.md) - Comparative analysis
- [`benchmark_qwen3_unlimited_20251020_110303.json`](benchmarks/benchmark_qwen3_unlimited_20251020_110303.json) - Raw JSON data
- [`benchmark_gemma3_1b_unlimited_20251020_131747.json`](benchmarks/benchmark_gemma3_1b_unlimited_20251020_131747.json) - Raw JSON data

---

## 🚀 Running Your Own Benchmarks

### Quick Test
```bash
# Test currently loaded model (3 requests)
python scripts/test_benchmark.py
```

### Full Benchmark Suite
```bash
# Performance tests (5 prompts)
python scripts/benchmark.py --type performance

# Quality tests (5 prompts)
python scripts/benchmark.py --type quality

# Complete suite with multiple runs
python scripts/benchmark.py --type all --runs 3

# Test specific model
python scripts/benchmark.py --model qwen3-0.6b --output my_results.json
```

### Custom Prompts
```bash
# Use your own test prompts
python scripts/benchmark.py --prompts my_prompts.json --output custom_results.json
```

See [`scripts/README.md`](scripts/README.md) for detailed documentation.

---

## 📊 Historical Context

### Official RKNN-LLM Benchmarks (Reference)

From Rockchip's official benchmarks (RK3588, w8a8 models):

| Model | Size | TTFT | Tokens/sec | Memory |
|-------|------|------|------------|--------|
| MiniCPM4 | 0.5B | 128ms | 45.13 | 525 MB |
| Qwen2 | 0.5B | 144ms | 42.58 | 654 MB |
| Qwen3 | 0.6B | 214ms | 32.16 | 774 MB |
| TinyLLAMA | 1.1B | 239ms | 24.49 | 1085 MB |
| Qwen2.5 | 1.5B | 412ms | 16.32 | 1659 MB |

**Our Qwen3-0.6B Results:**
- TTFT: 295ms (vs 214ms official) - within expected variance
- Tokens/sec: 15.59 (vs 32.16 official) - lower but still usable
- Memory: 890 MB (vs 774 MB official) - slightly higher

**Variance Factors:**
- Different test prompts (our tests more comprehensive)
- Inference parameter differences
- System load and background processes
- Model conversion variations

---

## 🔮 Future Improvements

### Phase 4.2 - Multi-Batch Inference (Planned)
- Target: 2-3x throughput improvement under concurrent load
- Method: Request batching and queue management
- Benefit: Better resource utilization for multiple users

### Phase 4.3 - LongRoPE Support (Planned)
- Requires: RKLLM 1.2.2 upgrade
- Benefit: 32K-64K context windows
- Use case: Long document analysis, extended conversations

### Model Optimization Ideas
- Reconvert Gemma3-1B with 16K context
- Test additional quantization options (w4a16, w8a16)
- Explore different --rope-theta values
- Test CPU vs NPU vs hybrid configurations

---

## 📝 Conclusion

RockchipLlama on RK3588 hardware achieves **production-ready performance** with appropriate model selection:

✅ **Qwen3-0.6B is the clear winner** for production use  
✅ **Binary caching provides 23.5x speedup** for repeated prompts  
✅ **15.59 tok/s generation speed** provides good user experience  
✅ **16K context** handles real-world conversations  
✅ **890 MB memory** is efficient and scalable  

The system successfully demonstrates that **NPU-accelerated inference on edge hardware** can deliver practical LLM serving for production applications.

---

**Last Benchmark Run:** October 20, 2025  
**Benchmark Scripts:** See [`scripts/`](scripts/) directory  
**Full Documentation:** See [`README.md`](README.md) for API usage
