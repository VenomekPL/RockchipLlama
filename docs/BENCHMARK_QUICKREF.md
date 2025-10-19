# Benchmark Quick Reference

## One-Line Commands

```bash
# Quick validation (3 requests, ~30 seconds)
python scripts/test_benchmark.py

# Performance suite (5 prompts, ~2-3 minutes)
python scripts/benchmark.py --type performance

# Quality suite (5 detailed prompts, ~5-10 minutes)
python scripts/benchmark.py --type quality

# Full benchmark (10 prompts × 3 runs, ~15-20 minutes)
python scripts/benchmark.py --type all --runs 3
```

## Command Options

```bash
python scripts/benchmark.py \
  --url http://localhost:8080 \        # API server URL
  --type {performance|quality|all} \   # Test suite type
  --runs 3 \                           # Number of iterations
  --model <model_name> \               # Model to test (optional)
  --output results.json \              # Output file
  --max-tokens 512 \                   # Max tokens per request
  --timeout 300                        # Timeout in seconds
```

## Metrics Cheat Sheet

| Metric | What it measures | Good value (RK3588 0.5-0.6B) |
|--------|------------------|------------------------------|
| **TTFT** | Time to first token | < 250ms |
| **Tokens/sec** | Generation speed | 32-45 tokens/sec |
| **Total Time** | End-to-end latency | Depends on length |
| **Memory** | RAM usage | 520-780 MB |

## Expected Performance (RK3588 w8a8)

| Model | TTFT | Tokens/sec | Memory |
|-------|------|------------|--------|
| Gemma-270M | ~150ms | ~40-45 | 616 MB |
| Qwen2-0.5B | ~144ms | ~42 | 654 MB |
| Qwen3-0.6B | ~214ms | ~32 | 774 MB |
| TinyLLAMA-1.1B | ~239ms | ~24 | 1085 MB |

## Quick Analysis

**Good Performance:**
- ✅ TTFT < 250ms (sub-1B models)
- ✅ Tokens/sec within 80-120% of expected
- ✅ Low variance across runs
- ✅ No timeouts or errors

**Performance Issues:**
- ❌ TTFT > 500ms consistently
- ❌ Tokens/sec < 50% of expected
- ❌ High variance between runs
- ❌ Frequent errors/timeouts

**Optimization Checklist:**
```bash
# 1. Check CPU frequency
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq

# 2. Check NPU load
watch -n 1 cat /sys/kernel/debug/rknpu/load

# 3. Check memory
free -h

# 4. Check thermal throttling
cat /sys/class/thermal/thermal_zone*/temp
```

## Model Comparison Script

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

## Result Files

**Console output**: Formatted summary with emojis
**JSON file**: Detailed metrics for analysis

```json
{
  "summary": {
    "avg_ttft_ms": 185.32,
    "avg_tokens_per_second": 38.45,
    "total_requests": 10,
    "successful_requests": 10
  },
  "detailed_results": [ /* per-request data */ ]
}
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No model loaded" | Load model: `curl -X POST http://localhost:8080/v1/models/load -d '{"model":"..."}'` |
| Request timeout | Increase timeout: `--timeout 600` |
| Low tokens/sec | Check CPU freq, NPU utilization, thermal |
| High variance | Run more iterations: `--runs 5` |

## Before/After Comparison

```bash
# Establish baseline
python scripts/benchmark.py --type all --runs 5 --output baseline.json

# ... make optimizations ...

# Test again
python scripts/benchmark.py --type all --runs 5 --output optimized.json

# Compare key metrics
jq '.summary.avg_tokens_per_second' baseline.json optimized.json
```

## Documentation

- **Full guide**: `docs/BENCHMARKING.md`
- **Test prompts**: `docs/benchmark_prompts.json`
- **Implementation**: `BENCHMARK_SUMMARY.md`
