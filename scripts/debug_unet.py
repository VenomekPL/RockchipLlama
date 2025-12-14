import numpy as np
from rknnlite.api import RKNNLite
import sys
import os
import traceback

def run_test():
    print("Running Debug UNet Test")
    
    rknn = RKNNLite()
    
    # Path to the model
    model_path = "models/stable-diffusion-lcm/unet_lcm_512.rknn"
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}")
        return

    print(f"Loading model from {model_path}")
    ret = rknn.load_rknn(model_path)
    if ret != 0:
        print("Load RKNN model failed")
        return

    # Initialize runtime
    # Note: Multi-core might cause issues, but Single-core also crashed in tests.
    print("Initializing runtime...")
    ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2)
    if ret != 0:
        print("Init runtime failed")
        return

    # Prepare Inputs (Correct Shapes for unet_lcm_512)
    # Input 0: sample (1, 4, 64, 64) float16
    sample = np.random.randn(1, 4, 64, 64).astype(np.float16)
    
    # Input 1: timestep (1,) int64
    timestep = np.array([1], dtype=np.int64)
    
    # Input 2: encoder_hidden_states (1, 77, 768) float16
    encoder_hidden_states = np.random.randn(1, 77, 768).astype(np.float16)
    
    # Input 3: timestep_cond (1, 256) float16
    timestep_cond = np.random.randn(1, 256).astype(np.float16)

    inputs = [sample, timestep, encoder_hidden_states, timestep_cond]
    
    print(f"Input shapes: {[i.shape for i in inputs]}")
    print(f"Input types: {[i.dtype for i in inputs]}")
    
    try:
        print("Running inference...")
        outputs = rknn.inference(inputs=inputs)
        print("Inference successful!")
        if outputs:
            print(f"Output shape: {outputs[0].shape}")
    except Exception as e:
        print(f"Inference failed: {e}")
        traceback.print_exc()

    rknn.release()

if __name__ == "__main__":
    run_test()
