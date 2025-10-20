# Unified API Architecture: Embeddings + Chat + Ollama

**Date:** October 21, 2025  
**Status:** 🎯 Implementation Plan  
**Goal:** Single queue serving OpenAI (chat + embeddings) AND Ollama APIs

---

## 🎉 Discovery: RKLLM Supports Embeddings!

```c
// RKLLM has built-in embedding extraction
RKLLM_INFER_GET_LAST_HIDDEN_LAYER = 1

// Returns hidden states from last layer
typedef struct {
    const float* hidden_states;  // Pointer to embeddings
    int embd_size;               // Dimension (e.g., 896 for Qwen3-0.6B)
    int num_tokens;              // Number of tokens embedded
} RKLLMResultLastHiddenLayer;
```

**This means we can build:**
- ✅ `/v1/embeddings` (OpenAI-compatible)
- ✅ `/api/embeddings` (Ollama-compatible)
- ✅ Both share same model, same queue!

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer                                │
├──────────────────────┬──────────────────────────────────────┤
│   OpenAI Routes      │         Ollama Routes                │
├──────────────────────┼──────────────────────────────────────┤
│ /v1/chat/completions │ /api/generate                        │
│ /v1/embeddings       │ /api/embeddings                      │
└──────────┬───────────┴──────────────┬───────────────────────┘
           │                          │
           ▼                          ▼
    ┌─────────────┐          ┌─────────────┐
    │   OpenAI    │          │   Ollama    │
    │  Adapters   │          │  Adapters   │
    └──────┬──────┘          └──────┬──────┘
           │                        │
           └────────────┬───────────┘
                        ▼
           ┌─────────────────────────┐
           │  Internal Request Type  │
           │  - InferenceRequest     │
           │  - EmbeddingRequest     │
           └───────────┬─────────────┘
                       │
                       ▼
           ┌─────────────────────────┐
           │   Unified Queue         │
           │   (asyncio.Semaphore)   │
           │   All requests queued!  │
           └───────────┬─────────────┘
                       │
                       ▼
           ┌─────────────────────────┐
           │   RKLLM Model           │
           │   - Mode: GENERATE      │
           │   - Mode: EMBEDDINGS    │
           └───────────┬─────────────┘
                       │
                       ▼
           ┌─────────────────────────┐
           │  Response Adapters      │
           │  Internal → API Format  │
           └─────────────────────────┘
```

---

## Request Flow Examples

### Example 1: OpenAI Chat Request
```
User: POST /v1/chat/completions
      {"model": "qwen", "messages": [...]}
      
  ↓ OpenAI Adapter
  
Internal: InferenceRequest(prompt="...", mode=GENERATE)
      
  ↓ Queue (position 1)
  
RKLLM: rkllm_run(mode=RKLLM_INFER_GENERATE)
      
  ↓ Response Adapter
  
User: {"choices": [{"message": {"content": "..."}}]}
```

### Example 2: OpenAI Embeddings Request
```
User: POST /v1/embeddings
      {"model": "qwen", "input": "Hello world"}
      
  ↓ OpenAI Adapter
  
Internal: EmbeddingRequest(text="Hello world", mode=EMBEDDINGS)
      
  ↓ Queue (position 2, waits for chat to finish)
  
RKLLM: rkllm_run(mode=RKLLM_INFER_GET_LAST_HIDDEN_LAYER)
      
  ↓ Extract hidden states
  
User: {"data": [{"embedding": [0.123, -0.456, ...]}]}
```

### Example 3: Ollama Generate Request
```
User: POST /api/generate
      {"model": "qwen", "prompt": "..."}
      
  ↓ Ollama Adapter
  
Internal: InferenceRequest(prompt="...", mode=GENERATE)
      
  ↓ Queue (position 3, shared with OpenAI!)
  
RKLLM: rkllm_run(mode=RKLLM_INFER_GENERATE)
      
  ↓ Response Adapter
  
User: {"response": "...", "done": true}
```

### Example 4: Mixed Requests (Queue Magic!)
```
Request Timeline:
  t=0.0s: OpenAI chat arrives → Queue position 1
  t=0.1s: Ollama generate arrives → Queue position 2 (waits)
  t=0.2s: OpenAI embeddings arrives → Queue position 3 (waits)
  
Processing:
  t=0.0-2.5s: OpenAI chat processing (2.5s)
  t=2.5-2.7s: Ollama generate processing (0.2s, short prompt)
  t=2.7-3.0s: OpenAI embeddings processing (0.3s, fast)
  
