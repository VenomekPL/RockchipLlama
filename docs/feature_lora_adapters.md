# Feature: LoRA Adapter Support

## Overview

LoRA (Low-Rank Adaptation) allows fine-tuned model behavior without replacing the base model. LoRA adapters are small files that modify specific model layers, enabling task-specific customization (e.g., coding assistant, medical Q&A, customer support tone) while sharing the same base model. This is essential for multi-tenant deployments and rapid iteration on model behavior.

## Current Status

**Partially Implemented** — The RKLLM wrapper has LoRA struct definitions but no API endpoint or runtime support.

In `src/models/rkllm_model.py`:

```python
# Line 139: LoRA params field exists in infer params struct
("lora_params", ctypes.c_void_p),

# Line 765, 1004: LoRA params set to None during inference
infer_params.lora_params = None
```

- The `RKLLMLoraParam` and `RKLLMLoraAdapter` ctypes structures are **not defined** in the wrapper.
- No `rkllm_load_lora()` binding exists.
- No API endpoint allows loading, listing, or switching LoRA adapters.
- No configuration option for specifying LoRA adapters.

## rknn-llm Reference Implementation

The rknn-llm flask server provides a complete LoRA implementation:

### C API

```c
// From rkllm.h (lines 96-104, 280)
typedef struct {
    const char* lora_adapter_path;  // Path to adapter file
    const char* lora_adapter_name;  // Name for referencing
    float scale;                     // Scaling factor (typically 1.0)
} RKLLMLoraAdapter;

typedef struct {
    const char* lora_adapter_name;  // Name of adapter to use
} RKLLMLoraParam;

// Load a LoRA adapter
int rkllm_load_lora(LLMHandle handle, RKLLMLoraAdapter* lora_adapter);
```

### Reference Server Code (from `flask_server.py`)

```python
# Define ctypes structures
class RKLLMLoraAdapter(ctypes.Structure):
    _fields_ = [
        ("lora_adapter_path", ctypes.c_char_p),
        ("lora_adapter_name", ctypes.c_char_p),
        ("scale", ctypes.c_float)
    ]

class RKLLMLoraParam(ctypes.Structure):
    _fields_ = [
        ("lora_adapter_name", ctypes.c_char_p)
    ]

# Load LoRA adapter during initialization
if lora_model_path:
    lora_adapter_name = "test"
    lora_adapter = RKLLMLoraAdapter()
    ctypes.memset(ctypes.byref(lora_adapter), 0, ctypes.sizeof(RKLLMLoraAdapter))
    lora_adapter.lora_adapter_path = ctypes.c_char_p(lora_model_path.encode('utf-8'))
    lora_adapter.lora_adapter_name = ctypes.c_char_p(lora_adapter_name.encode('utf-8'))
    lora_adapter.scale = 1.0

    rkllm_load_lora = rkllm_lib.rkllm_load_lora
    rkllm_load_lora.argtypes = [RKLLM_Handle_t, ctypes.POINTER(RKLLMLoraAdapter)]
    rkllm_load_lora.restype = ctypes.c_int
    rkllm_load_lora(self.handle, ctypes.byref(lora_adapter))

    # Set LoRA params for inference
    rkllm_lora_params = RKLLMLoraParam()
    rkllm_lora_params.lora_adapter_name = ctypes.c_char_p(lora_adapter_name.encode('utf-8'))

# Use during inference
self.rkllm_infer_params.lora_params = ctypes.pointer(rkllm_lora_params) if rkllm_lora_params else None
```

## Implementation Plan

### Step 1: Define LoRA Ctypes Structures

Add the missing struct definitions to `src/models/rkllm_model.py`:

```python
class RKLLMLoraAdapter(ctypes.Structure):
    _fields_ = [
        ("lora_adapter_path", ctypes.c_char_p),
        ("lora_adapter_name", ctypes.c_char_p),
        ("scale", ctypes.c_float)
    ]

class RKLLMLoraParam(ctypes.Structure):
    _fields_ = [
        ("lora_adapter_name", ctypes.c_char_p)
    ]
```

### Step 2: Bind `rkllm_load_lora`

```python
# In RKLLMModel initialization
self._load_lora = self.lib.rkllm_load_lora
self._load_lora.argtypes = [ctypes.c_void_p, ctypes.POINTER(RKLLMLoraAdapter)]
self._load_lora.restype = ctypes.c_int

def load_lora_adapter(self, adapter_path: str, adapter_name: str, scale: float = 1.0):
    adapter = RKLLMLoraAdapter()
    ctypes.memset(ctypes.byref(adapter), 0, ctypes.sizeof(RKLLMLoraAdapter))
    adapter.lora_adapter_path = adapter_path.encode('utf-8')
    adapter.lora_adapter_name = adapter_name.encode('utf-8')
    adapter.scale = scale

    ret = self._load_lora(self.handle, ctypes.byref(adapter))
    if ret != 0:
        raise RuntimeError(f"Failed to load LoRA adapter: {adapter_path}")

    self._loaded_loras[adapter_name] = {
        "path": adapter_path, "scale": scale
    }
```

