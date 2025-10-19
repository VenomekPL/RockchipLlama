# Phase 3: Real RKLLM Integration - Roadmap

## Current Status: Phase 2 Complete ✅

The API server is fully functional with:
- ✅ FastAPI server with OpenAI-compatible endpoints
- ✅ Model management (load/unload/list)
- ✅ Singleton pattern for thread-safe operations
- ✅ Comprehensive benchmarking system
- ✅ Response capture for quality comparison
- ✅ Documentation and organization

## What's Next: Phase 3 Goals 🎯

### 1. Real NPU Inference

Replace mock responses with actual RKLLM runtime calls:

```python
# Current (Phase 2): Mock implementation
def generate(self, prompt: str) -> str:
    return ""  # Placeholder

# Target (Phase 3): Real NPU inference
def generate(self, prompt: str) -> str:
    # Actual RKLLM inference
    input_ids = self.tokenize(prompt)
    output_ids = rkllm.rkllm_run(self.model, input_ids, ...)
    return self.detokenize(output_ids)
```

### 2. RKLLM Library Integration

Study and implement patterns from RKNN-LLM examples:

**Key Functions to Implement:**
- `rkllm_init()` - Initialize model
- `rkllm_run()` - Run inference
- `rkllm_destroy()` - Clean up resources

**Reference Code:**
- `RKNN-LLM/examples/rkllm_api_demo/src/rkllm_demo.cpp`
- `RKNN-LLM/examples/rkllm_api_demo_fo/src/rkllm_demo.cpp`

### 3. Python ctypes Bindings

Create Python bindings for RKLLM C API:

```python
from ctypes import *

# Load library
rkllm_lib = CDLL("librkllm.so")

# Define structures
class RKLLMInput(Structure):
    _fields_ = [
        ("input_ids", POINTER(c_int)),
        ("length", c_int),
        # ...
    ]

# Define functions
rkllm_init = rkllm_lib.rkllm_init
rkllm_init.argtypes = [POINTER(RKLLMInput)]
rkllm_init.restype = c_int
```

## Implementation Plan 📋

### Step 1: Study Reference Implementation (1-2 days)

**Tasks:**
- Read RKLLM C++ demo code thoroughly
- Understand initialization parameters
- Map API calls to Python equivalents
- Identify required data structures

**Key Files:**
```
RKNN-LLM/
├── include/rkllm.h                    # API definitions
├── examples/rkllm_api_demo/           # C++ reference
└── runtime/Linux/librkllm_api/        # Runtime libraries
```

### Step 2: Create Python Bindings (2-3 days)

**Create:** `src/models/rkllm_wrapper.py`

```python
"""
Python wrapper for RKLLM C API using ctypes
"""

class RKLLMWrapper:
    def __init__(self, model_path: str):
        self.lib = self._load_library()
        self.model = None
        
    def _load_library(self):
        # Load librkllm.so
        pass
    
    def init_model(self, max_context_len: int, num_npu_core: int):
        # Call rkllm_init()
        pass
    
    def run_inference(self, prompt: str, max_tokens: int) -> str:
        # Call rkllm_run()
        pass
    
    def destroy(self):
        # Call rkllm_destroy()
        pass
```

### Step 3: Update ModelManager (1 day)

**Modify:** `src/models/model_manager.py`

```python
from .rkllm_wrapper import RKLLMWrapper

class ModelManager:
    def load_model(self, model_name: str, ...):
        # Replace mock with real wrapper
        self.current_model = RKLLMWrapper(model_path)
        self.current_model.init_model(max_context_len, num_npu_core)
    
    def generate(self, prompt: str, max_tokens: int) -> str:
        # Call actual inference
        return self.current_model.run_inference(prompt, max_tokens)
```

### Step 4: Update Response Streaming (1-2 days)

**Modify:** `src/api/chat_completions.py` and `src/api/completions.py`

```python
# Current: Mock chunks
async for chunk in mock_stream():
    yield chunk

# Target: Real streaming from RKLLM
async for token in model.stream_generate(prompt):
    yield format_chunk(token)
```

