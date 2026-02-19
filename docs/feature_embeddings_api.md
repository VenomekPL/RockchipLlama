# Feature: Embeddings API Endpoint

## Overview

The Embeddings API allows clients to generate vector representations (embeddings) of text input. These embeddings can be used for semantic search, clustering, classification, and retrieval-augmented generation (RAG). This feature is critical for building intelligent search and recommendation systems on Rockchip hardware.

## Current Status

**Disabled** — Full implementation exists but all endpoints are commented out.

- `src/models/rkllm_model.py` contains a complete `get_embeddings()` method (lines ~915-1071) that uses `RKLLM_INFER_GET_LAST_HIDDEN_LAYER` to extract hidden states and normalize them to L2-unit vectors.
- `src/api/openai_routes.py` has a full `/v1/embeddings` endpoint implementation (lines ~594-688) that is commented out.
- `src/api/ollama_routes.py` has a full `/api/embeddings` endpoint (lines ~258-400) that is commented out.
- **Reason for disabling**: "Embedding model (Qwen3-Embedding-0.6B) has compatibility issues with current RKLLM runtime."

### What Works

The underlying RKLLM runtime supports embedding extraction:

```c
// From rkllm.h - inference mode for embeddings
RKLLM_INFER_GET_LAST_HIDDEN_LAYER = 1  // Retrieves last hidden layer

// Result structure
typedef struct {
    const float* hidden_states;  // size: num_tokens * embd_size
    int embd_size;               // embedding dimension
    int num_tokens;              // number of tokens
} RKLLMResultLastHiddenLayer;
```

### Existing Code in `rkllm_model.py`

```python
async def get_embeddings(self, texts: list[str]) -> dict:
    """Extract embeddings using RKLLM_INFER_GET_LAST_HIDDEN_LAYER mode."""
    # Sets infer mode to GET_LAST_HIDDEN_LAYER
    # Runs inference for each text
    # Collects hidden states from callback
    # Averages token embeddings (mean pooling)
    # L2-normalizes the result
    # Returns {"embeddings": [...], "model": ..., "usage": ...}
```

## rknn-llm Reference

The RKLLM runtime natively supports:

- `RKLLM_INFER_GET_LAST_HIDDEN_LAYER` — extract hidden states for embedding generation.
- `RKLLM_INFER_GET_LOGITS` — extract raw logits (useful for reranking).
- v1.2.3 adds "automatic cache reuse for embedding input" improving efficiency of repeated embedding operations.

### Relevant C API

```c
// Set inference mode to get hidden layer
RKLLMInferParam infer_params;
infer_params.mode = RKLLM_INFER_GET_LAST_HIDDEN_LAYER;

// Run inference
rkllm_run(handle, &input, &infer_params, userdata);

// In callback, access hidden states:
// result->last_hidden_layer.hidden_states (float array)
// result->last_hidden_layer.embd_size (dimension)
// result->last_hidden_layer.num_tokens (token count)
```

## Implementation Plan

### Step 1: Diagnose Compatibility Issue

Investigate the specific compatibility issue with Qwen3-Embedding-0.6B:

1. Check RKLLM runtime version compatibility with embedding models.
2. Test with alternative models (e.g., text models used in embedding mode).
3. Review RKLLM error logs when loading the embedding model.
4. Check if the issue is model-specific or affects all embedding extraction.

### Step 2: Re-enable OpenAI Embeddings Endpoint

Uncomment and update the `/v1/embeddings` endpoint in `src/api/openai_routes.py`:

```python
@router.post("/v1/embeddings")
async def create_embedding(request: EmbeddingRequest):
    model = request.model or settings.DEFAULT_MODEL
    texts = request.input if isinstance(request.input, list) else [request.input]

    result = await model_instance.get_embeddings(texts)

    return {
        "object": "list",
        "data": [
            {"object": "embedding", "embedding": emb, "index": i}
            for i, emb in enumerate(result["embeddings"])
        ],
        "model": model,
        "usage": result["usage"]
    }
```

### Step 3: Re-enable Ollama Embeddings Endpoint

Uncomment and update the `/api/embeddings` endpoint in `src/api/ollama_routes.py`.

### Step 4: Add Embedding Model Configuration

Update `config/inference_config.json` to support dedicated embedding model configuration:

```json
{
  "embedding_model": {
    "model_path": "models/qwen3-embedding-0.6b",
    "max_context_len": 512,
    "pooling_strategy": "mean",
    "normalize": true
  }
}
```

### Step 5: Implement Fallback Pooling Strategies

Enhance the embedding extraction with configurable pooling:

```python
def pool_embeddings(hidden_states, strategy="mean"):
    if strategy == "mean":
        return np.mean(hidden_states, axis=0)
    elif strategy == "cls":
        return hidden_states[0]
    elif strategy == "last":
        return hidden_states[-1]
```

### Step 6: Leverage Automatic Cache Reuse (v1.2.3)

The rknn-llm v1.2.3 adds automatic cache reuse for embedding input. Ensure the implementation benefits from this optimization for batch embedding requests.

## Goals

1. Working `/v1/embeddings` endpoint compatible with OpenAI API format.
2. Working `/api/embeddings` endpoint compatible with Ollama API format.
3. Support for both dedicated embedding models and text-model-based embeddings.
4. Efficient batch embedding with automatic cache reuse.
5. Configurable pooling strategies (mean, CLS, last token).

## Definition of Done

- [ ] Root cause of Qwen3-Embedding-0.6B compatibility issue identified and documented.
- [ ] `/v1/embeddings` endpoint is active and returns OpenAI-compatible responses.
- [ ] `/api/embeddings` endpoint is active and returns Ollama-compatible responses.
- [ ] Single text and batch text inputs are supported.
- [ ] Embeddings are L2-normalized by default.
- [ ] Embedding dimension is correctly reported in response.
- [ ] Error handling for unsupported models and invalid inputs.
- [ ] Token usage is tracked and reported.
- [ ] Performance benchmarks for embedding generation (tokens/s, latency).

## Test Approach

### Unit Tests

- Test embedding extraction with mock RKLLM hidden layer output.
- Test L2 normalization produces unit vectors.
- Test pooling strategies (mean, CLS, last).
- Test batch input handling.

### Integration Tests

- Send single text to `/v1/embeddings` and verify response format.
- Send batch texts and verify each embedding has correct dimension.
- Test with different model types (embedding model vs. text model).
- Verify embedding similarity: semantically similar texts should have high cosine similarity.

### Manual Testing

```bash
# Test OpenAI embeddings endpoint
curl -X POST http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-0.6b",
    "input": "Hello world"
  }'

# Test batch embeddings
curl -X POST http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-0.6b",
    "input": ["Hello world", "Goodbye world"]
  }'

# Test with Python OpenAI client
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8080/v1", api_key="not-needed")
response = client.embeddings.create(model="qwen3-0.6b", input="test text")
print(f"Embedding dimension: {len(response.data[0].embedding)}")
```

## References

- [OpenAI Embeddings API](https://platform.openai.com/docs/api-reference/embeddings)
- [Ollama Embeddings API](https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings)
- RKLLM C API: `external/rknn-llm/rkllm-runtime/Linux/librkllm_api/include/rkllm.h` (lines 50-53, 206-210)
- Existing disabled implementation: `src/models/rkllm_model.py` (lines ~915-1071)
- Existing disabled endpoint: `src/api/openai_routes.py` (lines ~594-688)
- RKLLM SDK Documentation: `external/rknn-llm/doc/Rockchip_RKLLM_SDK_EN_1.2.3.pdf`
