# 🚀 Technocore RKLLM Improvements to Implement

Based on review of `/home/angeiv/AI/technocore/modules/rkllm/`, here are the key improvements we should implement:

## 1. ✅ Prompt Caching System (HIGH PRIORITY)

**Current Issue:** Every request processes the system prompt from scratch, wasting time on repeated prefill operations.

**Technocore Solution:**
- Model-specific cache directories: `/cache/<model_name>/`
- Named prompt caches: `system_prompt.bin`, `common_instruction.bin`
- Metadata tracking: JSON files with cache info
- RKLLM runtime support via `rkllm_load_prompt_cache()`

**Implementation:**
```python
class RKLLMEngine:
    def save_prompt_cache(self, cache_name: str, prompt_content: str):
        """Save commonly used prompts (e.g., system prompt) for faster reuse"""
        model_cache_dir = f"/cache/{self.loaded_model_name}/"
        # Save as .bin for RKLLM runtime
        # Save as .txt for readability
        # Save .json metadata
    
    def load_prompt_cache(self, cache_name: str):
        """Load pre-processed prompt cache"""
        # Returns cached prompt if available
```

**Benefits:**
- **Faster TTFT** for chat completions (system prompt already processed)
- **Reduced latency** for repeated tasks (evaluation, sorting)
- **Better UX** for chat applications

**Files to modify:**
- `src/models/rkllm_model.py` - Add caching methods
- `src/api/openai_routes.py` - Use cached system prompts
- Add `/cache/` directory structure

---

## 2. ✅ Dynamic Context Size Detection (MEDIUM PRIORITY)

**Current Issue:** Fixed context size doesn't optimize for different models.

**Technocore Solution:**
```python
def _detect_model_context_size(self, model_path: str) -> int:
    """
    Auto-detect context size based on model AND hardware constraints
    
    Rules:
    - RKLLM has HARD LIMIT of 16K context
    - RK3588 memory limits:
      - Qwen3-0.6B: Can use 16K
      - Qwen3-4B: Use 4K (conservative)
      - Larger models: Use 4K-8K
    """
    if '0.6b' in filename:
        return 16384  # Can handle full context
    elif '4b' in filename:
        return 4096   # Conservative for RK3588
    elif 'ctx' in filename:
        # Extract explicit ctx value
        return min(extracted_value, 16384)
```

**Benefits:**
- **Optimal memory usage** for each model
- **Prevents OOM** errors on larger models
- **Maximizes context** for smaller models

---

## 3. ✅ Model Manager with Friendly Names (HIGH PRIORITY)

**Current Issue:** Using full filenames is cumbersome.

**Technocore Solution:**
```python
class ModelManager:
    def _create_friendly_name(self, filename: str) -> str:
        """
        Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm
        →
        qwen3-0.6b-opt0-hybrid0
        """
    
    def find_model_path(self, model_identifier: str):
        """Accept both friendly names and full filenames"""
```

**API Usage:**
```bash
# Before (cumbersome)
curl -X POST /v1/models/load -d '{"model": "Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm"}'

# After (friendly)
curl -X POST /v1/models/load -d '{"model": "qwen3-0.6b"}'
```

---

## 4. ⚠️ Model Swapping Pattern (CRITICAL - Already Partially Implemented)

**Technocore Approach:**
```python
def load_model(self, model_path: str):
    """Load model - destroys previous if exists"""
    with self._model_lock:
        # Destroy previous model
        if self.handle:
            self.rkllm_destroy(self.handle)
            self.handle = RKLLM_Handle_t()
        
        # Initialize new model
        ret = self.rkllm_init(...)
```

**Our Current Approach:**
- Raise error if trying to load different model
- Forces server restart for model switching

**Decision:** Keep our conservative approach until we verify Technocore's destroy/init sequence doesn't hang on RK3588.

---

## 5. ✅ Enhanced Callback with Usage Tracking (MEDIUM PRIORITY)

**Technocore Enhancement:**
```python
def _callback_impl(self, result_ptr, _userdata, state):
    """Track tokens in real-time during generation"""
    if state == RKLLM_RUN_NORMAL:
        # Emit token
        token = result_ptr.contents.text.decode("utf-8")
        self._out_queue.put(token)
        
        # Track emitted count
        self._emitted_token_count += 1
        
        # Update perf stats continuously
        perf = result_ptr.contents.perf
        self._last_prefill_tokens = perf.prefill_tokens
        self._last_generate_tokens = perf.generate_tokens
```

**Benefits:**
- Real-time token counting during streaming
- Better progress tracking for long generations
- Accurate usage reporting even if generation is aborted

---

## 6. ✅ Clear KV Cache Support (LOW PRIORITY)

**Technocore Feature:**
```python
def clear_cache(self):
    """Clear KV cache and prompt cache"""
    if self._rkllm_clear_kv_cache is not None:
        # Clear all cache sequences
        self._rkllm_clear_kv_cache(self.handle, -1, None, None)
    
    # Reset chat template
    self.set_chat_template("", "", "")
```

**Use Cases:**
- Reset conversation context
- Free memory between sessions
- Start fresh without reloading model

---

## 7. ✅ Environment-Based Configuration (LOW PRIORITY)

**Technocore Pattern:**
```python
DEFAULT_MAX_CONTEXT = int(os.environ.get("RKLLM_MAX_CONTEXT", "4096"))
DEFAULT_TOP_K = int(os.environ.get("RKLLM_TOP_K", "20"))
DEFAULT_TEMPERATURE = float(os.environ.get("RKLLM_TEMPERATURE", "0.6"))
```

**Benefits:**
- Docker-friendly configuration
- No code changes for parameter tuning
- Easy A/B testing

---

## Implementation Priority

### Phase 1: Immediate (This Session)
1. ✅ **Prompt Caching** - Biggest performance win
2. ✅ **Friendly Model Names** - Better UX
3. ✅ **Dynamic Context Detection** - Prevent OOM issues

### Phase 2: Next Session
4. Enhanced callback with real-time tracking
5. Clear KV cache support
6. Environment-based configuration

### Phase 3: Future
7. Test model swapping (if Technocore's approach works reliably)

---

## Key Code Locations in Technocore

- **Engine:** `/home/angeiv/AI/technocore/modules/rkllm/app/rkllm_engine.py`
- **Model Manager:** `/home/angeiv/AI/technocore/modules/rkllm/app/model_manager.py`
- **Multi-Model Server:** `/home/angeiv/AI/technocore/modules/rkllm/app/multi_model/`

---

## Notes

### What Works Well in Technocore:
- ✅ Comprehensive prompt caching system
- ✅ Model-specific cache organization
- ✅ Friendly model names
- ✅ Context size auto-detection
- ✅ Real-time usage tracking

### What We Should Keep From Our Implementation:
- ✅ Conservative model loading (no swapping at runtime)
- ✅ Comprehensive benchmark system
- ✅ Detailed performance metrics extraction
- ✅ OpenAI API compatibility
- ✅ Markdown report generation

### Questions to Verify:
1. Does Technocore's model swapping work reliably on RK3588?
2. Does `rkllm_load_prompt_cache()` actually work with RKLLM runtime v1.2.1?
3. What's the performance gain from prompt caching in practice?

---

**Next Steps:** Implement Phase 1 improvements while keeping our stable foundation.
