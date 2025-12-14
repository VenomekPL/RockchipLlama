import sys
import os
from pathlib import Path
import time

# Add src and root to path
sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent.parent))

from models.stable_diffusion import StableDiffusionRKNN
from config.settings import settings

import asyncio

async def test_sd_generation():
    print("Initializing Stable Diffusion...")
    try:
        sd = StableDiffusionRKNN(
            model_dir="models/stable-diffusion-lcm"
        )
        print("✅ Initialization successful")
        
        # Manually load models since generate() usually expects them loaded or loads them?
        # Let's check if generate loads them.
        # Usually ModelManager handles loading.
        # But here we are using the class directly.
        # We should call load() if it exists.
        print("Loading models...")
        sd.load()
        
    except Exception as e:
        print(f"❌ Initialization/Loading failed: {e}")
        return

    print("Generating image (warmup)...")
    start = time.time()
    try:
        images = await sd.generate(
            prompt="A futuristic city on Mars, high quality, 8k",
            num_inference_steps=4,
            guidance_scale=8.0
        )
        print(f"✅ Generation successful in {time.time() - start:.2f}s")
        
        output_path = "test_sd_output.png"
        images[0].save(output_path)
        print(f"Saved to {output_path}")
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
    finally:
        sd.unload()

if __name__ == "__main__":
    asyncio.run(test_sd_generation())
