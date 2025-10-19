"""
Configuration settings for RockchipLlama server
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Server configuration"""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "info"
    
    # Model settings
    models_dir: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    default_model: str = "google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm"
    
    # RKLLM Runtime settings
    rkllm_lib_path: str = "/usr/lib/librkllmrt.so"  # System library path
    max_context_len: int = 512  # Default context length
    max_new_tokens: int = 512  # Default max generation length
    
    # Performance settings
    num_npu_core: int = 3  # RK3588 has 3 NPU cores
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
