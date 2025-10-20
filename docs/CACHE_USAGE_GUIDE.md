# Prompt Caching System - User Guide

## 🚀 Overview

The RockchipLlama prompt caching system allows you to **reuse previously processed prompts** to significantly reduce Time-To-First-Token (TTFT) and improve overall performance.

### Key Features

✅ **Multi-Cache Support** - Combine multiple cached prompts in a single request  
✅ **Automatic System Cache** - Default system prompt is always cached automatically  
✅ **Flexible Combination** - Mix cached and non-cached content seamlessly  
✅ **Cache Tracking** - Know exactly which caches were used in each response  
✅ **Model-Specific** - Each model has its own cache directory  

---

## 🎯 How It Works

### Single Cache File Limitation (RKLLM)

The RKLLM runtime supports **ONE cache file per inference call**:

```c
struct RKLLMPromptCacheParam {
    int save_prompt_cache;      // 1 = save cache
    char* prompt_cache_path;    // Single path (not an array!)
}
```

### Our Solution: Application-Level Combination

We work around this limitation by **concatenating multiple caches** at the application layer before sending to RKLLM:

```
User Request with cache_prompts: ["coding_rules", "project_context"]
         ↓
Application loads and combines:
  1. system (auto-loaded)
  2. coding_rules
  3. project_context
         ↓
Combined prompt sent to RKLLM:
  "system content\n\ncoding_rules content\n\nproject_context content\n\nuser message"
```

---

## 📖 Usage Examples

### Example 1: No Cache (System Cache Auto-Applied)

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-0.6b",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

**What Happens:**
- System cache is automatically loaded
- User message is appended
- Response includes: `"cached_prompts": ["system"]`

---

### Example 2: Single Additional Cache

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-0.6b",
    "messages": [
      {"role": "user", "content": "Write a Python function"}
    ],
    "cache_prompts": "coding_rules"
  }'
```

**What Happens:**
- System cache loaded first
- "coding_rules" cache loaded second
- Combined: `system + coding_rules + user_message`
- Response includes: `"cached_prompts": ["system", "coding_rules"]`

---

### Example 3: Multiple Caches (Recommended!)

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-0.6b",
    "messages": [
      {"role": "user", "content": "Implement the login feature"}
    ],
    "cache_prompts": ["coding_rules", "project_context", "api_docs"]
  }'
```

**What Happens:**
- Loads in order: system → coding_rules → project_context → api_docs
- All concatenated with `\n\n` separators
- Response includes: `"cached_prompts": ["system", "coding_rules", "project_context", "api_docs"]`

---

## 🔍 Cache Order & Precedence

Caches are **always loaded in this order**:

1. **System** (automatic, first position)
2. **User-specified caches** (in the order provided)
3. **User message** (last position)

### Example Flow:

```python
cache_prompts = ["coding_rules", "project_context"]

# Final prompt structure:
"""
{system cache content}

{coding_rules cache content}

{project_context cache content}

User: Implement the login feature
"""
```

---

## 📊 Response Metadata

Every response includes cache tracking in the `usage` object:

```json
{
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 50,
    "total_tokens": 200,
    "cached_prompts": ["system", "coding_rules", "project_context"],
    "cache_hit": true
  }
}
```

**Fields:**
- `cached_prompts` - Array of cache names that were applied
- `cache_hit` - `true` if any caches were used, `false` if none

---

## 🛠️ Managing Caches

### List All Caches

```bash
# All models
curl http://localhost:8080/v1/cache

# Specific model
curl http://localhost:8080/v1/cache/qwen3-0.6b
```

### Get Cache Details

```bash
curl http://localhost:8080/v1/cache/qwen3-0.6b/system | jq .
```

**Response:**
```json
{
  "object": "cache",
  "model": "qwen3-0.6b",
  "cache_name": "system",
  "metadata": {
    "cache_name": "system",
    "model_name": "qwen3-0.6b",
    "created_at": 1760978881.11,
    "content_length": 1326,
    "source": "/path/to/config/system.txt"
  },
  "content": "You are a virtual voice assistant...",
  "content_preview": "You are a virtual voice assistant..."
}
```

### Create Custom Cache

**(Coming Soon)**

```bash
curl -X POST http://localhost:8080/v1/cache/qwen3-0.6b \
  -H "Content-Type: application/json" \
  -d '{
    "cache_name": "coding_rules",
    "content": "You are an expert Python developer. Always follow PEP 8..."
  }'
```

### Delete Cache

```bash
curl -X DELETE http://localhost:8080/v1/cache/qwen3-0.6b/coding_rules
```

**Note:** System cache cannot be deleted (auto-regenerates on next load)

---

## 💡 Use Cases

### Use Case 1: Coding Assistant

```json
{
  "cache_prompts": ["coding_rules", "style_guide", "project_structure"],
  "messages": [{"role": "user", "content": "Add error handling"}]
}
```

**Benefit:** Consistent coding standards across all responses

### Use Case 2: Customer Support

