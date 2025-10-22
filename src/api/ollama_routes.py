"""
Ollama-compatible API routes

These routes provide Ollama API compatibility while using the
same underlying RKLLM model and queue as OpenAI routes.

All requests are translated to internal format, queued with OpenAI
requests, and responses are translated back to Ollama format.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from src.api.schemas import (
    OllamaGenerateRequest, OllamaGenerateResponse,
    OllamaChatRequest, OllamaChatResponse,
    OllamaEmbeddingRequest, OllamaEmbeddingResponse
)
from src.api.adapters import (
    ollama_generate_to_internal,
    ollama_chat_to_internal,
    internal_to_ollama_generate,
    internal_to_ollama_chat
)
from src.models.inference_types import InferenceResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["ollama"])


async def ensure_model_loaded(preferred_model: Optional[str] = None):
    """
    Ensure a model is loaded. If not, auto-load the first available model.
    
    Args:
        preferred_model: Optional preferred model name
        
    Returns:
        The loaded model
        
    Raises:
        HTTPException if no model can be loaded
    """
    from src.main import model_manager
    
    # Check if a model is already loaded
    current_model = model_manager.get_current_model()
    if current_model is not None:
        return current_model
    
    logger.info("No model loaded, attempting to auto-load...")
    
    # Get list of available models
    available = model_manager.list_available_models()
    if not available:
        raise HTTPException(
            status_code=503,
            detail="No models available. Please place .rkllm files in the models directory."
        )
    
    # Try to load preferred model or first available
    model_to_load = None
    if preferred_model:
        # Check if preferred model exists
        for model_info in available:
            if model_info['name'] == preferred_model:
                model_to_load = preferred_model
                break
    
    # If no preferred or not found, use first available
    if model_to_load is None:
        model_to_load = available[0]['name']
    
    logger.info(f"Auto-loading model: {model_to_load}")
    
    # Load the model (use default settings)
    try:
        model_manager.load_model(
            model_name=model_to_load,
            max_context_len=16384,  # Default context length
            num_npu_core=3  # Default NPU cores for RK3588
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to auto-load model: {str(e)}"
        )
    
    current_model = model_manager.get_current_model()
    if current_model is None:
        raise HTTPException(
            status_code=500,
            detail="Model loaded but not available"
        )
    
    logger.info(f"Successfully auto-loaded model: {model_to_load}")
    return current_model


@router.post("/generate", response_model=OllamaGenerateResponse)
async def ollama_generate(request: OllamaGenerateRequest):
    """
    Ollama-compatible text generation endpoint
    
    Shares the same queue and model as OpenAI /v1/chat/completions.
    Auto-loads the specified model if not already loaded.
    
    Example:
        curl -X POST http://localhost:8080/api/generate \\
          -d '{
            "model": "qwen3-0.6b",
            "prompt": "Why is the sky blue?",
            "stream": false
          }'
    """
    from src.main import model_manager
    
    logger.info(f"Ollama generate request: {request.prompt[:50]}...")
    
    # Ensure model is loaded (auto-load if needed)
    await ensure_model_loaded(preferred_model=request.model)
    
    # Convert to internal format
    internal_req = ollama_generate_to_internal(request)
    
    logger.info(f"Ollama params: max_tokens={internal_req.max_tokens}, temp={internal_req.temperature}, prompt_len={len(internal_req.prompt)}")
    
    # Get model and generate (uses shared queue with OpenAI!)
    model = model_manager.get_current_model()
    
    try:
        # Call model's async generate (same queue as OpenAI routes)
        text, stats = await model.generate_async(
            prompt=internal_req.prompt,
            max_new_tokens=internal_req.max_tokens,
            temperature=internal_req.temperature,
            top_p=internal_req.top_p,
            top_k=internal_req.top_k,
            repeat_penalty=internal_req.repeat_penalty
        )
        
        # Build internal response
        internal_resp = InferenceResponse(
            text=text,
            finish_reason="stop",
            prefill_tokens=stats.get('prefill_tokens', 0) if stats else 0,
            prefill_time_ms=stats.get('prefill_time_ms', 0.0) if stats else 0.0,
            generate_tokens=stats.get('generate_tokens', 0) if stats else 0,
            generate_time_ms=stats.get('generate_time_ms', 0.0) if stats else 0.0,
            request_id=internal_req.request_id
        )
        
        # Convert to Ollama format
        return internal_to_ollama_generate(internal_resp, request.model)
        
    except Exception as e:
        logger.error(f"Error in Ollama generate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=OllamaChatResponse)
async def ollama_chat(request: OllamaChatRequest):
    """
    Ollama-compatible chat endpoint
    
    Shares the same queue and model as OpenAI /v1/chat/completions.
    Auto-loads the specified model if not already loaded.
    
    Example:
        curl -X POST http://localhost:8080/api/chat \\
          -d '{
            "model": "qwen3-0.6b",
            "messages": [
              {"role": "user", "content": "Hello!"}
            ]
          }'
    """
    from src.main import model_manager
    
    logger.info(f"Ollama chat request: {len(request.messages)} messages")
    
    # Ensure model is loaded (auto-load if needed)
    await ensure_model_loaded(preferred_model=request.model)
    
    # Convert to internal format
    internal_req = ollama_chat_to_internal(request)
    
    # Get model and generate
    model = model_manager.get_current_model()
    
    try:
        # Call model's async generate (same queue!)
        text, stats = await model.generate_async(
            prompt=internal_req.prompt,
            max_new_tokens=internal_req.max_tokens,
            temperature=internal_req.temperature,
            top_p=internal_req.top_p,
            top_k=internal_req.top_k,
            repeat_penalty=internal_req.repeat_penalty
        )
        
        # Build internal response
        internal_resp = InferenceResponse(
            text=text,
            finish_reason="stop",
            prefill_tokens=stats.get('prefill_tokens', 0) if stats else 0,
            prefill_time_ms=stats.get('prefill_time_ms', 0.0) if stats else 0.0,
            generate_tokens=stats.get('generate_tokens', 0) if stats else 0,
            generate_time_ms=stats.get('generate_time_ms', 0.0) if stats else 0.0,
            request_id=internal_req.request_id
        )
        
        # Convert to Ollama format
        return internal_to_ollama_chat(internal_resp, request.model)
        
    except Exception as e:
        logger.error(f"Error in Ollama chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags")
async def ollama_list_models():
    """
    Ollama-compatible model list endpoint
    
    Returns list of available models in Ollama format.
    """
    from src.main import model_manager
    
    # Get available models from registry
    available = model_manager.list_available_models()
    
    # Convert to Ollama format
    models = []
    for model_info in available:
        models.append({
            "name": model_info['name'],
            "modified_at": "2025-10-21T00:00:00Z",
            "size": 0,  # Size not tracked yet
            "digest": "",
            "details": {
                "format": "rkllm",
                "family": model_info.get("architecture", "unknown"),
                "parameter_size": model_info.get("description", "")
            }
        })
    
    return {"models": models}


# ============================================================================
# OLLAMA EMBEDDINGS ENDPOINT
# ============================================================================
# TEMPORARILY DISABLED: Embedding model has compatibility issues with RKLLM runtime.
# Will re-enable when verified compatible embedding model is available.
# ============================================================================

# @router.post("/embed", response_model=OllamaEmbeddingResponse)
# @router.post("/embeddings", response_model=OllamaEmbeddingResponse)
# async def ollama_embeddings(request: OllamaEmbeddingRequest):
#     """
#     Ollama-compatible embeddings endpoint
#     
#     Endpoint: POST /api/embed or POST /api/embeddings
#     
#     Uses dedicated Qwen3-Embedding-0.6B model for text embeddings.
#     
#     Request:
#         {
#             "model": "qwen3-0.6b-embedding",
#             "prompt": "The quick brown fox"
#         }
#     
#     Response:
#         {
#             "embedding": [0.123, -0.456, ...],
#             "model": "qwen3-0.6b-embedding",
#             "created_at": "2025-10-21T12:34:56Z",
#             "total_duration": 150000000,  // nanoseconds
#             "load_duration": 0,
#             "prompt_eval_count": 5
#         }
#     """
#     from src.api.adapters import ollama_embedding_to_internal, internal_to_ollama_embedding
#     from src.models.inference_types import InferenceResponse
#     from src.main import model_manager
#     from config.settings import inference_config
#     
#     logger.info(f"📥 Ollama embedding request for model: {request.model}")
#     
#     try:
#         # Always use the dedicated embedding model
#         embedding_model_name = "qwen3-0.6b-embedding"
#         
#         # Load embedding model if not already loaded
#         current_model = model_manager.get_current_model()
#         if not current_model or current_model.model_name != embedding_model_name:
#             logger.info(f"Loading embedding model: {embedding_model_name}")
#             try:
#                 model_manager.load_model(embedding_model_name)
#                 current_model = model_manager.get_current_model()
#             except Exception as e:
#                 raise HTTPException(
#                     status_code=503,
#                     detail=f"Failed to load embedding model '{embedding_model_name}': {str(e)}"
#                 )
#         
#         # Get current model
#         current_model = model_manager.get_current_model()
#         if not current_model:
#             raise HTTPException(status_code=503, detail="No model loaded")
#         
#         # Convert to internal format
#         internal_req = ollama_embedding_to_internal(request)
#         
#         # Get embeddings
#         embedding_vec, stats = await current_model.get_embeddings(
#             text=internal_req.prompt,
#             inference_config=inference_config
#         )
#         
#         # Create internal response
#         internal_resp = InferenceResponse(
#             embedding=embedding_vec,
#             embedding_dim=stats.get("embedding_dim"),
#             tokens_processed=stats.get("tokens_processed", 0),
#             time_ms=stats.get("time_ms", 0.0)
#         )
#         
#         # Convert to Ollama format
#         response = internal_to_ollama_embedding(internal_resp, current_model.model_name or request.model)
#         
#         logger.info(f"✅ Generated {len(embedding_vec)}-dim embedding")
#         
#         return response
#         
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Embedding generation failed: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))
    from src.api.adapters import ollama_embedding_to_internal, internal_to_ollama_embedding
    from src.models.inference_types import InferenceResponse
    from src.main import model_manager
    from config.settings import inference_config
    
    logger.info(f"📥 Ollama embedding request for model: {request.model}")
    
    try:
        # Always use the dedicated embedding model
        embedding_model_name = "qwen3-0.6b-embedding"
        
        # Load embedding model if not already loaded
        current_model = model_manager.get_current_model()
        if not current_model or current_model.model_name != embedding_model_name:
            logger.info(f"Loading embedding model: {embedding_model_name}")
            try:
                model_manager.load_model(embedding_model_name)
                current_model = model_manager.get_current_model()
            except Exception as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to load embedding model '{embedding_model_name}': {str(e)}"
                )
        
        # Get current model
        current_model = model_manager.get_current_model()
        if not current_model:
            raise HTTPException(status_code=503, detail="No model loaded")
        
        # Convert to internal format
        internal_req = ollama_embedding_to_internal(request)
        
        # Get embeddings
        embedding_vec, stats = await current_model.get_embeddings(
            text=internal_req.prompt,
            inference_config=inference_config
        )
        
        # Create internal response
        internal_resp = InferenceResponse(
            embedding=embedding_vec,
            embedding_dim=stats.get("embedding_dim"),
            tokens_processed=stats.get("tokens_processed", 0),
            time_ms=stats.get("time_ms", 0.0)
        )
        
        # Convert to Ollama format
        response = internal_to_ollama_embedding(internal_resp, current_model.model_name or request.model)
        
        logger.info(f"✅ Generated {len(embedding_vec)}-dim embedding")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Ollama embeddings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