Total: 3 requests, 3 seconds, all APIs work together!
```

---

## Implementation Plan

### Phase 1: Internal Request Types ✅ (Foundation)

**File:** `src/models/inference_types.py`

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class InferenceMode(Enum):
    GENERATE = "generate"      # Text generation
    EMBEDDINGS = "embeddings"  # Extract embeddings

@dataclass
class InferenceRequest:
    """Unified request format for all APIs"""
    prompt: str
    mode: InferenceMode = InferenceMode.GENERATE
    
    # Generation params (used when mode=GENERATE)
    max_tokens: int = 512
    temperature: float = 0.8
    top_p: float = 0.9
    top_k: int = 20
    stop: list[str] | None = None
    stream: bool = False
    
    # Embedding params (used when mode=EMBEDDINGS)
    # (embeddings are automatic, just need mode switch)
    
    # Metadata
    request_id: str = ""
    source_api: str = "openai"  # "openai" or "ollama"

@dataclass
class InferenceResponse:
    """Unified response format"""
    # For generation
    text: str | None = None
    finish_reason: str | None = None
    
    # For embeddings
    embedding: list[float] | None = None
    embedding_dim: int | None = None
    
    # Common
    tokens_processed: int = 0
    time_ms: float = 0.0
    request_id: str = ""
```

### Phase 2: RKLLM Model Updates ✅ (Core)

**File:** `src/models/rkllm_model.py`

**Add embedding support:**

```python
def get_embeddings(
    self,
    prompt: str,
    callback: Optional[Callable[[str], None]] = None
) -> tuple[list[float], Optional[dict]]:
    """
    Extract embeddings from prompt using last hidden layer
    
    Args:
        prompt: Input text to embed
        callback: Optional callback (not used for embeddings)
        
    Returns:
        (embedding_vector, performance_stats)
    """
    self.generated_text.clear()
    self.generation_state = LLMCallState.RKLLM_RUN_NORMAL
    self.current_callback = callback
    self.perf_stats = None
    
    # Create input
    rkllm_input = RKLLMInput()
    rkllm_input.role = b"user"
    rkllm_input.enable_thinking = False
    rkllm_input.input_type = RKLLMInputType.RKLLM_INPUT_PROMPT
    rkllm_input.prompt_input = prompt.encode('utf-8')
    
    # Configure for embeddings extraction
    infer_param = RKLLMInferParam()
    infer_param.mode = RKLLMInferMode.RKLLM_INFER_GET_LAST_HIDDEN_LAYER  # ← KEY!
    infer_param.keep_history = 0
    infer_param.lora_params = None
    infer_param.prompt_cache_params = None
    
    logger.info("Running NPU inference for embeddings...")
    
    # Run inference
    ret = self.lib.rkllm_run(
        self.handle,
        ctypes.byref(rkllm_input),
        ctypes.byref(infer_param),
        None
    )
    
    if ret != 0:
        raise RuntimeError(f"rkllm_run failed with code {ret}")
    
    # Extract embeddings from callback result
    # (Need to update callback to capture hidden states)
    if self.last_hidden_states is not None:
        embedding = self.last_hidden_states.copy()
        return embedding, self.perf_stats
    else:
        raise RuntimeError("No embeddings returned from model")

async def get_embeddings_async(
    self,
    prompt: str,
    callback: Optional[Callable[[str], None]] = None
) -> tuple[list[float], Optional[dict]]:
    """
    Async wrapper for get_embeddings with queue management
    
    Same semaphore as generate_async - all requests queued together!
    """
    if self._batch_semaphore is None:
        raise RuntimeError("Model not loaded")
    
    async with self._batch_semaphore:
        # Run in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.get_embeddings(prompt=prompt, callback=callback)
        )
        return result
```

**Update callback to capture embeddings:**

```python
def _callback_impl(self, result, userdata, state):
    """Internal callback - handle both text and embeddings"""
    try:
        if state == LLMCallState.RKLLM_RUN_FINISH:
            self.generation_state = state
            
            # Extract performance stats
            if result and result.contents:
                perf = result.contents.perf
                self.perf_stats = {
                    'prefill_time_ms': perf.prefill_time_ms,
                    'prefill_tokens': perf.prefill_tokens,
                    'generate_time_ms': perf.generate_time_ms,
                    'generate_tokens': perf.generate_tokens,
                    'memory_usage_mb': perf.memory_usage_mb
                }
                
                # Check if we got embeddings (last hidden layer)
                hidden = result.contents.last_hidden_layer
                if hidden.embd_size != 0:
                    # Extract embeddings as list
                    num_floats = hidden.embd_size * hidden.num_tokens
                    self.last_hidden_states = [
                        hidden.hidden_states[i] for i in range(num_floats)
                    ]
                    logger.debug(f"Extracted embeddings: dim={hidden.embd_size}, tokens={hidden.num_tokens}")
                    
        # ... existing text generation handling ...
```

