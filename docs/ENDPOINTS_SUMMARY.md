# API Endpoints Quick Reference

## 📝 Your Questions Answered

### 1. ✅ Chat endpoint accepts multiple messages in OpenAI format!

```json
{
  "model": "qwen3-0.6b",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a programming language..."},
    {"role": "user", "content": "Tell me more"}
  ]
}
```

### 2. 🆕 Added one-shot completion endpoint!

```bash
POST /v1/completions
{
  "model": "qwen3-0.6b",
  "prompt": "Once upon a time",
  "max_tokens": 256
}
```

### 3. 📊 Difference between model endpoints:

| Endpoint | Purpose | Returns |
|----------|---------|---------|
| `GET /v1/models` | OpenAI-compatible model list | Just model IDs |
| `GET /v1/models/available` | Detailed server info | Size, path, loaded status |

---

## 🎯 All Endpoints

### Chat & Completion

```
POST /v1/chat/completions      # Multi-turn chat (OpenAI format)
POST /v1/completions           # One-shot text completion 🆕
```

### Model Management

```
POST /v1/models/load           # Load a model
POST /v1/models/unload         # Unload current model
GET  /v1/models/loaded         # Check which model is loaded
GET  /v1/models/available      # Detailed model info (size, path, status)
GET  /v1/models                # OpenAI-compatible model list
```

### Binary Cache

```
POST   /v1/cache/{model}              # Create binary cache
GET    /v1/cache                      # List all caches (all models)
GET    /v1/cache/{model}              # List caches for model
GET    /v1/cache/{model}/{name}       # Get cache info
DELETE /v1/cache/{model}/{name}       # Delete cache
```

### Utility

```
GET /v1/health                 # Health check
```

---

## 💡 Quick Examples

### Multi-turn Chat
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3-0.6b",
    "messages": [
      {"role": "system", "content": "You are a coding assistant."},
      {"role": "user", "content": "Write a Python hello world"}
    ]
  }'
```

### One-shot Completion
```bash
curl -X POST http://localhost:8080/v1/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3-0.6b",
    "prompt": "def factorial(n):\n    # Calculate factorial\n",
    "max_tokens": 100
  }'
```

### Get Model Info
```bash
# Simple list (OpenAI format)
curl http://localhost:8080/v1/models

# Detailed info
curl http://localhost:8080/v1/models/available
```

---

## 🔍 When to Use What

### Chat vs Completion

| Use Case | Endpoint |
|----------|----------|
| Multi-turn conversation | `/v1/chat/completions` |
| System prompt + user message | `/v1/chat/completions` |
| Code completion | `/v1/completions` |
| Story generation | `/v1/completions` |
| Raw prompt continuation | `/v1/completions` |

### Models Endpoints

| Use Case | Endpoint |
|----------|----------|
| Get model ID for API call | `GET /v1/models` |
| Check model file size | `GET /v1/models/available` |
| See which model is loaded | `GET /v1/models/available` |
| OpenAI client compatibility | `GET /v1/models` |
| Server administration | `GET /v1/models/available` |

---

## 📚 Complete Documentation

See **API_REFERENCE.md** for full examples, workflows, and detailed documentation.
