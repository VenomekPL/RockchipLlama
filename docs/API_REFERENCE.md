# RockchipLlama API Reference

## Base URL
```
http://localhost:8080/v1
```

---

## 📦 Model Management Endpoints

### Load Model
```http
POST /v1/models/load
Content-Type: application/json

{
  "model": "qwen3-0.6b"
}
```

**Response:**
```json
{
  "success": true,
  "model": "qwen3-0.6b",
  "message": "Model loaded successfully"
}
```

---

### Unload Model
```http
POST /v1/models/unload
```

**Response:**
```json
{
  "success": true,
  "message": "Model unloaded successfully"
}
```

---

### Get Loaded Model
```http
GET /v1/models/loaded
```

**Response:**
```json
{
  "loaded": true,
  "model": "qwen3-0.6b"
}
```

---

### Get Available Models
```http
GET /v1/models/available
```

**Response:**
```json
{
  "models": [
    {
      "name": "qwen3-0.6b",
      "path": "/path/to/model.rkllm",
      "size_mb": 450.2
    }
  ]
}
```

---

## 💬 Chat Endpoints

### Chat Completion (OpenAI Compatible)
**✨ Accepts multiple messages like OpenAI's chat API!**

```http
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "qwen3-0.6b",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.8,
  "max_tokens": 512,
  "stream": false
}
```

**Multi-turn conversation example:**
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3-0.6b",
    "messages": [
      {"role": "system", "content": "You are a coding assistant."},
      {"role": "user", "content": "What is Python?"},
      {"role": "assistant", "content": "Python is a high-level programming language..."},
      {"role": "user", "content": "Show me a hello world example"}
    ]
  }'
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1729467234,
  "model": "qwen3-0.6b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 10,
    "total_tokens": 35
  }
}
```

---

### Text Completion (OpenAI Compatible) 🆕
**Simple one-shot completion without chat formatting**

```http
POST /v1/completions
Content-Type: application/json

{
  "model": "qwen3-0.6b",
  "prompt": "Once upon a time",
  "temperature": 0.8,
  "max_tokens": 256
}
```

**Example:**
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3-0.6b",
    "prompt": "def fibonacci(n):\n    # Python function to calculate fibonacci\n",
    "max_tokens": 200,
    "temperature": 0.7
  }'
```

**Response:**
```json
{
  "id": "cmpl-abc123",
  "object": "text_completion",
  "created": 1729467234,
  "model": "qwen3-0.6b",
  "choices": [
    {
      "text": "    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
      "index": 0,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 28,
    "total_tokens": 43
  }
}
```

**When to use:**
- ✅ Code completion
- ✅ Story/text generation
- ✅ Single-shot prompts
- ❌ Multi-turn conversations (use `/v1/chat/completions` instead)

---

## 🚀 Binary Cache Endpoints

### Create Binary Cache (for currently loaded model)
```http
POST /v1/cache/{model_name}
Content-Type: application/json

{
  "cache_name": "system",
  "prompt": "You are a helpful AI assistant specialized in coding..."
}
```

**Example:**
```bash
# Make sure model is loaded first!
curl -X POST http://localhost:8080/v1/models/load \
  -H 'Content-Type: application/json' \
  -d '{"model": "qwen3-0.6b"}'

# Then create cache
curl -X POST http://localhost:8080/v1/cache/qwen3-0.6b \
  -H 'Content-Type: application/json' \
  -d '{
    "cache_name": "system",
    "prompt": "You are a helpful AI assistant specialized in coding. You provide clear, concise answers."
  }'
```

**Response:**
```json
{
  "object": "cache.created",
  "model": "qwen3-0.6b",
  "cache_name": "system",
  "size_mb": 12.5,
  "ttft_ms": 85.3,
  "prompt_length": 150,
  "timestamp": 1729467234,
  "message": "Binary cache generated successfully (12.50 MB)"
}
```

**Notes:**
- ⚠️ **Model must be loaded** before creating cache
- ⚠️ **Must match loaded model** - If `qwen3-0.6b` is loaded, use `/v1/cache/qwen3-0.6b`
- Creates `.rkllm_cache` file containing NPU state
- Saves 50-70% TTFT on subsequent requests
- Cache files stored in `cache/{model_name}/{cache_name}.rkllm_cache`

---

### List All Caches (All Models)
```http
GET /v1/cache
```

**Response:**
```json
{
  "qwen3-0.6b": [
    {
      "cache_name": "system",
      "size_mb": 12.5,
      "created_at": 1729467234,
      "modified_at": 1729467234,
      "prompt_length": 150,
      "source": "api"
    }
  ],
  "qwen3-1.5b": [
    {
      "cache_name": "coding_rules",
      "size_mb": 15.2,
      "created_at": 1729467100,
      "modified_at": 1729467100,
      "prompt_length": 200,
      "source": "api"
    }
  ]
}
```

---

### List Caches for Specific Model
```http
GET /v1/cache/{model_name}
```

**Example:**
```bash
curl http://localhost:8080/v1/cache/qwen3-0.6b
```