### Phase 3: Format Adapters ✅ (Translation)

**File:** `src/api/adapters.py` (NEW)

```python
"""Format adapters for different API styles"""
from src.models.inference_types import InferenceRequest, InferenceResponse, InferenceMode
from src.api.schemas import (
    ChatCompletionRequest, ChatCompletionResponse,
    EmbeddingRequest, EmbeddingResponse,
    OllamaGenerateRequest, OllamaGenerateResponse,
    OllamaEmbeddingRequest, OllamaEmbeddingResponse
)
import time

# ============================================================================
# OpenAI → Internal
# ============================================================================

def openai_chat_to_internal(request: ChatCompletionRequest) -> InferenceRequest:
    """Convert OpenAI chat request to internal format"""
    # Extract prompt from messages (last user message)
    prompt = ""
    for msg in request.messages:
        if msg.role == "user":
            prompt = msg.content
    
    return InferenceRequest(
        prompt=prompt,
        mode=InferenceMode.GENERATE,
        max_tokens=request.max_tokens or 512,
        temperature=request.temperature or 0.8,
        top_p=request.top_p or 0.9,
        stream=request.stream or False,
        stop=request.stop,
        source_api="openai",
        request_id=f"chatcmpl-{int(time.time()*1000)}"
    )

def openai_embedding_to_internal(request: EmbeddingRequest) -> InferenceRequest:
    """Convert OpenAI embedding request to internal format"""
    # Handle both string and array input
    if isinstance(request.input, str):
        prompt = request.input
    else:
        prompt = request.input[0]  # For now, handle first item
    
    return InferenceRequest(
        prompt=prompt,
        mode=InferenceMode.EMBEDDINGS,
        source_api="openai",
        request_id=f"embed-{int(time.time()*1000)}"
    )

# ============================================================================
# Ollama → Internal
# ============================================================================

def ollama_generate_to_internal(request: OllamaGenerateRequest) -> InferenceRequest:
    """Convert Ollama generate request to internal format"""
    return InferenceRequest(
        prompt=request.prompt,
        mode=InferenceMode.GENERATE,
        max_tokens=request.options.get("num_predict", 512) if request.options else 512,
        temperature=request.options.get("temperature", 0.8) if request.options else 0.8,
        top_p=request.options.get("top_p", 0.9) if request.options else 0.9,
        top_k=request.options.get("top_k", 20) if request.options else 20,
        stream=request.stream or False,
        source_api="ollama",
        request_id=f"ollama-{int(time.time()*1000)}"
    )

def ollama_embedding_to_internal(request: OllamaEmbeddingRequest) -> InferenceRequest:
    """Convert Ollama embedding request to internal format"""
    return InferenceRequest(
        prompt=request.prompt,
        mode=InferenceMode.EMBEDDINGS,
        source_api="ollama",
        request_id=f"ollama-embed-{int(time.time()*1000)}"
    )

# ============================================================================
# Internal → OpenAI
# ============================================================================

def internal_to_openai_chat(response: InferenceResponse, request_id: str) -> ChatCompletionResponse:
    """Convert internal response to OpenAI chat format"""
    return ChatCompletionResponse(
        id=request_id,
        object="chat.completion",
        created=int(time.time()),
        model="rkllm",
        choices=[{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response.text or ""
            },
            "finish_reason": response.finish_reason or "stop"
        }],
        usage={
            "prompt_tokens": 0,
            "completion_tokens": response.tokens_processed,
            "total_tokens": response.tokens_processed
        }
    )

def internal_to_openai_embedding(response: InferenceResponse, request_id: str) -> EmbeddingResponse:
    """Convert internal response to OpenAI embedding format"""
    return EmbeddingResponse(
        object="list",
        data=[{
            "object": "embedding",
            "embedding": response.embedding or [],
            "index": 0
        }],
        model="rkllm",
        usage={
            "prompt_tokens": response.tokens_processed,
            "total_tokens": response.tokens_processed
        }
    )

# ============================================================================
# Internal → Ollama
# ============================================================================

def internal_to_ollama_generate(response: InferenceResponse) -> OllamaGenerateResponse:
    """Convert internal response to Ollama generate format"""
    return OllamaGenerateResponse(
        model="rkllm",
        created_at=int(time.time()),
        response=response.text or "",
        done=True,
        total_duration=int(response.time_ms * 1_000_000),  # Convert to nanoseconds
        eval_count=response.tokens_processed
    )

def internal_to_ollama_embedding(response: InferenceResponse) -> OllamaEmbeddingResponse:
    """Convert internal response to Ollama embedding format"""
    return OllamaEmbeddingResponse(
        embedding=response.embedding or []
    )
```

