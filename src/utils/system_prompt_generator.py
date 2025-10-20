"""
System Prompt Cache Generator

Automatically generates and caches default system prompts for models.
"""
import os
from pathlib import Path
from typing import Optional


class SystemPromptGenerator:
    """Generates and manages default system prompt caches"""
    
    def __init__(self, system_prompt_file: str = "config/system.txt"):
        """
        Initialize system prompt generator
        
        Args:
            system_prompt_file: Path to default system prompt file (relative to project root)
        """
        # Find project root (parent of src directory)
        if Path(system_prompt_file).is_absolute():
            self.system_prompt_file = Path(system_prompt_file)
        else:
            # Get project root (parent of src directory where this file is located)
            project_root = Path(__file__).parent.parent.parent
            self.system_prompt_file = project_root / system_prompt_file
        
        self._cached_content: Optional[str] = None
    
    def load_system_prompt(self) -> str:
        """
        Load system prompt from file
        
        Returns:
            System prompt content
            
        Raises:
            FileNotFoundError: If system prompt file doesn't exist
        """
        if not self.system_prompt_file.exists():
            raise FileNotFoundError(
                f"System prompt file not found: {self.system_prompt_file}\n"
                f"Please create it with your default system prompt."
            )
        
        # Cache the content for efficiency
        if self._cached_content is None:
            with open(self.system_prompt_file, 'r', encoding='utf-8') as f:
                self._cached_content = f.read().strip()
        
        return self._cached_content
    
    def get_cache_source_path(self) -> str:
        """Get the source file path for metadata"""
        return str(self.system_prompt_file)
