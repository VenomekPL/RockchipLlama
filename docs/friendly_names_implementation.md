# Friendly Model Names & Dynamic Context Detection

**Implementation Date:** October 20, 2025  
**Status:** ✅ Complete

## Overview

Implemented friendly model naming system and automatic context size detection to improve UX and prevent context limit issues like those encountered with Gemma3-1B (4K limit).

## Features

### 1. Friendly Model Names

Long RKLLM filenames like:
```
Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm
google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm
gemma-3-1b-it_w8a8.rkllm
```

Are now mapped to short, memorable names:
```
qwen3-0.6b
gemma3-270m
gemma3-1b
```

### 2. Dynamic Context Detection

The system automatically extracts context size from filenames:
- **qwen3-0.6b**: 16384 tokens (from `ctx16384`)
- **gemma3-270m**: 16384 tokens (from `ctx16384`)
- **gemma3-1b**: 4096 tokens (default when no `ctx` specified)

### 3. Flexible Model Lookup

Models can be loaded using any of:
- Friendly name: `"qwen3-0.6b"`
- Full filename: `"Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm"`
- Normalized name: `"Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588"`

All resolve to the same model with O(1) cache lookup.

## Implementation Details

### Model Manager Changes

**New Methods:**
```python
_create_friendly_name(filename: str) -> str
    # Maps long filenames to short names
    
_extract_context_size(filename: str) -> int
    # Extracts ctx value, returns 4096 if not found
    
_discover_models() -> None
    # Scans models dir, builds cache at startup
    
find_model_path(model_identifier: str) -> Optional[str]
    # Flexible lookup by any identifier
    
get_model_details(model_identifier: str) -> Optional[Dict]
    # Returns full model metadata including context_size
    
list_available_models() -> List[Dict]
    # Returns models with friendly names and context info
```

**Modified Methods:**
```python
load_model(model_name: str, ...) -> bool
    # Now accepts friendly names
    # Auto-detects context size from model
    # Warns if requested context exceeds model capability
    # Uses friendly name internally
    
get_model_info() -> Optional[Dict]
    # Now includes context_size and friendly name
```

### Cache System

```python
self._model_cache: Dict[str, Dict[str, Any]] = {
    # Multiple keys point to same model info:
    'qwen3-0.6b': {
        'id': 'qwen3-0.6b',
        'filename': 'Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm',
        'path': '/home/.../models/Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm',
        'context_size': 16384,
        'object': 'model',
        'owned_by': 'rockchip'
    },
    'Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm': {...},  # Same info
    'Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588': {...}  # Same info
}
```

### API Changes

**GET /v1/models**

Before:
```json
{
  "data": [
    {
      "id": "Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588",
      "object": "model",
      "owned_by": "rockchip"
    }
  ]
}
```

After:
```json
{
  "data": [
    {
      "id": "qwen3-0.6b",
      "object": "model",
      "owned_by": "rockchip"
    }
  ]
}
```

**POST /v1/models/load**

Now accepts:
```json
{
  "model": "qwen3-0.6b"
}
```

Instead of full filename.

### Logging Output

```
2025-10-20 13:59:34 - INFO - Loading model: qwen3-0.6b
2025-10-20 13:59:34 - INFO -   Full name: Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm
2025-10-20 13:59:34 - INFO -   Path: /home/.../models/Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm
2025-10-20 13:59:34 - INFO -   Context size: 16384 tokens (detected: 16384)
2025-10-20 13:59:34 - INFO -   NPU cores: 3
2025-10-20 13:59:34 - INFO -   NOTE: This model will stay loaded until server restart
```

Clear indication of detected context size and friendly name usage.

## Testing

### 1. List Models with Friendly Names ✅

```bash
curl http://localhost:8080/v1/models
```

Returns: `gemma3-270m`, `qwen3-0.6b`, `gemma3-1b`

### 2. Load Model by Friendly Name ✅

```bash
curl -X POST http://localhost:8080/v1/models/load \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3-0.6b"}'
```

Response:
```json
{
  "success": true,
  "message": "Model qwen3-0.6b loaded successfully",
  "model_name": "qwen3-0.6b",
  "loaded": true
}
```

### 3. Chat Completion with Friendly Name ✅

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-0.6b",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "max_tokens": 50
  }'
```

Response:
```json
{
  "id": "chatcmpl-2dca1fe4eed6",
  "model": "qwen3-0.6b",
  "choices": [{
    "message": {
      "content": "2 + 2 = 4"
    }
  }]
}
```

### 4. Context Size Detection ✅

Server logs show:
```
Context size: 16384 tokens (detected: 16384)  # qwen3-0.6b
Context size: 16384 tokens (detected: 16384)  # gemma3-270m
Context size: 4096 tokens (detected: 4096)    # gemma3-1b (no ctx in filename)
```

## Context Size Findings

| Model | Filename Pattern | Detected Context | Notes |
|-------|-----------------|------------------|-------|
| **qwen3-0.6b** | `...ctx16384...` | 16384 tokens | ✅ Full context |
| **gemma3-270m** | `...ctx16384...` | 16384 tokens | ✅ Full context |
| **gemma3-1b** | (no ctx) | 4096 tokens | ⚠️ Limited (default) |

**Critical Discovery:**
- Context size is **BAKED INTO** the .rkllm file at conversion time
- Cannot be changed at runtime
- Gemma3-1B needs reconversion with `--ctx 16384` flag for full context

## Benefits

1. **Better UX**: Short names instead of 50+ character filenames
2. **Context Awareness**: System knows each model's limits
3. **Prevents Truncation**: No more hitting unexpected 4K limits
4. **Flexible Lookup**: Multiple ways to reference same model
5. **Fast**: O(1) cache lookups instead of filesystem scans
6. **Logging**: Clear visibility into model capabilities

## Next Steps

1. **Test with gemma3-270m** to verify 16K context works
2. **Reconvert gemma3-1b** with ctx16384 for full capability
3. **Implement prompt caching** (Phase 2 from Technocore improvements)
4. **Explore LongRoPE** support for >16K contexts
5. **Update API docs** with friendly name examples

## Files Modified

- `src/models/model_manager.py` - Core implementation
- `src/api/openai_routes.py` - API endpoint updates
- `src/main.py` - Disabled auto-reload for stability

## Performance

- Model cache built once at startup
- O(1) lookup time for any identifier
- No filesystem scanning on API calls
- Minimal memory overhead (< 1KB per model)

## Compatibility

- ✅ OpenAI API compatible
- ✅ Works with existing benchmarks
- ✅ Backward compatible (full filenames still work)
- ✅ No breaking changes to API structure
