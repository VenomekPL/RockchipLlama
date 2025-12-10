# RockchipLlama Testing Guide

This document outlines the testing scenarios for verifying the RockchipLlama server on RK3588 hardware (Orange Pi 5 Max).

## 🛠️ Prerequisites

1.  **Hardware**: Orange Pi 5 Max (RK3588) with 16GB RAM.
2.  **Environment**: Python virtual environment activated.
3.  **Server**: Running locally on port 8080.

```bash
source venv/bin/activate
./start_server.sh
```

## 🧪 Test Scenarios

### 1. Smoke Test (Basic Inference)
**Goal**: Verify the server is up, model loads, and basic inference works.
**Script**: `scripts/test_simple_inference.py`

```bash
python scripts/test_simple_inference.py
```
**Success Criteria**:
- Server returns 200 OK.
- Model loads successfully.
- A coherent response is generated.

### 2. Chat Template Verification (New Feature)
**Goal**: Ensure the `chat_template` config in `inference_config.json` is correctly applied by the RKLLM runtime.
**Method**: Use a strong system prompt that requires specific formatting to be respected.

**Manual Test**:
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-0.6b",
    "messages": [
      {"role": "system", "content": "You are a pirate. Always speak like a pirate."},
      {"role": "user", "content": "Hello, who are you?"}
    ],
    "temperature": 0.1
  }'
```
**Success Criteria**:
- Response starts with "Ahoy!" or similar pirate-speak.
- If the response is generic ("I am an AI assistant"), the template might be failing to pass the system prompt correctly.

### 3. Concurrency & Queue System
**Goal**: Verify the queue handles multiple simultaneous requests without crashing or mixing up responses.
**Script**: `scripts/test_batch_concurrent.py`

```bash
# Test with 4 concurrent requests
python scripts/test_batch_concurrent.py
```
**Success Criteria**:
- All 4 requests complete successfully.
- No "Server Busy" errors (unless queue is full).
- Logs show requests being queued and processed.

### 4. Binary Caching (Performance)
**Goal**: Verify that creating and using a binary cache reduces Time To First Token (TTFT).
**Script**: `scripts/test_benchmark.py`

```bash
python scripts/test_benchmark.py
```
**Success Criteria**:
- First run (Cache Creation): TTFT ~1-2s.
- Second run (Cache Hit): TTFT < 100ms.
- API returns `cache_hit: true`.

### 5. Ollama API Compatibility
**Goal**: Verify the server works with Ollama clients/endpoints.
**Method**: Use `curl` to hit the Ollama-style endpoints.

```bash
# Generate Endpoint
curl -X POST http://localhost:8080/api/generate -d '{
  "model": "qwen3-0.6b",
  "prompt": "Why is the sky blue?",
  "stream": false
}'

# Chat Endpoint
curl -X POST http://localhost:8080/api/chat -d '{
  "model": "qwen3-0.6b",
  "messages": [ { "role": "user", "content": "Hello!" } ],
  "stream": false
}'
```
**Success Criteria**:
- JSON response follows Ollama format (`response` field instead of `choices`).
- `done: true` is present.

### 6. Stability & Memory Leak Check
**Goal**: Ensure repeated model loading/unloading doesn't crash the NPU.
**Script**: Custom loop script (to be created if needed).

```bash
# Simple loop test
for i in {1..10}; do
  curl -X POST http://localhost:8080/v1/models/unload
  curl -X POST http://localhost:8080/v1/models/load -d '{"model": "qwen3-0.6b"}'
  sleep 2
done
```
**Success Criteria**:
- No segmentation faults in server logs.
- Memory usage (htop) remains stable.

## 📋 Test Checklist for Release v1.0

| Feature | Test Method | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Basic Inference** | `test_simple_inference.py` | ⬜ | |
| **Chat Templates** | Pirate Prompt Test | ⬜ | Needs verification with v1.2.3 |
| **Queue System** | `test_batch_concurrent.py` | ⬜ | |
| **Binary Cache** | `test_benchmark.py` | ⬜ | Expect ~75ms TTFT |
| **Ollama API** | `curl /api/chat` | ⬜ | |
| **Model Switching** | Load/Unload Loop | ⬜ | |
