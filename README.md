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

✅ **Phase 3 Complete** - Friendly Model Names + Dynamic Context Detection

**Completed:**
- ✅ FastAPI server with OpenAI API compatibility
- ✅ Real RKLLM ctypes bindings with NPU inference
- ✅ **Friendly model names**: `qwen3-0.6b`, ~~`gemma3-270m`~~, `gemma3-1b`
- ✅ **Dynamic context detection**: Automatically extracts from filename (4K-16K)
- ✅ **Automatic model swapping**: Unloads old model when loading new one
- ✅ Comprehensive benchmarking suite with accurate RKLLM perf stats
- ✅ Configurable inference parameters via `config/inference_config.json`
- ✅ Smart model loading (skips reload if same model)
- ✅ GPU acceleration + 4-thread big core optimization (RK3588)

**Benchmark Results (RK3588 NPU):**
- ✅ **Qwen3-0.6B**: 15.59 tokens/sec, 16K context, 890 MB RAM - **RECOMMENDED**
- ❌ **Gemma3-270m**: ~~29.80 tokens/sec~~ - **REMOVED** (produces garbage output)
- ✅ **Gemma3-1B**: 13.50 tokens/sec, 4K context, 1243 MB RAM (needs 16K reconversion)

**Current Focus:**
- 🔄 Testing extended context capabilities (up to 16K)
- 🔄 Model reconversion for consistent 16K context support

**Next Enhancements:**
- ⏳ Prompt caching system for improved TTFT
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

# Load a model
curl -X POST http://localhost:8080/v1/models/load \
  -H 'Content-Type: application/json' \
  -d '{"model": "google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588"}'
```

### 4. Run Inference

```bash
# Using curl
curl -X POST http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "current",
    "messages": [{"role": "user", "content": "Explain quantum computing"}],
    "temperature": 0.7,
    "max_tokens": 512
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

### 5. Run Benchmarks

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