# RockchipLlama Project Review & Analysis

**Date:** December 10, 2025
**Model:** Gemini 3 Pro (Preview)

## 1. Project Overview
RockchipLlama is a high-performance, OpenAI-compatible API server designed to run Large Language Models (LLMs) on Rockchip NPUs (specifically RK3588, RK3576, etc.). It leverages the `rknn-llm` runtime for hardware acceleration.

### Key Components
- **Core Server**: FastAPI-based application (`src/main.py`).
- **Runtime Wrapper**: `src/models/rkllm_model.py` uses `ctypes` to directly bind to the C++ `librkllmrt.so` library, avoiding the overhead of the official Python bindings for better control.
- **API Layer**: Implements OpenAI-compatible endpoints (`/v1/chat/completions`, `/v1/models`) and custom management routes.
- **Concurrency**: Implements a semaphore-based multi-batch inference system (`generate_async`) to manage NPU core usage efficiently.

## 2. Architecture Analysis

### 2.1. Inference Pipeline
1.  **Request**: Comes in via FastAPI (`openai_routes.py`).
2.  **Queueing**: `RKLLMModel.generate_async` uses an `asyncio.Semaphore` to limit concurrent requests to the configured `n_batch` (default 3 for RK3588).
3.  **Execution**:
    -   Uses `ctypes` to call `rkllm_run` (blocking) or `rkllm_run_async` (non-blocking).
    -   Callbacks are used to stream generated tokens back to Python.
4.  **Output**: Streamed back to the client via Server-Sent Events (SSE).

### 2.2. Memory Management
-   **Prompt Cache**: Supports saving/loading binary prompt caches (`.rkllm_cache`) to disk to speed up initialization for static system prompts.
-   **KV Cache**: Managed internally by the runtime. The project exposes `n_keep` and `n_batch` parameters to control memory usage.

## 3. External Dependency: `rknn-llm` (v1.2.3)

The `external/rknn-llm` submodule has been updated to version **1.2.3**.

### 3.1. New Features in v1.2.3
-   **New Models**: Support for **Qwen3-VL**, **DeepSeek-OCR**, InternVL3.5, and Gemma3n (embedding support).
-   **Automatic Cache Reuse**: Specifically for **Embedding Inputs** (`RKLLM_INPUT_EMBED`). The runtime now automatically detects and reuses cache for shared prefixes in embeddings.
-   **External Chat Templates**: Support for loading chat templates from an external file, decoupling the template from the model file.
-   **Function Calling**: Enhanced support (introduced in v1.2.1, refined in v1.2.3).

### 3.2. Impact on RockchipLlama
-   **Qwen3-VL**: The project can now support this state-of-the-art vision-language model.
-   **DeepSeek-OCR**: Enables high-performance OCR capabilities on the NPU.
-   **Cache Reuse**: To benefit from this, the project needs to support `RKLLM_INPUT_EMBED` input type (currently primarily uses `RKLLM_INPUT_PROMPT`).

## 4. Gap Analysis & Recommendations

### 4.1. Missing Bindings
The current `src/models/rkllm_model.py` is missing bindings for recent API additions:
-   `rkllm_set_function_tools`: Enables native function calling support on the NPU.
-   `rkllm_set_cross_attn_params`: Required for advanced multimodal features.

### 4.2. Recommendations
1.  **Update Bindings**: Extend `RKLLMModel` to include the missing C functions mentioned above.
2.  **Support Embeddings Input**: Implement a path to use `RKLLM_INPUT_EMBED` to leverage the new automatic cache reuse feature, especially for RAG applications.
3.  **Multimodal Support**: Create a pipeline for Qwen3-VL and DeepSeek-OCR, which requires handling `RKLLM_INPUT_MULTIMODAL` and integrating with `rknn-toolkit2` for the vision encoder part.

## 5. Implementation Status (v1.2.3 Updates)
-   ✅ **Chat Templates**: Implemented `rkllm_set_chat_template` binding and configuration in `src/models/rkllm_model.py` and `config/inference_config.json`.
-   ℹ️ **Automatic Cache Reuse**: Confirmed to be specific to `RKLLM_INPUT_EMBED`. Current text generation pipeline uses `RKLLM_INPUT_PROMPT`, so manual binary cache is still relevant. Future work could explore using embedding inputs for RAG to leverage auto-cache.

## 6. Documentation Links
-   [RKLLM Runtime Analysis](docs/rkllm.md)
-   [Official Changelog](external/rknn-llm/CHANGELOG.md)
