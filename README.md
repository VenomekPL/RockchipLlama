# RockchipLlama

OpenAI-compatible REST API server optimized for Rockchip RK3588 NPU, delivering production-ready LLM inference on ARM hardware.

## Overview

FastAPI server leveraging Rockchip's Neural Processing Unit (NPU) for efficient large language model inference. Compatible with OpenAI and Ollama API specifications for seamless integration with existing applications.

## Key Features

✅ **Production Ready** - 15.59 tok/s with Qwen3-0.6B  
🔥 **Binary Caching** - 23.5x faster TTFT (1775ms → 75ms)  
🔌 **OpenAI Compatible** - Drop-in replacement for OpenAI API  
🦙 **Ollama Compatible** - Full Ollama API support  
🚀 **NPU Accelerated** - Real RKLLM runtime integration  
📦 **Model Management** - Dynamic loading with friendly names  
⚙️ **Configurable** - Runtime parameter tuning without restart  
🔄 **Queue-Based Concurrency** - Stable parallel request handling

## Quick Start

```bash
# 1. Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Download default models (Qwen3-0.6B)
python scripts/download_models.py

# 3. Start server (sudo required for performance tuning)
sudo ./start_server.sh

# 4. Load model & chat
curl -X POST http://localhost:8021/v1/models/load \
  -d '{"model": "qwen3-0.6b"}'

curl -X POST http://localhost:8021/v1/chat/completions \
  -d '{
    "model": "qwen3-0.6b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

Server available at: http://localhost:8021  
Interactive docs: http://localhost:8021/docs

## 📚 Documentation

- **[Scripts & Tools](scripts/README.md)** - Benchmarking, downloading, and utility scripts
- **[Benchmark Results](benchmarks/README.md)** - Performance reports and comparisons
- **[Architecture](docs/README.md)** - System design and implementation details

## 🚀 Performance Tuning

The server includes a script to lock the RK3588 CPU and NPU clocks to their maximum frequencies for consistent inference speed.

- **Automatic:** `sudo ./start_server.sh` will attempt to set these frequencies on startup.
- **Manual:** Run `sudo ./scripts/fix_freq_rk3588.sh` directly.

*Note: These settings reset on reboot.*

## 📦 Model Management

### Default Models
Run `python scripts/download_models.py` to fetch the recommended models:
- **qwen3-0.6b**: Fast, efficient chat model (16k context)
- **qwen3-0.6b-embedding**: Compatible embedding model

### Custom Models
To add your own RKLLM models (e.g., from HuggingFace):
1. Create a folder in `models/` with your desired model name (e.g., `models/my-llama/`).
2. Place the `.rkllm` file inside that folder.
3. The server will automatically detect it as `my-llama`.

```bash
models/
├── qwen3-0.6b/           # Model ID: qwen3-0.6b
│   └── model.rkllm
└── my-llama/             # Model ID: my-llama
    └── llama-3-8b.rkllm
```

## 🔥 Binary Caching (Manual)

Reduce Time To First Token (TTFT) by saving the NPU state for common prompts (like system prompts).

**1. Create a Cache:**
```bash
curl -X POST http://localhost:8021/v1/cache/qwen3-0.6b \
  -d '{
    "cache_name": "system_prompt",
    "prompt": "You are a helpful assistant..."
  }'
```

**2. Use the Cache:**
The server currently does not automatically apply caches. This feature is for manual state management and testing. Future updates will integrate this into the chat completion flow.

## 📊 Benchmarking

Use the included suite to test performance on your hardware.

```bash
# Run full benchmark suite
python scripts/benchmark.py --model qwen3-0.6b --type all

# Generate Markdown report
python scripts/benchmark.py --model qwen3-0.6b --output benchmarks/my_report.json
```

See **[benchmarks/README.md](benchmarks/README.md)** for detailed results.
{
  "model": "qwen3-0.6b",
  "use_cache": "system",  # ← 75ms vs 1775ms!
  "messages": [{"role": "user", "content": "Help me code"}]
}
```

### Model Management

```bash
# List available models
GET /v1/models/available

# Load model
POST /v1/models/load
{"model": "qwen3-0.6b"}

# Get loaded model
GET /v1/models/loaded

# Unload model
POST /v1/models/unload
```

### Cache Management

```bash
# Create binary cache
POST /v1/cache/{model}
{"cache_name": "system", "prompt": "..."}

# List caches
GET /v1/cache/{model}

# Delete cache
DELETE /v1/cache/{model}/{cache_name}
```

### OpenAI Python Client

