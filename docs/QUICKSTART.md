# RockchipLlama - Quick Start Guide

## Phase 2 Complete! ✅

We've successfully built a **FastAPI-based OpenAI-compatible REST API server** with proper modular structure!

## What's Working

### ✅ Server Infrastructure
- FastAPI server running on `http://0.0.0.0:8080`
- Auto-reload enabled for development
- CORS middleware configured
- Global exception handling
- Logging system

### ✅ API Endpoints (OpenAI Compatible)

#### 1. **GET /** - Server Info
```bash
curl http://localhost:8080/
```

#### 2. **GET /v1/models** - List Available Models
```bash
curl http://localhost:8080/v1/models
```
Returns all 3 models:
- `gemma-3-1b-it_w8a8`
- `Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588`
- `google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588`

#### 3. **POST /v1/chat/completions** - Chat Completion
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma-3-270m",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ],
    "max_tokens": 100,
    "temperature": 0.8
  }'
```

Supports both streaming and non-streaming modes!

#### 4. **GET /v1/health** - Health Check
```bash
curl http://localhost:8080/v1/health
```

#### 5. **GET /docs** - Interactive API Documentation
Open in browser: http://192.168.10.53:8080/docs

## Project Structure

```
RockchipLlama/
├── venv/                    # Python virtual environment ✅
├── requirements.txt         # Dependencies ✅
├── test_api.py             # Test script ✅
├── models/                  # Your 3 .rkllm models ✅
│   ├── gemma-3-1b-it_w8a8.rkllm
│   ├── Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm
│   └── google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm
└── src/                     # Application source ✅
    ├── main.py             # FastAPI entry point (routing master)
    ├── api/                # API routes (separate logic)
    │   ├── schemas.py      # Pydantic models (OpenAI spec)
    │   └── openai_routes.py # OpenAI-compatible endpoints
    ├── models/             # Model management
    │   └── rkllm_model.py  # RKLLM wrapper (placeholder)
    └── config/             # Configuration
        └── settings.py     # Server settings
```

## How to Run

### Start Server
```bash
cd /home/angeiv/AI/RockchipLlama/src
source ../venv/bin/activate
python main.py
```

Server will start on: `http://0.0.0.0:8080`

### Run Tests
```bash
cd /home/angeiv/AI/RockchipLlama
source venv/bin/activate
python scripts/test_api.py
```

### Access from Network
- Local: `http://localhost:8080`
- Network: `http://192.168.10.53:8080`
- Docs: `http://192.168.10.53:8080/docs`

## What's Next (Phase 3)

### 🔧 RKLLM Integration (Priority)
Currently using placeholder responses. Need to:
1. **Load RKLLM library** via ctypes
2. **Initialize model** with proper parameters
3. **Implement inference** with real NPU calls
4. **Add streaming callback** for token-by-token generation

### 📚 Reference Code Available
- Flask example: `external/rknn-llm/examples/rkllm_server_demo/flask_server.py`
- C++ API: `external/rknn-llm/examples/rkllm_api_demo/`
- Documentation: `docs/rkllm.md`

### 🎯 Next Steps
1. Study Flask reference implementation
2. Extract RKLLM ctypes bindings
3. Implement model loading in `rkllm_model.py`
4. Test with Gemma-3-270M (fastest model)
5. Add proper error handling

## Testing with OpenAI Client

The API is OpenAI-compatible! Test with official client:

```python
from openai import OpenAI

client = OpenAI(
    api_key="not-needed",
    base_url="http://localhost:8080/v1"
)

response = client.chat.completions.create(
    model="gemma-3-270m",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

## Architecture Highlights

### ✅ Modular Design
- **`main.py`**: Routing master, FastAPI app initialization
- **`openai_routes.py`**: All OpenAI endpoint logic (separate file as requested!)
- **`schemas.py`**: Pydantic models for type safety
- **`rkllm_model.py`**: Model wrapper (ready for RKLLM integration)

### ✅ OpenAI Specification Compliance
- Proper request/response schemas
- Token usage tracking
- Finish reasons
- Streaming support (SSE format)
- Model listing

### ✅ Production-Ready Features
- CORS enabled
- Exception handling
- Request logging
- Health checks
- Auto-generated docs

## Configuration

Edit `src/config/settings.py` or use environment variables:

```bash
HOST=0.0.0.0
PORT=8080
MODELS_DIR=/home/angeiv/AI/RockchipLlama/models
DEFAULT_MODEL=google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm
NUM_NPU_CORE=3
```

## Status

**Phase 2: ✅ COMPLETE**
- Venv created and configured
- All dependencies installed
- FastAPI server running
- OpenAI-compatible endpoints working
- Modular structure implemented
- Test suite passing

**Phase 3: 🔄 READY TO START**
- RKLLM runtime integration pending
- Real NPU inference pending
- Model loading pending

---

**🎉 Great progress! The API framework is complete and ready for RKLLM integration!**
