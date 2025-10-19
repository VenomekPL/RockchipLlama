"""
Model Manager Service
Handles model lifecycle: loading, unloading, tracking
"""
import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from threading import Lock

from models.rkllm_model import RKLLMModel
from config.settings import settings

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Singleton service for managing RKLLM model lifecycle
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize model manager"""
        if not hasattr(self, 'initialized'):
            self.current_model: Optional[RKLLMModel] = None
            self.current_model_name: Optional[str] = None
            self.models_dir = settings.models_dir
            self.initialized = True
            logger.info(f"ModelManager initialized with models_dir: {self.models_dir}")
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available .rkllm models in models directory
        
        Returns:
            List of model info dictionaries
        """
        if not os.path.exists(self.models_dir):
            logger.warning(f"Models directory does not exist: {self.models_dir}")
            return []
        
        models = []
        for filename in os.listdir(self.models_dir):
            if filename.endswith('.rkllm'):
                filepath = os.path.join(self.models_dir, filename)
                file_size = os.path.getsize(filepath)
                
                # Extract model name (without .rkllm extension)
                model_name = filename.replace('.rkllm', '')
                
                models.append({
                    'name': model_name,
                    'filename': filename,
                    'path': filepath,
                    'size_bytes': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'loaded': (model_name == self.current_model_name)
                })
        
        return sorted(models, key=lambda x: x['size_bytes'])
    
    def get_model_path(self, model_name: str) -> Optional[str]:
        """
        Get full path for a model by name
        
        Args:
            model_name: Model name (with or without .rkllm extension)
            
        Returns:
            Full path to model file, or None if not found
        """
        # Add .rkllm extension if not present
        if not model_name.endswith('.rkllm'):
            filename = f"{model_name}.rkllm"
        else:
            filename = model_name
        
        filepath = os.path.join(self.models_dir, filename)
        
        if os.path.exists(filepath):
            return filepath
        
        logger.warning(f"Model file not found: {filepath}")
        return None
    
    def is_model_loaded(self) -> bool:
        """Check if any model is currently loaded"""
        return self.current_model is not None
    
    def get_loaded_model_name(self) -> Optional[str]:
        """Get name of currently loaded model"""
        return self.current_model_name
    
    def load_model(
        self,
        model_name: str,
        max_context_len: Optional[int] = None,
        num_npu_core: Optional[int] = None
    ) -> bool:
        """
        Load a model into memory
        
        Args:
            model_name: Name of model to load
            max_context_len: Maximum context length (default from settings)
            num_npu_core: Number of NPU cores to use (default from settings)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If model not found
            RuntimeError: If loading fails
        """
        with self._lock:
            try:
                # Get model path
                model_path = self.get_model_path(model_name)
                if not model_path:
                    raise ValueError(f"Model not found: {model_name}")
                
                # Unload current model if any
                if self.current_model is not None:
                    logger.info(f"Unloading current model: {self.current_model_name}")
                    self.unload_model()
                
                # Use defaults from settings if not provided
                if max_context_len is None:
                    max_context_len = settings.max_context_len
                if num_npu_core is None:
                    num_npu_core = settings.num_npu_core
                
                logger.info(f"Loading model: {model_name}")
                logger.info(f"  Path: {model_path}")
                logger.info(f"  Context length: {max_context_len}")
                logger.info(f"  NPU cores: {num_npu_core}")
                
                # Create and load model
                model = RKLLMModel(
                    model_path=model_path,
                    lib_path=settings.rkllm_lib_path
                )
                
                model.load(
                    max_context_len=max_context_len,
                    num_npu_core=num_npu_core
                )
                
                # Store loaded model
                self.current_model = model
                self.current_model_name = model_name.replace('.rkllm', '')
                
                logger.info(f"✅ Model loaded successfully: {self.current_model_name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}", exc_info=True)
                self.current_model = None
                self.current_model_name = None
                raise RuntimeError(f"Failed to load model: {e}")
    
    def unload_model(self) -> bool:
        """
        Unload currently loaded model
        
        Returns:
            True if successful, False if no model was loaded
        """
        with self._lock:
            if self.current_model is None:
                logger.warning("No model to unload")
                return False
            
            try:
                logger.info(f"Unloading model: {self.current_model_name}")
                self.current_model.unload()
                self.current_model = None
                self.current_model_name = None
                logger.info("✅ Model unloaded successfully")
                return True
                
            except Exception as e:
                logger.error(f"Error unloading model: {e}", exc_info=True)
                return False
    
    def get_current_model(self) -> Optional[RKLLMModel]:
        """
        Get currently loaded model instance
        
        Returns:
            RKLLMModel instance or None if no model loaded
        """
        return self.current_model
    
    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about currently loaded model
        
        Returns:
            Dictionary with model info or None if no model loaded
        """
        if self.current_model is None:
            return None
        
        return {
            'name': self.current_model_name,
            'path': self.current_model.model_path,
            'loaded': True
        }


# Global model manager instance
model_manager = ModelManager()
