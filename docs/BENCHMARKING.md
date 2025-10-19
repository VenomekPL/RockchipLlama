# Benchmarking Guide

This document explains how to benchmark the RockchipLlama API server to measure performance metrics like TTFT (Time To First Token), tokens/second, and overall inference speed.

## Overview

The benchmark suite includes:
- **Performance Tests**: 5 quick prompts to measure speed and throughput
- **Quality Tests**: 5 detailed prompts to assess creativity, reasoning, and consistency
- **Comprehensive metrics**: TTFT, tokens/sec, memory usage, input processing speed

## Quick Start

### 1. Quick Test (3 requests)

Run a quick benchmark to verify everything is working:

```bash
python scripts/test_benchmark.py
```

This will:
- Check if a model is loaded
- Run 3 simple inference requests
- Measure TTFT and tokens/sec
- Display summary statistics

### 2. Full Performance Benchmark

Run the complete performance test suite (5 prompts):

```bash
python scripts/benchmark.py --type performance
```

### 3. Quality Assessment Benchmark

Run detailed quality tests (5 complex prompts):

```bash
python scripts/benchmark.py --type quality
```

### 4. Complete Benchmark Suite

Run all tests multiple times for statistical accuracy:

```bash
python scripts/benchmark.py --type all --runs 3
```

### 5. Full Benchmark with Response Capture (NEW!)

Run comprehensive benchmarks on all models and capture full responses for quality comparison:

```bash
# Benchmark all available models
python scripts/benchmark_full.py --all-models

# Benchmark a specific model
python scripts/benchmark_full.py --model google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588

# Custom settings
python scripts/benchmark_full.py --all-models --max-context 8192 --npu-cores 2
```

This generates:
- **Markdown reports** (`benchmarks/benchmark_YYYYMMDD_nonce.md`) with full prompts and responses
- **JSON data** (`benchmarks/benchmark_YYYYMMDD_nonce.json`) with detailed metrics
- Human-readable comparison of model quality and performance

## Command Reference

### Basic Usage

```bash
python scripts/benchmark.py [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--url URL` | API server base URL | http://localhost:8080 |
| `--type {performance,quality,all}` | Type of benchmark to run | performance |
| `--runs N` | Number of times to run each test | 1 |
| `--model MODEL` | Model to load before testing | Currently loaded model |
| `--output FILE` | Output file for detailed results | benchmark_results.json |
| `--max-tokens N` | Maximum tokens to generate | 512 |
| `--timeout N` | Request timeout in seconds | 300 |

### Examples

**Test with specific model:**
```bash
python scripts/benchmark.py \
  --model google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588 \
  --type performance
```

**Run multiple iterations for better statistics:**
```bash
python scripts/benchmark.py --type all --runs 5 --output my_results.json
```

**Test different server:**
```bash
python scripts/benchmark.py --url http://192.168.10.53:8080 --type performance
```

## Metrics Explained

### Time to First Token (TTFT)

The time from sending the request until receiving the first token of the response. This measures:
- Input processing speed (prefill phase)
- Model loading latency
- Network and API overhead

Lower TTFT = better user experience for interactive applications.

**Expected values (RK3588):**
- 0.5B models: 130-215 ms
- 1.1B models: 240-250 ms
- 1.5B models: 410-790 ms

### Tokens Per Second

The generation speed during the output phase (after first token).

**Formula:** `tokens_per_second = output_tokens / generate_time_ms * 1000`

**Expected values (RK3588 w8a8):**
- Qwen2-0.5B: ~42 tokens/sec
- MiniCPM4-0.5B: ~45 tokens/sec
- Qwen3-0.6B: ~32 tokens/sec
- TinyLLAMA-1.1B: ~24 tokens/sec
- Qwen2.5-1.5B: ~16 tokens/sec

### Input Processing Speed

The speed of processing input tokens during the prefill phase.

**Formula:** `input_tokens_per_second = input_tokens / prefill_time_ms * 1000`

This measures how fast the model can consume and process the context.

### Memory Usage

RAM consumed during inference (when available from RKLLM runtime).

**Expected values (RK3588):**
- 0.5B models: 520-654 MB
- 0.6B models: ~774 MB
- 1.1B models: ~1085 MB
- 1.5B models: 1450-1660 MB

## Benchmark Test Suites

### Performance Tests (Quick Prompts)

Located in `docs/benchmark_prompts.json` under `performance_tests`:

1. **Technical Explanation** - AI/ML prompt continuation
2. **Creative Writing** - Story prompt completion
3. **Scientific Discussion** - Climate change analysis
4. **Historical Analysis** - Roman Empire factors
5. **Technology Trends** - Edge computing challenges

These tests measure:
- Tokens per second
- TTFT consistency
- Processing efficiency
- Memory usage

### Quality Tests (Detailed Prompts)

Located in `docs/benchmark_prompts.json` under `quality_tests`:

1. **Creativity** - Fantasy story (300-500 words)
2. **Planning** - Software development plan
3. **Coding** - Python function with documentation
4. **Instruction Following** - Structured JSON response
5. **Consistency** - Roman Empire essay (800-1200 words)

These tests assess:
- Response quality
- Instruction adherence
- Output consistency
- Long-form generation capability

## Understanding Results

### Sample Output

