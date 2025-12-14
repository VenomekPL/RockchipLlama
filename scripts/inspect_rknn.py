import sys
from rknnlite.api import RKNNLite

def inspect_rknn(model_path):
    rknn = RKNNLite(verbose=True)
    
    print(f"Loading {model_path}...")
    ret = rknn.load_rknn(model_path)
    if ret != 0:
        print("Load failed!")
        return

    print("Init runtime...")
    ret = rknn.init_runtime()
    if ret != 0:
        print("Init runtime failed!")
        return

    print("\n--- Inspection Complete (Check logs above for details) ---")
    rknn.release()

if __name__ == "__main__":
    model_path = "models/stable-diffusion-lcm/unet_lcm_512.rknn"
    inspect_rknn(model_path)
