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

🔧 **Phase 3 In Progress** - RKLLM NPU integration (model loads but outputs garbage)

**Completed:**
- ✅ FastAPI server with OpenAI API compatibility
- ✅ Model management system (load/unload/list)
- ✅ Comprehensive benchmarking suite
- ✅ Real RKLLM ctypes bindings implemented
- ✅ Model successfully loads on NPU (RKLLM 1.2.1 + driver 0.9.7)
- ✅ GPU acceleration + 4-thread big core optimization

**Current Issues:**
- ❌ NPU generates text but output is incoherent/off-topic
- ❌ Token counting incorrect (not using RKLLM perf stats)
- ❌ Prompt handling needs investigation
- 🔄 Need to extract RKLLMPerfStat from callback for accurate metrics

## Repository Structure

```
├── src/
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   ├── openai_routes.py       # OpenAI-compatible endpoints
│   │   ├── model_routes.py        # Model management API
│   │   └── schemas.py             # Pydantic data models
│   ├── models/
│   │   ├── model_manager.py       # Singleton model lifecycle manager
│   │   └── rkllm_model.py         # RKLLM runtime wrapper
│   └── config/
│       └── settings.py            # Configuration management
├── docs/
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