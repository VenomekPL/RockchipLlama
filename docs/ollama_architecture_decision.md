# Ollama API Implementation - Architecture Decision

**Date:** October 21, 2025  
**Status:** 🤔 Design Phase  
**Decision:** Pending

---

## The Challenge

We want to add Ollama API compatibility, but we have:
- ✅ **One NPU** - Can only run one model instance
- ✅ **One Model Instance** - RKLLM handle loaded once
- ✅ **OpenAI API** - Already using queue-based concurrency
- ❓ **How to add Ollama** - Without breaking existing setup?

---

## Options Analysis

### Option 1: Shared Queue (Format Translation) ⭐ **RECOMMENDED**

**Architecture:**
```
┌─────────────────┐         ┌──────────────────┐
│  OpenAI Routes  │         │  Ollama Routes   │
│ /v1/chat/...    │         │ /api/generate    │
└────────┬────────┘         └────────┬─────────┘
         │                           │
         │  (OpenAI format)         │  (Ollama format)
         │                           │
         ▼                           ▼
    ┌────────────────────────────────────────┐
    │    Format Adapters (translate)         │
    │  OpenAI → Internal  |  Ollama → Internal│
    └────────┬───────────────────────┬────────┘
             │                       │
             └───────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Shared Queue       │
              │   (Semaphore n=1)    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   RKLLM Model        │
              │   (Single Instance)  │
              └──────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Response Adapters  │
              │   Internal → Format  │
              └──────────────────────┘
```

**How It Works:**
1. **Request comes in** (OpenAI or Ollama format)
2. **Adapter translates** to internal common format
3. **Queue handles** concurrency (existing semaphore)
4. **Model generates** (same code path)
5. **Response adapter** translates back to requested format

**Pros:**
- ✅ Reuses existing queue system
- ✅ No model duplication
- ✅ Both APIs share NPU fairly
- ✅ Simple to implement (just translation layers)

**Cons:**
- ⚠️ APIs coupled at backend
- ⚠️ Can't tune params differently per API

**Code Impact:**
```python
# src/api/ollama_routes.py (NEW)
@router.post("/api/generate")
async def ollama_generate(request: OllamaGenerateRequest):
    # 1. Translate Ollama → Internal
    internal_request = translate_ollama_to_internal(request)
    
    # 2. Use same model/queue as OpenAI
    response = await model.generate_async(**internal_request)
    
    # 3. Translate Internal → Ollama
    return translate_internal_to_ollama(response)
```

---

### Option 2: HTTP Proxy (Lazy Approach)

**Architecture:**
```
┌──────────────────┐
│  Ollama Routes   │
│ /api/generate    │
└────────┬─────────┘
         │
         │ (internally calls)
         ▼
┌──────────────────────┐
│  OpenAI Routes       │
│  /v1/chat/completions│
└──────────────────────┘
         │
         ▼
    (existing flow)
```

**How It Works:**
1. Ollama endpoint receives request
2. Translates to OpenAI format
3. Makes HTTP call to own OpenAI endpoint
4. Translates response back

**Pros:**
- ✅ Zero backend changes
- ✅ Fastest to implement

**Cons:**
- ❌ HTTP overhead (localhost call)
- ❌ Not a "real" implementation
- ❌ Awkward error handling

---

### Option 3: Dual Model Loading ❌ **NOT POSSIBLE**

