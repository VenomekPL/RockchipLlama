"""
Format adapters for translating between different API styles and internal format.

This module provides bidirectional translation:
- OpenAI <-> Internal
- Ollama <-> Internal

All requests pass through internal format before reaching the model,
and all responses are translated back to the originating API format.
"""
import time
from datetime import datetime
from typing import List
from src.models.inference_types import InferenceRequest, InferenceResponse, InferenceMode
from src.api.schemas import (
    ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChoice,
    CompletionRequest, CompletionResponse, CompletionChoice,
    OllamaGenerateRequest, OllamaGenerateResponse,
    OllamaChatRequest, OllamaChatResponse,
    ChatMessage, Usage
)


# ============================================================================
# OpenAI → Internal
# ============================================================================

def openai_chat_to_internal(request: ChatCompletionRequest) -> InferenceRequest:
    """
    Convert OpenAI chat completion request to internal format
    
    Extracts the last user message as the prompt and converts
    parameters to internal format.
    """
    # Extract prompt from messages (concatenate for context)
    prompt_parts = []
    for msg in request.messages:
        if msg.role == "system":
            prompt_parts.append(f"System: {msg.content}")
        elif msg.role == "user":
            prompt_parts.append(f"User: {msg.content}")
        elif msg.role == "assistant":
            prompt_parts.append(f"Assistant: {msg.content}")
    
    # Simple format for now (can be enhanced with chat templates later)
    prompt = "\n".join(prompt_parts) + "\nAssistant:"
    
    return InferenceRequest(
        prompt=prompt,
        mode=InferenceMode.GENERATE,
        max_tokens=request.max_tokens or 512,
        temperature=request.temperature or 0.8,
        top_p=request.top_p or 0.9,
        top_k=request.top_k or 20,
        repeat_penalty=request.repeat_penalty or 1.1,
        stop=request.stop if isinstance(request.stop, list) else ([request.stop] if request.stop else None),
        stream=request.stream or False,
        source_api="openai",
        request_id=f"chatcmpl-{int(time.time()*1000)}"
    )


def openai_completion_to_internal(request: CompletionRequest) -> InferenceRequest:
    """Convert OpenAI text completion request to internal format"""
    return InferenceRequest(
        prompt=request.prompt,
        mode=InferenceMode.GENERATE,
        max_tokens=request.max_tokens or 512,
        temperature=request.temperature or 0.8,
        top_p=request.top_p or 0.9,
        top_k=request.top_k or 20,
        repeat_penalty=request.repeat_penalty or 1.1,
        stop=request.stop if isinstance(request.stop, list) else ([request.stop] if request.stop else None),
        stream=request.stream or False,
        source_api="openai",
        request_id=f"cmpl-{int(time.time()*1000)}"
    )


# ============================================================================
# Ollama → Internal
# ============================================================================

def ollama_generate_to_internal(request: OllamaGenerateRequest) -> InferenceRequest:
    """
    Convert Ollama generate request to internal format
    
    Maps Ollama's options dict to internal parameters.
    """
    options = request.options or {}
    
    return InferenceRequest(
        prompt=request.prompt,
        mode=InferenceMode.GENERATE,
        max_tokens=options.get("num_predict", 512),
        temperature=options.get("temperature", 0.8),
        top_p=options.get("top_p", 0.9),
        top_k=options.get("top_k", 20),
        repeat_penalty=options.get("repeat_penalty", 1.1),
        stop=options.get("stop", None),
        stream=request.stream or False,
        source_api="ollama",
        request_id=f"ollama-{int(time.time()*1000)}"
    )


