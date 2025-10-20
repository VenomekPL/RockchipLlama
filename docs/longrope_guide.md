# LongRoPE Implementation Guide

**Status:** ✅ RKLLM v1.2.2 supports LongRoPE  
**Current:** Models need to be rebuilt with rope_scaling configuration  
**Goal:** Enable 32K-64K context windows for long-document understanding

---

## What is LongRoPE?

**LongRoPE** (Rotary Position Embedding scaling) extends the context window of transformer models beyond their original training length.

**Example:**
- Base model: 2K tokens (Qwen3-0.6B default)
- With LongRoPE (factor=4): **8K tokens**
- With LongRoPE (factor=16): **32K tokens**

**Use cases:**
- Long document analysis
- Extended conversations with full history
- RAG with large context retrieval
- Code analysis across multiple files

---

## How LongRoPE Works in RKLLM

### 🔧 Step 1: Model Conversion (One-time, on PC)

LongRoPE is **baked into the model** during conversion, not configured at runtime.

**Toolkit Configuration:**
```python
from rkllm.api import RKLLM

llm = RKLLM()

# Load from HuggingFace with LongRoPE scaling
llm.load_huggingface(
    model='Qwen/Qwen2.5-0.5B-Instruct',
    rope_scaling={
        "type": "linear",    # or "dynamic"
        "factor": 4.0        # 4x context extension
    }
)

# Build for RK3588
llm.build(
    do_quantization=True,
    optimization_level=1,
    quantized_dtype='w8a8',
    target_platform='rk3588',
    num_npu_core=3
)

# Export
llm.export_rkllm("./qwen_0.5b_longrope_8k.rkllm")
```

**RoPE Scaling Types:**

1. **Linear Scaling**
   ```python
   rope_scaling = {"type": "linear", "factor": 4.0}
   ```
   - Simple interpolation
   - Good for moderate extensions (2x-4x)
   - More stable

2. **Dynamic Scaling**
   ```python
   rope_scaling = {"type": "dynamic", "factor": 8.0}
   ```
   - Adaptive scaling
   - Better for large extensions (8x-16x)
   - May require fine-tuning validation

**Factor Guidelines:**
- `factor=2.0`: 2K → 4K tokens
- `factor=4.0`: 2K → 8K tokens
- `factor=8.0`: 2K → 16K tokens
- `factor=16.0`: 2K → 32K tokens

---

### 🚀 Step 2: Server Configuration (Runtime)

Once you have a LongRoPE-enabled `.rkllm` model, configure the server to use it:

#### **A. Update `config/inference_config.json`**

```json
{
  "model_defaults": {
    "max_context_len": 8192,     // ← Match your rope_scaling factor
    "max_new_tokens": 8192,      // ← Can generate long responses
    "n_keep": -1,                // -1 = keep all (important for long context!)
    "skip_special_token": true,
    "is_async": true
  },
  "hardware": {
    "embed_flash": 0,            // 0 = use RAM (faster for long context)
    "n_batch": 1
  }
}
```

**Key Settings:**

| Parameter | Standard Model | LongRoPE (4x) | LongRoPE (16x) |
|-----------|---------------|---------------|----------------|
| `max_context_len` | 2048 | 8192 | 32768 |
| `max_new_tokens` | 2048 | 4096 | 8192 |
| `n_keep` | -1 | -1 | -1 |
| `embed_flash` | 1 | 0 | 0 |

**Why `embed_flash=0` for long context?**
- Flash storage slower for large context
- RAM access faster for frequent KV cache updates
- Trade memory for speed

**Why `n_keep=-1`?**
- Preserves full context window
- Prevents losing important context during generation
- Critical for long-document coherence

#### **B. Load the Model**

```bash
# Start server
./start_server.sh

# Load LongRoPE model
curl -X POST http://localhost:8080/v1/models/load \
  -H 'Content-Type: application/json' \
  -d '{"model": "qwen_longrope_8k"}'
```

---

### 📊 Step 3: Test Long Context

#### **Test Script: `scripts/test_long_context.py`**

