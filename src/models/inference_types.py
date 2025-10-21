"""
Internal request/response types for unified API handling.

These types are API-agnostic and used internally to process requests
from different API formats (OpenAI, Ollama, etc.) through a shared queue.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class InferenceMode(Enum):
    """Inference operation mode"""
    GENERATE = "generate"      # Text generation
    EMBEDDINGS = "embeddings"  # Extract embeddings (future)


@dataclass
class InferenceRequest:
    """
    Unified request format for all APIs
    
    This internal format allows different API styles (OpenAI, Ollama)
    to be processed through the same model queue.
    """
    prompt: str
    mode: InferenceMode = InferenceMode.GENERATE
    
    # Generation parameters (used when mode=GENERATE)
    max_tokens: int = 512
    temperature: float = 0.8
    top_p: float = 0.9
    top_k: int = 20
    repeat_penalty: float = 1.1
    stop: Optional[list[str]] = None
    stream: bool = False
    
    # Metadata
    request_id: str = ""
    source_api: str = "openai"  # "openai" or "ollama"


@dataclass
class InferenceResponse:
    """
    Unified response format
    
    Contains all information needed to format responses
    for different API styles.
    """
    # For generation
    text: Optional[str] = None
    finish_reason: Optional[str] = None
    
    # For embeddings (future)
    embedding: Optional[list[float]] = None
    embedding_dim: Optional[int] = None
    
    # Common metadata
    tokens_processed: int = 0
    time_ms: float = 0.0
    request_id: str = ""
    
    # Performance stats
    prefill_time_ms: float = 0.0
    prefill_tokens: int = 0
    generate_time_ms: float = 0.0
    generate_tokens: int = 0
