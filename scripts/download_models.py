import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.settings import settings

MODELS = {
    "qwen3-0.6b": {
        "repo_id": "Pelochus/ez-rknn-llm-models",
        "filename": "Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm",
        "folder": "qwen3-0.6b"
    },
    "qwen3-0.6b-embedding": {
        "repo_id": "Pelochus/ez-rknn-llm-models",
        "filename": "Qwen3-Embedding-0.6B_w8a8.rkllm",
        "folder": "qwen3-0.6b-embedding"
    }
}

def download_models():
    print("🚀 Checking models...")
    
    models_dir = Path(settings.models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    
    for model_key, info in MODELS.items():
        folder_path = models_dir / info["folder"]
        folder_path.mkdir(parents=True, exist_ok=True)
        
        file_path = folder_path / info["filename"]
        
        if file_path.exists():
            print(f"✅ {model_key} already exists at {file_path}")
            print(f"   Skipping download to save bandwidth.")
            continue
            
        print(f"⬇️  Downloading {model_key} from {info['repo_id']}...")
        try:
            downloaded_path = hf_hub_download(
                repo_id=info["repo_id"],
                filename=info["filename"],
                local_dir=folder_path,
                local_dir_use_symlinks=False
            )
            print(f"✅ Downloaded {model_key} to {downloaded_path}")
        except Exception as e:
            print(f"❌ Failed to download {model_key}: {e}")
            print(f"   Please manually download {info['filename']} and place it in {folder_path}")

if __name__ == "__main__":
    download_models()