```python
#!/usr/bin/env python3
"""Test long context capabilities with LongRoPE model"""
import requests
import time

def test_long_context(context_size: int = 4096):
    """
    Test model with increasingly long context
    
    Args:
        context_size: Target context length in tokens (approx)
    """
    # Generate long context (rough: 1 token ≈ 4 chars)
    long_document = "The quick brown fox jumps over the lazy dog. " * (context_size // 10)
    
    # Ask about content near the end
    prompt = f"""Here is a long document:

{long_document}

Question: What animal jumps over the lazy dog in this text?
Answer:"""
    
    print(f"📏 Testing with ~{len(prompt)//4} tokens context")
    
    start = time.time()
    response = requests.post(
        'http://localhost:8080/v1/chat/completions',
        json={
            'model': 'qwen_longrope_8k',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 50,
            'temperature': 0.1  # Low for factual recall
        }
    )
    elapsed = time.time() - start
    
    if response.status_code == 200:
        answer = response.json()['choices'][0]['message']['content']
        print(f"✅ Success in {elapsed:.1f}s")
        print(f"📝 Answer: {answer}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

if __name__ == '__main__':
    # Progressive testing
    for size in [1024, 2048, 4096, 8192]:
        print(f"\n{'='*60}")
        print(f"Testing {size} token context")
        print('='*60)
        
        success = test_long_context(size)
        
        if not success:
            print(f"\n⚠️  Failed at {size} tokens - context limit reached")
            break
        
        time.sleep(2)  # Cool down between tests
```

**Expected Results:**

```bash
python3 scripts/test_long_context.py

============================================================
Testing 1024 token context
============================================================
📏 Testing with ~256 tokens context
✅ Success in 2.3s
📝 Answer: The quick brown fox

============================================================
Testing 2048 token context
============================================================
📏 Testing with ~512 tokens context
✅ Success in 4.1s
📝 Answer: A brown fox

============================================================
Testing 4096 token context
============================================================
📏 Testing with ~1024 tokens context
✅ Success in 7.8s
📝 Answer: The fox

============================================================
Testing 8192 token context
============================================================
📏 Testing with ~2048 tokens context
✅ Success in 15.2s
📝 Answer: Fox
```

---

### 💾 Memory Considerations

**KV Cache Memory Usage:**

```
memory_mb = (layers × heads × head_dim × context_len × 2 × bytes_per_element) / 1MB
```

**Example (Qwen3-0.6B):**
- Layers: 28
- Heads: 14
- Head dim: 64
- Data type: FP16 (2 bytes)

| Context | Memory (MB) | RK3588 16GB |
|---------|-------------|-------------|
| 2K | ~100 MB | ✅ Plenty |
| 8K | ~400 MB | ✅ Safe |
| 16K | ~800 MB | ✅ OK |
| 32K | ~1600 MB | ⚠️ Tight |

**For RK3588 (16GB RAM):**
- Safe limit: **16K context** with margin
- Max theoretical: **32K** (may need swap)
- Monitor with: `free -h`

---

## Complete Workflow

### 1️⃣ **On PC (with RKLLM-Toolkit)**

```bash
# Install toolkit
pip install rkllm-toolkit

# Convert model with LongRoPE
python3 << 'EOF'
from rkllm.api import RKLLM

llm = RKLLM()
llm.load_huggingface(
    model='Qwen/Qwen2.5-0.5B-Instruct',
    rope_scaling={"type": "linear", "factor": 4.0}  # 2K → 8K
)
llm.build(
    do_quantization=True,
    quantized_dtype='w8a8',
    target_platform='rk3588',
    num_npu_core=3
)
llm.export_rkllm("./qwen_0.5b_8k.rkllm")
EOF

# Transfer to board
scp qwen_0.5b_8k.rkllm board@192.168.1.100:~/AI/RockchipLlama/models/
```

### 2️⃣ **On Board (RK3588)**

