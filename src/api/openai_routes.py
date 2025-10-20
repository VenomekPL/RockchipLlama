"""
OpenAI-compatible API endpoints
Implements /v1/chat/completions and /v1/models
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
import time
import uuid
import logging
import os
from typing import AsyncGenerator, Optional, List
import json

from api.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatMessage,
    Usage,
    ModelListResponse,
    ModelInfo,
    ErrorResponse,
    MessageRole,
    CompletionRequest,
    CompletionResponse,
    CompletionChoice
)
from models.model_manager import model_manager
from config.settings import settings

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/v1", tags=["OpenAI Compatible"])


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


def format_chat_prompt(messages: list) -> str:
    """
    Format chat messages into a single prompt string
    
    Args:
        messages: List of chat messages
        
    Returns:
        Formatted prompt string
    """
    prompt_parts = []
    
    for msg in messages:
        role = msg.role if hasattr(msg, 'role') else msg.get('role', 'user')
        content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
        
        if role == "system":
            prompt_parts.append(f"System: {content}")
        elif role == "user":
            prompt_parts.append(f"User: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")
    
    # Add final assistant prompt
    prompt_parts.append("Assistant:")
    
    return "\n".join(prompt_parts)


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    """
    Create a chat completion (OpenAI compatible)
    
    Endpoint: POST /v1/chat/completions
    
    Supports binary prompt caching for 50-70% TTFT reduction.
    Use 'use_cache' parameter to specify which binary cache to load.
    """
    try:
        logger.info(f"Chat completion request for model: {request.model}")
        logger.debug(f"Messages: {len(request.messages)}, Stream: {request.stream}")
        
        # Ensure model is loaded
        current_model = await ensure_model_loaded(preferred_model=request.model)
        
        # Format messages into prompt
        prompt = format_chat_prompt(request.messages)
        
        # Setup binary cache if requested
        binary_cache_path = None
        cache_used = False
        if request.use_cache:
            cache_mgr = current_model.cache_manager
            if cache_mgr.cache_exists(request.model, request.use_cache):
                binary_cache_path = cache_mgr.get_cache_path(request.model, request.use_cache)
                cache_used = True
                logger.info(f"🔥 Loading binary cache: {request.use_cache}")
            else:
                logger.warning(f"Cache '{request.use_cache}' not found, proceeding without cache")
        
        # Generate completion ID and timestamp
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created_time = int(time.time())
        
        # Handle streaming response
        if request.stream:
            return StreamingResponse(
                stream_chat_completion(
                    prompt=prompt,
                    request=request,
                    completion_id=completion_id,
                    created_time=created_time,
                    binary_cache_path=binary_cache_path
                ),
                media_type="text/event-stream"
            )
        
        # Non-streaming response - use loaded model
        generated_text, perf_stats = current_model.generate(
            prompt=prompt,
            max_new_tokens=request.max_tokens or 512,
            temperature=request.temperature or 0.8,
            top_p=request.top_p or 0.9,
            top_k=request.top_k or 20,  # User preference: 20
            repeat_penalty=getattr(request, 'repeat_penalty', None) or 1.1,
            binary_cache_path=binary_cache_path,
            save_binary_cache=False  # Load, don't save
        )
        
        # Log performance stats if available
        if perf_stats:
            logger.info(f"Performance: TTFT={perf_stats.get('prefill_time_ms', 0):.1f}ms, "
                       f"Gen={perf_stats.get('generate_time_ms', 0):.1f}ms, "
                       f"Tokens={perf_stats.get('generate_tokens', 0)}, "
                       f"Speed={perf_stats.get('generate_tokens', 0) / (perf_stats.get('generate_time_ms', 1) / 1000):.1f} tok/s")
        
        # Create response
        response = ChatCompletionResponse(
            id=completion_id,
            created=created_time,
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role=MessageRole.assistant,
                        content=generated_text
                    ),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=len(prompt.split()),  # Rough estimate
                completion_tokens=len(generated_text.split()),  # Rough estimate
                total_tokens=len(prompt.split()) + len(generated_text.split()),
                cache_hit=cache_used,
                cached_prompts=[request.use_cache] if cache_used else None
            )
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in chat completion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def stream_chat_completion(
    prompt: str,
    request: ChatCompletionRequest,
    completion_id: str,
    created_time: int,
    binary_cache_path: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Stream chat completion tokens
    
    Yields SSE-formatted chunks
    
    Args:
        binary_cache_path: Path to binary cache file to load
    """
    try:
        # Buffer for collecting generated text
        generated_text = ""
        chunk_buffer = []  # Store chunks to yield
        
        def streaming_callback(token: str):
            """Callback for streaming tokens - stores chunks to be yielded"""
            nonlocal generated_text
            generated_text += token
            # Create and buffer chunk
            chunk = ChatCompletionChunk(
                id=completion_id,
                created=created_time,
                model=request.model,
                choices=[{
                    "index": 0,
                    "delta": {"content": token},
                    "finish_reason": None
                }]
            )
            chunk_buffer.append(chunk)
        
        # Ensure model is loaded (auto-load if needed)
        try:
            current_model = await ensure_model_loaded(preferred_model=request.model)
        except HTTPException as e:
            # Return error in SSE format
            error_data = {"error": {"message": e.detail, "type": "model_loading_failed"}}
            yield f"data: {json.dumps(error_data)}\n\n"
            return
        
        # Generate with streaming (this will fill chunk_buffer via callback)
        _, perf_stats = current_model.generate(
            prompt=prompt,
            max_new_tokens=request.max_tokens or 512,
            temperature=request.temperature or 0.8,
            top_p=request.top_p or 0.9,
            top_k=request.top_k or 20,  # User preference: 20
            repeat_penalty=getattr(request, 'repeat_penalty', None) or 1.1,
            callback=streaming_callback,
            binary_cache_path=binary_cache_path,
            save_binary_cache=False  # Load, don't save
        )
        
        # Yield all buffered chunks
        for chunk in chunk_buffer:
            yield f"data: {chunk.model_dump_json()}\n\n"
        
        # Send final chunk with finish_reason and perf stats
        usage_data = {
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(generated_text.split()),
            "total_tokens": len(prompt.split()) + len(generated_text.split())
        }
        
        # Add RKLLM perf stats if available
        if perf_stats:
            usage_data.update({
                "prefill_time_ms": perf_stats.get('prefill_time_ms', 0),
                "prefill_tokens": perf_stats.get('prefill_tokens', 0),
                "generate_time_ms": perf_stats.get('generate_time_ms', 0),
                "generate_tokens": perf_stats.get('generate_tokens', 0),
                "memory_usage_mb": perf_stats.get('memory_usage_mb', 0)
            })
        
        final_chunk = ChatCompletionChunk(
            id=completion_id,
            created=created_time,
            model=request.model,
            choices=[{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }],
            usage=usage_data
        )
        
        yield f"data: {final_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Error in streaming: {e}", exc_info=True)
        error_data = {"error": {"message": str(e), "type": "internal_error"}}
        yield f"data: {json.dumps(error_data)}\n\n"


