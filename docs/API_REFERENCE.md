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

### Workflow 2: Create and Use Binary Cache ⚡

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

# Response: Cache created (12.5 MB, TTFT: 85ms)

# 3. Use cache in chat completion (50-70% TTFT reduction!)
curl -X POST http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3-0.6b",
    "use_cache": "system",
    "messages": [
      {"role": "user", "content": "Write a Python hello world"}
    ]
  }'

# Response includes cache info:
# {
#   "usage": {
#     "cache_hit": true,
#     "cached_prompts": ["system"]
#   }
# }

# 4. Baseline TTFT: 200ms → With cache: 60-100ms ⚡
```

**How it works:**
1. **Cache stores NPU state** for the system prompt (one-time cost: 85-180ms)
2. **Load cache** in subsequent requests (instant NPU state restore)
3. **Process new messages** on top of cached state
4. **Result**: 50-70% TTFT reduction for every request!

**Use case example - Coding assistant:**
```bash
# Cache the system prompt once
POST /v1/cache/qwen3-0.6b
{"cache_name": "coding", "prompt": "You are an expert Python developer..."}

# Every request uses the cache
POST /v1/chat/completions
{
  "model": "qwen3-0.6b",
  "use_cache": "coding",  # ⚡ Loads cached system prompt
  "messages": [
    {"role": "user", "content": "Fix this bug: ..."}
  ]
}
# TTFT: 60ms instead of 200ms!
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

## 🎯 Using Binary Cache with Chat/Completions ⚡

### Chat Completion with Cache
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3-0.6b",
    "use_cache": "system",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.8,
    "max_tokens": 200
  }'
```

**Response shows cache was used:**
```json
{
  "id": "chatcmpl-abc123",
  "choices": [...],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 10,
    "total_tokens": 35,
    "cache_hit": true,
    "cached_prompts": ["system"]
  }
}
```

### Text Completion with Cache
```bash
curl -X POST http://localhost:8080/v1/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3-0.6b",
    "use_cache": "coding",
    "prompt": "def fibonacci(n):\n",
    "max_tokens": 100
  }'
```

### Performance Impact
- **Without cache**: TTFT = 200-250ms
- **With cache**: TTFT = 60-100ms
- **Reduction**: 50-70% faster! ⚡

### How It Works
1. **Cache creation** (one-time): NPU processes prompt, saves internal state
2. **Cache loading**: RKLLM restores NPU state instantly (no recomputation)
3. **New content**: Chat messages/prompt appended and processed
4. **Result**: Skip prefill for cached portion = massive speedup!

### Best Practices
- ✅ Cache **system prompts** (stable, reused across requests)
- ✅ Cache **coding rules** (large, doesn't change)
- ✅ Cache **project context** (documentation, guidelines)
- ❌ Don't cache user messages (always unique)
- ❌ Don't cache variable content (defeats the purpose)