**Why it won't work:**
- ❌ Only 1 NPU
- ❌ RKLLM multi-instance unreliable
- ❌ Memory constraints (2x model = 2x RAM)
- ❌ Batch inference broken (can't use n_batch=2)

**Verdict:** Not viable with current RKLLM limitations.

---

## Recommendation: **Option 1 - Shared Queue**

### Implementation Plan

#### Phase 1: Internal Common Format
```python
# src/models/inference_types.py (NEW)
from dataclasses import dataclass

@dataclass
class InferenceRequest:
    """Internal format - API-agnostic"""
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.8
    top_p: float = 0.9
    top_k: int = 20
    stop: list[str] | None = None
    stream: bool = False

@dataclass
class InferenceResponse:
    """Internal format - API-agnostic"""
    text: str
    finish_reason: str
    tokens_generated: int
    time_ms: float
```

#### Phase 2: Format Adapters
```python
# src/api/adapters.py (NEW)

def openai_to_internal(request: ChatCompletionRequest) -> InferenceRequest:
    """OpenAI → Internal"""
    # Extract last user message
    prompt = extract_prompt_from_messages(request.messages)
    return InferenceRequest(
        prompt=prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        # ... etc
    )

def ollama_to_internal(request: OllamaGenerateRequest) -> InferenceRequest:
    """Ollama → Internal"""
    return InferenceRequest(
        prompt=request.prompt,
        max_tokens=request.options.get("num_predict", 512),
        temperature=request.options.get("temperature", 0.8),
        # ... etc
    )

def internal_to_openai(response: InferenceResponse) -> ChatCompletionResponse:
    """Internal → OpenAI"""
    return ChatCompletionResponse(
        choices=[{
            "message": {"role": "assistant", "content": response.text},
            "finish_reason": response.finish_reason
        }]
    )

def internal_to_ollama(response: InferenceResponse) -> OllamaGenerateResponse:
    """Internal → Ollama"""
    return OllamaGenerateResponse(
        response=response.text,
        done=True,
        # ... etc
    )
```

#### Phase 3: Update Routes
```python
# src/api/openai_routes.py (MODIFY)
@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    # Translate
    internal_req = openai_to_internal(request)
    
    # Execute (shared queue)
    internal_resp = await model.generate_async(**asdict(internal_req))
    
    # Translate back
    return internal_to_openai(internal_resp)

# src/api/ollama_routes.py (NEW)
@router.post("/api/generate")
async def ollama_generate(request: OllamaGenerateRequest):
    # Translate
    internal_req = ollama_to_internal(request)
    
    # Execute (SAME queue as OpenAI!)
    internal_resp = await model.generate_async(**asdict(internal_req))
    
    # Translate back
    return internal_to_ollama(internal_resp)
```

---

## What This Gives You

### ✅ Compatibility
```bash
# OpenAI client
curl -X POST http://localhost:8080/v1/chat/completions \
  -d '{"model": "qwen", "messages": [...]}'

# Ollama client
curl -X POST http://localhost:8080/api/generate \
  -d '{"model": "qwen", "prompt": "..."}'

# Both use SAME model, SAME queue!
```

### ✅ Fair Queuing
- Request 1: OpenAI format → enters queue position 1
- Request 2: Ollama format → enters queue position 2
- Request 3: OpenAI format → enters queue position 3
- **All processed sequentially, fairly**

### ✅ Single Source of Truth
- One model instance
- One configuration
- One queue system
- Two API surfaces

---

## Concerns & Mitigations

### Concern 1: "What if Ollama needs different parameters?"

**Mitigation:**
- Format adapters handle parameter mapping
- Internal format supports all common params
- Can add API-specific overrides if needed

### Concern 2: "Performance overhead from translation?"

**Mitigation:**
- Translation is pure Python (microseconds)
- NPU inference dominates time (milliseconds)
- Overhead negligible (<0.1% of total time)

### Concern 3: "Can't optimize separately?"

**Mitigation:**
- True, but NPU is the bottleneck, not API format
- Optimization happens at model/config level
- Both APIs benefit equally from improvements

---

## Alternative: Staged Approach

If you're uncertain, we can do:

### Stage 1: Proof of Concept (HTTP Proxy)
- Quick implementation (1 hour)
- Validate Ollama API format
- Test client compatibility
- No backend changes

### Stage 2: Proper Implementation (Shared Queue)
- Refactor to internal format (2-3 hours)
- Clean architecture
- Production ready

---

## Decision Points

**Go with Shared Queue if:**
- ✅ You want production-quality implementation
- ✅ You value clean architecture
- ✅ You're OK with both APIs sharing resources

**Go with HTTP Proxy if:**
- ✅ You want to test Ollama API quickly
- ✅ You might not keep it long-term
- ✅ You want zero risk to existing OpenAI API

**Skip Ollama if:**
- ✅ OpenAI API already covers your needs
- ✅ No users asking for Ollama compatibility
- ✅ Rather focus on other features (embeddings, RAG, etc.)

---

## My Recommendation

**Start with HTTP Proxy (Stage 1)**

Why?
1. Validates if Ollama API is actually useful for your users
2. Takes 1 hour to implement
3. Zero risk to existing system
4. Can upgrade to Shared Queue later if valuable

**Then decide:**
- If Ollama gets used → Upgrade to Shared Queue
- If Ollama rarely used → Keep proxy or remove
- If not needed → Remove and focus elsewhere

---

## Your Call! 🎯

What would you prefer?

**A)** Shared Queue (proper, clean, 2-3 hours)  
**B)** HTTP Proxy (quick test, 1 hour)  
**C)** Skip Ollama, focus on other features  

Let me know and I'll implement it! 🚀
