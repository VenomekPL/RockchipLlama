import os
from huggingface_hub import hf_hub_download
import shutil
from pathlib import Path

REPO_ID = "happyme531/Stable-Diffusion-1.5-LCM-ONNX-RKNN2"
DEST_DIR = Path("models/stable-diffusion-lcm")

FILES = {
    "model/text_encoder/model.rknn": "text_encoder.rknn",
    "model/unet/model.rknn": "unet_lcm_512.rknn",
    "model/vae_decoder/model.rknn": "vae_decoder.rknn",
    "model/unet/config.json": "unet_config.json",
    "model/vae_decoder/config.json": "vae_decoder_config.json",
    "model/text_encoder/config.json": "text_encoder_config.json",
    "model/scheduler/scheduler_config.json": "scheduler_config.json"
}

def download_models():
    if not DEST_DIR.exists():
        DEST_DIR.mkdir(parents=True)
        print(f"Created directory: {DEST_DIR}")

    print(f"Downloading models from {REPO_ID}...")
    
    for repo_path, local_name in FILES.items():
        dest_path = DEST_DIR / local_name
        if dest_path.exists():
            print(f"✅ {local_name} already exists")
            continue
            
        print(f"⬇️ Downloading {local_name} (from {repo_path})...")
        try:
            # Download to a temporary path first
            file_path = hf_hub_download(
                repo_id=REPO_ID,
                filename=repo_path,
                local_dir=DEST_DIR,
                local_dir_use_symlinks=False
            )
            
            # Move/Rename to the expected name
            # hf_hub_download preserves the directory structure (e.g. model/text_encoder/model.rknn)
            downloaded_path = DEST_DIR / repo_path
            
            # We want it at DEST_DIR / local_name
            if downloaded_path.exists():
                # Create parent dir if it doesn't exist (it should from download)
                shutil.move(str(downloaded_path), str(dest_path))
                print(f"✅ Downloaded and renamed to {local_name}")
                
                # Clean up empty directories if possible
                try:
                    os.rmdir(downloaded_path.parent)
                    os.rmdir(downloaded_path.parent.parent)
                except:
                    pass
            else:
                print(f"❌ Downloaded file not found at {downloaded_path}")

        except Exception as e:
            print(f"❌ Failed to download {local_name}: {e}")

if __name__ == "__main__":
    download_models()