### Phase 4: API Endpoints ✅ (Routes)

**File:** `src/api/embeddings_routes.py` (NEW)

```python
"""OpenAI-compatible embeddings API"""
from fastapi import APIRouter, HTTPException
from src.api.schemas import EmbeddingRequest, EmbeddingResponse
from src.api.adapters import openai_embedding_to_internal, internal_to_openai_embedding
from src.models.inference_types import InferenceResponse

router = APIRouter(prefix="/v1", tags=["embeddings"])

@router.post("/embeddings", response_model=EmbeddingResponse)
async def create_embedding(request: EmbeddingRequest):
    """
    Create embeddings for input text
    
    Compatible with OpenAI embeddings API
    """
    from src.main import model_manager
    
    if not model_manager.is_loaded():
        raise HTTPException(status_code=503, detail="No model loaded")
    
    # Convert to internal format
    internal_req = openai_embedding_to_internal(request)
    
    # Get embeddings (uses shared queue!)
    model = model_manager.get_model()
    embedding, stats = await model.get_embeddings_async(
        prompt=internal_req.prompt
    )
    
    # Build response
    internal_resp = InferenceResponse(
        embedding=embedding,
        embedding_dim=len(embedding),
        tokens_processed=stats['prefill_tokens'] if stats else 0,
        time_ms=stats['prefill_time_ms'] if stats else 0.0,
        request_id=internal_req.request_id
    )
    
    # Convert to OpenAI format
    return internal_to_openai_embedding(internal_resp, internal_req.request_id)
```

**File:** `src/api/ollama_routes.py` (NEW)

```python
"""Ollama-compatible API"""
from fastapi import APIRouter, HTTPException
from src.api.schemas import (
    OllamaGenerateRequest, OllamaGenerateResponse,
    OllamaEmbeddingRequest, OllamaEmbeddingResponse
)
from src.api.adapters import (
    ollama_generate_to_internal, internal_to_ollama_generate,
    ollama_embedding_to_internal, internal_to_ollama_embedding
)
from src.models.inference_types import InferenceResponse

router = APIRouter(prefix="/api", tags=["ollama"])

@router.post("/generate", response_model=OllamaGenerateResponse)
async def ollama_generate(request: OllamaGenerateRequest):
    """Ollama-compatible generate endpoint"""
    from src.main import model_manager
    
    if not model_manager.is_loaded():
        raise HTTPException(status_code=503, detail="No model loaded")
    
    # Convert to internal format
    internal_req = ollama_generate_to_internal(request)
    
    # Generate (uses shared queue with OpenAI!)
    model = model_manager.get_model()
    text, stats = await model.generate_async(
        prompt=internal_req.prompt,
        max_new_tokens=internal_req.max_tokens,
        temperature=internal_req.temperature,
        top_p=internal_req.top_p,
        top_k=internal_req.top_k
    )
    
    # Build response
    internal_resp = InferenceResponse(
        text=text,
        finish_reason="stop",
        tokens_processed=stats['generate_tokens'] if stats else 0,
        time_ms=(stats['prefill_time_ms'] + stats['generate_time_ms']) if stats else 0.0
    )
    
    # Convert to Ollama format
    return internal_to_ollama_generate(internal_resp)

@router.post("/embeddings", response_model=OllamaEmbeddingResponse)
async def ollama_embeddings(request: OllamaEmbeddingRequest):
    """Ollama-compatible embeddings endpoint"""
    from src.main import model_manager
    
    if not model_manager.is_loaded():
        raise HTTPException(status_code=503, detail="No model loaded")
    
    # Convert to internal format
    internal_req = ollama_embedding_to_internal(request)
    
    # Get embeddings (uses shared queue!)
    model = model_manager.get_model()
    embedding, _ = await model.get_embeddings_async(
        prompt=internal_req.prompt
    )
    
    # Build response
    internal_resp = InferenceResponse(
        embedding=embedding,
        embedding_dim=len(embedding)
    )
    
    # Convert to Ollama format
    return internal_to_ollama_embedding(internal_resp)
```