@router.post("/completions", response_model=CompletionResponse)
async def create_completion(request: CompletionRequest):
    """
    Create a text completion (OpenAI compatible)
    
    Endpoint: POST /v1/completions
    
    Simple one-shot completion without chat formatting.
    For multi-turn conversations, use /v1/chat/completions instead.
    """
    try:
        logger.info(f"Text completion request for model: {request.model}")
        logger.debug(f"Prompt length: {len(request.prompt)}, Stream: {request.stream}")
        
        # Ensure model is loaded
        current_model = await ensure_model_loaded(preferred_model=request.model)
        
        # Setup binary cache if requested
        binary_cache_path = None
        cache_used = False
        if request.use_cache:
            cache_mgr = current_model.cache_manager
            if cache_mgr.cache_exists(request.model, request.use_cache):
                binary_cache_path = cache_mgr.get_cache_path(request.model, request.use_cache)
                cache_used = True
                logger.info(f"🔥 Loading binary cache: {request.use_cache}")
            else:
                logger.warning(f"Cache '{request.use_cache}' not found, proceeding without cache")
        
        # Generate completion ID and timestamp
        completion_id = f"cmpl-{uuid.uuid4().hex[:12]}"
        created_time = int(time.time())
        
        # Handle streaming response
        if request.stream:
            raise HTTPException(
                status_code=501,
                detail="Streaming not yet implemented for text completions. Use stream=false or /v1/chat/completions for streaming."
            )
        
        # Non-streaming response
        generated_text, perf_stats = current_model.generate(
            prompt=request.prompt,
            max_new_tokens=request.max_tokens or 512,
            temperature=request.temperature or 0.8,
            top_p=request.top_p or 0.9,
            top_k=request.top_k or 20,
            repeat_penalty=request.repeat_penalty or 1.1,
            binary_cache_path=binary_cache_path,
            save_binary_cache=False  # Load, don't save
        )
        
        # Log performance stats if available
        if perf_stats:
            logger.info(f"Performance: TTFT={perf_stats.get('prefill_time_ms', 0):.1f}ms, "
                       f"Gen={perf_stats.get('generate_time_ms', 0):.1f}ms, "
                       f"Tokens={perf_stats.get('generate_tokens', 0)}, "
                       f"Speed={perf_stats.get('generate_tokens', 0) / (perf_stats.get('generate_time_ms', 1) / 1000):.1f} tok/s")
        
        # Create response
        response = CompletionResponse(
            id=completion_id,
            created=created_time,
            model=request.model,
            choices=[
                CompletionChoice(
                    text=generated_text,
                    index=0,
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=len(request.prompt.split()),  # Rough estimate
                completion_tokens=len(generated_text.split()),  # Rough estimate
                total_tokens=len(request.prompt.split()) + len(generated_text.split()),
                cache_hit=cache_used,
                cached_prompts=[request.use_cache] if cache_used else None
            )
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in text completion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """
    List available models (OpenAI compatible)
    
    Endpoint: GET /v1/models
    
    Returns models with friendly names and context information
    """
    try:
        # Get models from model manager (includes friendly names and context)
        available_models = model_manager.list_available_models()
        
        # Create model info list
        models = []
        for model_info in available_models:
            models.append(
                ModelInfo(
                    id=model_info['friendly_name'],
                    created=int(time.time()),
                    owned_by="rockchip"
                )
            )
        
        return ModelListResponse(data=models)
        
    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model_manager.is_model_loaded(),
        "loaded_model": model_manager.get_loaded_model_name(),
        "timestamp": int(time.time())
    }


# ============================================================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/cache")
async def list_all_caches():
    """
    List all prompt caches across all models
    
    Endpoint: GET /v1/cache
    
    Returns:
        Dictionary with model names as keys, each containing list of cache metadata
    """
    try:
        current_model = model_manager.get_current_model()
        if not current_model or not hasattr(current_model, 'cache_manager'):
            raise HTTPException(status_code=503, detail="No model loaded with cache support")
        
        caches = current_model.cache_manager.list_all_caches()
        
        return {
            "object": "list",
            "data": caches,
            "timestamp": int(time.time())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing all caches: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/{model_name}")
async def list_model_caches(model_name: str):
    """
    List prompt caches for a specific model
    
    Endpoint: GET /v1/cache/{model_name}
    
    Returns:
        List of cache metadata for the specified model
    """
    try:
        current_model = model_manager.get_current_model()
        if not current_model or not hasattr(current_model, 'cache_manager'):
            raise HTTPException(status_code=503, detail="No model loaded with cache support")
        
        caches = current_model.cache_manager.list_caches(model_name)
        
        return {
            "object": "list",
            "model": model_name,
            "data": caches,
            "count": len(caches),
            "timestamp": int(time.time())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing caches for {model_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/{model_name}/{cache_name}")
async def get_cache_info(model_name: str, cache_name: str):
    """
    Get detailed information about a specific cache
    
    Endpoint: GET /v1/cache/{model_name}/{cache_name}
    
    Returns:
        Cache metadata and content (if requested)
    """
    try:
        current_model = model_manager.get_current_model()
        if not current_model or not hasattr(current_model, 'cache_manager'):
            raise HTTPException(status_code=503, detail="No model loaded with cache support")
        
        cache_mgr = current_model.cache_manager
        
        # Check if cache exists
        if not cache_mgr.cache_exists(model_name, cache_name):
            raise HTTPException(
                status_code=404, 
                detail=f"Cache '{cache_name}' not found for model '{model_name}'"
            )
        
        # Get metadata
        caches = cache_mgr.list_caches(model_name)
        cache_info = next((c for c in caches if c['cache_name'] == cache_name), None)
        
        if not cache_info:
            raise HTTPException(status_code=404, detail=f"Cache '{cache_name}' not found for model '{model_name}'")
        
        return {
            "object": "cache",
            "model": model_name,
            "cache_name": cache_name,
            "size_mb": cache_info['size_mb'],
            "created_at": cache_info['created_at'],
            "modified_at": cache_info['modified_at'],
            "prompt_length": cache_info.get('prompt_length', 0),
            "source": cache_info.get('source', 'unknown'),
            "timestamp": int(time.time())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cache info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/{model_name}")
async def generate_cache(
    model_name: str,
    request: Request
):
    """
    Generate a binary RKLLM cache file for faster TTFT
    
    Endpoint: POST /v1/cache/{model_name}
    
    Body:
        {
            "cache_name": "system",  // Name for the binary cache
            "prompt": "..."          // Prompt to cache
        }
    
    This creates a .rkllm_cache file containing the NPU state after prefill.
    Subsequent requests can load this cache to skip prefill entirely (50-70% TTFT reduction).
    
    Returns:
        {
            "object": "cache.created",
            "model": "qwen3-0.6b",
            "cache_name": "system",
            "size_mb": 12.5,
            "ttft_ms": 180.3,
            "message": "Binary cache generated successfully"
        }
    """
    try:
        # Get request body
        body = await request.json()
        cache_name = body.get("cache_name")
        prompt = body.get("prompt")
        
        if not cache_name:
            raise HTTPException(status_code=400, detail="cache_name is required")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt is required")
        
        # Validate cache name
        if not cache_name.replace("-", "").replace("_", "").isalnum():
            raise HTTPException(
                status_code=400,
                detail="cache_name must be alphanumeric (hyphens and underscores allowed)"
            )
        
        current_model = model_manager.get_current_model()
        if not current_model:
            raise HTTPException(status_code=503, detail="No model loaded")
        
        if current_model.model_name != model_name:
            raise HTTPException(
                status_code=400,
                detail=f"Model '{model_name}' not loaded. Currently loaded: '{current_model.model_name}'"
            )
        
        cache_mgr = current_model.cache_manager
        
        # Get binary cache path
        binary_cache_path = cache_mgr.get_cache_path(model_name, cache_name)
        
        # Check if already exists - delete it first
        if cache_mgr.cache_exists(model_name, cache_name):
            logger.warning(f"Binary cache '{cache_name}' already exists, deleting before recreation")
            # Delete existing cache file
            try:
                import os
                if os.path.exists(binary_cache_path):
                    os.remove(binary_cache_path)
                    logger.info(f"Deleted existing cache file: {binary_cache_path}")
            except Exception as e:
                logger.error(f"Failed to delete existing cache: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Cannot overwrite existing cache: {e}"
                )
        
        logger.info(f"🔥 Generating binary cache: {cache_name}")
        logger.info(f"   Prompt length: {len(prompt)} chars")
        logger.info(f"   Output path: {binary_cache_path}")
        
        # Generate binary cache by running inference with save_binary_cache=True
        start_time = time.time()
        _, perf_stats = current_model.generate(
            prompt=prompt,
            max_new_tokens=1,  # Minimal generation, we just need the prefill cache
            binary_cache_path=binary_cache_path,
            save_binary_cache=True
        )
        generation_time_ms = (time.time() - start_time) * 1000
        
        # Verify cache was created
        if not cache_mgr.cache_exists(model_name, cache_name):
            raise HTTPException(
                status_code=500,
                detail="Binary cache generation failed - file not created"
            )
        
        # Save metadata
        cache_mgr.save_metadata(
            model_name=model_name,
            cache_name=cache_name,
            prompt_length=len(prompt),
            source="api",
            ttft_ms=perf_stats.get('prefill_time_ms', 0) if perf_stats else generation_time_ms
        )
        
        # Get cache info
        cache_info = cache_mgr.get_cache_info(model_name, cache_name)
        if not cache_info:
            raise HTTPException(
                status_code=500,
                detail="Binary cache created but info unavailable"
            )
        
        logger.info(f"✅ Binary cache generated: {cache_info['size_mb']:.2f} MB in {generation_time_ms:.1f}ms")
        
        return {
            "object": "cache.created",
            "model": model_name,
            "cache_name": cache_name,
            "size_mb": cache_info['size_mb'],
            "ttft_ms": perf_stats.get('prefill_time_ms', 0) if perf_stats else generation_time_ms,
            "prompt_length": len(prompt),
            "timestamp": int(time.time()),
            "message": f"Binary cache generated successfully ({cache_info['size_mb']:.2f} MB)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating binary cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/{model_name}/{cache_name}")
async def delete_cache(model_name: str, cache_name: str):
    """
    Delete a specific cache
    
    Endpoint: DELETE /v1/cache/{model_name}/{cache_name}
    
    Note: Cannot delete 'system' cache
    """
    try:
        # Prevent deletion of system cache
        if cache_name == "system":
            raise HTTPException(
                status_code=403, 
                detail="Cannot delete system cache. It will be auto-regenerated on model load."
            )
        
        current_model = model_manager.get_current_model()
        if not current_model or not hasattr(current_model, 'cache_manager'):
            raise HTTPException(status_code=503, detail="No model loaded with cache support")
        
        cache_mgr = current_model.cache_manager
        
        # Check if cache exists
        if not cache_mgr.cache_exists(model_name, cache_name):
            raise HTTPException(
                status_code=404, 
                detail=f"Cache '{cache_name}' not found for model '{model_name}'"
            )
        
        # Delete cache
        success = cache_mgr.delete_cache(model_name, cache_name)
        
        if success:
            return {
                "object": "cache.deleted",
                "model": model_name,
                "cache_name": cache_name,
                "deleted": True,
                "timestamp": int(time.time())
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete cache")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
