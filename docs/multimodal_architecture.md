# RKLLM Multimodal Architecture Explained

## Why are there so many files?

You might notice that running a multimodal model (like Qwen2-VL) on Rockchip hardware involves more files and moving parts than standard CPU/GPU runtimes like `llama.cpp` or `vLLM`. Here is the technical breakdown of why this is the case.

### 1. The "Split Brain" Architecture

In standard runtimes, the Vision Encoder (the part that "sees" the image) and the LLM (the part that "speaks") are often loaded by a single monolithic executable. The runtime has built-in support for standard vision architectures (like CLIP or SigLIP) and runs them on the same device (GPU/CPU) as the LLM.

**On Rockchip NPUs, the process is decoupled for hardware efficiency:**

1.  **The LLM (`.rkllm`)**: This file contains *only* the Large Language Model weights, compiled specifically for the NPU. It expects **embeddings** (mathematical representations of data) as input, not raw text or raw images.
2.  **The Vision Encoder (`.rknn` or `.onnx`)**: This is a completely separate neural network. It takes a raw image and converts it into the embeddings that the LLM understands. This model must also be compiled for the NPU (as `.rknn`) or run on the CPU (as `.onnx`).
3.  **The Glue (`imgenc`)**: Because the NPU requires highly specific memory layouts and quantization formats, Rockchip provides a standalone binary (`imgenc`) to handle the image preprocessing and encoding.

### 2. The Pipeline

When you send an image to our server, the following pipeline executes:

```mermaid
graph LR
    A[User Image (JPG/PNG)] -->|Raw Bytes| B(Server API)
    B -->|Save to Temp| C[imgenc Binary]
    C -->|Load| D[Vision Model (.rknn/.onnx)]
    D -->|Encode| E[Image Embeddings (.bin)]
    E -->|Load| F(RKLLM Runtime)
    F -->|Generate| G[Text Response]
```

### 3. File Inventory

This architecture results in the following file structure in your `models/` folder:

*   **`Qwen2-VL-2B-Instruct.rkllm`**: The main LLM.
*   **`qwen2_vl_2b_vision_rk3588.rknn`** (or `.onnx`): The separate vision encoder model.
*   **`demo_Linux_aarch64/imgenc`**: The executable responsible for running the vision encoder.
*   **`lib/`**: Shared libraries required by the `imgenc` binary.

### Summary

While more complex to manage, this "split" approach allows Rockchip to optimize the Vision Encoder and the LLM independently. The Vision Encoder can run on one set of NPU cores while the LLM runs on another, or they can be pipelined for better performance. Our "Universal" server implementation abstracts this complexity away from you, handling the coordination between these separate binaries automatically.
