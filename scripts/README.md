# Scripts Directory# Scripts Directory



Benchmark and performance testing tools for RockchipLlama.This directory contains all test and benchmark scripts for the RockchipLlama project.



## Benchmark Scripts## 📋 Scripts Overview



### benchmark.py (23 KB)### Benchmark Scripts

**Full-featured benchmark suite with comprehensive metrics**

**`benchmark.py`** (22KB)

Usage:- Comprehensive performance benchmarking suite

```bash- Measures TTFT, tokens/sec, input processing speed, memory usage

# Performance tests (5 prompts)- Supports performance and quality test suites

python scripts/benchmark.py --type performance- Statistical analysis with multiple runs

- JSON output for tracking

# Complete suite with iterations

python scripts/benchmark.py --type all --runs 3**Usage:**

``````bash

# Performance tests

### benchmark_full.py (13 KB)python scripts/benchmark.py --type performance

**Extended benchmark with unlimited token generation**

# Quality tests

### generate_report.py (8 KB)python scripts/benchmark.py --type quality

**Markdown report generator from benchmark JSON**

# Complete suite

### test_benchmark.py (6 KB)python scripts/benchmark.py --type all --runs 3

**Quick 3-request benchmark for rapid testing**

# Specific model

---python scripts/benchmark.py --model <model_name>

```

## Performance Results

**`test_benchmark.py`** (5.8KB)

See **[BENCHMARKS.md](../BENCHMARKS.md)** for complete benchmark results and analysis.- Quick benchmark validation

- Runs 3 simple inference requests

**Quick Summary:**- Fast performance check (~30 seconds)

- Qwen3-0.6B: 15.59 tok/s ⭐

- With binary cache: 75ms TTFT (23.5x faster!) 🔥**Usage:**

```bash
python scripts/test_benchmark.py
```

### Test Scripts

**`test_api.py`** (3.8KB)
- Tests OpenAI-compatible API endpoints
- Validates chat completions, model listing, health checks
- Quick validation of API functionality

**Usage:**
```bash
python scripts/test_api.py
```

**`test_model_management.py`** (6.7KB)
- Tests model lifecycle management
- Validates load, unload, list operations
- Comprehensive model management testing

**Usage:**
```bash
python scripts/test_model_management.py
```

**`test_binary_cache.py`** (4.4KB)
- Tests binary cache creation and loading
- Validates RKLLM native prompt caching
- Created during Phase 4.1 development

**Usage:**
```bash
python scripts/test_binary_cache.py
```

**`test_cache_integration.py`** (6.8KB)
- Integration tests for binary cache API
- Tests cache creation, loading, and usage
- Validates cache_hit metadata

**Usage:**
```bash
python scripts/test_cache_integration.py
```

**`test_simple_performance.py`** (3.1KB)
- Quick performance comparison test
- Tests with and without cache
- Simple validation of cache benefits

**Usage:**
```bash
python scripts/test_simple_performance.py
```

**`test_real_cache_performance.py`** (10.4KB)
- Comprehensive cache performance test
- Uses real 1326-char system prompt
- Measures actual TTFT improvements
- Documents expected vs actual results

**Usage:**
```bash
python scripts/test_real_cache_performance.py
```

## 🚀 Quick Start

From the project root directory:

```bash
# Activate virtual environment
source venv/bin/activate

# Run API tests
python scripts/test_api.py

# Run model management tests
python scripts/test_model_management.py

# Quick benchmark
python scripts/test_benchmark.py

# Full benchmark
python scripts/benchmark.py --type all --runs 3
```

## 📊 Benchmark Output

Benchmark scripts generate:
- **Console output**: Formatted summary with statistics
- **JSON file**: Detailed per-request metrics (`benchmark_results.json`)

Example JSON output location: Project root directory

## 🔗 Related Documentation

- **[../docs/BENCHMARKING.md](../docs/BENCHMARKING.md)** - Complete benchmarking guide
- **[../docs/BENCHMARK_QUICKREF.md](../docs/BENCHMARK_QUICKREF.md)** - Quick reference
- **[../docs/MODEL_MANAGEMENT.md](../docs/MODEL_MANAGEMENT.md)** - Model management guide
- **[../docs/QUICKSTART.md](../docs/QUICKSTART.md)** - Getting started guide

## 🛠️ Requirements

All scripts require:
- Python virtual environment activated
- Dependencies installed from `requirements.txt`
- API server running (except for standalone utilities)

## 💡 Tips

1. **Always activate venv first**: `source venv/bin/activate`
2. **Start server if needed**: `./start_server.sh`
3. **Load a model before benchmarking**: See MODEL_MANAGEMENT.md
4. **Run from project root**: All paths are relative to root directory
5. **Check server is running**: `curl http://localhost:8080/v1/health`

## 📝 Adding New Scripts

When adding new test or benchmark scripts:
1. Place them in this `scripts/` directory
2. Update this README
3. Update main project README if significant
4. Update DOCUMENTATION_INDEX.md
5. Follow existing naming conventions: `test_*.py` or `benchmark*.py`
