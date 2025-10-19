# Benchmarking System - Implementation Summary

## Overview

Comprehensive performance benchmarking system for RockchipLlama API server, designed to measure TTFT (Time To First Token), tokens/second, and overall inference performance based on RKNN-LLM benchmark methodology.

## Files Created

### 1. `benchmark.py` (Primary Benchmark Suite)
**Purpose**: Full-featured benchmark tool with comprehensive metrics collection

**Features:**
- Supports performance and quality test suites
- Measures TTFT, tokens/sec, input processing speed, memory usage
- Statistical analysis: mean, median, min, max
- JSON output for detailed results
- Multiple run support for statistical accuracy
- Model loading integration
- Command-line interface with extensive options

**Key Classes:**
- `PerformanceMetrics`: Per-request metrics dataclass
- `BenchmarkSummary`: Aggregate statistics dataclass
- `BenchmarkRunner`: Main benchmark orchestration class

**Usage:**
```bash
# Quick performance test
python benchmark.py --type performance

# Quality assessment
python benchmark.py --type quality

# Complete suite with iterations
python benchmark.py --type all --runs 3

# Test specific model
python benchmark.py --model <model_name> --output results.json
```

### 2. `test_benchmark.py` (Quick Test)
**Purpose**: Simplified benchmark for rapid testing

**Features:**
- Runs 3 quick inference requests
- Measures basic metrics: TTFT, tokens/sec, total time
- Minimal dependencies
- Quick validation before full benchmarks

**Usage:**
```bash
python test_benchmark.py
```

### 3. `docs/benchmark_prompts.json` (Test Prompts)
**Purpose**: Curated test prompts for consistent benchmarking

**Structure:**
```json
{
  "performance_tests": {
    "description": "Speed and efficiency tests",
    "tests": [
      {
        "id": "completion_01",
        "name": "Technical Explanation",
        "prompt": "..."
      }
      // ... 5 total performance tests
    ]
  },
  "quality_tests": {
    "description": "Qualitative assessment tests",
    "tests": [
      {
        "id": "creativity_01",
        "name": "Fantasy Story Creation",
        "category": "creativity",
        "prompt": "..."
      }
      // ... 5 total quality tests
    ]
  }
}
```

**Performance Tests (5 prompts):**
1. Technical Explanation - AI/ML topic
2. Creative Writing - Story completion
3. Scientific Discussion - Climate change
4. Historical Analysis - Roman Empire
5. Technology Trends - Edge computing

**Quality Tests (5 prompts):**
1. Creativity - Fantasy story (300-500 words)
2. Planning - Software development plan
3. Coding - Python function with docs
4. Instruction Following - JSON response
5. Consistency - Essay (800-1200 words)

### 4. `docs/BENCHMARKING.md` (Comprehensive Guide)
**Purpose**: Complete documentation for benchmarking system

**Contents:**
- Quick start guide
- Command reference
- Metrics explanation (TTFT, tokens/sec, etc.)
- Expected performance values for RK3588
- Understanding results
- Troubleshooting guide
- Best practices
- Advanced usage (custom prompts, Python API)
- CI/CD integration examples

## Metrics Collected

### Primary Metrics

1. **TTFT (Time To First Token)**
   - Measures: Input processing speed (prefill phase)
   - Units: milliseconds (ms)
   - Expected (RK3588 0.5-0.6B): 130-215 ms

2. **Tokens Per Second**
   - Measures: Output generation speed
   - Formula: `output_tokens / generate_time_ms * 1000`
   - Expected (RK3588 w8a8): 32-45 tokens/sec for 0.5-0.6B models

3. **Input Processing Speed**
   - Measures: Prefill efficiency
   - Formula: `input_tokens / prefill_time_ms * 1000`
   - Units: tokens/second

4. **Total Inference Time**
   - Measures: End-to-end request duration
   - Includes: Network, processing, generation
   - Units: milliseconds

5. **Memory Usage**
   - Measures: RAM consumed during inference
   - Units: MB
   - Expected (RK3588): 525-774 MB for 0.5-0.6B models

### Statistical Analysis

For all metrics, the system calculates:
- **Mean**: Average across all runs
- **Median**: Middle value (robust to outliers)
- **Minimum**: Best performance observed
- **Maximum**: Worst performance observed

## Expected Performance (RK3588 w8a8)

Based on official RKNN-LLM benchmarks:

| Model | Size | TTFT | Tokens/sec | Memory |
|-------|------|------|------------|--------|
| MiniCPM4 | 0.5B | 128ms | 45.13 | 525 MB |
| Qwen2 | 0.5B | 144ms | 42.58 | 654 MB |
| Qwen3 | 0.6B | 214ms | 32.16 | 774 MB |
| TinyLLAMA | 1.1B | 239ms | 24.49 | 1085 MB |
| Qwen2.5 | 1.5B | 412ms | 16.32 | 1659 MB |

