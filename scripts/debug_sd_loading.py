import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

def check_dependencies():
    print("Checking dependencies...")
    try:
        import rknnlite
        print("✅ rknnlite found")
    except ImportError:
        print("❌ rknnlite NOT found")

    try:
        import diffusers
        print("✅ diffusers found")
    except ImportError:
        print("❌ diffusers NOT found")

    try:
        import PIL
        print("✅ PIL found")
    except ImportError:
        print("❌ PIL NOT found")

def check_files():
    print("\nChecking model files...")
    base_path = Path("models/stable-diffusion-lcm")
    
    files = [
        "text_encoder.rknn",
        "unet_lcm_512.rknn",
        "vae_decoder.rknn"
    ]
    
    if not base_path.exists():
        print(f"❌ Directory not found: {base_path}")
        return

    for f in files:
        p = base_path / f
        if p.exists():
            print(f"✅ Found {f} ({p.stat().st_size / 1024 / 1024:.2f} MB)")
        else:
            print(f"❌ Missing {f}")

if __name__ == "__main__":
    check_dependencies()
    check_files()
