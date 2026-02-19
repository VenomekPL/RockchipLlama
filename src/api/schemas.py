"""
OpenAI-compatible API schemas
Following OpenAI API specification for chat completions
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal, Union
from enum import Enum


class MessageRole(str, Enum):
    """Chat message roles"""
    system = "system"
    user = "user"
    assistant = "assistant"
    tool = "tool"


class ImageUrl(BaseModel):
    """Image URL object"""
    url: str
    detail: Optional[str] = "auto"


class ContentPart(BaseModel):
    """Part of a multimodal message content"""
    type: Literal["text", "image_url"]
    text: Optional[str] = None
    image_url: Optional[ImageUrl] = None


class ChatMessage(BaseModel):
    """Single chat message"""
    role: MessageRole
    content: Union[str, List[ContentPart]]
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request"""
    model: str = Field(default="default", description="Model to use for completion")
    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")
    temperature: Optional[float] = Field(default=0.8, ge=0.0, le=2.0, description="Sampling temperature (RKLLM default: 0.8)")
    top_p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0, description="Nucleus sampling parameter (RKLLM default: 0.9)")
    enable_thinking: Optional[bool] = Field(default=None, description="Enable/disable Thinking Mode (overrides server config)")
    top_k: Optional[int] = Field(default=20, ge=1, description="Top-k sampling parameter (User preference: 20)")
    max_tokens: Optional[int] = Field(default=-1, description="Maximum tokens to generate (-1 for unbound/model limit)")
    stream: Optional[bool] = Field(default=False, description="Enable streaming responses")
    stop: Optional[Union[str, List[str]]] = Field(default=None, description="Stop sequences")
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0, description="RKLLM presence_penalty (default: 0.0)")
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0, description="RKLLM frequency_penalty (default: 0.0)")
    repeat_penalty: Optional[float] = Field(default=1.1, ge=1.0, le=2.0, description="RKLLM repeat_penalty (default: 1.1)")
    n: Optional[int] = Field(default=1, ge=1, le=1, description="Number of completions (only 1 supported)")
    user: Optional[str] = None
    
    # 🔥 Binary prompt caching support
    use_cache: Optional[str] = Field(
        default=None,
        description="Binary cache name to load for 50-70% TTFT reduction. "
                    "The cached prompt (e.g., system prompt) is loaded from NPU state, "
                    "then new messages are processed on top of it."
    )
    
    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "model": "gemma-3-270m",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"}
                ],
                "temperature": 0.8,
                "max_tokens": 512,
                "use_cache": "system"
            }
        }
    }


class ChatCompletionChoice(BaseModel):
    """Single completion choice"""
    index: int
    message: ChatMessage
    finish_reason: Literal["stop", "length", "tool_calls", "content_filter", "null"] = "stop"


class Usage(BaseModel):
    """Token usage information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    # 🔥 NEW: Cache usage tracking
    cached_prompts: Optional[List[str]] = Field(
        default=None,
        description="List of cache names that were applied to this request"
    )
    cache_hit: Optional[bool] = Field(
        default=None,
        description="Whether any caches were used in this request"
    )


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response"""
    id: str = Field(description="Unique completion ID")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(description="Unix timestamp")
    model: str = Field(description="Model used")
    choices: List[ChatCompletionChoice]
    usage: Usage


class ChatCompletionChunk(BaseModel):
    """Streaming chunk for chat completion"""
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Usage] = None  # Performance stats in final chunk


class ModelInfo(BaseModel):
    """Model information"""
    id: str
    object: Literal["model"] = "model"
    created: int
    owned_by: str = "rockchip"


class ModelListResponse(BaseModel):
    """List of available models"""
    object: Literal["list"] = "list"
    data: List[ModelInfo]


class ErrorResponse(BaseModel):
    """Error response"""
    error: Dict[str, Any]


# ============================================================================
# TEXT COMPLETION SCHEMAS (OpenAI /v1/completions)
# ============================================================================

