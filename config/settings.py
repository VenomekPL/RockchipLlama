"""
Configuration settings for RockchipLlama server
"""
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import os
import json
from pathlib import Path


class Settings(BaseSettings):
    """Server configuration"""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "info"
    
    # Model settings
    models_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    default_model: str = "qwen3-0.6b"
    hf_home: str = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface/hub"))
    
    # RKLLM Runtime settings
    rkllm_lib_path: str = "/usr/lib/librkllmrt.so"  # System library path
    max_context_len: int = 512  # Default context length
    max_new_tokens: int = 512  # Default max generation length
    
    # Performance settings
    num_npu_core: int = 3  # RK3588 has 3 NPU cores
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def load_inference_config() -> Dict[str, Any]:
    """Load inference configuration from JSON file"""
    config_path = Path(__file__).parent / "inference_config.json"
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default config if file not found
        return {
            "inference_params": {
                "top_k": 1,
                "top_p": 0.9,
                "temperature": 0.8,
                "repeat_penalty": 0.9,
                "max_new_tokens": 512,
                "max_context_len": 512,
                "skip_special_token": True,
                "is_async": False
            },
            "hardware": {
                "num_npu_cores": 3,
                "enabled_cpus_mask": 240,
                "num_threads": 4
            }
        }


# Global settings instances
settings = Settings()
inference_config = load_inference_config()