```
================================================================================
📊 BENCHMARK SUMMARY
================================================================================

Model: google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588
Timestamp: 2025-10-19T15:30:45.123456
Duration: 45.67 seconds

Requests:
  Total: 10
  Successful: 10 ✅
  Failed: 0 ❌

Time to First Token (TTFT):
  Average: 185.32 ms
  Median: 178.45 ms
  Min: 145.67 ms
  Max: 234.89 ms

Total Inference Time:
  Average: 3456.78 ms (3.46 sec)
  Min: 2345.67 ms
  Max: 5678.90 ms

Generation Speed (Tokens/Second):
  Average: 38.45 tokens/sec
  Median: 39.12 tokens/sec
  Min: 32.34 tokens/sec
  Max: 44.56 tokens/sec

Token Statistics:
  Total Input Tokens: 1,234
  Total Output Tokens: 5,678
  Total Tokens: 6,912
  Avg Input/Request: 123.4
  Avg Output/Request: 567.8

================================================================================
```

### Interpreting Performance

**Good Performance:**
- TTFT < 250ms for models under 1B parameters
- Tokens/sec within 80-120% of expected range
- Consistent speeds across multiple runs (low variance)
- No failed requests

**Performance Issues:**
- TTFT > 500ms consistently
- Tokens/sec < 50% of expected values
- High variance between runs
- Frequent timeouts or errors

**Optimization Checklist:**
1. ✅ CPU frequency maximized (use scripts/set_max_freq.sh)
2. ✅ NPU cores properly configured (3 for RK3588)
3. ✅ Model optimization level = 0
4. ✅ Sufficient memory available
5. ✅ No background processes competing for NPU

## Detailed Results File

After each benchmark run, detailed results are saved to JSON:

```json
{
  "summary": {
    "total_requests": 10,
    "successful_requests": 10,
    "avg_ttft_ms": 185.32,
    "avg_tokens_per_second": 38.45,
    ...
  },
  "detailed_results": [
    {
      "prompt_id": "completion_01",
      "prompt_name": "Technical Explanation",
      "ttft_ms": 178.45,
      "total_time_ms": 3456.78,
      "input_tokens": 25,
      "output_tokens": 128,
      "tokens_per_second": 39.12,
      "response_text": "...",
      "success": true
    },
    ...
  ]
}
```

This file can be used for:
- Long-term performance tracking
- Comparing different models
- Identifying performance regressions
- Statistical analysis
- Generating reports

## Comparing Models

To benchmark multiple models:

```bash
```bash
#!/bin/bash
# benchmark_all_models.sh

MODELS=(
  "google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588"
  "Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588"
  "gemma-3-1b-it_w8a8"
)

for MODEL in "${MODELS[@]}"; do
  echo "Testing $MODEL..."
  python scripts/benchmark.py \
    --model "$MODEL" \
    --type performance \
    --runs 3 \
    --output "results_${MODEL}.json"
  
  curl -X POST http://localhost:8080/v1/models/unload
  sleep 2
done

echo "All benchmarks complete!"
```
```

## Continuous Integration

Integrate benchmarking into CI/CD:

```yaml
# .github/workflows/benchmark.yml
name: Performance Benchmark

on:
  push:
    branches: [main]
  pull_request:

jobs:
  benchmark:
    runs-on: [self-hosted, rk3588]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Start API Server
        run: |
          source venv/bin/activate
          ./start_server.sh &
          sleep 5
      
      - name: Run Benchmarks
        run: |
          source venv/bin/activate
          python scripts/benchmark.py --type performance --runs 3
      
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: benchmark_results.json
```

## Troubleshooting

### Issue: "No model loaded"

**Solution:** Load a model before benchmarking:
```bash
curl -X POST http://localhost:8080/v1/models/load \
  -H 'Content-Type: application/json' \
  -d '{"model": "google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588"}'
```

Or use the `--model` flag:
```bash
python benchmark.py --model google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588
```

### Issue: "Request timed out"

**Solutions:**
- Increase timeout: `--timeout 600`
- Reduce max tokens: `--max-tokens 256`
- Check NPU utilization: `watch -n 1 cat /sys/kernel/debug/rknpu/load`

### Issue: Low tokens/sec

**Checklist:**
1. Verify CPU frequency: `cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq`
2. Check NPU cores: Model should use all 3 cores on RK3588
3. Monitor memory: `free -h`
4. Check for thermal throttling: `cat /sys/class/thermal/thermal_zone*/temp`

### Issue: High variance in results

**Solutions:**
- Run more iterations: `--runs 5`
- Ensure consistent system state (no background tasks)
- Use CPU affinity for big cores (0xF0 on RK3588)
- Disable CPU frequency scaling during tests

## Best Practices

1. **Warm-up runs**: First inference is often slower (model loading, cache warming)
2. **Multiple iterations**: Run at least 3-5 times for reliable statistics
3. **Consistent environment**: Same CPU frequency, no background tasks
4. **Document configuration**: Record NPU cores, context length, optimization level
5. **Version tracking**: Note RKLLM version, model version, API version
6. **Baseline establishment**: Create baseline results for comparison
7. **Regular testing**: Run benchmarks after changes to catch regressions

## Advanced Usage

### Custom Prompts

Edit `docs/benchmark_prompts.json` to add your own test cases:

```json
{
  "performance_tests": {
    "tests": [
      {
        "id": "custom_01",
        "name": "My Custom Test",
        "prompt": "Your test prompt here..."
      }
    ]
  }
}
```

### Python API

Use the benchmark module programmatically:

```python
import sys
sys.path.append('scripts')
from benchmark import BenchmarkRunner

runner = BenchmarkRunner(base_url="http://localhost:8080")
runner.load_model("google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588")

results = runner.run_benchmark_suite("performance", num_runs=3)
summary = runner.calculate_summary(results, "gemma-270m", duration=60.0)
runner.print_summary(summary)
runner.save_results(results, summary, "my_results.json")
```

## References

- [RKNN-LLM Benchmark Data](../external/rknn-llm/benchmark.md)
- [Benchmark Prompts](./benchmark_prompts.json)
- [Model Management Guide](../MODEL_MANAGEMENT.md)
- [RKLLM Documentation](./rkllm.md)