### Step 5: Testing & Validation (2-3 days)

**Run benchmarks with real inference:**
```bash
# Re-run full benchmark suite
python scripts/benchmark_full.py --all-models

# Verify quality of responses
cat benchmarks/benchmark_*.md

# Compare performance metrics
python scripts/benchmark.py --type all --runs 5
```

**Validate:**
- ✅ Models load correctly
- ✅ Inference produces coherent text
- ✅ Streaming works properly
- ✅ Memory usage is reasonable
- ✅ Performance meets expectations
- ✅ Error handling is robust

### Step 6: Documentation Update (1 day)

**Update files:**
- `README.md` - Mark Phase 3 complete
- `docs/RKLLM_INTEGRATION.md` - Document implementation details
- `docs/BENCHMARKING.md` - Add real performance results
- `benchmarks/README.md` - Update with actual quality comparison

## Technical Challenges 🔧

### 1. Memory Management
**Challenge:** Proper allocation/deallocation of buffers  
**Solution:** Use Python context managers, careful with ctypes pointers

### 2. Tokenization
**Challenge:** RKLLM may require pre-tokenized input  
**Solution:** Integrate tokenizer library (tiktoken/transformers)

### 3. Streaming Implementation
**Challenge:** Token-by-token generation vs batch output  
**Solution:** Callback functions or async generators

### 4. Error Handling
**Challenge:** C API errors need Python exception mapping  
**Solution:** Wrapper function to translate return codes

### 5. Thread Safety
**Challenge:** NPU access from multiple threads  
**Solution:** Keep singleton pattern, add locks if needed

## Expected Outcomes 🎯

After Phase 3 completion:

### Functional
- ✅ Real text generation from prompts
- ✅ Streaming responses with proper SSE format
- ✅ Multiple models working correctly
- ✅ Proper resource management

### Performance
- TTFT: 50-200ms (depending on prompt length)
- Throughput: 10-30 tokens/sec (model dependent)
- Memory: Stable, no leaks
- NPU utilization: >80%

### Quality
- Coherent text generation
- Proper instruction following
- Consistent responses
- Model-appropriate capabilities

### Benchmarks
All markdown reports will show:
- Full prompt text
- Actual generated responses
- Meaningful quality comparisons
- Real performance metrics

## Timeline Estimate 📅

| Phase | Tasks | Duration | Status |
|-------|-------|----------|--------|
| Study | Read docs, analyze examples | 1-2 days | ⏳ Next |
| Bindings | Create ctypes wrapper | 2-3 days | ⏳ Pending |
| Integration | Update ModelManager | 1 day | ⏳ Pending |
| Streaming | Implement real streaming | 1-2 days | ⏳ Pending |
| Testing | Validation & benchmarks | 2-3 days | ⏳ Pending |
| Docs | Update documentation | 1 day | ⏳ Pending |
| **TOTAL** | **Complete Phase 3** | **8-12 days** | ⏳ Not Started |

## Success Criteria ✅

Phase 3 will be considered complete when:

1. ✅ All 3 models generate real text responses
2. ✅ Streaming responses work correctly
3. ✅ Benchmarks show actual performance data
4. ✅ Quality comparison is meaningful
5. ✅ No memory leaks or crashes
6. ✅ Documentation is updated
7. ✅ Tests pass with real inference

## Getting Started

When ready to begin Phase 3:

```bash
# 1. Study the reference implementation
cd RKNN-LLM/examples/rkllm_api_demo
cat src/rkllm_demo.cpp

# 2. Examine the header file
cat ../../include/rkllm.h

# 3. Create a simple test wrapper
cd ~/AI/RockchipLlama
mkdir -p src/models/rkllm
touch src/models/rkllm/__init__.py
touch src/models/rkllm/wrapper.py

# 4. Start implementation
# Follow the plan above step by step
```

---

**Current Phase**: 2 (Mock API) ✅  
**Next Phase**: 3 (Real RKLLM) ⏳  
**Final Phase**: 4 (Production Ready) 🎯
