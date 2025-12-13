# Scripts Directory

This directory contains the benchmark and utility scripts for the RockchipLlama project.

## 📋 Scripts Overview

### Benchmark Scripts

**`benchmark.py`**
- Full-featured benchmark suite with comprehensive metrics
- Measures TTFT, tokens/sec, input processing speed, memory usage
- Supports performance and quality test suites
- Generates **Markdown reports** with collapsible thinking sections
- JSON output for tracking

**Usage:**
```bash
# Performance tests
python scripts/benchmark.py --type performance

# Quality tests
python scripts/benchmark.py --type quality

# Complete suite
python scripts/benchmark.py --type all --runs 3

# Specific model with custom output
python scripts/benchmark.py --model qwen3-0.6b --output benchmarks/my_report.json
```

### Utility Scripts

**`download_models.py`**
- Downloads recommended models (Qwen3-0.6B) from HuggingFace.
- Checks for existing files to avoid re-downloading.
- Automatically sets up the correct folder structure.

**`fix_freq_rk3588.sh`**
- Locks CPU and NPU clocks to maximum frequency.
- **Requires sudo**.
- Run this before benchmarking for consistent results.
- Automatically called by `start_server.sh`.

**`generate_report.py`**
- Legacy script. Use `benchmark.py` which now generates Markdown reports automatically.

## 🚀 Quick Start

From the project root directory:

```bash
# Activate virtual environment
source venv/bin/activate

# Full benchmark
python scripts/benchmark.py --type all --runs 3
```

## 📊 Benchmark Output

Benchmark scripts generate:
- **Console output**: Formatted summary with statistics
- **JSON file**: Detailed per-request metrics (`benchmark_results.json`)

## 💡 Tips

1. **Always activate venv first**: `source venv/bin/activate`
2. **Start server if needed**: `./start_server.sh` (in a separate terminal)
3. **Run from project root**: All paths are relative to root directory
4. **Check server is running**: `curl http://localhost:8021/v1/health`
