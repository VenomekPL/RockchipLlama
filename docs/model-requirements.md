# Model Requirements for Testing

## Model Download Location

**Pre-converted RKLLM Models**: [rkllm_model_zoo](https://console.box.lenovo.com/l/l0tXb8)  
**Fetch Code**: `rkllm`

⚠️ **Note**: This is a password-protected Lenovo Box instance. You'll need to enter the fetch code to access.

---

## Recommended Models for Initial Testing

Based on the benchmark data and our RK3588 target platform, here are the models we should test:

### Priority 1: Small, Fast Models (Best for Testing)

#### 1. **Qwen2-0.5B** (HIGHEST PRIORITY)
- **Size**: 0.5B parameters
- **Format**: w8a8 quantization
- **Performance on RK3588**:
  - TTFT: 143.83 ms
  - Throughput: 42.58 tokens/s
  - Memory: 654 MB
- **Why**: Smallest, fastest, most practical for edge deployment
- **File to download**: `Qwen2-0.5B-Instruct_W8A8_RK3588.rkllm`

#### 2. **MiniCPM4-0.5B**
- **Size**: 0.5B parameters
- **Format**: w8a8
- **Performance on RK3588**:
  - TTFT: 128.46 ms (even faster prefill!)
  - Throughput: 45.13 tokens/s
  - Memory: 524 MB (lowest memory!)
- **Why**: Fastest TTFT, lowest memory usage
- **File to download**: `MiniCPM4-0.5B_W8A8_RK3588.rkllm`

#### 3. **Qwen3-0.6B**
- **Size**: 0.6B parameters
- **Format**: w8a8
- **Performance on RK3588**:
  - TTFT: 213.50 ms
  - Throughput: 32.16 tokens/s
  - Memory: 773 MB
- **Why**: Latest Qwen version, supports thinking mode
- **File to download**: `Qwen3-0.6B_W8A8_RK3588.rkllm`

### Priority 2: Medium Models (For Production Use)

#### 4. **Qwen2.5-1.5B**
- **Size**: 1.5B parameters
- **Format**: w8a8
- **Performance on RK3588**:
  - TTFT: 412.27 ms
  - Throughput: 16.32 tokens/s
  - Memory: 1659 MB
- **Why**: Better quality, still reasonably fast
- **File to download**: `Qwen2.5-1.5B-Instruct_W8A8_RK3588.rkllm`

#### 5. **TinyLLAMA-1.1B**
- **Size**: 1.1B parameters
- **Format**: w8a8
- **Performance on RK3588**:
  - TTFT: 239.00 ms
  - Throughput: 24.49 tokens/s
  - Memory: 1085 MB
- **Why**: Popular model, good baseline for comparison
- **File to download**: `TinyLlama-1.1B-Chat_W8A8_RK3588.rkllm`

### Priority 3: Advanced Testing (Optional)

#### 6. **Gemma2-2B**
- **Size**: 2B parameters
- **Format**: w8a8
- **Performance on RK3588**:
  - TTFT: 679.90 ms
  - Throughput: 9.80 tokens/s
  - Memory: 2765 MB
- **Why**: Google model, different architecture
- **File to download**: `Gemma2-2B_W8A8_RK3588.rkllm`

---

## Initial Testing Recommendation

**Start with these 2 models:**

### 1. Qwen2-0.5B-Instruct (Primary)
```
File: Qwen2-0.5B-Instruct_W8A8_RK3588.rkllm
Why: 
- Best balance of speed and quality
- 42.58 tokens/s is very responsive
- Only 654 MB RAM
- Well-documented, widely used
- Supports function calling
```

### 2. MiniCPM4-0.5B (Backup/Comparison)
```
File: MiniCPM4-0.5B_W8A8_RK3588.rkllm
Why:
- Fastest TTFT (128ms)
- Lowest memory (524 MB)
- Can run alongside Qwen2 for comparison
- Great for multi-instance testing
```

---

## What to Download First

### Minimal Setup (Good for Quick Start)
Download just these files from the model zoo:

1. `Qwen2-0.5B-Instruct_W8A8_RK3588.rkllm` (~300-400 MB)
2. `MiniCPM4-0.5B_W8A8_RK3588.rkllm` (~250-350 MB)

**Total download**: ~600-750 MB

### Comprehensive Setup (Better Testing)
Add these for more thorough testing:

3. `Qwen3-0.6B_W8A8_RK3588.rkllm` (~400 MB)
4. `Qwen2.5-1.5B-Instruct_W8A8_RK3588.rkllm` (~1 GB)
5. `TinyLlama-1.1B-Chat_W8A8_RK3588.rkllm` (~700 MB)

**Total download**: ~3-4 GB

---

## File Naming Convention (Expected)

Based on the benchmark and typical RKLLM naming:

```
<ModelFamily>-<Size>-<Variant>_<Quantization>_<Platform>.rkllm

Examples:
- Qwen2-0.5B-Instruct_W8A8_RK3588.rkllm
- Qwen2.5-1.5B-Instruct_W8A8_RK3588.rkllm
- TinyLlama-1.1B-Chat_W8A8_RK3588.rkllm
- MiniCPM4-0.5B_W8A8_RK3588.rkllm
- Gemma2-2B_W8A8_RK3588.rkllm
```

---

## Testing Strategy

### Phase 1: Basic Functionality
**Use**: Qwen2-0.5B-Instruct
- Test RKLLM initialization
- Test single inference
- Test streaming
- Validate callback mechanism

### Phase 2: Server Testing
**Use**: Qwen2-0.5B-Instruct
- Test Flask/Gradio examples
- Validate OpenAI API compatibility
- Test concurrent requests
- Measure performance

### Phase 3: FastAPI Development
**Use**: Qwen2-0.5B-Instruct + MiniCPM4-0.5B
- Build FastAPI server
- Test multi-model support
- Benchmark async performance
- Test multi-batch inference

### Phase 4: Advanced Features
**Use**: Qwen3-0.6B (supports thinking mode)
- Function calling
- Thinking mode
- Multi-turn conversations
- Prompt cache

### Phase 5: Load Testing
**Use**: All models
- Multi-user scenarios
- Memory pressure testing
- Multi-instance inference
- Performance optimization

---

## Alternative: HuggingFace + Convert Yourself

If the password-protected model zoo is too much hassle, we can:

1. **Download from HuggingFace** (open, no password):
   ```bash
   # Example: Qwen2-0.5B-Instruct
   git clone https://huggingface.co/Qwen/Qwen2-0.5B-Instruct
   ```

2. **Convert using RKLLM-Toolkit**:
   ```python
   from rkllm.api import RKLLM
   
   llm = RKLLM()
   llm.load_huggingface(model='Qwen/Qwen2-0.5B-Instruct')
   llm.build(
       do_quantization=True,
       optimization_level=1,
       quantized_dtype='w8a8',
       target_platform='rk3588',
       num_npu_core=3
   )
   llm.export_rkllm("./qwen2-0.5b.rkllm")
   ```

**Trade-off**:
- ✅ No password needed
- ✅ Latest models from HuggingFace
- ❌ Requires PC with RKLLM-Toolkit
- ❌ Conversion takes time (~30-60 min per model)
- ❌ Requires more disk space (HF model + RKLLM model)

---

## Storage Planning

### On Your PC (for download):
```
models/
├── qwen2-0.5b-instruct.rkllm      # 350 MB
├── minicpm4-0.5b.rkllm             # 300 MB
├── qwen3-0.6b.rkllm                # 400 MB
├── qwen2.5-1.5b-instruct.rkllm    # 1 GB
└── tinyllama-1.1b-chat.rkllm      # 700 MB
Total: ~2.75 GB
```

### On RK3588 Board:
```
/data/models/
└── qwen2-0.5b-instruct.rkllm      # Start with just this one
```

### In Docker Container:
```
/app/models/  (mounted volume)
└── qwen2-0.5b-instruct.rkllm
```

---

## Access Instructions

### Step 1: Access Model Zoo
1. Navigate to: https://console.box.lenovo.com/l/l0tXb8
2. Enter fetch code: `rkllm`
3. Browse to find pre-converted models for RK3588

### Step 2: Download Priority Models
Look for these files in the zoo:
- `Qwen2-0.5B*RK3588*.rkllm` (must have)
- `MiniCPM4-0.5B*RK3588*.rkllm` (highly recommended)
- Any other small models (< 1GB) for testing

### Step 3: Transfer to Development
```bash
# Local to project
cp ~/Downloads/*.rkllm /home/angeiv/AI/RockchipLlama/models/

# Later: Project to board (when testing)
adb push models/qwen2-0.5b-instruct.rkllm /data/models/
```

---

## What We Need RIGHT NOW

**For immediate testing of the examples:**

1. **Download**: `Qwen2-0.5B-Instruct_W8A8_RK3588.rkllm`
2. **Place in**: `/home/angeiv/AI/RockchipLlama/models/`
3. **Test with**: Flask example from `external/rknn-llm/examples/rkllm_server_demo/`

This single model will let us:
- ✅ Test all basic RKLLM functionality
- ✅ Validate the Flask server example
- ✅ Benchmark performance
- ✅ Start FastAPI development
- ✅ Test OpenAI compatibility

---

## Summary

**Minimum to get started**: 1 model (Qwen2-0.5B)  
**Recommended for testing**: 2 models (Qwen2-0.5B + MiniCPM4-0.5B)  
**Comprehensive testing**: 5 models (add Qwen3, Qwen2.5, TinyLLAMA)

**Next step**: Download Qwen2-0.5B-Instruct from the model zoo and we can start testing!
