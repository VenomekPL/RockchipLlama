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
from .stable_diffusion import StableDiffusionRKNN

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
            self.sd_model: Optional[StableDiffusionRKNN] = None
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
        print(f"DEBUG: Scanning directory: {self.models_dir}")
        logger.info(f"Scanning directory: {self.models_dir}")
        try:
            entries = os.listdir(self.models_dir)
            print(f"DEBUG: Found entries: {entries}")
            logger.info(f"Found entries: {entries}")
        except Exception as e:
            print(f"DEBUG: Error listing directory: {e}")
            logger.error(f"Error listing directory: {e}")
            return

        # Auto-download if empty
        if not entries:
            logger.warning("No models found. Attempting to download default models...")
            try:
                from scripts.download_models import download_models
                download_models()
                # Re-scan after download
                entries = os.listdir(self.models_dir)
            except Exception as e:
                logger.error(f"Failed to auto-download models: {e}")

        for folder_name in entries:
            folder_path = os.path.join(self.models_dir, folder_name)
            print(f"DEBUG: Checking entry: {folder_name}, path: {folder_path}, isdir: {os.path.isdir(folder_path)}")
            logger.info(f"Checking entry: {folder_name}, path: {folder_path}, isdir: {os.path.isdir(folder_path)}")
            
            # Skip files in root models directory
            if not os.path.isdir(folder_path):
                continue
            
            # Check for Stable Diffusion model
            if 'unet_lcm_512.rknn' in os.listdir(folder_path) or 'text_encoder.rknn' in os.listdir(folder_path):
                print(f"DEBUG: Found Stable Diffusion model in {folder_name}")
                self._model_cache[folder_name] = {
                    'path': folder_path,
                    'type': 'stable-diffusion',
                    'filename': 'stable-diffusion',
                    'context_size': 0
                }
                model_count += 1
                continue

            # Find .rkllm files in this folder
            rkllm_files = [f for f in os.listdir(folder_path) if f.endswith('.rkllm')]
            print(f"DEBUG: Folder {folder_name} files: {rkllm_files}")
            
            if not rkllm_files:
                print(f"DEBUG: No .rkllm file found in {folder_path}")
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
            print(f"DEBUG: Added model to cache: {friendly_name}")
            model_count += 1
            
            logger.info(
                f"Discovered local model: {friendly_name} "
                f"({model_filename}, ctx={context_size})"
            )
        
        # Scan Hugging Face cache
        self._discover_hf_models()
        
        logger.info(f"Total models discovered: {len(self._model_cache)}")

    def _discover_hf_models(self):
        """Scan Hugging Face cache for .rkllm files"""
        try:
            from huggingface_hub import scan_cache_dir
            
            # Check if HF_HOME exists
            if not os.path.exists(settings.hf_home):
                logger.debug(f"HF_HOME not found at {settings.hf_home}, skipping HF scan")
                return

            hf_cache = scan_cache_dir(settings.hf_home)
            
            for repo in hf_cache.repos:
                # repo.repo_id looks like "google/gemma-2b"
                repo_name = repo.repo_id.replace('/', '-')
                
                for revision in repo.revisions:
                    # Check snapshot directory for .rkllm files
                    snapshot_path = revision.snapshot_path
                    if not os.path.exists(snapshot_path):
                        continue
                        
                    for root, _, files in os.walk(snapshot_path):
                        for file in files:
                            if file.endswith('.rkllm'):
                                full_path = os.path.join(root, file)
                                filename = file
                                
                                # Create friendly name
                                # Strategy: hf-{repo_name} if unique, else hf-{repo_name}-{filename}
                                friendly_name = f"hf-{repo_name}"
                                
                                # If multiple models in repo, append filename stem
                                # Or if name collision with existing model
                                if friendly_name in self._model_cache:
                                    stem = Path(filename).stem
                                    friendly_name = f"{friendly_name}-{stem}"
                                
                                context_size = self._extract_context_size(filename)
                                
                                model_info = {
                                    'id': friendly_name,
                                    'filename': filename,
                                    'folder': 'huggingface', # Virtual folder
                                    'path': full_path,
                                    'context_size': context_size,
                                    'object': 'model',
                                    'owned_by': 'huggingface',
                                    'repo_id': repo.repo_id
                                }
                                
                                self._model_cache[friendly_name] = model_info
                                logger.info(f"Discovered HF model: {friendly_name} (ctx={context_size})")
                                
        except ImportError:
            logger.warning("huggingface_hub not installed. Skipping HF model discovery.")
        except Exception as e:
            logger.error(f"Error scanning HF cache: {e}")
    
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
        print(f"DEBUG: list_available_models called. Cache size: {len(self._model_cache)}")
        # Return unique models (avoid duplicates from multiple lookup keys)
        seen_paths = set()
        unique_models = []
        
        for key, model_info in self._model_cache.items():
            path = model_info['path']
            print(f"DEBUG: Processing cache entry: {key} -> {path}")
            if path not in seen_paths:
                try:
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
                except Exception as e:
                    print(f"DEBUG: Error getting info for {path}: {e}")
        
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
    
    async def get_stable_diffusion_model(self) -> Optional[StableDiffusionRKNN]:
        """
        Get or load the Stable Diffusion model.
        Loads on demand if not already loaded.
        """
        with self._lock:
            if self.sd_model and self.sd_model.is_loaded:
                return self.sd_model
            
            # Check if SD model path exists
            sd_path = settings.sd_model_path
            if not os.path.exists(sd_path):
                logger.warning(f"Stable Diffusion model path not found: {sd_path}")
                return None
                
            # If an LLM is loaded, we might need to unload it to free up NPU/RAM
            # For now, let's try to keep both if possible, or unload LLM if memory is tight.
            # Given 5.6GB requirement for SD, it's safer to unload LLM on 8GB/16GB boards.
            if self.current_model:
                logger.info("Unloading LLM to free resources for Stable Diffusion...")
                self.unload_model()
            
            try:
                logger.info(f"Initializing Stable Diffusion from {sd_path}")
                self.sd_model = StableDiffusionRKNN(sd_path)
                self.sd_model.load()
                return self.sd_model
            except Exception as e:
                logger.error(f"Failed to load Stable Diffusion: {e}")
                self.sd_model = None
                return None

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
                # Unload SD model if loaded (to free resources for LLM)
                if self.sd_model and self.sd_model.is_loaded:
                    logger.info("Unloading Stable Diffusion to free resources for LLM...")
                    self.sd_model.unload()
                    self.sd_model = None

                # Get model details (handles friendly names, filenames, etc.)
                model_details = self.get_model_details(model_name)
                if not model_details:
                    raise ValueError(f"Model not found: {model_name}")
                
                model_path = model_details['path']
                friendly_name = model_details['id']
                
                # Handle Stable Diffusion
                if model_details.get('type') == 'stable-diffusion':
                    logger.info(f"Loading Stable Diffusion model from {model_path}")
                    
                    # Unload LLM if loaded
                    if self.current_model:
                        logger.info(f"Unloading LLM '{self.current_model_name}' to load Stable Diffusion")
                        self.unload_model()
                    
                    if self.sd_model and self.sd_model.is_loaded:
                        logger.info("Stable Diffusion already loaded")
                        return True
                        
                    self.sd_model = StableDiffusionRKNN(model_dir=model_path)
                    self.sd_model.load()
                    return True

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
        Unload currently loaded model (LLM or Stable Diffusion)
        
        Returns:
            True if successful, False if no model was loaded
        """
        with self._lock:
            unloaded_something = False
            
            # Unload LLM
            if self.current_model is not None:
                try:
                    logger.info(f"Unloading LLM: {self.current_model_name}")
                    self.current_model.unload()
                    self.current_model = None
                    self.current_model_name = None
                    logger.info("✅ LLM unloaded successfully")
                    unloaded_something = True
                except Exception as e:
                    logger.error(f"Error unloading LLM: {e}", exc_info=True)
            
            # Unload Stable Diffusion
            if self.sd_model is not None:
                try:
                    logger.info("Unloading Stable Diffusion model")
                    self.sd_model.unload()
                    self.sd_model = None
                    logger.info("✅ Stable Diffusion unloaded successfully")
                    unloaded_something = True
                except Exception as e:
                    logger.error(f"Error unloading Stable Diffusion: {e}", exc_info=True)

            if not unloaded_something:
                logger.warning("No model to unload")
                return False
                
            return True
    
    def get_current_model(self) -> Optional[RKLLMModel]:
        """
        Get currently loaded model instance
        
        Returns:
            RKLLMModel instance or None if no model loaded
        """
        return self.current_model
    
    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about currently loaded model (LLM or Stable Diffusion)
        
        Returns:
            Dictionary with model info or None if no model loaded
        """
        # Check for Stable Diffusion
        if self.sd_model and self.sd_model.is_loaded:
             return {
                'name': 'stable-diffusion',
                'path': self.sd_model.model_dir,
                'loaded': True,
                'type': 'stable-diffusion',
                'context_size': 0
            }

        if self.current_model is None or self.current_model_name is None:
            return None
        
        # Get full details from cache
        model_details = self.get_model_details(self.current_model_name)
        
        return {
            'name': self.current_model_name,  # Friendly name
            'path': self.current_model.model_path,
            'loaded': True,
            'type': 'llm',
            'context_size': model_details['context_size'] if model_details else None,
            'filename': model_details['filename'] if model_details else None
        }

    def download_model_from_hf(self, repo_id: str, filename: str, friendly_name: Optional[str] = None) -> Any:
        """
        Download a model from Hugging Face Hub.
        Returns a generator that yields progress updates.
        """
        from huggingface_hub import hf_hub_download, get_hf_file_metadata, hf_hub_url
        import time
        import shutil
        
        # Determine friendly name if not provided
        if not friendly_name:
            friendly_name = filename.replace('.rkllm', '').lower()
            # Clean up name
            friendly_name = re.sub(r'[^\w\-_]', '_', friendly_name)
            
        target_dir = os.path.join(self.models_dir, friendly_name)
        os.makedirs(target_dir, exist_ok=True)
        
        logger.info(f"Starting download: {repo_id}/{filename} -> {target_dir}")
        
        # Shared state for progress tracking
        progress_state = {
            "status": "starting",
            "downloaded": 0,
            "total": 0,
            "percent": 0,
            "speed": 0,
            "error": None,
            "completed": False
        }
        
        def download_thread():
            try:
                # Get file info first to know total size
                try:
                    url = hf_hub_url(repo_id, filename)
                    meta = get_hf_file_metadata(url)
                    progress_state["total"] = meta.size
                except Exception as e:
                    logger.warning(f"Could not get metadata: {e}")
                    progress_state["total"] = 0

                progress_state["status"] = "downloading"
                
                # Run download
                hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    local_dir=target_dir,
                    local_dir_use_symlinks=False,
                    resume_download=True
                )
                
                progress_state["status"] = "processing"
                progress_state["percent"] = 100
                progress_state["completed"] = True
                
                # Trigger discovery to find the new model
                self._discover_models()
                
            except Exception as e:
                logger.error(f"Download failed: {e}")
                progress_state["status"] = "failed"
                progress_state["error"] = str(e)

        # Start download in background thread
        thread = threading.Thread(target=download_thread)
        thread.start()
        
        # Generator to yield progress
        while not progress_state["completed"] and progress_state["status"] != "failed":
            # Monitor file size if possible
            try:
                # Find the partial file or the final file
                final_path = os.path.join(target_dir, filename)
                
                current_size = 0
                if os.path.exists(final_path):
                    current_size = os.path.getsize(final_path)
                
                # If we can't find the file, check for any file in that dir growing
                if current_size == 0:
                    for f in os.listdir(target_dir):
                        fp = os.path.join(target_dir, f)
                        if os.path.isfile(fp):
                            current_size = max(current_size, os.path.getsize(fp))
                
                progress_state["downloaded"] = current_size
                if progress_state["total"] > 0:
                    progress_state["percent"] = (current_size / progress_state["total"]) * 100
                
            except Exception:
                pass
            
            yield progress_state
            time.sleep(0.5)
            
        yield progress_state


# Global model manager instance
model_manager = ModelManager()
