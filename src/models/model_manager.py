"""
Model Manager - Handles model discovery and lifecycle with friendly names
"""
import os
import re
import sys
import logging
from typing import Optional, List, Dict, Any
import threading
from pathlib import Path

# Add project root to path for config imports
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from config.settings import settings
from .rkllm_model import RKLLMModel

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Singleton service for managing RKLLM model lifecycle with friendly names
    """
    _instance = None
    _lock = threading.Lock()
    
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
            self._model_cache: Dict[str, Dict[str, Any]] = {}
            self._instance_lock = threading.Lock()
            self.initialized = True
            logger.info(f"ModelManager initialized with models_dir: {self.models_dir}")
            self._discover_models()
    
    def _create_friendly_name_from_filename(self, filename: str) -> str:
        """
        DEPRECATED: Create a friendly name from RKLLM filename
        
        This is now replaced by folder-based naming.
        Folder name = friendly name (user-defined).
        """
        # Remove .rkllm extension
        name = filename.replace('.rkllm', '').lower()
        
        # Extract key components for common patterns
        if 'qwen3' in name and '0.6b' in name:
            return 'qwen3-0.6b'
        elif 'qwen3' in name and '4b' in name:
            return 'qwen3-4b'
        elif 'qwen2' in name and '0.5b' in name:
            return 'qwen2-0.5b'
        elif 'qwen2' in name and '1.5b' in name:
            return 'qwen2-1.5b'
        elif 'gemma' in name and '1b' in name:
            return 'gemma3-1b'
        elif 'gemma' in name and '270m' in name:
            return 'gemma3-270m'
        elif 'gemma' in name and '2b' in name:
            return 'gemma3-2b'
        else:
            # Fallback: use first part before version/config
            parts = name.replace('_', '-').split('-')
            return parts[0] if parts else name
    
    def _extract_context_size(self, filename: str) -> int:
        """Extract context size from filename or return default"""
        ctx_match = re.search(r'ctx(\d+)', filename)
        if ctx_match:
            return int(ctx_match.group(1))
        # If no ctx specified, model was likely built with 4K context
        return 4096
    
    def _discover_models(self):
        """
        Scan models directory for model folders and build cache
        
        New Structure:
            models/
            ├── qwen3-0.6b/           # Folder name = friendly name
            │   └── model.rkllm       # Actual model file
            ├── qwen3-4b/
            │   └── model.rkllm
            └── gemma3-1b/
                └── model.rkllm
        
        Folder name is used as the friendly name.
        User can rename folders to customize friendly names.
        """
        if not os.path.exists(self.models_dir):
            logger.warning(f"Models directory not found: {self.models_dir}")
            return
        
        self._model_cache.clear()
        model_count = 0
        
        # Scan for model folders
        for folder_name in os.listdir(self.models_dir):
            folder_path = os.path.join(self.models_dir, folder_name)
            
            # Skip files in root models directory
            if not os.path.isdir(folder_path):
                continue
            
            # Find .rkllm files in this folder
            rkllm_files = [f for f in os.listdir(folder_path) if f.endswith('.rkllm')]
            
            if not rkllm_files:
                logger.warning(f"No .rkllm file found in {folder_path}")
                continue
            
            # Use first .rkllm file found (user responsibility to have only one)
            if len(rkllm_files) > 1:
                logger.warning(
                    f"Multiple .rkllm files in {folder_path}. "
                    f"Using first one: {rkllm_files[0]}"
                )
            
            model_filename = rkllm_files[0]
            model_path = os.path.join(folder_path, model_filename)
            
            # Folder name IS the friendly name
            friendly_name = folder_name
            
            # Extract context size from filename
            context_size = self._extract_context_size(model_filename)
            
            model_info = {
                'id': friendly_name,
                'filename': model_filename,
                'folder': folder_name,
                'path': model_path,
                'context_size': context_size,
                'object': 'model',
                'owned_by': 'rkllm'
            }
            
            # Store by friendly name only (folder name)
            self._model_cache[friendly_name] = model_info
            model_count += 1
            
            logger.info(
                f"Discovered model: {friendly_name} "
                f"({model_filename}, ctx={context_size})"
            )
        
        logger.info(f"Discovered {model_count} models")
    
    def find_model_path(self, model_identifier: str) -> Optional[str]:
        """Find model path by friendly name, filename, or normalized name
        
        Args:
            model_identifier: Can be:
                - Friendly name: "qwen3-0.6b"
                - Full filename: "Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm"
                - Normalized name: "Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588"
        
        Returns:
            Full path to model file, or None if not found
        """
        # Direct lookup
        if model_identifier in self._model_cache:
            return self._model_cache[model_identifier]['path']
        
        # Case-insensitive search
        model_id_lower = model_identifier.lower()
        for key, model_info in self._model_cache.items():
            if key.lower() == model_id_lower:
                return model_info['path']
        
        return None
    
    def get_model_details(self, model_identifier: str) -> Optional[Dict[str, Any]]:
        """Get full model information by friendly name or filename"""
        if model_identifier in self._model_cache:
            return self._model_cache[model_identifier].copy()
        
        # Case-insensitive search
        model_id_lower = model_identifier.lower()
        for key, model_info in self._model_cache.items():
            if key.lower() == model_id_lower:
                return model_info.copy()
        
        return None
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available .rkllm models with friendly names and context info
        
        Returns:
            List of model info dictionaries with friendly names
        """
        # Return unique models (avoid duplicates from multiple lookup keys)
        seen_paths = set()
        unique_models = []
        
        for model_info in self._model_cache.values():
            path = model_info['path']
            if path not in seen_paths:
                file_size = os.path.getsize(path)
                model_entry = {
                    'name': model_info['id'],  # Friendly name
                    'friendly_name': model_info['id'],
                    'filename': model_info['filename'],
                    'path': path,
                    'context_size': model_info['context_size'],
                    'size_bytes': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'loaded': (model_info['id'] == self.current_model_name or 
                              model_info['filename'].replace('.rkllm', '') == self.current_model_name),
                    'object': 'model',
                    'owned_by': 'rkllm'
                }
                unique_models.append(model_entry)
                seen_paths.add(path)
        
        return sorted(unique_models, key=lambda x: x['size_bytes'])
    
    def get_model_path(self, model_name: str) -> Optional[str]:
        """
        Get full path for a model by friendly name, filename, or normalized name
        
        Args:
            model_name: Model identifier (friendly name, filename, or normalized)
                - Friendly: "qwen3-0.6b"
                - Filename: "Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm"
                - Normalized: "Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588"
        
        Returns:
            Full path to model file, or None if not found
        """
        # Use the cache lookup
        return self.find_model_path(model_name)
    
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
            model_name: Name of model to load (can be friendly name, filename, or full path)
            max_context_len: Maximum context length (auto-detected from model if not provided)
            num_npu_core: Number of NPU cores to use (default from settings)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If model not found
            RuntimeError: If loading fails
        """
        with self._lock:
            try:
                # Get model details (handles friendly names, filenames, etc.)
                model_details = self.get_model_details(model_name)
                if not model_details:
                    raise ValueError(f"Model not found: {model_name}")
                
                model_path = model_details['path']
                friendly_name = model_details['id']
                detected_context = model_details['context_size']
                
                # Check if this model is already loaded
                if self.current_model is not None and self.current_model_name == friendly_name:
                    logger.info(f"Model '{friendly_name}' is already loaded, skipping reload")
                    return True
                
                # If a different model is already loaded, unload it first
                if self.current_model is not None:
                    logger.info(f"Unloading current model '{self.current_model_name}' to load '{friendly_name}'")
                    try:
                        self.unload_model()
                    except Exception as e:
                        logger.error(f"Failed to unload current model: {e}")
                        # Continue anyway - try to load new model
                        self.current_model = None
                        self.current_model_name = None
                
                # Use detected context size if not explicitly provided
                if max_context_len is None:
                    max_context_len = detected_context
                    logger.info(f"Using detected context size: {max_context_len} tokens")
                else:
                    # Warn if requested context exceeds model's capability
                    if max_context_len > detected_context:
                        logger.warning(
                            f"Requested context length ({max_context_len}) exceeds "
                            f"model's built-in context size ({detected_context}). "
                            f"Using detected context size."
                        )
                        max_context_len = detected_context
                
                # Ensure max_context_len is set
                if max_context_len is None:
                    max_context_len = settings.max_context_len
                    logger.warning(f"Could not detect context size, using default: {max_context_len}")
                
                # Use default NPU cores from settings if not provided
                if num_npu_core is None:
                    num_npu_core = settings.num_npu_core
                
                logger.info(f"Loading model: {friendly_name}")
                logger.info(f"  Full name: {model_details['filename']}")
                logger.info(f"  Path: {model_path}")
                logger.info(f"  Context size: {max_context_len} tokens (detected: {detected_context})")
                logger.info(f"  NPU cores: {num_npu_core}")
                logger.info(f"  NOTE: This model will stay loaded until server restart")
                
                # Create and load model
                model = RKLLMModel(
                    model_path=model_path,
                    lib_path=settings.rkllm_lib_path
                )
                
                model.load(
                    max_context_len=max_context_len,
                    num_npu_core=num_npu_core
                )
                
                # Store loaded model with friendly name
                self.current_model = model
                self.current_model_name = friendly_name
                
                logger.info(f"✅ Model loaded successfully: {friendly_name}")
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
        if self.current_model is None or self.current_model_name is None:
            return None
        
        # Get full details from cache
        model_details = self.get_model_details(self.current_model_name)
        
        return {
            'name': self.current_model_name,  # Friendly name
            'path': self.current_model.model_path,
            'loaded': True,
            'context_size': model_details['context_size'] if model_details else None,
            'filename': model_details['filename'] if model_details else None
        }


# Global model manager instance
model_manager = ModelManager()