def ollama_chat_to_internal(request: OllamaChatRequest) -> InferenceRequest:
    """
    Convert Ollama chat request to internal format
    
    Similar to OpenAI chat but with Ollama's parameter names.
    """
    options = request.options or {}
    
    # Build prompt from messages
    prompt_parts = []
    for msg in request.messages:
        if msg.role == "system":
            prompt_parts.append(f"System: {msg.content}")
        elif msg.role == "user":
            prompt_parts.append(f"User: {msg.content}")
        elif msg.role == "assistant":
            prompt_parts.append(f"Assistant: {msg.content}")
    
    prompt = "\n".join(prompt_parts) + "\nAssistant:"
    
    return InferenceRequest(
        prompt=prompt,
        mode=InferenceMode.GENERATE,
        max_tokens=options.get("num_predict", 512),
        temperature=options.get("temperature", 0.8),
        top_p=options.get("top_p", 0.9),
        top_k=options.get("top_k", 20),
        repeat_penalty=options.get("repeat_penalty", 1.1),
        stop=options.get("stop", None),
        stream=request.stream or False,
        source_api="ollama",
        request_id=f"ollama-chat-{int(time.time()*1000)}"
    )


# ============================================================================
# Internal → OpenAI
# ============================================================================

def internal_to_openai_chat(
    response: InferenceResponse,
    model_name: str
) -> ChatCompletionResponse:
    """Convert internal response to OpenAI chat completion format"""
    return ChatCompletionResponse(
        id=response.request_id,
        object="chat.completion",
        created=int(time.time()),
        model=model_name,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=response.text or ""
                ),
                finish_reason=response.finish_reason or "stop"
            )
        ],
        usage=Usage(
            prompt_tokens=response.prefill_tokens,
            completion_tokens=response.generate_tokens,
            total_tokens=response.prefill_tokens + response.generate_tokens
        )
    )


def internal_to_openai_completion(
    response: InferenceResponse,
    model_name: str
) -> CompletionResponse:
    """Convert internal response to OpenAI text completion format"""
    return CompletionResponse(
        id=response.request_id,
        object="text_completion",
        created=int(time.time()),
        model=model_name,
        choices=[
            CompletionChoice(
                text=response.text or "",
                index=0,
                finish_reason=response.finish_reason or "stop"
            )
        ],
        usage=Usage(
            prompt_tokens=response.prefill_tokens,
            completion_tokens=response.generate_tokens,
            total_tokens=response.prefill_tokens + response.generate_tokens
        )
    )


# ============================================================================
# Internal → Ollama
# ============================================================================

def internal_to_ollama_generate(
    response: InferenceResponse,
    model_name: str
) -> OllamaGenerateResponse:
    """Convert internal response to Ollama generate format"""
    # Convert milliseconds to nanoseconds
    total_duration_ns = int((response.prefill_time_ms + response.generate_time_ms) * 1_000_000)
    prompt_eval_duration_ns = int(response.prefill_time_ms * 1_000_000)
    eval_duration_ns = int(response.generate_time_ms * 1_000_000)
    
    return OllamaGenerateResponse(
        model=model_name,
        created_at=datetime.now().isoformat(),
        response=response.text or "",
        done=True,
        total_duration=total_duration_ns,
        load_duration=0,  # Model already loaded
        prompt_eval_count=response.prefill_tokens,
        prompt_eval_duration=prompt_eval_duration_ns,
        eval_count=response.generate_tokens,
        eval_duration=eval_duration_ns
    )


def internal_to_ollama_chat(
    response: InferenceResponse,
    model_name: str
) -> OllamaChatResponse:
    """Convert internal response to Ollama chat format"""
    # Convert milliseconds to nanoseconds
    total_duration_ns = int((response.prefill_time_ms + response.generate_time_ms) * 1_000_000)
    prompt_eval_duration_ns = int(response.prefill_time_ms * 1_000_000)
    eval_duration_ns = int(response.generate_time_ms * 1_000_000)
    
    return OllamaChatResponse(
        model=model_name,
        created_at=datetime.now().isoformat(),
        message=ChatMessage(
            role="assistant",
            content=response.text or ""
        ),
        done=True,
        total_duration=total_duration_ns,
        load_duration=0,
        prompt_eval_count=response.prefill_tokens,
        prompt_eval_duration=prompt_eval_duration_ns,
        eval_count=response.generate_tokens,
        eval_duration=eval_duration_ns
    )
