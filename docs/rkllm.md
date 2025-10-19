# RKLLM Runtime Analysis and Documentation

## Overview

RKLLM (Rockchip LLM) is a runtime library designed for efficient large language model inference on Rockchip NPU hardware. This document provides an in-depth analysis of the RKLLM runtime capabilities, API structure, parameters, and implementation patterns based on version 1.2.1 and 1.2.2.

**Latest Version Features (v1.2.1 & v1.2.2):**
- ✅ Multi-instance inference support
- ✅ LongRoPE support for extended context
- ✅ Multi-batch inference capabilities
- ✅ Optimized KV cache clearing interface
- ✅ Improved chat template parsing with thinking mode selection
- ✅ OpenAI-compatible format in server demo
- ✅ Performance statistics tracking
- ✅ Function calling capability
- ✅ Cross-attention inference

---

## Table of Contents
1. [Core Architecture](#core-architecture)
2. [API Structure](#api-structure)
3. [Initialization Parameters](#initialization-parameters)
4. [Input Types](#input-types)
5. [Inference Modes](#inference-modes)
6. [Advanced Features](#advanced-features)
7. [Server Implementation Patterns](#server-implementation-patterns)
8. [Performance Optimization](#performance-optimization)
9. [Limitations and Constraints](#limitations-and-constraints)

---

## Core Architecture

### Library Structure
- **Runtime Library**: `librkllmrt.so` (Linux) - Core inference engine
- **Language Bindings**: C/C++ API with ctypes Python wrapper
- **Platform Support**: RK3588, RK3576, RK3562, RV1126B
- **Quantization Support**: W8A8, W4A16 (group sizes: 32/64/128 for w4, 128/256/512 for w8)

### Key Components

```
┌─────────────────────────────────────┐
│        Application Layer            │
│  (Flask/Gradio/Custom Server)       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        RKLLM API Layer              │
│  - Initialization                   │
│  - Inference Control                │
│  - Memory Management                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      RKLLM Runtime (librkllmrt.so)  │
│  - Model Loading                    │
│  - NPU Scheduling                   │
│  - KV Cache Management              │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        NPU Driver Layer             │
│     (RKNN NPU Hardware)             │
└─────────────────────────────────────┘
```

---

## API Structure

### Core Data Types

#### Handle
```c
typedef void* LLMHandle;
```
Opaque handle to the LLM instance. Each handle represents a separate model instance.

#### Callback States
```c
typedef enum {
    RKLLM_RUN_NORMAL  = 0,  // Normal token generation
    RKLLM_RUN_WAITING = 1,  // Waiting for complete UTF-8 character
    RKLLM_RUN_FINISH  = 2,  // Generation complete
    RKLLM_RUN_ERROR   = 3   // Error occurred
} LLMCallState;
```

#### Result Callback
```c
typedef int(*LLMResultCallback)(RKLLMResult* result, void* userdata, LLMCallState state);
```
**Return values:**
- `0`: Continue inference normally
- `1`: Pause inference (allows modification/intervention, then resume with `rkllm_run`)

---

## Initialization Parameters

### RKLLMParam Structure

```c
typedef struct {
    // Model Configuration
    const char* model_path;         // Path to .rkllm model file
    int32_t max_context_len;        // Maximum context window (up to 16K)
    int32_t max_new_tokens;         // Maximum tokens to generate
    
    // Sampling Parameters
    int32_t top_k;                  // Top-K sampling (1 = greedy)
    float top_p;                    // Nucleus sampling threshold
    float temperature;              // Sampling temperature (0.0-2.0+)
    float repeat_penalty;           // Repetition penalty multiplier
    float frequency_penalty;        // Frequency-based penalty
    float presence_penalty;         // Presence-based penalty
    
    // Mirostat Sampling
    int32_t mirostat;               // 0=disabled, 1/2=enabled
    float mirostat_tau;             // Target perplexity
    float mirostat_eta;             // Learning rate
    
    // Context Management
    int32_t n_keep;                 // Tokens to keep when shifting window (-1=keep all)
    
    // Behavior Flags
    bool skip_special_token;        // Skip special tokens in output
    bool is_async;                  // Async inference mode
    
    // Multimodal Support
    const char* img_start;          // Image start token (e.g., "<|vision_start|>")
    const char* img_end;            // Image end token (e.g., "<|vision_end|>")
    const char* img_content;        // Image content token (e.g., "<|image_pad|>")
    
    // Extended Parameters
    RKLLMExtendParam extend_param;  // See below
} RKLLMParam;
```

### RKLLMExtendParam Structure

```c
typedef struct {
    int32_t base_domain_id;         // Domain ID (typically 0)
    int8_t embed_flash;             // 1=load embeddings from flash, 0=RAM
    int8_t enabled_cpus_num;        // Number of CPU cores to use
    uint32_t enabled_cpus_mask;     // CPU core bitmask
    uint8_t n_batch;                // Batch size (>1 for multi-batch inference)
    int8_t use_cross_attn;          // Enable cross-attention (non-zero=enable)
    uint8_t reserved[104];          // Reserved for future use
} RKLLMExtendParam;
```

**CPU Configuration Examples:**
```c
// RK3588/RK3576: Use big cores (4-7)
enabled_cpus_mask = (1<<4)|(1<<5)|(1<<6)|(1<<7);  // 0xF0
enabled_cpus_num = 4;

// Other platforms: Use cores 0-3
enabled_cpus_mask = (1<<0)|(1<<1)|(1<<2)|(1<<3);  // 0x0F
enabled_cpus_num = 4;
```

### Typical Initialization Pattern

```python
# Python example
param = RKLLMParam()
param.model_path = b"/path/to/model.rkllm"
param.max_context_len = 4096
param.max_new_tokens = 4096
param.top_k = 1
param.top_p = 0.9
param.temperature = 0.8
param.repeat_penalty = 1.1
param.frequency_penalty = 0.0
param.presence_penalty = 0.0
param.skip_special_token = True
param.is_async = False
param.n_keep = -1

# Extended parameters
param.extend_param.base_domain_id = 0
param.extend_param.embed_flash = 1
param.extend_param.enabled_cpus_num = 4
param.extend_param.enabled_cpus_mask = 0xF0  # RK3588 big cores
param.extend_param.n_batch = 1  # Single batch
param.extend_param.use_cross_attn = 0

# Initialize
ret = rkllm_init(handle, param, callback)
```

---

## Input Types

### Input Type Enumeration

```c
typedef enum {
    RKLLM_INPUT_PROMPT      = 0,  // Text string input
    RKLLM_INPUT_TOKEN       = 1,  // Pre-tokenized IDs
    RKLLM_INPUT_EMBED       = 2,  // Embedding vectors
    RKLLM_INPUT_MULTIMODAL  = 3   // Text + image embeddings
} RKLLMInputType;
```

### RKLLMInput Structure

```c
typedef struct {
    const char* role;               // "user", "assistant", "tool", "system"
    bool enable_thinking;           // Enable thinking mode (Qwen3+)
    RKLLMInputType input_type;      // Type of input
    union {
        const char* prompt_input;           // Text prompt
        RKLLMEmbedInput embed_input;        // Embedding data
        RKLLMTokenInput token_input;        // Token IDs
        RKLLMMultiModelInput multimodal_input;  // Multimodal data
    };
} RKLLMInput;
```

### Input Type Details

#### 1. Prompt Input (Most Common)
```c
RKLLMInput input;
input.role = "user";
input.enable_thinking = false;
input.input_type = RKLLM_INPUT_PROMPT;
input.prompt_input = "What is the capital of France?";
```

#### 2. Token Input
```c
RKLLMTokenInput token_input;
token_input.input_ids = token_array;  // int32_t array
token_input.n_tokens = token_count;

RKLLMInput input;
input.input_type = RKLLM_INPUT_TOKEN;
input.token_input = token_input;
```

#### 3. Embedding Input
```c
RKLLMEmbedInput embed_input;
embed_input.embed = embedding_array;  // float array
embed_input.n_tokens = num_tokens;

RKLLMInput input;
input.input_type = RKLLM_INPUT_EMBED;
input.embed_input = embed_input;
```

#### 4. Multimodal Input
```c
RKLLMMultiModelInput multimodal;
multimodal.prompt = "What is in this image?";
multimodal.image_embed = image_features;  // From vision encoder
multimodal.n_image_tokens = tokens_per_image;
multimodal.n_image = number_of_images;
multimodal.image_width = width;
multimodal.image_height = height;

RKLLMInput input;
input.input_type = RKLLM_INPUT_MULTIMODAL;
input.multimodal_input = multimodal;
```

---

## Inference Modes

### RKLLMInferMode Enumeration

```c
typedef enum {
    RKLLM_INFER_GENERATE                = 0,  // Standard text generation
    RKLLM_INFER_GET_LAST_HIDDEN_LAYER   = 1,  // Extract embeddings
    RKLLM_INFER_GET_LOGITS              = 2   // Get raw logits
} RKLLMInferMode;
```

### RKLLMInferParam Structure

```c
typedef struct {
    RKLLMInferMode mode;                        // Inference mode
    RKLLMLoraParam* lora_params;                // Optional LoRA adapter
    RKLLMPromptCacheParam* prompt_cache_params; // Optional prompt cache
    int keep_history;                           // 0=clear history, 1=keep
} RKLLMInferParam;
```

### Mode Usage Examples

#### Standard Generation
```c
RKLLMInferParam params;
memset(&params, 0, sizeof(RKLLMInferParam));
params.mode = RKLLM_INFER_GENERATE;
params.keep_history = 0;  // Single-turn mode

rkllm_run(handle, &input, &params, NULL);
```

#### Extract Hidden Layer (for embeddings)
```c
params.mode = RKLLM_INFER_GET_LAST_HIDDEN_LAYER;
rkllm_run(handle, &input, &params, NULL);

// In callback:
if (result->last_hidden_layer.embd_size != 0) {
    int data_size = result->last_hidden_layer.embd_size * 
                    result->last_hidden_layer.num_tokens * 
                    sizeof(float);
    // Process hidden states
    float* hidden_states = result->last_hidden_layer.hidden_states;
}
```

#### Multi-turn Conversation
```c
params.keep_history = 1;  // Keep conversation context
rkllm_run(handle, &input, &params, NULL);
```

---

## Advanced Features

### 1. LoRA Adapter Support

**Loading Multiple LoRA Adapters:**
```c
// Load first adapter
RKLLMLoraAdapter lora1;
lora1.lora_adapter_path = "adapter1.rkllm";
lora1.lora_adapter_name = "style_adapter";
lora1.scale = 1.0;
rkllm_load_lora(handle, &lora1);

// Load second adapter
RKLLMLoraAdapter lora2;
lora2.lora_adapter_path = "adapter2.rkllm";
lora2.lora_adapter_name = "knowledge_adapter";
lora2.scale = 0.8;
rkllm_load_lora(handle, &lora2);

// Use specific adapter for inference
RKLLMLoraParam lora_params;
lora_params.lora_adapter_name = "style_adapter";
infer_params.lora_params = &lora_params;
```

### 2. Prompt Cache Management

**Save and Load Prompt Cache:**
```c
// Save cache during inference
RKLLMPromptCacheParam cache_params;
cache_params.save_prompt_cache = 1;
cache_params.prompt_cache_path = "./prompt_cache.bin";
infer_params.prompt_cache_params = &cache_params;

// Load cached prompt later
rkllm_load_prompt_cache(handle, "./prompt_cache.bin");

// Release cache from memory
rkllm_release_prompt_cache(handle);
```

**Benefits:**
- Reuse prefill computation for repeated prompts
- Faster inference for common system prompts
- Reduces redundant NPU operations

### 3. KV Cache Management

**Clear KV Cache:**
```c
// Clear entire cache, keep system prompt
rkllm_clear_kv_cache(handle, 1, NULL, NULL);

// Clear entire cache, including system prompt
rkllm_clear_kv_cache(handle, 0, NULL, NULL);

// Clear specific range (per-batch)
int start_pos[] = {10};  // Start position
int end_pos[] = {50};    // End position
rkllm_clear_kv_cache(handle, 0, start_pos, end_pos);
```

**Get Cache Size:**
```c
int cache_sizes[n_batch];
rkllm_get_kv_cache_size(handle, cache_sizes);
printf("Current KV cache size: %d tokens\n", cache_sizes[0]);
```

### 4. Custom Chat Templates

**Override Default Template:**
```c
const char* system = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>";
const char* prefix = "<|im_start|>user\n";
const char* postfix = "<|im_end|>\n<|im_start|>assistant\n";

rkllm_set_chat_template(handle, system, prefix, postfix);
```

### 5. Function Calling (v1.2.1+)

**Configure Function Tools:**
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_temperature",
            "description": "Get current temperature at a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City, State, Country"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"]
                    }
                },
                "required": ["location"]
            }
        }
    }
]

system_prompt = "You are a helpful assistant."
tool_response_str = "tool_response"

rkllm_model.set_function_tools(
    system_prompt=system_prompt,
    tools=json.dumps(tools),
    tool_response_str=tool_response_str
)
```

**Processing Function Calls:**
```python
# Model returns: <tool_call>{"name": "get_current_temperature", "arguments": {...}}</tool_call>
matches = re.findall(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", response)
function_calls = [json.loads(match) for match in matches]

# Execute functions and return results
messages.append({'role': 'tool', 'name': fn_name, 'content': fn_result})
```

### 6. Cross-Attention Support (v1.2.1+)

**For Encoder-Decoder Models:**
```c
RKLLMCrossAttnParam cross_attn;
cross_attn.encoder_k_cache = encoder_keys;   // [layers][tokens][kv_heads][head_dim]
cross_attn.encoder_v_cache = encoder_values; // [layers][kv_heads][head_dim][tokens]
cross_attn.encoder_mask = attention_mask;    // [tokens]
cross_attn.encoder_pos = positions;          // [tokens]
cross_attn.num_tokens = num_encoder_tokens;

rkllm_set_cross_attn_params(handle, &cross_attn);
```

### 7. Multi-Instance Inference (v1.2.2+)

**Running Multiple Models Simultaneously:**
```python
# Create multiple handles
handle1 = RKLLM_Handle_t()
handle2 = RKLLM_Handle_t()

# Initialize with different models
rkllm_init(ctypes.byref(handle1), ctypes.byref(param1), callback1)
rkllm_init(ctypes.byref(handle2), ctypes.byref(param2), callback2)

# Run independently
rkllm_run(handle1, input1, params1, None)
rkllm_run(handle2, input2, params2, None)
```

### 8. Multi-Batch Inference (v1.2.1+)

**Process Multiple Inputs Concurrently:**
```c
// Set batch size during initialization
param.extend_param.n_batch = 4;  // Process 4 inputs at once

// All batch inputs share the same parameters
// Improves throughput for serving multiple users
```

### 9. Thinking Mode (v1.2.1+)

**Enable Reasoning Before Response:**
```c
RKLLMInput input;
input.role = "user";
input.enable_thinking = true;  // Model will output <think>...</think> tags
input.prompt_input = "Solve this complex problem...";
```

**Output Format:**
```
<think>
[Internal reasoning process]
Step 1: ...
Step 2: ...
</think>

[Final answer to user]
```

---

## Server Implementation Patterns

### Flask Server Architecture

**Key Design Patterns from `flask_server.py`:**

#### 1. Thread-Safe Request Handling
```python
lock = threading.Lock()
is_blocking = False

@app.route('/rkllm_chat', methods=['POST'])
def receive_message():
    global is_blocking
    
    # Reject requests if busy
    if is_blocking or global_state == 0:
        return jsonify({'status': 'error', 
                       'message': 'Server busy'}), 503
    
    lock.acquire()
    try:
        is_blocking = True
        # Process request
    finally:
        lock.release()
        is_blocking = False
```

#### 2. Streaming vs Non-Streaming Response
```python
if data["stream"] == False:
    # Non-streaming: wait for complete response
    model_thread = threading.Thread(target=rkllm_model.run, args=(...))
    model_thread.start()
    model_thread.join()
    return jsonify(response)
else:
    # Streaming: yield tokens as generated
    def generate():
        model_thread = threading.Thread(...)
        model_thread.start()
        while not finished:
            while len(global_text) > 0:
                yield f"{json.dumps(token_data)}\n\n"
    return Response(generate(), content_type='text/plain')
```

#### 3. Message Role Handling
```python
for message in messages:
    if message['role'] == 'system':
        system_prompt = message['content']
        continue
    if message['role'] == 'assistant':
        continue  # Skip assistant messages
    if message['role'] == 'user':
        input_prompt = message['content']
    elif message['role'] == 'tool':
        input_prompt.append(message['content'])
```

#### 4. OpenAI-Compatible Response Format
```python
response = {
    "id": "rkllm_chat",
    "object": "rkllm_chat",
    "created": None,
    "choices": [{
        "index": 0,
        "message": {
            "role": "assistant",
            "content": output_text
        },
        "logprobs": None,
        "finish_reason": "stop"
    }],
    "usage": {
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None
    }
}
```

### Gradio Server Pattern

**Simpler Interface for Interactive Chat:**
```python
def chat_with_rkllm(user_message, history):
    # Add user message to history
    _, history = get_user_input(user_message, history)
    
    # Generate response
    result_history = get_RKLLM_output(history)
    
    return result_history
```

---

## Performance Optimization

### Performance Statistics (v1.2.1+)

**RKLLMPerfStat Structure:**
```c
typedef struct {
    float prefill_time_ms;      // Prefill stage duration
    int prefill_tokens;         // Tokens in prefill
    float generate_time_ms;     // Generation stage duration
    int generate_tokens;        // Tokens generated
    float memory_usage_mb;      // Memory usage (VmHWM)
} RKLLMPerfStat;
```

**Access in Callback:**
```c
int callback(RKLLMResult* result, void* userdata, LLMCallState state) {
    if (state == RKLLM_RUN_FINISH) {
        printf("Prefill: %d tokens in %.2f ms (%.2f tokens/sec)\n",
               result->perf.prefill_tokens,
               result->perf.prefill_time_ms,
               result->perf.prefill_tokens / (result->perf.prefill_time_ms / 1000.0));
        
        printf("Generate: %d tokens in %.2f ms (%.2f tokens/sec)\n",
               result->perf.generate_tokens,
               result->perf.generate_time_ms,
               result->perf.generate_tokens / (result->perf.generate_time_ms / 1000.0));
        
        printf("Memory usage: %.2f MB\n", result->perf.memory_usage_mb);
    }
    return 0;
}
```

### Optimization Strategies

#### 1. CPU Core Affinity
```c
// Use big cores on RK3588 for better performance
param.extend_param.enabled_cpus_mask = 0xF0;  // Cores 4-7
param.extend_param.enabled_cpus_num = 4;
```

#### 2. Embed Flash (Memory Optimization)
```c
// Store embeddings in flash to reduce RAM usage
param.extend_param.embed_flash = 1;
```

#### 3. Context Window Management
```c
// Keep important tokens when context is full
param.n_keep = 512;  // Keep first 512 tokens (system prompt)
param.max_context_len = 4096;
```

#### 4. Batch Processing
```c
// Process multiple requests in one forward pass
param.extend_param.n_batch = 4;  // 4x throughput improvement
```

#### 5. Prompt Cache Reuse
```c
// Cache common system prompts
cache_params.save_prompt_cache = 1;
cache_params.prompt_cache_path = "./system_cache.bin";
```

#### 6. Resource Limits
```python
import resource
# Increase file descriptor limit for concurrent connections
resource.setrlimit(resource.RLIMIT_NOFILE, (102400, 102400))
```

#### 7. Frequency Scaling
```bash
# Fix CPU/NPU frequencies for consistent performance
sudo bash fix_freq_rk3588.sh
```

---

## Limitations and Constraints

### Hardware Constraints

1. **Platform-Specific:**
   - RK3588: 3 NPU cores, 6 TOPS total
   - RK3576: 2 NPU cores, 4 TOPS total
   - RK3562: Limited NPU capabilities
   - RV1126B: Basic NPU support

2. **Memory:**
   - Model size limited by available RAM
   - KV cache grows with context length
   - Multimodal models require additional memory for image features

3. **Context Length:**
   - Maximum 16K tokens (with LongRoPE in v1.2.2)
   - Practical limit depends on model size and available memory
   - KV cache memory: `layers × heads × head_dim × context_len × 2 × sizeof(dtype)`

### Software Constraints

1. **Model Format:**
   - Must use converted `.rkllm` models
   - Quantization: W8A8 or W4A16 only
   - No FP16/FP32 inference on NPU

2. **Concurrency:**
   - Single-threaded inference per handle
   - Multi-instance support requires multiple handles
   - Thread-safe locking required for server applications

3. **Input/Output:**
   - Text input limited by tokenizer
   - Streaming only outputs complete UTF-8 characters
   - No real-time token cancellation during generation

4. **Multimodal:**
   - Vision encoder must be separate RKNN model
   - Image features must be pre-computed
   - Limited to specific image sizes per model

### API Constraints

1. **Synchronous Operations:**
   - Model loading blocks execution
   - Inference runs synchronously unless `is_async=True`
   - Callback executes in inference thread

2. **State Management:**
   - `keep_history=0`: Stateless (recommended for REST API)
   - `keep_history=1`: Stateful (requires careful KV cache management)

3. **Error Handling:**
   - Limited error messages from C library
   - Callback receives `RKLLM_RUN_ERROR` state
   - No automatic retry mechanism

### Performance Considerations

1. **Prefill vs Generation:**
   - Prefill (first token): Higher latency, processes all input tokens
   - Generation (subsequent tokens): Lower latency, one token per step
   - Prefill time scales with input length

2. **Batch Processing:**
   - Increases throughput but also increases latency per request
   - All batch items wait for slowest completion
   - Memory usage scales linearly with batch size

3. **Quantization Trade-offs:**
   - W8A8: Better accuracy, higher memory usage
   - W4A16: Lower memory, slightly reduced accuracy
   - Group quantization improves W4A16 quality

---

## Best Practices

### 1. Server Deployment
```python
# Use threading for concurrent handling
app.run(host='0.0.0.0', port=8080, threaded=True, debug=False)

# Implement request queuing
from queue import Queue
request_queue = Queue(maxsize=10)

# Set timeouts
socket.setdefaulttimeout(30)
```

### 2. Error Recovery
```python
try:
    ret = rkllm_run(handle, input, params, None)
    if ret != 0:
        rkllm_clear_kv_cache(handle, 0, None, None)
        # Retry or return error
except Exception as e:
    rkllm_abort(handle)
    # Clean up and restart
```

### 3. Memory Management
```python
# Monitor memory usage
import psutil
process = psutil.Process()
memory_mb = process.memory_info().rss / 1024 / 1024

# Implement cache eviction
if memory_mb > threshold:
    rkllm_clear_kv_cache(handle, 1, None, None)
```

### 4. Logging and Debugging
```bash
# Enable detailed logging
export RKLLM_LOG_LEVEL=1  # 0=ERROR, 1=INFO, 2=DEBUG
```

---

## Example: Complete Python Wrapper

```python
class RKLLMServer:
    def __init__(self, model_path, platform="rk3588"):
        self.handle = RKLLM_Handle_t()
        
        # Set parameters
        param = RKLLMParam()
        param.model_path = model_path.encode('utf-8')
        param.max_context_len = 4096
        param.max_new_tokens = 2048
        param.top_k = 1
        param.top_p = 0.9
        param.temperature = 0.8
        param.repeat_penalty = 1.1
        param.skip_special_token = True
        param.is_async = False
        
        param.extend_param.base_domain_id = 0
        param.extend_param.embed_flash = 1
        param.extend_param.enabled_cpus_num = 4
        param.extend_param.enabled_cpus_mask = 0xF0
        param.extend_param.n_batch = 1
        param.extend_param.use_cross_attn = 0
        
        # Initialize
        ret = rkllm_init(ctypes.byref(self.handle), 
                        ctypes.byref(param), 
                        self.callback)
        
        if ret != 0:
            raise RuntimeError("RKLLM initialization failed")
    
    def callback(self, result, userdata, state):
        # Handle streaming output
        if state == RKLLM_RUN_NORMAL:
            text = result.contents.text.decode('utf-8')
            self.output_buffer.append(text)
        elif state == RKLLM_RUN_FINISH:
            self.finished = True
        elif state == RKLLM_RUN_ERROR:
            self.error = True
        return 0
    
    def generate(self, prompt, stream=False):
        self.output_buffer = []
        self.finished = False
        self.error = False
        
        # Prepare input
        input_data = RKLLMInput()
        input_data.role = b"user"
        input_data.enable_thinking = False
        input_data.input_type = RKLLM_INPUT_PROMPT
        input_data.prompt_input = prompt.encode('utf-8')
        
        # Prepare inference params
        infer_params = RKLLMInferParam()
        infer_params.mode = RKLLM_INFER_GENERATE
        infer_params.keep_history = 0
        
        # Run in thread
        thread = threading.Thread(
            target=rkllm_run,
            args=(self.handle, ctypes.byref(input_data), 
                  ctypes.byref(infer_params), None)
        )
        thread.start()
        
        if stream:
            while not self.finished and not self.error:
                while len(self.output_buffer) > 0:
                    yield self.output_buffer.pop(0)
                time.sleep(0.01)
        else:
            thread.join()
            return ''.join(self.output_buffer)
    
    def __del__(self):
        if hasattr(self, 'handle'):
            rkllm_destroy(self.handle)
```

---

## Deployment Patterns (Official Examples)

### Flask Server Deployment

**Location**: `/external/rknn-llm/examples/rkllm_server_demo/`

#### One-Click Deployment Script
```bash
./build_rkllm_server_flask.sh \
  --workshop /user/data \
  --model_path /user/data/model.rkllm \
  --platform rk3588 \
  [--lora_model_path /path/to/lora.rkllm] \
  [--prompt_cache_path /path/to/cache.bin]
```

**What it does:**
1. Checks Linux environment
2. Auto-installs Flask if missing
3. Pushes `rkllm_server/` files to board
4. Indexes RKLLM model
5. Starts server on `0.0.0.0:8080`

#### OpenAI-Compatible API Format

**Request Structure:**
```json
{
  "model": "your_model_name",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false,
  "enable_thinking": false,
  "tools": null
}
```

**Response Structure (Non-Streaming):**
```json
{
  "id": "rkllm_chat",
  "object": "chat.completion",
  "created": 1677652288,
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Response text..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": null,
    "completion_tokens": null,
    "total_tokens": null
  }
}
```

**Response Structure (Streaming):**
```json
{
  "id": "rkllm_chat",
  "object": "chat.completion.chunk",
  "choices": [{
    "index": 0,
    "delta": {
      "content": "token"
    },
    "finish_reason": null
  }]
}
```

#### Function Calling Implementation

The Flask server supports OpenAI-style function calling:

**Step 1**: Define tools and send first request
```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_temperature",
        "description": "Get current temperature",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }
}]

