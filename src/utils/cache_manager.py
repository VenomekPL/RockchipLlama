"""
Binary Prompt Cache Manager for RKLLM Models

Handles REAL RKLLM binary prompt caching for performance optimization.
Binary caches save NPU computation state for 50-70% TTFT reduction.
"""
import os
import json
import time
from typing import Optional, Dict, Any, List
from pathlib import Path


class PromptCacheManager:
    """Manages RKLLM binary prompt caches (NPU state caching)"""
    
    def __init__(self, cache_base_dir: str = "cache"):
        """
        Initialize cache manager
        
        Args:
            cache_base_dir: Base directory for all caches (default: "cache", relative to project root)
        """
        # Find project root (parent of src directory)
        if Path(cache_base_dir).is_absolute():
            self.cache_base_dir = Path(cache_base_dir)
        else:
            # Get project root (parent of src directory where this file is located)
            project_root = Path(__file__).parent.parent.parent
            self.cache_base_dir = project_root / cache_base_dir
        
        self.cache_base_dir.mkdir(exist_ok=True)
    
    def _get_model_cache_dir(self, model_name: str) -> Path:
        """Get cache directory for a specific model"""
        cache_dir = self.cache_base_dir / model_name
        cache_dir.mkdir(exist_ok=True)
        return cache_dir
    
    def get_cache_path(self, model_name: str, cache_name: str) -> str:
        """
        Get the path to a binary cache file (.rkllm_cache)
        
        Args:
            model_name: Friendly model name
            cache_name: Cache identifier
            
        Returns:
            Absolute path to binary cache file
        """
        cache_dir = self._get_model_cache_dir(model_name)
        return str(cache_dir / f"{cache_name}.rkllm_cache")
    
    def cache_exists(self, model_name: str, cache_name: str) -> bool:
        """
        Check if a binary cache file exists
        
        Args:
            model_name: Friendly model name
            cache_name: Cache identifier
            
        Returns:
            True if cache exists, False otherwise
        """
        path = self.get_cache_path(model_name, cache_name)
        return os.path.exists(path)
    
    def get_cache_info(self, model_name: str, cache_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a binary cache file
        
        Args:
            model_name: Friendly model name
            cache_name: Cache identifier
            
        Returns:
            Dictionary with size_mb, created_at, modified_at, or None if doesn't exist
        """
        path = self.get_cache_path(model_name, cache_name)
        if not os.path.exists(path):
            return None
        
        stat = os.stat(path)
        
        # Try to load metadata if it exists
        metadata_path = path.replace('.rkllm_cache', '.json')
        metadata = {}
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except:
                pass
        
        return {
            "cache_name": cache_name,
            "model_name": model_name,
            "path": path,
            "size_mb": stat.st_size / (1024 * 1024),
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
            "prompt_length": metadata.get("prompt_length", 0),
            "source": metadata.get("source", "unknown")
        }
    
    def save_metadata(
        self, 
        model_name: str, 
        cache_name: str, 
        prompt_length: int,
        source: str = "api",
        ttft_ms: float = 0.0
    ):
        """
        Save metadata for a binary cache
        
        Args:
            model_name: Friendly model name
            cache_name: Cache identifier
            prompt_length: Length of cached prompt in characters
            source: Source of the cache (api, system, etc.)
            ttft_ms: Time to first token in milliseconds
        """
        cache_dir = self._get_model_cache_dir(model_name)
        metadata_path = cache_dir / f"{cache_name}.json"
        
        metadata = {
            "cache_name": cache_name,
            "model_name": model_name,
            "created_at": time.time(),
            "prompt_length": prompt_length,
            "source": source,
            "ttft_ms": ttft_ms
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def delete_cache(self, model_name: str, cache_name: str) -> bool:
        """
        Delete a binary cache file and its metadata
        
        Args:
            model_name: Friendly model name
            cache_name: Cache identifier
            
        Returns:
            True if deleted, False if didn't exist
        """
        path = self.get_cache_path(model_name, cache_name)
        metadata_path = path.replace('.rkllm_cache', '.json')
        
        deleted = False
        if os.path.exists(path):
            os.remove(path)
            print(f"[CACHE] Deleted binary cache: {cache_name}")
            deleted = True
        
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
            deleted = True
        
        return deleted
    
    def list_caches(self, model_name: str) -> List[Dict[str, Any]]:
        """
        List all binary cache files for a model
        
        Args:
            model_name: Friendly model name
            
        Returns:
            List of dictionaries with cache information
        """
        cache_dir = self._get_model_cache_dir(model_name)
        caches = []
        
        for cache_file in cache_dir.glob("*.rkllm_cache"):
            cache_name = cache_file.stem
            info = self.get_cache_info(model_name, cache_name)
            if info:
                caches.append(info)
        
        # Sort by creation time, newest first
        caches.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        return caches
    
    def list_all_caches(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List all binary caches across all models
        
        Returns:
            Dictionary mapping model names to lists of cache info
        """
        all_caches = {}
        
        if not self.cache_base_dir.exists():
            return all_caches
        
        for model_dir in self.cache_base_dir.iterdir():
            if model_dir.is_dir():
                model_name = model_dir.name
                caches = self.list_caches(model_name)
                if caches:
                    all_caches[model_name] = caches
        
        return all_caches
    
    def ensure_model_cache_dir(self, model_name: str) -> Path:
        """
        Ensure cache directory exists for a model
        
        Args:
            model_name: Friendly model name
            
        Returns:
            Path to model cache directory
        """
        return self._get_model_cache_dir(model_name)
