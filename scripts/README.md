# Scripts Directory

This directory contains all test and benchmark scripts for the RockchipLlama project.

## 📋 Scripts Overview

### Benchmark Scripts

**`benchmark.py`** (22KB)
- Comprehensive performance benchmarking suite
- Measures TTFT, tokens/sec, input processing speed, memory usage
- Supports performance and quality test suites
- Statistical analysis with multiple runs
- JSON output for tracking

**Usage:**
```bash
# Performance tests
python scripts/benchmark.py --type performance

# Quality tests
python scripts/benchmark.py --type quality

# Complete suite
python scripts/benchmark.py --type all --runs 3

# Specific model
python scripts/benchmark.py --model <model_name>
```

**`test_benchmark.py`** (5.8KB)
- Quick benchmark validation
- Runs 3 simple inference requests
- Fast performance check (~30 seconds)

**Usage:**
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