---

## Queue Behavior

### All Requests Share One Queue!

```python
# In RKLLMModel class
class RKLLMModel:
    _batch_semaphore: asyncio.Semaphore = None  # SHARED!
    
    async def generate_async(self, ...):
        async with self._batch_semaphore:  # ← Queue position
            # Generate text
            
    async def get_embeddings_async(self, ...):
        async with self._batch_semaphore:  # ← Same queue!
            # Extract embeddings
```

**Fairness:**
- Request arrives → gets next queue position
- Doesn't matter if it's chat, embedding, OpenAI, or Ollama
- First in, first out (FIFO)

---

## Testing Plan

### Test 1: Single Embedding
```bash
curl -X POST http://localhost:8080/v1/embeddings \
  -d '{
    "model": "qwen3-0.6b",
    "input": "The quick brown fox"
  }'

# Expected:
{
  "data": [{
    "embedding": [0.123, -0.456, 0.789, ...],  # 896 dimensions
    "index": 0
  }],
  "usage": {"prompt_tokens": 5, "total_tokens": 5}
}
```

### Test 2: Batch Embeddings
```bash
curl -X POST http://localhost:8080/v1/embeddings \
  -d '{
    "model": "qwen3-0.6b",
    "input": ["Hello", "World", "Test"]
  }'
```

### Test 3: Mixed APIs (Queue Test!)
```bash
# Terminal 1: OpenAI chat (slow)
time curl -X POST http://localhost:8080/v1/chat/completions \
  -d '{"messages": [{"role": "user", "content": "Write a story"}], "max_tokens": 500}'

# Terminal 2: (immediate) Ollama generate
time curl -X POST http://localhost:8080/api/generate \
  -d '{"prompt": "Quick question", "stream": false}'

# Terminal 3: (immediate) OpenAI embeddings
time curl -X POST http://localhost:8080/v1/embeddings \
  -d '{"input": "Test text"}'

# All should queue properly!
```

### Test 4: Similarity Search
```python
import numpy as np

# Get embeddings for documents
docs = ["Python is great", "I love programming", "The weather is nice"]
embeddings = [get_embedding(doc) for doc in docs]

# Query
query_emb = get_embedding("coding is fun")

# Calculate cosine similarity
similarities = [
    np.dot(query_emb, doc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(doc_emb))
    for doc_emb in embeddings
]

# Expect: "I love programming" to be most similar
```

---

## Performance Expectations

### Embeddings vs Generation

| Operation | Time | Reason |
|-----------|------|--------|
| Embeddings (5 tokens) | ~100ms | Only prefill, no generation |
| Chat (5→50 tokens) | ~500ms | Prefill + 50 token generation |
| Embeddings (100 tokens) | ~300ms | Longer prefill |
| Chat (100→50 tokens) | ~800ms | Long prefill + generation |

**Key insight:** Embeddings are FAST (no generation loop!)

---

## Benefits of This Architecture

### ✅ Unified Queue
- Single semaphore controls all access
- Fair scheduling regardless of API
- No resource conflicts

### ✅ Format Agnostic
- Model doesn't care about API format
- Easy to add new APIs (just adapters)
- Internal format is clean

### ✅ OpenAI + Ollama Compatible
- Serve both ecosystems
- Users choose their preferred API
- Same backend, same quality

### ✅ Embeddings Enable RAG
- Semantic search
- Document similarity
- Knowledge bases
- ChatGPT-style retrieval

---

## Next Steps

1. ✅ **Phase 1:** Create internal types (`inference_types.py`)
2. ✅ **Phase 2:** Add embedding support to RKLLM model
3. ✅ **Phase 3:** Build format adapters
4. ✅ **Phase 4:** Create API routes
5. ✅ **Phase 5:** Test embeddings
6. ✅ **Phase 6:** Test mixed queue
7. ✅ **Phase 7:** Document & ship!

**Estimated time:** 4-6 hours for full implementation

---

## Decision Time! 🎯

Ready to build this? It gives you:
- ✅ Embeddings API (OpenAI-compatible)
- ✅ Ollama API (generate + embeddings)
- ✅ All APIs sharing one queue
- ✅ Production-ready architecture

**Shall we start with Phase 1?** 🚀
