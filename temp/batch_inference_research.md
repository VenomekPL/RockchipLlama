# RKLLM Batch Inference Research

**Date:** October 20, 2025  
**Source:** external/rknn-llm/rkllm-runtime/Linux/librkllm_api/include/rkllm.h

---

## 🎯 DISCOVERY: Native Batch Inference Support!

RKLLM **DOES support batch inference natively!**

### Key Finding: `n_batch` Parameter

Located in `RKLLMExtendParam` structure (line 58):

```c
typedef struct {
    int32_t      base_domain_id;
    int8_t       embed_flash;
    int8_t       enabled_cpus_num;
    uint32_t     enabled_cpus_mask;
    uint8_t      n_batch;               /**< Number of input samples processed concurrently in one forward pass. Set to >1 to enable batched inference. Default is 1. */
    int8_t       use_cross_attn;
    uint8_t      reserved[104];
} RKLLMExtendParam;
```

**Documentation says:**
> "Number of input samples processed concurrently in one forward pass. Set to >1 to enable batched inference. Default is 1."

---

## 📋 Batch Inference Implementation Plan

### Phase 4.2: Multi-Batch Inference

#### Part 1: Enable Batch Parameter (Simple)

**Current State:**
- We initialize RKLLM with default `n_batch = 1`
- Only process one request at a time

**Changes Needed:**
1. Add `n_batch` parameter to `config/inference_config.json`
2. Pass `n_batch` to `RKLLMExtendParam` during model initialization
3. Test with `n_batch = 2, 4, 8` to find optimal value

**Expected Impact:**
- Enables hardware capability for batch processing
- Prerequisite for concurrent request handling

---

#### Part 2: Request Queue & Batching System (Complex)

**Architecture:**

```
Client Request 1 ──┐
Client Request 2 ──┼──> Request Queue ──> Batcher ──> RKLLM (n_batch=4) ──> Response Router
Client Request 3 ──┤                                                              │
Client Request 4 ──┘                                                              ├──> Client 1
                                                                                   ├──> Client 2
                                                                                   ├──> Client 3
                                                                                   └──> Client 4
```

**Components Needed:**

1. **Request Queue**
   - Thread-safe queue (asyncio.Queue)
   - Each request contains: prompt, params, response callback
   - FIFO ordering (can add priority later)

2. **Batch Collector**
   - Collect up to `n_batch` requests from queue
   - Wait timeout (e.g., 10ms) before processing incomplete batch
   - Group requests with compatible parameters

3. **Batch Processor**
   - Call `rkllm_run()` or `rkllm_run_async()` with batched inputs
   - RKLLM processes all inputs in parallel on NPU
   - Route each result back to correct client

4. **Response Router**
   - Map batch results to original requests
   - Send responses to correct clients
   - Handle streaming vs non-streaming

---

### Key Questions to Research

#### Q1: How does RKLLM handle batched inputs?

**Hypothesis:** Need to call `rkllm_run()` multiple times or provide array of inputs?

**Need to check:**
- Look at examples in `external/rknn-llm/examples/`
- Search for batch usage in Flask/Gradio examples
- Check if there's a `rkllm_run_batch()` function

#### Q2: Does each batch request need separate RKLLMInput?

Looking at `RKLLMInput` structure:
```c
typedef struct {
    const char* role;
    bool enable_thinking;
    RKLLMInputType input_type;
    union {
        const char* prompt_input;
        // ... other types
    };
} RKLLMInput;
```

**It's a single input structure!**

**Question:** With `n_batch=4`, do we:
- A) Call `rkllm_run()` 4 times in parallel?
- B) Pass array of 4 `RKLLMInput` structures?
- C) Something else?

**Action:** Search examples for usage pattern.

#### Q3: How are batch results returned?

**From callback signature:**
```c
typedef int(*LLMResultCallback)(RKLLMResult* result, void* userdata, LLMCallState state);
```

**Possibilities:**
- A) Callback called once per batch item (4x for n_batch=4)
- B) Callback called once with array of results
- C) Need batch-specific callback

**Action:** Check examples and test.

---

