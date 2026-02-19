# Feature: Advanced Vision Model Support

## Overview

Expand multimodal vision-language model (VLM) support to cover the full range of models supported by rknn-llm v1.2.3, including newer architectures like InternVL3.5, DeepSeekOCR, Qwen3-VL, and Gemma3n. This feature enhances RockchipLlama's ability to process images alongside text queries, enabling OCR, image understanding, visual Q&A, and document analysis use cases.

## Current Status

**Partially Implemented** — Basic Qwen2-VL support exists via the Split Brain architecture.

In `src/models/rkllm_model.py`:

```python
# Lines ~705-742: Multimodal support exists
if image_data:
    image_embeds = self._encode_image(image_data)  # Calls external imgenc binary
    rkllm_input.input_type = RKLLMInputType.RKLLM_INPUT_MULTIMODAL
    mm_input.image_embed = ...  # Embedding array from vision encoder
```

**Current architecture (Split Brain)**:
1. **Vision Encoder**: Separate `.rknn` model executed via `imgenc` binary (RKNN runtime).
2. **LLM Decoder**: `.rkllm` model executed via RKLLM runtime.
3. Vision embeddings are passed to the LLM via `RKLLM_INPUT_MULTIMODAL`.

**Supported**: Qwen2-VL (basic image + text queries).

**Not yet supported**:
- InternVL3 / InternVL3.5
- DeepSeekOCR
- Qwen3-VL (with mrope position encoding)
- Gemma3n (with embedding input)
- SmolVLM
- MiniCPM-V-2_6
- Janus-Pro-1B
- Multi-image input
- Video frame input

## rknn-llm Reference Implementation

The rknn-llm submodule provides a comprehensive multimodal demo:

### Directory Structure

```
external/rknn-llm/examples/multimodal_model_demo/
├── export/
│   ├── export_vision.py           # Generic vision model export
│   ├── export_vision_qwen2.py     # Qwen2-VL specific export
│   ├── export_vision_rknn.py      # ONNX → RKNN conversion
│   ├── export_rkllm.py            # LLM export for multimodal
│   └── modeling_deepseekv2.py     # DeepSeekOCR support
├── deploy/
│   ├── src/main.cpp               # Multimodal inference (C++)
│   ├── src/img_encoder.cpp        # Image encoding module
│   └── 3rdparty/                  # OpenCV, RKNN runtime
├── data/
│   ├── datasets.json              # 20 MMBench evaluation examples
│   └── datasets/                  # Test images
└── infer.py                       # HuggingFace reference inference
```

### Multimodal C++ Deploy Code (`main.cpp`)

Key patterns from the reference implementation:

```cpp
// 1. Load vision encoder (RKNN)
rknn_context ctx;
rknn_init(&ctx, model_path, model_size, 0, NULL);

// 2. Encode image → embeddings
float* image_embed = encode_image(ctx, image_path, &n_tokens);

// 3. Pass embeddings to LLM (RKLLM)
RKLLMMultiModalInput mm_input;
mm_input.prompt = prompt;
mm_input.image_embed = image_embed;
mm_input.n_image_tokens = n_tokens;
mm_input.n_image = 1;
mm_input.image_width = width;
mm_input.image_height = height;

RKLLMInput rkllm_input;
rkllm_input.input_type = RKLLM_INPUT_MULTIMODAL;
rkllm_input.multimodal_input = mm_input;
rkllm_run(handle, &rkllm_input, &infer_params, NULL);
```

### Model-Specific Export Scripts

Each vision model has specific export requirements:

- **Qwen2-VL / Qwen3-VL**: Requires mrope (multimodal rotary position encoding) support.
- **InternVL3**: Uses a different vision encoder architecture.
- **DeepSeekOCR**: Requires `modeling_deepseekv2.py` for custom architecture.
- **SmolVLM**: Lightweight vision model with different preprocessing.

### Cross-Attention for Encoder-Decoder Models