### Step 3: Support Per-Request LoRA Selection

Allow specifying which LoRA adapter to use in inference requests:

```python
def generate(self, prompt, lora_adapter_name=None, ...):
    infer_params = RKLLMInferParam()
    if lora_adapter_name and lora_adapter_name in self._loaded_loras:
        lora_param = RKLLMLoraParam()
        lora_param.lora_adapter_name = lora_adapter_name.encode('utf-8')
        infer_params.lora_params = ctypes.pointer(lora_param)
    else:
        infer_params.lora_params = None
```

### Step 4: Add Configuration Support

Update `config/inference_config.json`:

```json
{
  "lora_adapters": [
    {
      "name": "coding-assistant",
      "path": "models/lora/coding-assistant.rkllm",
      "scale": 1.0,
      "auto_load": true
    },
    {
      "name": "medical-qa",
      "path": "models/lora/medical-qa.rkllm",
      "scale": 0.8,
      "auto_load": false
    }
  ]
}
```

### Step 5: Add API Endpoints

```python
# List loaded LoRA adapters
@router.get("/v1/lora")
async def list_lora_adapters():
    return {"adapters": model_instance.list_lora_adapters()}

# Load a new LoRA adapter
@router.post("/v1/lora")
async def load_lora_adapter(request: LoraLoadRequest):
    model_instance.load_lora_adapter(request.path, request.name, request.scale)
    return {"status": "loaded", "name": request.name}

# Use LoRA in chat completion (extend existing endpoint)
# Add optional "lora_adapter" field to ChatCompletionRequest
```

### Step 6: Add Model Name Suffix Convention

Support LoRA selection via model name suffix:

```python
# Request: {"model": "qwen3-0.6b:coding-assistant"}
# Parses as: base_model="qwen3-0.6b", lora="coding-assistant"
```

## Goals

1. Load LoRA adapters at startup or dynamically at runtime.
2. Per-request LoRA adapter selection via API.
3. Multiple LoRA adapters loaded simultaneously.
4. LoRA adapter management endpoints (list, load).
5. Configuration-driven auto-loading of adapters.

## Definition of Done

- [ ] `RKLLMLoraAdapter` and `RKLLMLoraParam` ctypes structs defined.
- [ ] `rkllm_load_lora()` bound and callable.
- [ ] LoRA adapters can be loaded from config at startup.
- [ ] LoRA adapters can be loaded dynamically via API endpoint.
- [ ] Per-request LoRA selection works in chat completion.
- [ ] `/v1/lora` endpoint lists loaded adapters.
- [ ] `POST /v1/lora` endpoint loads new adapters.
- [ ] Model name suffix convention (e.g., `model:lora_name`) supported.
- [ ] Error handling for missing/invalid adapter files.
- [ ] Multiple adapters can coexist (loaded, selectable per-request).

## Test Approach

### Unit Tests

- Test LoRA adapter struct creation and memory layout.
- Test `load_lora_adapter()` with mock RKLLM library.
- Test per-request LoRA selection in inference params.
- Test model name parsing for LoRA suffix.

### Integration Tests

- Load a LoRA adapter and verify it's listed.
- Send inference request with LoRA and verify params are passed to RKLLM.
- Test switching between LoRA adapters across requests.
- Test inference without LoRA after loading one (ensure base model still works).

### Manual Testing

```bash
# List LoRA adapters
curl http://localhost:8080/v1/lora

# Load a LoRA adapter
curl -X POST http://localhost:8080/v1/lora \
  -H "Content-Type: application/json" \
  -d '{"name": "coding", "path": "/models/lora/coding.rkllm", "scale": 1.0}'

# Use LoRA in chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-0.6b:coding",
    "messages": [{"role": "user", "content": "Write a Python function to sort a list"}]
  }'
```

## References

- [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
- RKLLM LoRA API: `external/rknn-llm/rkllm-runtime/Linux/librkllm_api/include/rkllm.h` (lines 96-104, 153-159, 280)
- rknn-llm server LoRA impl: `external/rknn-llm/examples/rkllm_server_demo/rkllm_server/flask_server.py` (lines ~274-295)
- Current stub: `src/models/rkllm_model.py` (line 139, 765, 1004)
- RKLLM SDK Documentation: `external/rknn-llm/doc/Rockchip_RKLLM_SDK_EN_1.2.3.pdf`