## Output Format

### Console Summary
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
```

### JSON Output (`benchmark_results.json`)
```json
{
  "summary": {
    "total_requests": 10,
    "successful_requests": 10,
    "failed_requests": 0,
    "avg_ttft_ms": 185.32,
    "median_ttft_ms": 178.45,
    "avg_tokens_per_second": 38.45,
    "median_tokens_per_second": 39.12,
    "total_input_tokens": 1234,
    "total_output_tokens": 5678,
    "model_name": "google_gemma-3-270m...",
    "timestamp": "2025-10-19T15:30:45.123456",
    "duration_seconds": 45.67
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
    }
    // ... more results
  ]
}
```

## Integration with Existing System

### Model Management Integration
- Automatically checks if model is loaded
- Can load model before benchmarking with `--model` flag
- Respects currently loaded model if no model specified
- Uses `/v1/models/loaded` and `/v1/models/load` endpoints

### API Compatibility
- Uses standard OpenAI-compatible endpoints
- Supports streaming responses for TTFT measurement
- Compatible with existing API infrastructure

### Test Suite Integration
- Follows same patterns as `test_api.py` and `test_model_management.py`
- Uses same dependencies (requests library)
- Consistent error handling and reporting

## Use Cases

### 1. Development Testing
```bash
# Quick validation during development
python test_benchmark.py
```

### 2. Model Comparison
```bash
# Test multiple models
for model in model1 model2 model3; do
  python benchmark.py --model "$model" --output "results_${model}.json"
done
```

### 3. Performance Regression Testing
```bash
# Run before and after changes
python benchmark.py --type all --runs 5 --output baseline.json
# ... make changes ...
python benchmark.py --type all --runs 5 --output after_changes.json
# Compare results
```

### 4. Hardware Validation
```bash
# Verify NPU performance meets expectations
python benchmark.py --type performance --runs 3
# Check if tokens/sec matches RKNN-LLM benchmarks
```

### 5. CI/CD Integration
```yaml
# GitHub Actions example
- name: Performance Benchmark
  run: |
    python benchmark.py --type performance --runs 3
    # Upload results as artifact
```

## Advantages Over Simple Testing

1. **Consistent Test Cases**: Curated prompts ensure reproducible results
2. **Statistical Rigor**: Multiple runs and statistical analysis
3. **Comprehensive Metrics**: Beyond simple "hello world" tests
4. **Performance Tracking**: JSON output enables long-term tracking
5. **Quality Assessment**: Dedicated tests for creativity, reasoning, coding
6. **Comparison Ready**: Results align with official RKNN-LLM benchmarks

## Next Steps

Once RKLLM runtime integration (Phase 3) is complete:

1. **Baseline Establishment**
   ```bash
   python benchmark.py --type all --runs 5 --output baseline_gemma270m.json
   ```

2. **Optimization Testing**
   - Test different NPU core counts
   - Try various context lengths
   - Measure CPU affinity impact
   - Test embed_flash optimization

3. **Model Comparison**
   - Benchmark all 3 models
   - Compare actual vs expected performance
   - Identify best model for use case

4. **Performance Documentation**
   - Document real-world results
   - Update README with actual metrics
   - Create performance optimization guide

## Files Modified

- **README.md**: Added benchmark section with quick examples
- **docs/copilot.md**: Documented benchmark system implementation

## Dependencies

All dependencies already in `requirements.txt`:
- `requests>=2.32.3` - HTTP client for API calls
- `json` - Built-in, for parsing responses
- Standard library: `time`, `statistics`, `dataclasses`, `argparse`

## Testing Status

- ✅ Benchmark script created and executable
- ✅ Quick test script created
- ✅ Test prompts defined (10 total: 5 performance + 5 quality)
- ✅ Documentation complete
- ⏳ Awaiting Phase 3 (RKLLM integration) for real NPU testing
- ⏳ Baseline performance metrics pending real inference

## Summary

The benchmarking system provides a production-ready performance measurement framework that:
- Follows RKNN-LLM benchmark methodology
- Measures all critical performance metrics
- Supports both quick testing and comprehensive analysis
- Produces detailed, trackable results
- Integrates seamlessly with existing API infrastructure
- Ready for immediate use once RKLLM runtime integration is complete

This gives you professional-grade performance testing capabilities comparable to what you'd find in commercial LLM serving platforms, specifically tailored for NPU-accelerated inference on RK3588 hardware.