class CompletionRequest(BaseModel):
    """OpenAI-compatible text completion request"""
    model: str = Field(default="default", description="Model to use for completion")
    prompt: str = Field(..., description="The prompt to generate completions for")
    temperature: Optional[float] = Field(default=0.8, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: Optional[int] = Field(default=20, ge=1, description="Top-k sampling parameter")
    max_tokens: Optional[int] = Field(default=512, ge=1, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(default=False, description="Enable streaming responses")
    stop: Optional[Union[str, List[str]]] = Field(default=None, description="Stop sequences")
    repeat_penalty: Optional[float] = Field(default=1.1, ge=1.0, le=2.0, description="RKLLM repeat_penalty")
    n: Optional[int] = Field(default=1, ge=1, le=1, description="Number of completions (only 1 supported)")
    user: Optional[str] = None
    
    # 🔥 Binary prompt caching support
    use_cache: Optional[str] = Field(
        default=None,
        description="Binary cache name to load for faster inference"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "qwen3-0.6b",
                "prompt": "Once upon a time",
                "temperature": 0.8,
                "max_tokens": 256
            }
        }


class CompletionChoice(BaseModel):
    """Single text completion choice"""
    text: str
    index: int
    finish_reason: Literal["stop", "length", "null"] = "stop"


class CompletionResponse(BaseModel):
    """OpenAI-compatible text completion response"""
    id: str = Field(description="Unique completion ID")
    object: Literal["text_completion"] = "text_completion"
    created: int = Field(description="Unix timestamp")
    model: str = Field(description="Model used")
    choices: List[CompletionChoice]
    usage: Usage


class TextCompletionChunk(BaseModel):
    """Streaming chunk for text completion"""
    id: str
    object: Literal["text_completion"] = "text_completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Usage] = None


# ============================================================================
# OLLAMA API SCHEMAS
# ============================================================================

class OllamaGenerateRequest(BaseModel):
    """Ollama-compatible generate request"""
    model: str = Field(..., description="Model name")
    prompt: str = Field(..., description="The prompt to generate from")
    stream: Optional[bool] = Field(default=False, description="Enable streaming")
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Model options (num_predict, temperature, top_k, top_p, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "qwen3-0.6b",
                "prompt": "Why is the sky blue?",
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "num_predict": 256
                }
            }
        }


class OllamaGenerateResponse(BaseModel):
    """Ollama-compatible generate response"""
    model: str
    created_at: str = Field(description="ISO 8601 timestamp")
    response: str = Field(description="Generated text")
    done: bool = Field(default=True)
    context: Optional[List[int]] = Field(default=None, description="Token context")
    total_duration: Optional[int] = Field(default=None, description="Total time in nanoseconds")
    load_duration: Optional[int] = Field(default=None, description="Model load time in nanoseconds")
    prompt_eval_count: Optional[int] = Field(default=None, description="Number of tokens in prompt")
    prompt_eval_duration: Optional[int] = Field(default=None, description="Prompt evaluation time")
    eval_count: Optional[int] = Field(default=None, description="Number of tokens generated")
    eval_duration: Optional[int] = Field(default=None, description="Generation time in nanoseconds")


class OllamaChatRequest(BaseModel):
    """Ollama-compatible chat request"""
    model: str = Field(..., description="Model name")
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    stream: Optional[bool] = Field(default=False, description="Enable streaming")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Model options")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "qwen3-0.6b",
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "stream": False
            }
        }


class OllamaChatResponse(BaseModel):
    """Ollama-compatible chat response"""
    model: str
    created_at: str
    message: ChatMessage
    done: bool = Field(default=True)
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


# ============================================================================
# EMBEDDING SCHEMAS (OpenAI /v1/embeddings)
# ============================================================================

class EmbeddingRequest(BaseModel):
    """OpenAI-compatible embedding request"""
    model: str = Field(default="default", description="Model to use for embeddings")
    input: Union[str, List[str]] = Field(..., description="Text(s) to embed - string or array of strings")
    encoding_format: Optional[Literal["float", "base64"]] = Field(
        default="float",
        description="Format for embeddings (only 'float' supported currently)"
    )
    dimensions: Optional[int] = Field(
        default=None,
        description="Embedding dimensions (model-dependent, truncation not supported)"
    )
    user: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "qwen3-0.6b",
                "input": "The quick brown fox jumps over the lazy dog",
                "encoding_format": "float"
            }
        }


class EmbeddingData(BaseModel):
    """Single embedding result"""
    object: Literal["embedding"] = "embedding"
    embedding: List[float] = Field(description="The embedding vector (normalized)")
    index: int = Field(description="Index in the input array")


class EmbeddingUsage(BaseModel):
    """Token usage for embeddings"""
    prompt_tokens: int
    total_tokens: int


class EmbeddingResponse(BaseModel):
    """OpenAI-compatible embedding response"""
    object: Literal["list"] = "list"
    data: List[EmbeddingData]
    model: str
    usage: EmbeddingUsage


# ============================================================================
# OLLAMA EMBEDDING SCHEMAS
# ============================================================================

class OllamaEmbeddingRequest(BaseModel):
    """Ollama-compatible embedding request"""
    model: str = Field(..., description="Model name")
    prompt: str = Field(..., description="Text to embed")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Model options")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "qwen3-0.6b",
                "prompt": "The quick brown fox"
            }
        }


class OllamaEmbeddingResponse(BaseModel):
    """Ollama-compatible embedding response"""
    embedding: List[float] = Field(description="The embedding vector")
    model: str
    created_at: str = Field(description="ISO 8601 timestamp")
    total_duration: Optional[int] = Field(default=None, description="Total time in nanoseconds")
    load_duration: Optional[int] = Field(default=None, description="Model load time in nanoseconds")
    prompt_eval_count: Optional[int] = Field(default=None, description="Number of tokens in prompt")