```c
// From rkllm.h (lines 170-189, 395-403)
typedef struct {
    float* encoder_k_cache;   // Key cache from encoder
    float* encoder_v_cache;   // Value cache from encoder
    float* encoder_mask;      // Attention mask
    int32_t* encoder_pos;     // Token positions
    int num_tokens;           // Sequence length
} RKLLMCrossAttnParam;

int rkllm_set_cross_attn_params(LLMHandle handle, RKLLMCrossAttnParam* params);
```

## Implementation Plan

### Step 1: Generalize Vision Encoder Interface

Abstract the vision encoder to support multiple model architectures:

```python
class VisionEncoder:
    """Abstract interface for vision model encoding."""

    def encode(self, image_data: bytes, image_format: str = "jpeg") -> VisionEmbedding:
        raise NotImplementedError

class VisionEmbedding:
    embed: np.ndarray        # float32 array
    n_tokens: int            # number of image tokens
    n_images: int            # number of images
    image_width: int
    image_height: int

class RKNNVisionEncoder(VisionEncoder):
    """Encodes images using external imgenc binary + RKNN model."""

    def __init__(self, model_path: str, imgenc_binary: str):
        self.model_path = model_path
        self.imgenc_binary = imgenc_binary

    def encode(self, image_data: bytes, image_format: str = "jpeg") -> VisionEmbedding:
        # Call imgenc binary with image data
        # Parse output embeddings
        # Return VisionEmbedding
```

### Step 2: Add Model-Specific Vision Configurations

```json
{
  "vision_models": {
    "qwen2-vl": {
      "encoder_model": "models/qwen2-vl-vision.rknn",
      "imgenc_binary": "bin/imgenc",
      "image_size": [448, 448],
      "n_image_tokens": 256,
      "preprocessing": "qwen2_vl"
    },
    "qwen3-vl": {
      "encoder_model": "models/qwen3-vl-vision.rknn",
      "imgenc_binary": "bin/imgenc",
      "image_size": [448, 448],
      "n_image_tokens": 256,
      "preprocessing": "qwen3_vl",
      "requires_mrope": true
    },
    "internvl3": {
      "encoder_model": "models/internvl3-vision.rknn",
      "imgenc_binary": "bin/imgenc_internvl",
      "image_size": [448, 448],
      "preprocessing": "internvl"
    },
    "deepseek-ocr": {
      "encoder_model": "models/deepseek-ocr-vision.rknn",
      "imgenc_binary": "bin/imgenc_deepseek",
      "image_size": [1024, 1024],
      "preprocessing": "deepseek_ocr"
    }
  }
}
```

### Step 3: Support Multi-Image Input

Extend the multimodal input to handle multiple images:

```python
# OpenAI vision API format:
# messages = [{"role": "user", "content": [
#     {"type": "text", "text": "Compare these images"},
#     {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
#     {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
# ]}]

def process_multimodal_message(content: list) -> tuple[str, list[bytes]]:
    text_parts = []
    images = []
    for item in content:
        if item["type"] == "text":
            text_parts.append(item["text"])
        elif item["type"] == "image_url":
            image_data = decode_image_url(item["image_url"]["url"])
            images.append(image_data)
    return " ".join(text_parts), images
```

### Step 4: Add Cross-Attention Support for Encoder-Decoder Models

Bind and expose `rkllm_set_cross_attn_params()` for models that use cross-attention:

```python
class RKLLMCrossAttnParam(ctypes.Structure):
    _fields_ = [
        ("encoder_k_cache", ctypes.POINTER(ctypes.c_float)),
        ("encoder_v_cache", ctypes.POINTER(ctypes.c_float)),
        ("encoder_mask", ctypes.POINTER(ctypes.c_float)),
        ("encoder_pos", ctypes.POINTER(ctypes.c_int32)),
        ("num_tokens", ctypes.c_int),
    ]

def set_cross_attn_params(self, k_cache, v_cache, mask, positions, num_tokens):
    params = RKLLMCrossAttnParam()
    params.encoder_k_cache = k_cache.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    params.encoder_v_cache = v_cache.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    params.encoder_mask = mask.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    params.encoder_pos = positions.ctypes.data_as(ctypes.POINTER(ctypes.c_int32))
    params.num_tokens = num_tokens
    self._set_cross_attn_params(self.handle, ctypes.byref(params))
```