data = {
    "messages": [{"role": "user", "content": "What's the temp in SF?"}],
    "tools": tools
}
```

**Step 2**: Parse function calls from response
```python
# Model returns: <tool_call>{"name": "get_temperature", ...}</tool_call>
matches = re.findall(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", response)
```

**Step 3**: Execute functions and send results back
```python
messages.append({
    'role': 'tool',
    'name': 'get_temperature',
    'content': '{"temperature": 72}'
})
```

### Gradio Server Deployment

**Location**: `/external/rknn-llm/examples/rkllm_server_demo/`

#### One-Click Deployment Script
```bash
./build_rkllm_server_gradio.sh \
  --workshop /user/data \
  --model_path /user/data/model.rkllm \
  --platform rk3588 \
  [--lora_model_path /path/to/lora.rkllm] \
  [--prompt_cache_path /path/to/cache.bin]
```

**Access Methods:**
1. **Web Interface**: Navigate to `http://[board_ip]:8080/` in browser
2. **API Access**: Use `gradio_client` library

```python
from gradio_client import Client

client = Client("http://172.16.10.xx:8080/")
_, history = client.predict(
    user_message="Hello",
    history=[],
    api_name="/get_user_input"
)
result = client.predict(
    history=history,
    api_name="/get_RKLLM_output"
)
```

**Key Features:**
- Automatic Markdown/HTML rendering
- Request queue for multi-user access
- Visual chat interface
- Real-time streaming display

### Important Implementation Notes

#### Thread Safety Pattern
```python
lock = threading.Lock()
is_blocking = False

@app.route('/rkllm_chat', methods=['POST'])
def receive_message():
    global is_blocking
    
    # Reject if busy
    if is_blocking or global_state == 0:
        return jsonify({'error': 'Server busy'}), 503
    
    lock.acquire()
    try:
        is_blocking = True
        # Process request...
    finally:
        lock.release()
        is_blocking = False
```

#### Resource Management
```python
import resource
# Increase file descriptor limit for many connections
resource.setrlimit(resource.RLIMIT_NOFILE, (102400, 102400))
```

#### Message Role Handling
- **system**: Stored as `system_prompt`, not passed to `rkllm_run`
- **assistant**: Skipped (history maintained by server)
- **user**: Passed as `prompt_input`
- **tool**: JSON-encoded function results

---

## Toolkit Python API Summary

### Model Building
```python
from rkllm.api import RKLLM

llm = RKLLM()

# Load and build model
ret = llm.load_huggingface(model='Qwen/Qwen2.5-0.5B-Instruct')
ret = llm.build(
    do_quantization=True,
    optimization_level=1,
    quantized_dtype='w8a8',
    target_platform='rk3588',
    num_npu_core=3
)

# Export to .rkllm file
ret = llm.export_rkllm("./qwen.rkllm")
```

### PC Simulation
```python
# Accuracy evaluation
inputs = {"input_ids": token_ids}
logits = llm.get_logits(inputs)

# Inference simulation
args = {"max_length": 128, "top_k": 1}
response = llm.chat_model("Hello", args)
```

### Model Update
```python
# Update v1.0.2 model to latest
ret = llm.update_rkllm(model="./old_model.rkllm")
```

---

## Conclusion

The RKLLM runtime provides a comprehensive API for efficient LLM inference on Rockchip NPU hardware. Key takeaways:

1. **Flexibility**: Supports multiple input types, inference modes, and advanced features (LoRA, function calling, multimodal)
2. **Performance**: Hardware acceleration with configurable CPU/NPU settings, batch processing, and caching
3. **Compatibility**: OpenAI-compatible server implementations available
4. **Limitations**: Hardware-specific constraints, quantization requirements, and single-threaded inference per handle

**Recommended for:**
- Edge AI deployment on Rockchip platforms
- Low-latency inference with NPU acceleration
- Resource-constrained environments
- OpenAI API-compatible services

**Not recommended for:**
- Training or fine-tuning (inference only)
- FP16/FP32 precision requirements
- Models larger than available RAM
- Real-time multi-user scenarios without batching

---

## Additional SDK Features (from Official Documentation)

### GPU Prefill Acceleration (RKLLMParam)
```c
bool use_gpu;  // Enable GPU for prefill acceleration (default: false)
```
- Available on supported platforms
- Accelerates the prefill stage using GPU alongside NPU
- Can significantly reduce TTFT (Time To First Token)

### NPU Core Configuration (RKLLMParam)
```c
int32_t num_npu_core;  // Number of NPU cores for inference
```
- **RK3588**: [1, 3] cores (3 TOPS total, 6 TOPS max)
- **RK3576**: [1, 2] cores (2 TOPS total, 4 TOPS max)
- **RK3562**: Limited NPU capabilities
- **RV1126B**: Basic NPU support

### Model Update Function (Toolkit)
```python
# Update old v1.0.2 models to latest version
ret = llm.update_rkllm(model="./model_1.0.2version.rkllm")
```
- Converts v1.0.2 models to v1.1+ format
- Preserves quantization type
- No need to rebuild from source

### PC Simulation Functions (Toolkit)

#### Accuracy Evaluation (Perplexity Testing)
```python
# Get logits for accuracy testing
inputs = {"input_ids": batch_tokens}
lm_logits = llm.get_logits(inputs)
```
- Enables Wikitext PPL testing on PC
- Validates quantization accuracy
- No hardware required

#### Simulated Inference
```python
args = {
    "max_length": 128,
    "top_k": 1,
    "temperature": 0.8,
    "do_sample": True,
    "repetition_penalty": 1.1
}
message = "Human: How's the weather today?\nAssistant:"
response = llm.chat_model(message, args)
```
- Test model behavior before deployment
- Validate chat template formatting
- Debug inference issues on PC

### Custom Model Conversion

The SDK supports custom model architectures through configuration files:

```json
{
    "BLOCKNAME": "CustomDecoderLayer",
    "TOKEN_EMBD": "embed_tokens",
    "ATTN_NORM": "input_layernorm",
    "ATTN_QKV": "self_attn.qkv_proj",
    "ATTN_OUT": "self_attn.o_proj",
    "FFN_NORM": "post_attention_layernorm",
    "FFN_UP": "mlp.up_proj",
    "FFN_GATE": "mlp.gate_proj",
    "FFN_DOWN": "mlp.down_proj",
    "ACT_TYPE": "silu",
    "OUTPUT_NORM": "norm",
    "OUTPUT": "lm_head",
    "KV_CONTINUOUS": "true"
}
```

**Supported Activation Types**: `["silu", "gelu", "relu", "fatrelu", "squarerelu", "swiglu"]`

**Cross-Attention Support**: Define `CROSS_ATTN_NORM`, `CROSS_ATTN_Q`, `CROSS_ATTN_OUT` for encoder-decoder models

### Performance Monitoring

Enable detailed logging:
```bash
# Basic performance data (TTFT, TPS, memory)
export RKLLM_LOG_LEVEL=1

# Detailed logs (cache length, detailed info)
export RKLLM_LOG_LEVEL=2
```

**Performance Metrics Captured:**
- **TTFT** (Time To First Token): Prefill latency
- **TPS** (Tokens Per Second): Generation throughput
- **Memory Usage**: VmHWM resident memory
- **Cache Length**: KV cache utilization

### Frequency Scaling Scripts

Fix CPU/NPU frequencies for consistent performance:
```bash
sudo bash fix_freq_rk3588.sh
sudo bash fix_freq_rk3576.sh
```
Located in: `/external/rknn-llm/scripts/`

### Multi-Batch Inference Details

When `n_batch > 1`, the callback receives an array of results:

```c
int callback(RKLLMResult* result, void* userdata, LLMCallState state) {
    if (state == RKLLM_RUN_NORMAL) {
        RKLLMResult batch1 = result[0];
        RKLLMResult batch2 = result[1];
        // Process each batch separately
    }
    return 0;
}
```

**Important**: All batches in a single run share the same parameters and process concurrently.

---

## References

- **Official Documentation**: `/external/rknn-llm/doc/Rockchip_RKLLM_SDK_EN_1.2.2.pdf`
- **RKLLM GitHub**: https://github.com/airockchip/rknn-llm
- **RKLLM Changelog**: `/external/rknn-llm/CHANGELOG.md`
- **API Header**: `/external/rknn-llm/rkllm-runtime/Linux/librkllm_api/include/rkllm.h`
- **Flask Server Example**: `/external/rknn-llm/examples/rkllm_server_demo/rkllm_server/flask_server.py`
- **Gradio Server Example**: `/external/rknn-llm/examples/rkllm_server_demo/rkllm_server/gradio_server.py`
- **C++ Demo**: `/external/rknn-llm/examples/rkllm_api_demo/deploy/src/llm_demo.cpp`
