# LongRoPE Quick Start

**What you need to do to enable long context (8K-32K tokens):**

## 1️⃣ On Your PC (with RKLLM-Toolkit)

```python
from rkllm.api import RKLLM

# Initialize
llm = RKLLM()

# Load model WITH LongRoPE
llm.load_huggingface(
    model='Qwen/Qwen2.5-0.5B-Instruct',
    rope_scaling={
        "type": "linear",  # or "dynamic"
        "factor": 4.0      # 2K → 8K context
    }
)

# Build for your board
llm.build(
    do_quantization=True,
    quantized_dtype='w8a8',
    target_platform='rk3588',
    num_npu_core=3
)

# Export
llm.export_rkllm("./qwen_0.5b_longrope_8k.rkllm")
```

**Scaling factors:**
- `factor=2.0`: 2K → 4K tokens
- `factor=4.0`: 2K → 8K tokens  ⭐ **RECOMMENDED**
- `factor=8.0`: 2K → 16K tokens
- `factor=16.0`: 2K → 32K tokens (may need validation)

## 2️⃣ Transfer Model to Board

```bash
scp qwen_0.5b_longrope_8k.rkllm board@YOUR_IP:~/AI/RockchipLlama/models/
```

## 3️⃣ Update Config on Board

Edit `config/inference_config.json`:

```json
{
  "model_defaults": {
    "max_context_len": 8192,    // ← MATCH YOUR ROPE FACTOR
    "max_new_tokens": 4096,
    "n_keep": -1,               // ← KEEP ALL CONTEXT
    "is_async": true
  },
  "hardware": {
    "embed_flash": 0,           // ← USE RAM (faster)
    "n_batch": 1
  }
}
```

## 4️⃣ Load and Test

```bash
# Start server
./start_server.sh

# Load LongRoPE model
curl -X POST http://localhost:8080/v1/models/load \
  -d '{"model": "qwen_0.5b_longrope_8k"}'

# Test long context
python3 scripts/test_long_context.py --max-size 8192
```

## Expected Results

```
📋 Testing 8,192 token context
📏 Testing ~2,048 tokens (8,192 chars)
✅ Perfect recall in 7.2s
   Answer: LONGROPE8192

📊 Maximum working context: 8,192 tokens
```

---

## That's It! 🎉

**Three key changes on the board:**
1. `max_context_len: 8192` (match rope factor)
2. `n_keep: -1` (preserve full context)
3. `embed_flash: 0` (use RAM not flash)

**Everything else is in the model file** (built on PC with toolkit).

---

See **[docs/longrope_guide.md](longrope_guide.md)** for full details!