### Step 5: Add Model Download/Setup Scripts

Create scripts for downloading and converting vision models:

```bash
# scripts/setup_vision_model.sh
# Downloads model from HuggingFace
# Exports vision encoder to ONNX
# Converts to RKNN format
# Exports LLM to RKLLM format
```

### Step 6: Update API for Vision Input

Ensure the OpenAI-compatible vision API format is fully supported:

```python
# Support both formats:
# 1. Simple: {"role": "user", "content": "Describe this image", "images": ["base64..."]}
# 2. OpenAI: {"role": "user", "content": [{"type": "text", ...}, {"type": "image_url", ...}]}
```

## Goals

1. Support all rknn-llm v1.2.3 vision models (InternVL3.5, DeepSeekOCR, Qwen3-VL, Gemma3n, SmolVLM).
2. Generalized vision encoder interface supporting multiple architectures.
3. Multi-image input support.
4. Cross-attention inference for encoder-decoder vision models.
5. Model-specific preprocessing and configuration.
6. OpenAI-compatible vision API format.

## Definition of Done

- [ ] Abstract `VisionEncoder` interface implemented.
- [ ] Qwen2-VL continues to work (no regression).
- [ ] At least one new vision model (e.g., InternVL3) is supported end-to-end.
- [ ] Multi-image input works for models that support it.
- [ ] Cross-attention params can be set via `rkllm_set_cross_attn_params()`.
- [ ] Vision model configuration is JSON-driven (not hardcoded).
- [ ] OpenAI vision API format fully supported (content array with image_url).
- [ ] Image preprocessing handles different model requirements.
- [ ] Setup/download scripts exist for supported vision models.
- [ ] Performance benchmarks for vision encoding + LLM inference.

## Test Approach

### Unit Tests

- Test `VisionEncoder` interface with mock encoder.
- Test image preprocessing for different model configurations.
- Test multi-image content parsing from OpenAI format.
- Test cross-attention param struct creation.

### Integration Tests

- End-to-end test: image + text → multimodal inference → text response.
- Test with different image formats (JPEG, PNG, WebP).
- Test with different image sizes (auto-resize).
- Test multi-image input with proper token counting.

### Benchmark Tests

- Measure vision encoding latency per model.
- Measure end-to-end latency (encode + prefill + generate).
- Compare against rknn-llm reference benchmarks.

### Manual Testing

```bash
# Test vision inference with base64 image
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2-vl",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "What is in this image?"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,/9j/..."}}
      ]
    }]
  }'

# Test with image URL
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2-vl",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this image"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
      ]
    }]
  }'
```

## References

- [OpenAI Vision API](https://platform.openai.com/docs/guides/vision)
- rknn-llm multimodal demo: `external/rknn-llm/examples/multimodal_model_demo/`
- Vision export scripts: `external/rknn-llm/examples/multimodal_model_demo/export/`
- C++ multimodal deploy: `external/rknn-llm/examples/multimodal_model_demo/deploy/src/main.cpp`
- Cross-attention API: `external/rknn-llm/rkllm-runtime/Linux/librkllm_api/include/rkllm.h` (lines 170-189, 395-403)
- Multimodal input struct: `external/rknn-llm/rkllm-runtime/Linux/librkllm_api/include/rkllm.h` (lines 127-135)
- Current implementation: `src/models/rkllm_model.py` (lines ~705-742)
- Architecture doc: `docs/multimodal_architecture.md`
- RKLLM SDK Documentation: `external/rknn-llm/doc/Rockchip_RKLLM_SDK_EN_1.2.3.pdf`