```python
from openai import OpenAI

client = OpenAI(
    base_url='http://localhost:8021/v1',
    api_key='dummy'  # Not required but OpenAI client needs something
)

# Chat completion
response = client.chat.completions.create(
    model='qwen3-0.6b',
    messages=[
        {'role': 'system', 'content': 'You are a helpful assistant'},
        {'role': 'user', 'content': 'Explain quantum computing'}
    ],
    temperature=0.7,
    max_tokens=512
)

print(response.choices[0].message.content)
```

---

### 5. Manage Prompt Caches (Binary NPU Caching)

**Binary caching stores NPU state for instant restoration - 23.5x faster!**

```bash
# Create a binary cache (saves NPU prefill state)
curl -X POST http://localhost:8021/v1/cache/qwen3-0.6b \
  -H 'Content-Type: application/json' \
  -d '{
    "cache_name": "system",
    "prompt": "You are a helpful AI assistant..."
  }'

# Response shows cache creation performance
{
  "object": "cache.created",
  "cache_name": "system",
  "size_mb": 32.42,
  "ttft_ms": 669.98,
  "message": "Binary cache generated successfully"
}

# Use the cache in chat (TTFT: 1775ms → 75.2ms!)
curl -X POST http://localhost:8021/v1/chat/completions \
  -d '{
    "use_cache": "system",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Response confirms cache usage
{
  "usage": {
    "cache_hit": true,
    "cached_prompts": ["system"]
  }
}

# List caches
curl http://localhost:8021/v1/cache/qwen3-0.6b

# Delete cache
curl -X DELETE http://localhost:8021/v1/cache/qwen3-0.6b/system
```

## Configuration

Runtime configuration without server restart!

**Inference Parameters** (`config/inference_config.json`):
```json
{
  "inference_params": {
    "top_k": 20,
    "top_p": 0.95,
    "temperature": 0.6,
    "repeat_penalty": 0.9
  },
  "chat_template": {
    "system_start": "<|im_start|>system\n",
    "system_end": "<|im_end|>\n",
    "user_start": "<|im_start|>user\n",
    "user_end": "<|im_end|>\n",
    "assistant_start": "<|im_start|>assistant\n",
    "assistant_end": "<|im_end|>\n"
  },
  "hardware": {
    "num_npu_cores": 3,
    "enabled_cpus_mask": 240,  // 0xF0 = big cores 4-7
    "num_threads": 4
  }
}
```

**Server Settings** (`config/settings.py` or `.env`):
```bash
HOST=0.0.0.0
PORT=8021
MODELS_DIR=./models
RKLLM_LIB_PATH=/usr/lib/librkllmrt.so
```

---

## Hardware Requirements

- **Platform:** ARM64 (Rockchip RK3588 or compatible)
- **NPU Drivers:** RKNN-LLM runtime library installed
- **Memory:** 2GB+ RAM (4GB recommended for larger models)
- **Storage:** 1-5GB per model + cache storage

**Tested On:**
- Orange Pi 5 Max (RK3588)
- NPU @ 1.0 GHz, CPU @ 2.3 GHz
- RKLLM 1.2.3

---

## Documentation

- 📊 **[docs/BENCHMARKS.md](docs/BENCHMARKS.md)** - Performance results & comparisons
- 🎯 **[docs/longrope_guide.md](docs/longrope_guide.md)** - LongRoPE (extended context) guide
- 🏗️ **[docs/queue_architecture.md](docs/queue_architecture.md)** - Queue-based concurrency design
- 🔧 **[docs/rkllm.md](docs/rkllm.md)** - RKLLM technical reference
- 📖 **[docs/copilot.md](docs/copilot.md)** - Full changelog & design notes

## Benchmarking

Run the comprehensive benchmark suite to test performance and quality:

```bash
# Run all 10 tests (5 performance, 5 quality) with unbound tokens
python scripts/benchmark.py
```

## Logging

Server logging is set to `WARNING` level by default to reduce noise.
To change this, edit `config/settings.py`.

---

## Repository Structure

```
├── src/                  # FastAPI application
│   ├── api/              # API routes (OpenAI compatible)
│   └── models/           # Model management & RKLLM wrapper
├── config/               # Configuration files
├── models/               # .rkllm model files (gitignored)
├── cache/                # Binary cache files (gitignored)
├── scripts/              # Benchmark & test scripts
├── benchmarks/           # Benchmark results & reports
├── docs/                 # Documentation
└── BENCHMARKS.md         # Performance results
```

---

## License

[License to be determined]

## Contributing

Issues and pull requests welcome! This project demonstrates production-ready NPU-accelerated LLM inference on edge hardware.