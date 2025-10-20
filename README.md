# RockchipLlama

A Docker-centric REST API server designed to be OpenAI/Ollama compliant, specifically optimized for Rockchip RK3588 and other RKNN-LLM based chips running on ARM architecture.

## Overview

This project provides a REST API server that leverages Rockchip's Neural Processing Unit (NPU) capabilities for efficient large language model inference. The server is designed to be compatible with OpenAI and Ollama API specifications, allowing seamless integration with existing applications.

## Target Platform

- **Architecture**: ARM64
- **Primary Target**: Rockchip RK3588
- **Compatible Chips**: Other RKNN-LLM based Rockchip SoCs
- **Requirements**: Proper NPU drivers installed and NPU detection capability

## Project Status

✅ **Phase 3 Complete** - Real RKLLM Integration + Production Validation
🔄 **Phase 4 In Progress** - Advanced Features (Prompt Caching, Multi-Batch, LongRoPE)

**Completed:**
- ✅ FastAPI server with OpenAI API compatibility
- ✅ Real RKLLM ctypes bindings with NPU inference
- ✅ **Friendly model names**: `qwen3-4b`, `qwen3-0.6b`, `gemma3-1b`
- ✅ **Dynamic context detection**: Automatically extracts from filename (4K-16K)
- ✅ **Automatic model swapping**: Unloads old model when loading new one
- ✅ Comprehensive benchmarking suite with accurate RKLLM perf stats
- ✅ Configurable inference parameters via `config/inference_config.json`
- ✅ Smart model loading (skips reload if same model)
- ✅ GPU acceleration + 4-thread big core optimization (RK3588)
- ✅ Production viability assessment (0.6B-1.5B sweet spot)
- ✅ **Prompt Caching System**: Multi-cache support, version tracking, auto-overwrite

**Phase 4 Goals:**
- ✅ **Prompt Caching**: Multi-cache support with version tracking and overwrite detection - **COMPLETE**
- 🔄 **Multi-Batch Inference**: 2-3x throughput improvement under load
- 🔄 **LongRoPE Support**: 32K-64K context windows (requires RKLLM 1.2.2 upgrade)

**Benchmark Results (RK3588 NPU @ Max Frequency):**
- ✅ **Qwen3-0.6B**: 15.59 tokens/sec, 16K context, 890 MB RAM - **RECOMMENDED** (Best balance)
- ✅ **Gemma3-1B**: 13.50 tokens/sec, 4K context, 1243 MB RAM - **USABLE** (Needs 16K reconversion)
- ⚠️ **Qwen3-4B**: 3.13 tokens/sec, 16K context, 5027 MB RAM - **TOO SLOW** (Production requires ≥5 tok/s)
- ❌ **Gemma3-270m**: ~~29.80 tokens/sec~~ - **REMOVED** (produces garbage output)

**Production Requirements:**
- Minimum viable speed: **5 tokens/sec** for acceptable UX
- Current hardware (RK3588 @ max freq): Best for 0.5B-1.5B models
- Qwen3-4B excellent quality but too slow for production use

**Hardware Status:**
- ✅ NPU: 1.0 GHz (max frequency)
- ✅ CPU Big Cores: 2.3 GHz (max frequency)
- ✅ GPU: 1.0 GHz (max frequency)
- ✅ Already optimized with frequency locking script

**Next Enhancements:**
- 🚀 **Phase 4.1**: Prompt caching (50-70% TTFT reduction)
- 🚀 **Phase 4.2**: Multi-batch inference (2-3x throughput gain)
- 🚀 **Phase 4.3**: LongRoPE for 32K-64K contexts

**Current Focus:**
- ✅ **Phase 4.1**: Prompt caching system - **COMPLETE**
- ⏳ **Phase 4.2**: Multi-batch inference for throughput
- ⏳ **Phase 4.3**: LongRoPE support for extended contexts

**Next Enhancements:**
- ⏳ Binary cache generation (actual TTFT improvements with RKLLM native caching)
- ⏳ Multi-batch inference (2-3x throughput under concurrent load)
- ⏳ LongRoPE support for >16K contexts (requires RKLLM 1.2.2 upgrade)
- ⏳ Multi-instance model serving

## Repository Structure

```
├── config/                        # Configuration files (PROJECT ROOT)
│   ├── inference_config.json      # RKLLM inference parameters
│   └── settings.py                # Server configuration
├── src/
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   ├── openai_routes.py       # OpenAI-compatible endpoints
│   │   ├── model_routes.py        # Model management API
│   │   └── schemas.py             # Pydantic data models
│   ├── models/
│   │   ├── model_manager.py       # Singleton model lifecycle manager
│   │   └── rkllm_model.py         # RKLLM runtime wrapper (real NPU)
├── docs/
│   ├── copilot.md                 # Design document + session notes
│   ├── BENCHMARKING.md            # Comprehensive benchmarking guide
│   ├── benchmark_prompts.json     # Test prompts for benchmarking
│   └── rkllm.md                   # RKLLM documentation
├── models/                        # Directory for .rkllm model files
├── scripts/                       # Test and benchmark scripts
│   ├── benchmark.py               # Full benchmark suite
│   ├── test_benchmark.py          # Quick benchmark test
│   ├── test_api.py                # API endpoint tests
│   └── test_model_management.py   # Model management tests
├── start_server.sh                # Server startup script
├── requirements.txt               # Python dependencies
├── QUICKSTART.md                  # Quick start guide
├── MODEL_MANAGEMENT.md            # Model management documentation
└── README.md                      # This file
```

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Server