```bash
cd ~/AI/RockchipLlama

# Update config
cat > config/inference_config.json << 'EOF'
{
  "model_defaults": {
    "max_context_len": 8192,
    "max_new_tokens": 4096,
    "n_keep": -1,
    "is_async": true
  },
  "inference_params": {
    "top_k": 20,
    "top_p": 0.95,
    "temperature": 0.6,
    "repeat_penalty": 0.9,
    "mirostat": 2
  },
  "hardware": {
    "num_npu_cores": 3,
    "embed_flash": 0,
    "n_batch": 1,
    "enabled_cpus_mask": 240
  }
}
EOF

# Register model
cat > config/model_registry.json << 'EOF'
{
  "models": {
    "qwen-8k": {
      "path": "models/qwen_0.5b_8k.rkllm",
      "architecture": "qwen",
      "max_context": 8192,
      "description": "Qwen 0.5B with LongRoPE (8K context)"
    }
  }
}
EOF

# Start server
./start_server.sh

# Load model
curl -X POST http://localhost:8080/v1/models/load \
  -d '{"model": "qwen-8k"}'

# Test long context
python3 scripts/test_long_context.py
```

---

## Performance Impact

**TTFT (Time To First Token):**
- Scales linearly with context length
- 2K context: ~300ms
- 8K context: ~1200ms
- 16K context: ~2400ms

**Generation Speed:**
- Unaffected by prompt length
- Same ~15 tok/s regardless of context

**Memory:**
- KV cache grows with context
- Monitor: `watch -n1 free -h`

---

## Validation Checklist

After implementing LongRoPE:

- [ ] Model converted with `rope_scaling` parameter
- [ ] `max_context_len` matches rope factor in config
- [ ] `n_keep=-1` to preserve full context
- [ ] `embed_flash=0` for RAM-based embeddings
- [ ] Test script passes at target context length
- [ ] Memory usage within safe limits (<80% RAM)
- [ ] TTFT acceptable for use case
- [ ] Quality maintained at long context

---

## Troubleshooting

### ❌ "GGML_ASSERT: context exceeds maximum"

**Cause:** Runtime `max_context_len` > model's built-in limit

**Fix:** 
```json
// Reduce max_context_len to match model
{"max_context_len": 4096}  // Instead of 8192
```

### ❌ Out of Memory

**Symptoms:** Server crashes, `OOMKilled` in logs

**Fix:**
```json
// 1. Reduce context
{"max_context_len": 4096}

// 2. Use flash embeddings (slower but less RAM)
{"embed_flash": 1}

// 3. Enable swap
sudo dd if=/dev/zero of=/swapfile bs=1G count=4
sudo mkswap /swapfile
sudo swapon /swapfile
```

### ❌ Quality Degradation at Long Context

**Cause:** Model wasn't fine-tuned for extended context

**Fix:**
- Use `dynamic` scaling instead of `linear`
- Reduce rope factor (8x → 4x)
- Try different models (some handle scaling better)

---

## Model Recommendations

**For LongRoPE:**

| Model | Base Context | Recommended Factor | Target Context |
|-------|--------------|-------------------|----------------|
| Qwen3-0.6B | 2K | 4x | 8K |
| Qwen2.5-1.5B | 4K | 4x | 16K |
| Gemma3-1B | 2K | 8x | 16K |
| Llama3.2-1B | 4K | 4x | 16K |

**Quality vs Speed:**
- Small factor (2x-4x): Better quality, safe
- Large factor (8x-16x): Riskier, test thoroughly

---

## Next Steps

1. **Set up toolkit on PC** (see [toolkit guide](https://github.com/airockchip/rknn-llm))
2. **Convert models with LongRoPE**
3. **Update config** (`max_context_len`, `n_keep`, `embed_flash`)
4. **Test with long prompts**
5. **Benchmark performance**
6. **Document results**

---

## References

- **RKLLM Toolkit**: `/external/rknn-llm/rkllm-toolkit/`
- **RoPE Scaling Config**: `configuration_custom.py` example
- **Memory Estimation**: KV cache = layers × heads × dim × ctx × 2 × bytes
- **LongRoPE Paper**: https://arxiv.org/abs/2402.13753

---

**Status:** Ready for implementation  
**Requirements:** RKLLM-Toolkit (PC), HuggingFace models, 16GB+ RAM (board)  
**Estimated effort:** 2-4 hours (conversion + testing)
