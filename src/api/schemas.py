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


class ChatMessage(BaseModel):
    """Single chat message"""
    role: MessageRole
    content: str
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request"""
    model: str = Field(default="default", description="Model to use for completion")
    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")
    temperature: Optional[float] = Field(default=0.8, ge=0.0, le=2.0, description="Sampling temperature (RKLLM default: 0.8)")
    top_p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0, description="Nucleus sampling parameter (RKLLM default: 0.9)")
    top_k: Optional[int] = Field(default=20, ge=1, description="Top-k sampling parameter (User preference: 20)")
    max_tokens: Optional[int] = Field(default=512, ge=1, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(default=False, description="Enable streaming responses")
    stop: Optional[Union[str, List[str]]] = Field(default=None, description="Stop sequences")
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0, description="RKLLM presence_penalty (default: 0.0)")
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0, description="RKLLM frequency_penalty (default: 0.0)")
    repeat_penalty: Optional[float] = Field(default=1.1, ge=1.0, le=2.0, description="RKLLM repeat_penalty (default: 1.1)")
    n: Optional[int] = Field(default=1, ge=1, le=1, description="Number of completions (only 1 supported)")
    user: Optional[str] = None
    
    # 🔥 NEW: Prompt caching support
    cache_prompts: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Cache name(s) to prepend to the prompt. Can be a single string or array of cache names. "
                    "System cache is always applied automatically. Multiple caches are concatenated in order."
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "gemma-3-270m",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"}
                ],
                "temperature": 0.8,
                "max_tokens": 512,
                "cache_prompts": ["coding_rules", "project_context"]
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
    usage: Optional[Dict[str, Any]] = None  # Performance stats in final chunk


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