### KV Cache Management with Batching

Important function found:
```c
int rkllm_get_kv_cache_size(LLMHandle handle, int* cache_sizes);
```

> "The array must be preallocated with space for `n_batch` elements."

**This confirms:** RKLLM maintains separate KV cache for each batch slot!

```c
int rkllm_clear_kv_cache(LLMHandle handle, int keep_system_prompt, int* start_pos, int* end_pos);
```

> "Array of start/end positions, one per batch."

**Implication:** Each batch slot is independent, can have different conversation history.

---

### Async Execution Support

```c
int rkllm_run_async(LLMHandle handle, RKLLMInput* rkllm_input, 
                    RKLLMInferParam* rkllm_infer_params, void* userdata);

int rkllm_is_running(LLMHandle handle);

int rkllm_abort(LLMHandle handle);
```

**Async capabilities:**
- `rkllm_run_async()` - Non-blocking inference
- `rkllm_is_running()` - Check if busy
- `rkllm_abort()` - Cancel ongoing inference

**Usage Pattern (hypothesis):**
1. Check `rkllm_is_running()` before submitting new request
2. Call `rkllm_run_async()` for non-blocking execution
3. Callback fires when results ready

---

## 🔍 Next Research Steps

### 1. Check Official Examples

Look at these files:
```
external/rknn-llm/examples/rkllm_server_demo/chat_api_flask.py
external/rknn-llm/examples/rkllm_server_demo/chat_api_gradio.py
external/rknn-llm/examples/rkllm_api_demo/
```

**Search for:**
- `n_batch` usage
- Multiple concurrent requests
- How they handle batching (if at all)

### 2. Read RKLLM SDK Documentation

File: `external/rknn-llm/doc/Rockchip_RKLLM_SDK_EN_1.2.2.pdf`

**Look for:**
- Batch inference section
- Performance optimization guide
- Example code snippets
- Best practices for `n_batch` configuration

### 3. Test Simple Batch Case

**Experiment:**
1. Set `n_batch = 2` in model init
2. Call `rkllm_run_async()` twice quickly
3. Observe:
   - Does second call block?
   - How are results returned?
   - Performance improvement?

---

## 📊 Expected Performance Impact

### Scenario: 4 Concurrent Users

**Current (n_batch=1, sequential):**
```
User 1: 300ms TTFT + 2000ms generation = 2300ms
User 2: waits 2300ms + 300ms + 2000ms = 4600ms
User 3: waits 4600ms + 300ms + 2000ms = 6900ms
User 4: waits 6900ms + 300ms + 2000ms = 9200ms

Average latency: (2300 + 4600 + 6900 + 9200) / 4 = 5750ms
Throughput: 4 requests / 9200ms = 0.43 req/sec
```

**With Batching (n_batch=4, parallel):**
```
All 4 users: 300ms TTFT + 2000ms generation = 2300ms (parallel!)

Average latency: 2300ms (for all!)
Throughput: 4 requests / 2300ms = 1.74 req/sec

Improvement: 4x throughput, 60% less average latency!
```

**Note:** Actual performance depends on NPU parallelization efficiency.
- Best case: Linear scaling (4x)
- Realistic: 2-3x improvement
- Worst case: Marginal improvement (memory bandwidth bottleneck)

---

## 🎯 Implementation Strategy

### Option A: Simple Concurrent (Recommended First)

**Pros:**
- Easier to implement
- Works with existing code
- Good for testing `n_batch` parameter

**Cons:**
- May not fully utilize batching
- Less efficient than true batching

**Approach:**
1. Enable `n_batch > 1` in model init
2. Use `rkllm_run_async()` for concurrent requests
3. Let RKLLM handle internal batching

### Option B: Explicit Batch Management (Advanced)

**Pros:**
- Maximum efficiency
- Full control over batching

**Cons:**
- Complex implementation
- Need to understand exact RKLLM batch API

**Approach:**
1. Queue incoming requests
2. Collect batches of size `n_batch`
3. Submit as batch to RKLLM (method TBD)
4. Route results back to clients

---

## 🚀 Recommended Implementation Plan

