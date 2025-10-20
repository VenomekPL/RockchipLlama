"""
Prompt Cache Manager for RKLLM Models

Handles saving, loading, and listing of prompt caches with model-specific organization.
Based on Technocore RKLLM implementation.
"""
import os
import json
import time
import glob
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path


class PromptCacheManager:
    """Manages prompt caches for RKLLM models"""
    
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
    
    def save_cache(
        self, 
        model_name: str, 
        cache_name: str, 
        content: str,
        source: Optional[str] = None,
        allow_overwrite: bool = True
    ) -> Dict[str, Any]:
        """
        Save a prompt cache for a model
        
        Args:
            model_name: Friendly model name (folder name)
            cache_name: Cache identifier (e.g., "system", "coding")
            content: Prompt content to cache
            source: Optional source file path for metadata
            allow_overwrite: If True, overwrites existing cache. If False, raises error if exists.
            
        Returns:
            Dictionary with save metadata (was_overwrite, old_size, new_size)
            
        Raises:
            FileExistsError: If cache exists and allow_overwrite=False
        """
        cache_dir = self._get_model_cache_dir(model_name)
        
        # Check if cache already exists
        bin_path = cache_dir / f"{cache_name}.bin"
        json_path = cache_dir / f"{cache_name}.json"
        
        was_overwrite = bin_path.exists()
        old_size = 0
        old_metadata = None
        
        if was_overwrite:
            if not allow_overwrite:
                raise FileExistsError(
                    f"Cache '{cache_name}' already exists for model '{model_name}'. "
                    f"Use allow_overwrite=True to replace it."
                )
            
            # Load old metadata for logging
            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        old_metadata = json.load(f)
                        old_size = old_metadata.get('content_length', 0)
                except Exception:
                    pass
            
            print(f"[CACHE] ⚠️  Overwriting existing cache '{cache_name}' for model '{model_name}'")
            if old_metadata:
                print(f"[CACHE]    Old: {old_size} chars, created {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(old_metadata.get('created_at', 0)))}")
                print(f"[CACHE]    New: {len(content)} chars")
        
        # Save binary cache (RKLLM format)
        with open(bin_path, 'wb') as f:
            f.write(content.encode('utf-8'))
        
        # Save metadata
        metadata = {
            "cache_name": cache_name,
            "model_name": model_name,
            "created_at": time.time(),
            "content_length": len(content),
            "source": source,
            "updated_at": time.time() if was_overwrite else None,
            "version": (old_metadata.get('version', 0) + 1) if old_metadata else 1
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        if was_overwrite:
            print(f"[CACHE] ✅ Overwritten '{cache_name}' for model '{model_name}' (v{metadata['version']})")
        else:
            print(f"[CACHE] ✅ Saved '{cache_name}' for model '{model_name}' ({len(content)} chars)")
        
        return {
            "was_overwrite": was_overwrite,
            "old_size": old_size,
            "new_size": len(content),
            "version": metadata['version'],
            "cache_name": cache_name,
            "model_name": model_name
        }
    
    def load_cache(self, model_name: str, cache_name: str) -> Optional[str]:
        """
        Load a cached prompt
        
        Args:
            model_name: Friendly model name
            cache_name: Cache identifier
            
        Returns:
            Cached content or None if not found
        """
        cache_dir = self._get_model_cache_dir(model_name)
        bin_path = cache_dir / f"{cache_name}.bin"
        
        if bin_path.exists():
            try:
                with open(bin_path, 'rb') as f:
                    content = f.read().decode('utf-8')
                print(f"[CACHE] Loaded '{cache_name}' from '{model_name}' cache")
                return content
            except Exception as e:
                print(f"[CACHE] Failed to load '{cache_name}': {e}")
                return None
        else:
            print(f"[CACHE] Cache '{cache_name}' not found for model '{model_name}'")
            return None
    
    def cache_exists(self, model_name: str, cache_name: str) -> bool:
        """Check if a cache exists"""
        cache_dir = self._get_model_cache_dir(model_name)
        bin_path = cache_dir / f"{cache_name}.bin"
        return bin_path.exists()
    
    def list_caches(self, model_name: str) -> List[Dict[str, Any]]:
        """
        List all caches for a model
        
        Args:
            model_name: Friendly model name
            
        Returns:
            List of cache metadata dictionaries
        """
        cache_dir = self._get_model_cache_dir(model_name)
        
        if not cache_dir.exists():
            return []
        
        caches = []
        for json_file in cache_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                caches.append(metadata)
            except Exception as e:
                print(f"[CACHE] Failed to read metadata from {json_file}: {e}")
        
        # Sort by creation time (newest first)
        return sorted(caches, key=lambda x: x.get('created_at', 0), reverse=True)
    
    def list_all_caches(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List all caches for all models
        
        Returns:
            Dictionary mapping model names to their cache lists
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
    
    def delete_cache(self, model_name: str, cache_name: str) -> bool:
        """
        Delete a specific cache
        
        Args:
            model_name: Friendly model name
            cache_name: Cache identifier
            
        Returns:
            True if deleted, False if not found
        """
        cache_dir = self._get_model_cache_dir(model_name)
        
        bin_path = cache_dir / f"{cache_name}.bin"
        json_path = cache_dir / f"{cache_name}.json"
        
        deleted = False
        if bin_path.exists():
            bin_path.unlink()
            deleted = True
        if json_path.exists():
            json_path.unlink()
            deleted = True
        
        if deleted:
            print(f"[CACHE] Deleted '{cache_name}' from '{model_name}' cache")
        
        return deleted
    
    def ensure_model_cache_dir(self, model_name: str) -> Path:
        """
        Ensure cache directory exists for a model
        
        Args:
            model_name: Friendly model name
            
        Returns:
            Path to model cache directory
        """
        return self._get_model_cache_dir(model_name)
    
    def load_multiple_caches(
        self, 
        model_name: str, 
        cache_names: List[str],
        include_system: bool = True
    ) -> tuple[str, List[str]]:
        """
        Load and concatenate multiple caches in order
        
        Args:
            model_name: Friendly model name
            cache_names: List of cache identifiers to load
            include_system: If True, prepend 'system' cache automatically
            
        Returns:
            Tuple of (concatenated_content, list_of_loaded_cache_names)
            
        Example:
            content, loaded = cache_mgr.load_multiple_caches(
                "qwen3-0.6b", 
                ["coding_rules", "project_context"],
                include_system=True
            )
            # Returns: system + coding_rules + project_context
            # loaded = ["system", "coding_rules", "project_context"]
        """
        parts = []
        loaded_caches = []
        
        # Always include system cache first if requested
        if include_system and "system" not in cache_names:
            cache_names = ["system"] + list(cache_names)
        
        for cache_name in cache_names:
            content = self.load_cache(model_name, cache_name)
            if content:
                parts.append(content)
                loaded_caches.append(cache_name)
                print(f"[CACHE] Loaded '{cache_name}' from '{model_name}' ({len(content)} chars)")
            else:
                print(f"[CACHE] Warning: '{cache_name}' not found for model '{model_name}'")
        
        # Concatenate with double newline separators
        combined = "\n\n".join(parts)
        
        if loaded_caches:
            print(f"[CACHE] Combined {len(loaded_caches)} caches: {', '.join(loaded_caches)} ({len(combined)} total chars)")
        
        return combined, loaded_caches