```json
{
  "cache_prompts": ["company_policies", "product_info", "faq"],
  "messages": [{"role": "user", "content": "How do I return an item?"}]
}
```

**Benefit:** Accurate, policy-compliant responses

### Use Case 3: Creative Writing

```json
{
  "cache_prompts": ["story_outline", "character_profiles", "world_building"],
  "messages": [{"role": "user", "content": "Continue the story"}]
}
```

**Benefit:** Maintain consistency in long-form content

### Use Case 4: Technical Documentation

```json
{
  "cache_prompts": ["api_reference", "code_examples", "best_practices"],
  "messages": [{"role": "user", "content": "Explain the authentication flow"}]
}
```

**Benefit:** Accurate, comprehensive technical answers

---

## ⚡ Performance Impact

### Expected Improvements (with caching):

| Scenario | TTFT Reduction | Notes |
|----------|---------------|-------|
| System prompt only | 30-50% | ~200-300 tokens cached |
| System + 1 custom cache | 50-70% | ~500-1000 tokens cached |
| System + 2-3 custom caches | 60-80% | ~1000-2000 tokens cached |

### Example Benchmark:

**Without Caching:**
- TTFT: 214ms
- Prompt: "User: Hello"

**With System Cache:**
- TTFT: ~107ms (50% reduction)
- Prompt: "System (1326 chars) + User: Hello"

**With Multiple Caches:**
- TTFT: ~64ms (70% reduction)
- Prompt: "System + Coding Rules + Project Context + User: Hello"

---

## 🔧 Technical Details

### File Structure

```
cache/
├── qwen3-0.6b/
│   ├── system.bin           # Binary cache content
│   ├── system.json          # Metadata
│   ├── coding_rules.bin
│   ├── coding_rules.json
│   ├── project_context.bin
│   └── project_context.json
├── qwen3-4b/
│   └── ...
└── gemma3-1b/
    └── ...
```

### Metadata Format

```json
{
  "cache_name": "coding_rules",
  "model_name": "qwen3-0.6b",
  "created_at": 1760978881.11,
  "content_length": 2450,
  "source": "manual_creation"
}
```

### Cache Loading Process

1. **Parse Request** - Extract `cache_prompts` from request
2. **Normalize** - Convert single string to array
3. **Load System** - Always load system cache first
4. **Load Custom** - Load user-specified caches in order
5. **Concatenate** - Join with `\n\n` separators
6. **Track** - Record which caches were loaded
7. **Send to RKLLM** - Combined prompt sent for inference
8. **Return Metadata** - Response includes `cached_prompts` array

---

## ❓ FAQ

### Q: Can I disable the system cache?

**A:** Not currently. The system cache is always applied automatically. This ensures consistent behavior and baseline performance.

### Q: What happens if a cache doesn't exist?

**A:** The system logs a warning and continues with the caches that do exist:
```
[CACHE] Warning: 'nonexistent_cache' not found for model 'qwen3-0.6b'
```

### Q: Can I use the same cache with different models?

**A:** No. Caches are model-specific. You need to create separate caches for each model.

### Q: How large can caches be?

**A:** There's no hard limit, but keep in mind:
- Larger caches = slower loading
- Recommended: 500-5000 chars per cache
- Total cached content should fit in context window

### Q: Can I mix cached and non-cached messages?

**A:** Yes! Caches are prepended to your messages. Example:
```
[system cache] + [custom caches] + [your messages]
```

### Q: Will caches expire?

**A:** Currently, no. Caches persist until manually deleted.

---

## 🚦 Best Practices

### ✅ DO:

- **Use system cache automatically** - It's always applied
- **Combine related caches** - Group logically related content
- **Keep caches focused** - One cache per topic/domain
- **Order matters** - Most general → most specific
- **Monitor cache usage** - Check `cached_prompts` in responses

### ❌ DON'T:

- **Don't duplicate content** - Avoid overlapping cache content
- **Don't over-cache** - Too many caches can slow down loading
- **Don't put user data in caches** - Caches are static, shared content
- **Don't create huge caches** - Keep them under 5000 chars

---

## 📚 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/cache` | GET | List all caches (all models) |
| `/v1/cache/{model}` | GET | List caches for specific model |
| `/v1/cache/{model}/{cache}` | GET | Get cache details + content |
| `/v1/cache/{model}/{cache}` | POST | Create new cache *(coming soon)* |
| `/v1/cache/{model}/{cache}` | DELETE | Delete cache (except system) |

---

## 🎯 Next Steps

Want to dive deeper? Check out:

- [PHASE_4_1_PROGRESS.md](./PHASE_4_1_PROGRESS.md) - Implementation details
- [PROMPT_CACHING_RESEARCH.md](./PROMPT_CACHING_RESEARCH.md) - Technical research
- [PHASE_4_1_TEST_RESULTS.md](./PHASE_4_1_TEST_RESULTS.md) - Test results

---

**Last Updated:** October 20, 2025  
**Version:** 1.0 (Phase 4.1)  
**Status:** ✅ Multi-cache support implemented