### Phase 4.2.1: Enable n_batch Parameter (1-2 hours)

1. Add `n_batch` to config
2. Update model initialization
3. Test with different values (2, 4, 8)
4. Benchmark single-user performance (ensure no regression)

### Phase 4.2.2: Research Examples (1 hour)

1. Study Flask/Gradio examples
2. Read SDK documentation
3. Understand exact batch API usage

### Phase 4.2.3: Implement Request Queue (2-3 hours)

1. Create async request queue
2. Implement batch collector
3. Use `rkllm_run_async()` for processing
4. Response routing

### Phase 4.2.4: Testing & Optimization (2 hours)

1. Load testing with multiple concurrent clients
2. Measure throughput improvement
3. Tune `n_batch` and queue timeout
4. Document configuration

**Total Estimated Time: 6-8 hours**

---

## 🔍 FINDINGS from Official Examples

### Flask Server Analysis

**File:** `external/rknn-llm/examples/rkllm_server_demo/rkllm_server/flask_server.py`

**Key Discovery:**
```python
rkllm_param.extend_param.n_batch = 1  # Line 231
```

**Official examples use `n_batch = 1`!** They do NOT use batch inference.

**Concurrency Handling:**
```python
# Line 158 - Thread lock for single-threaded processing
lock = threading.Lock()

# Line 161 - Global blocking flag
is_blocking = False
```

**Their approach:**
- Use thread lock to serialize requests
- Only ONE request processed at a time
- No concurrent inference
- No batch processing

**This means:**
- ❌ Official examples don't demonstrate batch inference
- ❌ They serialize all requests (one at a time)
- ✅ Setting `n_batch > 1` is possible but not demonstrated
- ✅ We can be pioneers in using this feature!

---

## 📋 REVISED Implementation Plan

Based on research findings, here's the updated approach:

### Discovery Summary

1. **n_batch parameter exists** in RKLLMExtendParam
2. **Official examples DON'T use it** (always set to 1)
3. **No example code** showing how to use n_batch > 1
4. **Documentation needed** - Need to read SDK PDF

### Two Possible Approaches

#### Approach A: Internal Batch Processing (RKLLM does the work)

**Hypothesis:**
- Set `n_batch = 4` during initialization
- Call `rkllm_run_async()` multiple times quickly
- RKLLM internally batches the 4 concurrent requests
- Callbacks fire individually for each request

**Pros:**
- Simplest implementation
- RKLLM handles batching internally
- Minimal code changes

**Cons:**
- Unclear if this is how it works
- No examples to reference
- Might not work as expected

**Testing Plan:**
1. Set `n_batch = 2`
2. Call `rkllm_run_async()` twice in quick succession
3. Monitor if second call blocks or both run concurrently
4. Check if there's performance improvement

---

#### Approach B: Explicit Batch API (Unknown)

**Hypothesis:**
- There might be a `rkllm_run_batch()` function we haven't found
- Or need to prepare array of RKLLMInput structures
- Pass all inputs at once to RKLLM

**Status:** Need to research if this exists

---

## ✅ Action Items (UPDATED)

- [x] Read `flask_server.py` for batch usage patterns - **DONE: They don't use it**
- [ ] Read SDK PDF (`Rockchip_RKLLM_SDK_EN_1.2.2.pdf`) for batch documentation
- [ ] Search SDK PDF for "batch", "n_batch", "concurrent"
- [ ] Test Approach A: Set `n_batch=2` and call `rkllm_run_async()` twice
- [ ] Implement request queue if Approach A works
- [ ] Benchmark concurrent request performance

---

## 📝 Updated Questions

1. ✅ **Does official code use n_batch?** NO - They use `n_batch=1` always
2. ❓ **How does n_batch actually work?** Need SDK PDF documentation
3. ❓ **Can we call rkllm_run_async() multiple times?** Need to test
4. ❓ **Does RKLLM automatically batch concurrent requests?** Unknown
5. ❓ **What's the optimal n_batch for RK3588?** Need benchmarking

**Next Step: Read SDK PDF for batch inference documentation!**