**Response:**
```json
[
  {
    "cache_name": "system",
    "size_mb": 12.5,
    "created_at": 1729467234,
    "modified_at": 1729467234,
    "prompt_length": 150,
    "source": "api"
  },
  {
    "cache_name": "coding_rules",
    "size_mb": 13.1,
    "created_at": 1729467300,
    "modified_at": 1729467300,
    "prompt_length": 180,
    "source": "api"
  }
]
```

---

### Get Specific Cache Info
```http
GET /v1/cache/{model_name}/{cache_name}
```

**Example:**
```bash
curl http://localhost:8080/v1/cache/qwen3-0.6b/system
```

**Response:**
```json
{
  "cache_name": "system",
  "size_mb": 12.5,
  "created_at": 1729467234,
  "modified_at": 1729467234,
  "prompt_length": 150,
  "source": "api"
}
```

---

### Delete Cache
```http
DELETE /v1/cache/{model_name}/{cache_name}
```

**Example:**
```bash
curl -X DELETE http://localhost:8080/v1/cache/qwen3-0.6b/old_cache
```

**Response:**
```json
{
  "object": "cache.deleted",
  "deleted": true,
  "cache_name": "old_cache"
}
```

**Note:** Cannot delete `system` cache (protected)

---

## 🔍 Utility Endpoints

### List Models (OpenAI Compatible)
**Returns model IDs in OpenAI format for API usage**

```http
GET /v1/models
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "qwen3-0.6b",
      "object": "model",
      "created": 1729467234,
      "owned_by": "rockchip"
    }
  ]
}
```

**Use case:** OpenAI-compatible clients, get model names for API calls

---

### Health Check
```http
GET /v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "current_model": "qwen3-0.6b"
}
```

---

## 🔄 Endpoint Comparison

### `/v1/models` vs `/v1/models/available`

| Feature | `/v1/models` | `/v1/models/available` |
|---------|--------------|------------------------|
| **Standard** | OpenAI-compatible | Custom |
| **Purpose** | Get model IDs for API | Get detailed model info |
| **Returns** | Model IDs only | Size, path, loaded status |
| **Use for** | Client compatibility | Server management |

**Example difference:**

```bash
# /v1/models (OpenAI format)
GET /v1/models
{
  "data": [
    {"id": "qwen3-0.6b", "object": "model", "owned_by": "rockchip"}
  ]
}

# /v1/models/available (detailed info)
GET /v1/models/available
{
  "models": [
    {
      "name": "qwen3-0.6b",
      "friendly_name": "qwen3-0.6b",
      "size_mb": 450.2,
      "path": "/path/to/qwen3-0.6b.rkllm",
      "loaded": true
    }
  ],
  "total": 1,
  "loaded_model": "qwen3-0.6b"
}
```

---

## 📝 Common Workflows

### Workflow 1: Basic Chat
```bash
# 1. Load model
curl -X POST http://localhost:8080/v1/models/load \
  -H 'Content-Type: application/json' \
  -d '{"model": "qwen3-0.6b"}'

# 2. Chat
curl -X POST http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3-0.6b",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

---

### Workflow 2: Create and Use Binary Cache

```bash
# 1. Load model
curl -X POST http://localhost:8080/v1/models/load \
  -H 'Content-Type: application/json' \
  -d '{"model": "qwen3-0.6b"}'

# 2. Create binary cache for system prompt
curl -X POST http://localhost:8080/v1/cache/qwen3-0.6b \
  -H 'Content-Type: application/json' \
  -d '{
    "cache_name": "system",
    "prompt": "You are a helpful AI assistant specialized in coding."
  }'

# 3. List caches to verify
curl http://localhost:8080/v1/cache/qwen3-0.6b

# 4. TODO: Use cache in chat (integration coming next)
# Will add `use_cache` parameter to chat endpoint
```

---

### Workflow 3: Cache Management

```bash
# List all caches across all models
curl http://localhost:8080/v1/cache

# List caches for specific model
curl http://localhost:8080/v1/cache/qwen3-0.6b

# Get specific cache info
curl http://localhost:8080/v1/cache/qwen3-0.6b/system

# Delete cache
curl -X DELETE http://localhost:8080/v1/cache/qwen3-0.6b/old_cache
```

---

## ⚠️ Important Notes

### Binary Cache Creation Requirements
1. **Model MUST be loaded first** - Cache generation requires active model
2. **Model name must match** - Use same model name in URL as loaded model
3. **One model at a time** - Only one model can be loaded simultaneously
4. **Cache persists** - Cache files remain after model unload

### Error Handling
- **503 Service Unavailable** - No model loaded
- **400 Bad Request** - Model name mismatch or invalid parameters
- **403 Forbidden** - Trying to delete protected cache (e.g., `system`)
- **404 Not Found** - Cache doesn't exist
- **500 Internal Server Error** - Cache generation failed

---

## 🎯 Next Steps

### Coming Soon: Cache Loading in Chat
```bash
# Will be able to use cache in chat like this:
curl -X POST http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3-0.6b",
    "use_cache": "system",  # 👈 Load binary cache
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'

# Expected: 50-70% TTFT reduction (200ms → 60-100ms)
```

This will load the cached NPU state for the system prompt, then process new messages on top of it.
