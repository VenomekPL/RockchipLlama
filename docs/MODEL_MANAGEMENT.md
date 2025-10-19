# Model Management Guide

## Overview

RockchipLlama now includes proper model management! Models must be **explicitly loaded** into memory before use.

## Quick Start

### 1. Check Available Models
```bash
curl http://localhost:8080/v1/models/available | jq
```

**Response:**
```json
{
  "models": [
    {
      "name": "google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588",
      "size_mb": 616.27,
      "loaded": false
    },
    ...
  ],
  "total": 3,
  "loaded_model": null
}
```

### 2. Load a Model
```bash
curl -X POST http://localhost:8080/v1/models/load \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588",
    "max_context_len": 512,
    "num_npu_core": 3
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Model google_gemma-3-270m... loaded successfully",
  "model_name": "google_gemma-3-270m...",
  "loaded": true
}
```

### 3. Check Loaded Model
```bash
curl http://localhost:8080/v1/models/loaded | jq
```

**Response:**
```json
{
  "loaded": true,
  "model_name": "google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588",
  "model_path": "/home/angeiv/AI/RockchipLlama/models/google_gemma-3-270m..."
}
```

### 4. Use Chat Completion
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google_gemma-3-270m",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

### 5. Unload Model
```bash
curl -X POST http://localhost:8080/v1/models/unload
```

## API Endpoints

### Model Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/models/available` | GET | List all models in models/ directory |
| `/v1/models/load` | POST | Load a model into memory |
| `/v1/models/unload` | POST | Unload current model |
| `/v1/models/loaded` | GET | Get currently loaded model info |

### Chat (OpenAI Compatible)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | Generate chat completion (requires loaded model) |
| `/v1/models` | GET | List models (OpenAI format) |
| `/v1/health` | GET | Health check |

## Console Interaction Methods

### 1. Using curl (Command Line)
```bash
# List models
curl http://localhost:8080/v1/models/available

# Load model
curl -X POST http://localhost:8080/v1/models/load \
  -H "Content-Type: application/json" \
  -d '{"model": "gemma-3-270m"}'

# Chat
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "test", "messages": [{"role": "user", "content": "Hi"}]}'
```

### 2. Using HTTPie (Prettier)
```bash
# Install: pip install httpie

# List models
http GET :8080/v1/models/available

# Load model
http POST :8080/v1/models/load model=gemma-3-270m

# Chat
http POST :8080/v1/chat/completions \
  model=test \
  messages:='[{"role":"user","content":"Hi"}]'
```

### 3. Using Python Requests
```python
import requests

# Load model
response = requests.post(
    "http://localhost:8080/v1/models/load",
    json={"model": "gemma-3-270m"}
)
print(response.json())

# Chat
response = requests.post(
    "http://localhost:8080/v1/chat/completions",
    json={
        "model": "test",
        "messages": [{"role": "user", "content": "Hello!"}]
    }
)
print(response.json())
```

### 4. Using OpenAI Python Client
```python
from openai import OpenAI

client = OpenAI(
    api_key="not-needed",
    base_url="http://localhost:8080/v1"
)

# First load model via regular requests
import requests
requests.post(
    "http://localhost:8080/v1/models/load",
    json={"model": "gemma-3-270m"}
)

# Then use OpenAI client
response = client.chat.completions.create(
    model="test",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### 5. Using Test Scripts
```bash
# Test all functionality
python test_model_management.py

# Test OpenAI compatibility
python test_api.py
```

### 6. Interactive API Docs (Swagger)
Open in browser: **http://192.168.10.53:8080/docs**

- Try all endpoints interactively
- See request/response schemas
- Built-in authentication testing

## Workflow

### Typical Usage Pattern
```bash
# 1. Start server
./start_server.sh

# 2. Check what models are available
curl http://localhost:8080/v1/models/available | jq

# 3. Load smallest model for testing
curl -X POST http://localhost:8080/v1/models/load \
  -H "Content-Type: application/json" \
  -d '{"model": "google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588"}'

# 4. Verify it loaded
curl http://localhost:8080/v1/models/loaded | jq

# 5. Use chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "test",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }' | jq

# 6. When done, unload model
curl -X POST http://localhost:8080/v1/models/unload
```

## Important Notes

### Model Loading
- **Loading takes time**: Model initialization can take 5-30 seconds depending on size
- **One model at a time**: Loading a new model unloads the current one
- **Memory required**: Ensure sufficient RAM for model + context (650MB-1.5GB per model)
- **Automatic path resolution**: Models are found in `/models/` directory automatically

### Model Names
You can use either:
- Full name: `google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588`
- Short name: `google_gemma-3-270m` (will find the .rkllm file)
- With extension: `gemma-3-1b-it_w8a8.rkllm`

### Error Handling
- **No model loaded**: Returns 400 error with helpful message
- **Model not found**: Returns 404 with available models
- **Loading failure**: Returns 500 with error details

## Your Models

Currently available:
1. **google_gemma-3-270m** (616 MB) - Smallest, fastest ⚡
2. **Qwen_Qwen3-0.6B** (909 MB) - Medium size
3. **gemma-3-1b-it** (1.5 GB) - Largest, instruction-tuned

## Next Steps

Once RKLLM runtime is integrated (Phase 3):
- Real NPU inference instead of placeholders
- Actual token generation
- Streaming responses
- Performance optimization

## Testing

Run comprehensive tests:
```bash
# Test model management
python test_model_management.py

# Test API compatibility  
python test_api.py
```

Both scripts include detailed output and error checking.
