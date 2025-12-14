# Stable Diffusion on RK3588 (RKNN)

This document outlines the feasibility and steps for integrating Stable Diffusion (Image Generation) into the RockchipLlama project using the RK3588 NPU.

## Executive Summary

**Status:** ✅ **Feasible** (with limitations)
**Recommended Model:** Stable Diffusion 1.5 with LCM (Latent Consistency Model)
**Performance:** ~10-25 seconds per image (depending on resolution)
**Hardware Requirement:** RK3588 with 8GB+ RAM (16GB recommended)

## 1. The Solution: Stable Diffusion 1.5 LCM

Standard Stable Diffusion requires 20-50 inference steps, which would take minutes on the NPU. **LCM (Latent Consistency Models)** distill this process down to **4-8 steps**, making on-device generation practical.

We have identified a working implementation:
*   **Repository:** [happyme531/Stable-Diffusion-1.5-LCM-ONNX-RKNN2](https://huggingface.co/happyme531/Stable-Diffusion-1.5-LCM-ONNX-RKNN2)
*   **Base Model:** `TheyCallMeHex/LCM-Dreamshaper-V7-ONNX` (SD 1.5 based)

### Performance Metrics (Single NPU Core)

| Resolution | Steps | Text Encoder | U-Net (per step) | VAE Decoder | Total Time | Memory Usage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **384x384** | 4 | 0.05s | 2.36s | 5.48s | **~15s** | ~5.2 GB |
| **512x512** | 4 | 0.05s | 5.65s | 11.13s | **~34s** | ~5.6 GB |

*Note: The NPU has 3 cores. We could potentially run the U-Net on multiple cores to speed this up, or run parallel requests.*

## 2. Integration Guide

### Prerequisites
The project requires `rknn-toolkit-lite2` and `numpy<2`. Our current environment uses `numpy>=1.26.0`, which is compatible (as long as we stay on 1.x).

### Installation Steps

1.  **Install Dependencies:**
    ```bash
    pip install diffusers pillow "numpy<2" rknn-toolkit-lite2
    ```
    *(Note: `rknn-toolkit-lite2` wheels are usually provided by Rockchip or the board vendor, e.g., Orange Pi).*

2.  **Model Conversion (Offline):**
    You cannot convert the model on the RK3588 directly (it requires x86_64). You must convert it on a PC using `rknn-toolkit2`.
    *   Download ONNX model.
    *   Run conversion script to generate `.rknn` files for:
        *   Text Encoder
        *   U-Net (The heavy lifter)
        *   VAE Decoder

3.  **Inference (On Device):**
    The inference pipeline consists of three stages:
    1.  **Text Encoder:** Python/ONNX or RKNN (Fast).
    2.  **U-Net:** RKNN (Heavy NPU usage).
    3.  **VAE Decoder:** RKNN (Moderate NPU usage).

### Proposed Architecture for RockchipLlama

We can add a new endpoint `/v1/images/generations` (OpenAI compatible).

```python
# Conceptual Implementation
@router.post("/v1/images/generations")
async def generate_image(request: ImageGenerationRequest):
    # 1. Encode Prompt
    latents = text_encoder(request.prompt)
    
    # 2. Run U-Net Loop (4 steps)
    for i in range(4):
        latents = rknn_unet.run(latents, timestep[i])
        
    # 3. Decode Image
    image = rknn_vae.run(latents)
    
    return image
```

## 3. Other Findings

### "DeepSeekOCR"
There is no specific "DeepSeekOCR" for RKNN. The user likely refers to:
1.  **PaddleOCR:** The industry standard for OCR on Rockchip. Highly optimized C++ ports exist (e.g., `yinghanguan/PaddleOCR2RKNN`).
2.  **Qwen2-VL / DeepSeek-VL:** We already support Qwen2-VL, which has excellent OCR capabilities ("Describe the text in this image").

### Flux Models
**Flux.1** (the current SOTA image model) is **not yet feasible** on RK3588. It is a 12B parameter model (vs SD 1.5's ~1B). It would require massive quantization and likely exceed memory bandwidth.
*Note: `happyme531/TangoFlux-ONNX-RKNN2` exists, but it is for **Audio Generation**, not images.*

## 4. Next Steps

1.  **Download Pre-converted Models:** Check if `happyme531` provides the `.rknn` files directly to save conversion time.
2.  **Create `src/models/stable_diffusion.py`:** Implement a wrapper class similar to `RKLLMModel` but using `rknn_lite`.
3.  **Add API Route:** Implement the OpenAI image generation API.

## Resources
*   [Hugging Face Repo (Source)](https://huggingface.co/happyme531/Stable-Diffusion-1.5-LCM-ONNX-RKNN2)
*   [RKNN Toolkit2](https://github.com/airockchip/rknn-toolkit2)
