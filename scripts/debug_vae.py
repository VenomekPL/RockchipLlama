import numpy as np
from rknnlite.api import RKNNLite

VAE_PATH = "models/stable-diffusion-lcm/vae_decoder.rknn"

def test_vae():
    print("Testing VAE...")
    rknn = RKNNLite()
    
    # Load
    ret = rknn.load_rknn(VAE_PATH)
    if ret != 0:
        print("Load failed")
        return
    
    # Init
    ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0)
    if ret != 0:
        print("Init failed")
        return
        
    # Prepare inputs
    # VAE decoder takes latents. Shape (1, 4, 64, 64) for 512x512 image.
    # Or maybe (1, 4, 96, 96) for 768x768.
    # Let's try 64x64 first.
    latents = np.zeros((1, 4, 64, 64), dtype=np.float32)
    
    inputs = [latents]
    
    try:
        outputs = rknn.inference(inputs=inputs)
        print("Success! Output shape:", outputs[0].shape)
    except Exception as e:
        print(f"Error: {e}")
    
    rknn.release()

if __name__ == "__main__":
    test_vae()
