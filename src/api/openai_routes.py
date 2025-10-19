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
from typing import AsyncGenerator, Optional
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
    MessageRole
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
    """
    try:
        logger.info(f"Chat completion request for model: {request.model}")
        logger.debug(f"Messages: {len(request.messages)}, Stream: {request.stream}")
        
        # Format messages into prompt
        prompt = format_chat_prompt(request.messages)
        
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
                    created_time=created_time
                ),
                media_type="text/event-stream"
            )
        
        # Ensure model is loaded (auto-load if needed)
        current_model = await ensure_model_loaded(preferred_model=request.model)
        
        # Non-streaming response - use loaded model
        generated_text = current_model.generate(
            prompt=prompt,
            max_new_tokens=request.max_tokens or 512,
            temperature=request.temperature or 0.8,
            top_p=request.top_p or 0.9,
            top_k=request.top_k or 20,  # User preference: 20
            repeat_penalty=getattr(request, 'repeat_penalty', None) or 1.1
        )
        
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
                completion_tokens=len(generated_text.split()),
                total_tokens=len(prompt.split()) + len(generated_text.split())
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
    created_time: int
) -> AsyncGenerator[str, None]:
    """
    Stream chat completion tokens
    
    Yields SSE-formatted chunks
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
        current_model.generate(
            prompt=prompt,
            max_new_tokens=request.max_tokens or 512,
            temperature=request.temperature or 0.8,
            top_p=request.top_p or 0.9,
            top_k=request.top_k or 20,  # User preference: 20
            repeat_penalty=getattr(request, 'repeat_penalty', None) or 1.1,
            callback=streaming_callback
        )
        
        # Yield all buffered chunks
        for chunk in chunk_buffer:
            yield f"data: {chunk.model_dump_json()}\n\n"
        
        # Send final chunk with finish_reason
        final_chunk = ChatCompletionChunk(
            id=completion_id,
            created=created_time,
            model=request.model,
            choices=[{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(generated_text.split()),
                "total_tokens": len(prompt.split()) + len(generated_text.split())
            }
        )
        
        yield f"data: {final_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Error in streaming: {e}", exc_info=True)
        error_data = {"error": {"message": str(e), "type": "internal_error"}}
        yield f"data: {json.dumps(error_data)}\n\n"


@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """
    List available models (OpenAI compatible)
    
    Endpoint: GET /v1/models
    """
    try:
        # Scan models directory
        models_dir = settings.models_dir
        model_files = []
        
        if os.path.exists(models_dir):
            model_files = [
                f for f in os.listdir(models_dir)
                if f.endswith('.rkllm')
            ]
        
        # Create model info list
        models = []
        for model_file in model_files:
            # Extract model name (remove .rkllm extension)
            model_name = model_file.replace('.rkllm', '')
            
            models.append(
                ModelInfo(
                    id=model_name,
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