```bash
./start_server.sh
# Or manually:
# cd src && uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

Server will be available at:
- API: http://localhost:8080
- Interactive docs: http://localhost:8080/docs
- Health check: http://localhost:8080/v1/health

### 3. Load a Model

```bash
# List available models
curl http://localhost:8080/v1/models/available

# Load a model (recommended: qwen3-0.6b)
curl -X POST http://localhost:8080/v1/models/load \
  -H 'Content-Type: application/json' \
  -d '{"model": "qwen3-0.6b"}'
```

### 4. Run Inference

```bash
# Basic inference
curl -X POST http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "current",
    "messages": [{"role": "user", "content": "Explain quantum computing"}],
    "temperature": 0.7,
    "max_tokens": 512
  }'

# With prompt caching (single cache)
curl -X POST http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "current",
    "messages": [{"role": "user", "content": "Write a Python function"}],
    "cache_prompts": "coding_rules"
  }'

# With multiple caches
curl -X POST http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "current",
    "messages": [{"role": "user", "content": "Refactor this code"}],
    "cache_prompts": ["coding_rules", "project_context"]
  }'

# Or use the OpenAI Python client
python -c "
from openai import OpenAI
client = OpenAI(base_url='http://localhost:8080/v1', api_key='dummy')
response = client.chat.completions.create(
    model='current',
    messages=[{'role': 'user', 'content': 'Hello!'}]
)
print(response.choices[0].message.content)
"
```

### 5. Manage Prompt Caches

```bash
# Create a cache
curl -X POST http://localhost:8080/v1/cache/qwen3-0.6b \
  -H 'Content-Type: application/json' \
  -d '{
    "cache_name": "coding_rules",
    "content": "You are an expert Python developer. Follow PEP 8..."
  }'

# List caches for a model
curl http://localhost:8080/v1/cache/qwen3-0.6b

# Get specific cache
curl http://localhost:8080/v1/cache/qwen3-0.6b/coding_rules

# Update cache (overwrites)
curl -X POST http://localhost:8080/v1/cache/qwen3-0.6b \
  -H 'Content-Type: application/json' \
  -d '{
    "cache_name": "coding_rules",
    "content": "Updated content...",
    "allow_overwrite": true
  }'

# Delete cache
curl -X DELETE http://localhost:8080/v1/cache/qwen3-0.6b/coding_rules
```

### 6. Run Benchmarks

```bash
# Quick test (3 requests)
python scripts/test_benchmark.py

# Full performance benchmark (5 prompts)
python scripts/benchmark.py --type performance

# Quality assessment (5 detailed prompts)
python scripts/benchmark.py --type quality

# Complete suite with multiple runs
python scripts/benchmark.py --type all --runs 3
```

## Configuration

### Inference Parameters

Edit `config/inference_config.json` to customize RKLLM inference parameters:

```json
{
  "inference_params": {
    "top_k": 20,              // Top-K sampling (1=greedy, higher=more random)
    "top_p": 0.95,            // Nucleus sampling (0.9 standard)
    "temperature": 0.6,       // Lower=focused, higher=creative
    "repeat_penalty": 0.9,    // <1.0=less repetition, >1.0=penalize repetition
    "frequency_penalty": 0.6,
    "presence_penalty": 0.1
  },
  "hardware": {
    "num_npu_cores": 3,       // RK3588 has 3 NPU cores
    "enabled_cpus_mask": 240, // 0xF0 = big cores 4-7
    "num_threads": 4
  }
}
```

**No server restart needed** - parameters are loaded when a model is loaded.

### Server Configuration

Edit `config/settings.py` or create `.env` file:

```bash
# Server settings
HOST=0.0.0.0
PORT=8080
LOG_LEVEL=info

# Model settings
MODELS_DIR=./models
DEFAULT_MODEL=Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm

# RKLLM settings
RKLLM_LIB_PATH=/usr/lib/librkllmrt.so
MAX_CONTEXT_LEN=512
MAX_NEW_TOKENS=512
NUM_NPU_CORE=3
```

## Documentation

📚 **[Documentation Index](docs/DOCUMENTATION_INDEX.md)** - Complete overview of all documentation

### User Guides
- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Detailed getting started guide
- **[docs/MODEL_MANAGEMENT.md](docs/MODEL_MANAGEMENT.md)** - Model lifecycle management
- **[docs/CACHE_USAGE_GUIDE.md](docs/CACHE_USAGE_GUIDE.md)** - Prompt caching guide
- **[docs/BENCHMARKING.md](docs/BENCHMARKING.md)** - Performance benchmarking guide
- **[docs/BENCHMARK_QUICKREF.md](docs/BENCHMARK_QUICKREF.md)** - Quick reference for benchmarks

### Technical Documentation
- **[docs/rkllm.md](docs/rkllm.md)** - RKLLM runtime documentation
- **[docs/copilot.md](docs/copilot.md)** - Design document and session notes

## Performance Expectations (RK3588)

Based on RKNN-LLM benchmarks for w8a8 models:

| Model | Size | TTFT | Tokens/sec | Memory |
|-------|------|------|------------|--------|
| MiniCPM4 | 0.5B | 128ms | 45.13 | 525 MB |
| Qwen2 | 0.5B | 144ms | 42.58 | 654 MB |
| Qwen3 | 0.6B | 214ms | 32.16 | 774 MB |
| TinyLLAMA | 1.1B | 239ms | 24.49 | 1085 MB |
| Qwen2.5 | 1.5B | 412ms | 16.32 | 1659 MB |

Use the benchmark tools to measure actual performance on your hardware.

## Getting Started

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for detailed setup and usage instructions.

## External Dependencies

The project will integrate with external repositories containing:
- Rockchip NPU drivers
- RKNN runtime libraries
- Reference examples and implementations

## License

[License to be determined]

## Contributing

[Contributing guidelines to be added]