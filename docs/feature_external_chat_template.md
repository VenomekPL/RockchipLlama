# Feature: External Chat Template File Loading

## Overview

External chat template loading allows users to define custom chat formatting rules in separate files rather than hardcoding them. This enables support for any model's chat format without code changes, making it easy to add new models and customize conversation formatting for specific use cases. The rknn-llm v1.2.3 specifically added "support for loading chat template from an external file."

## Current Status

**Partially Implemented** — Code exists but is disabled.

In `src/models/rkllm_model.py`:

```python
# Lines ~503-537: set_chat_template method exists
def set_chat_template(self, system_prompt, prefix, postfix):
    # Calls rkllm_set_chat_template if available (v1.2.1+)

# Lines ~461-465: Disabled to avoid interference with manual formatting
# Chat template is NOT set via RKLLM API; instead, manual ChatML
# formatting is done in openai_routes.py
```

**Current approach**: RockchipLlama manually formats prompts as ChatML in `openai_routes.py`:

```python
# From openai_routes.py ~line 110-170
def format_chat_prompt(messages):
    # Hardcoded ChatML format:
    # <|im_start|>system\n{content}<|im_end|>
    # <|im_start|>user\n{content}<|im_end|>
    # <|im_start|>assistant
```

This works for Qwen-family models (which use ChatML) but doesn't support other formats like Llama, Gemma, or Phi chat templates.

## rknn-llm Reference

### C API

```c
// From rkllm.h (lines 367-380)
// Sets the chat template with system prompt, prefix, and postfix
int rkllm_set_chat_template(LLMHandle handle,
                             const char* system_prompt,
                             const char* prompt_prefix,
                             const char* prompt_postfix);
```

### rknn-llm v1.2.3 Feature

v1.2.3 release notes state: "Added support for loading chat template from an external file." This implies the RKLLM runtime can now read chat template configurations from a file path, making it easier to support new model formats.

### Reference Server Code (from `flask_server.py`)

```python
# Chat template configuration (commented out as example)
system_prompt = "<|im_start|>system You are a helpful assistant. <|im_end|>"
prompt_prefix = "<|im_start|>user"
prompt_postfix = "<|im_end|><|im_start|>assistant"
self.set_chat_template(
    self.handle,
    ctypes.c_char_p(system_prompt.encode('utf-8')),
    ctypes.c_char_p(prompt_prefix.encode('utf-8')),
    ctypes.c_char_p(prompt_postfix.encode('utf-8'))
)
```

## Implementation Plan

### Step 1: Create Chat Template File Format

Define a JSON-based chat template file format stored alongside models:

```json
{
  "name": "chatml",
  "description": "ChatML format used by Qwen, Yi, and others",
  "system_prefix": "<|im_start|>system\n",
  "system_suffix": "<|im_end|>\n",
  "user_prefix": "<|im_start|>user\n",
  "user_suffix": "<|im_end|>\n",
  "assistant_prefix": "<|im_start|>assistant\n",
  "assistant_suffix": "<|im_end|>\n",
  "tool_prefix": "<|im_start|>tool\n",
  "tool_suffix": "<|im_end|>\n",
  "default_system_prompt": "You are a helpful assistant.",
  "stop_sequences": ["<|im_end|>", "<|endoftext|>"],
  "bos_token": "",
  "eos_token": "<|im_end|>"
}
```

### Step 2: Create Template Library

Provide built-in templates for common model families:

```
config/chat_templates/
├── chatml.json          # Qwen, Yi, OpenChat
├── llama3.json          # Llama 3 / 3.1 / 3.2
├── gemma.json           # Gemma 2 / 3
├── phi3.json            # Phi-3 / Phi-3.5
├── deepseek.json        # DeepSeek models
└── plain.json           # No formatting (raw prompt)
```

### Step 3: Implement Template Loader

```python
class ChatTemplate:
    def __init__(self, template_path: str):
        with open(template_path) as f:
            self.config = json.load(f)

    def format_messages(self, messages: list[dict]) -> str:
        """Format a list of messages using the template."""
        formatted = ""
        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "")
            prefix = self.config.get(f"{role}_prefix", "")
            suffix = self.config.get(f"{role}_suffix", "")
            formatted += f"{prefix}{content}{suffix}"
        # Add assistant trigger
        formatted += self.config.get("assistant_prefix", "")
        return formatted

    @property
    def stop_sequences(self) -> list[str]:
        return self.config.get("stop_sequences", [])
```

### Step 4: Integrate with RKLLM API

Two approaches:

**Approach A: Use `rkllm_set_chat_template()` (RKLLM-native)**

```python
def apply_template_to_rkllm(self, template: ChatTemplate):
    system = template.config["default_system_prompt"]
    prefix = template.config["user_prefix"]
    postfix = template.config["user_suffix"] + template.config["assistant_prefix"]
    self._set_chat_template(self.handle,
        system.encode('utf-8'), prefix.encode('utf-8'), postfix.encode('utf-8'))
```

**Approach B: Python-side formatting (current approach, more flexible)**

Keep formatting in Python but use template configs instead of hardcoded ChatML:

```python
# In openai_routes.py
template = ChatTemplate(model_template_path)
formatted_prompt = template.format_messages(request.messages)
```

### Step 5: Auto-detect Template from Model

Add template auto-detection based on model name:

```python
TEMPLATE_MAP = {
    "qwen": "chatml",
    "llama": "llama3",
    "gemma": "gemma",
    "phi": "phi3",
    "deepseek": "deepseek",
}

def detect_template(model_name: str) -> str:
    for key, template in TEMPLATE_MAP.items():
        if key in model_name.lower():
            return template
    return "chatml"  # default
```

### Step 6: Add Configuration Option

In `config/inference_config.json`:

```json
{
  "chat_template": {
    "auto_detect": true,
    "default_template": "chatml",
    "custom_template_path": null,
    "override_per_model": {
      "qwen3-0.6b": "chatml",
      "llama3-8b": "llama3"
    }
  }
}
```

## Goals

1. Support loading chat templates from external JSON files.
2. Provide built-in templates for all models supported by rknn-llm.
3. Auto-detect template based on model name.
4. Allow per-model template override in configuration.
5. Replace hardcoded ChatML formatting with configurable templates.

## Definition of Done

- [ ] Chat template JSON format defined and documented.
- [ ] Built-in templates created for: ChatML, Llama 3, Gemma, Phi, DeepSeek.
- [ ] `ChatTemplate` class loads and applies templates from files.
- [ ] `format_chat_prompt()` in `openai_routes.py` uses template instead of hardcoded ChatML.
- [ ] Template auto-detection based on model name works.
- [ ] Custom template path supported in config.
- [ ] Stop sequences loaded from template and used in inference.
- [ ] `rkllm_set_chat_template()` API optionally used when RKLLM-native formatting is preferred.
- [ ] Template applied correctly for all roles: system, user, assistant, tool.
- [ ] Existing ChatML behavior preserved as default (no regression).

## Test Approach

### Unit Tests

- Test template loading from JSON file.
- Test `format_messages()` produces correct output for each template type.
- Test auto-detection maps model names to correct templates.
- Test fallback to default template for unknown models.
- Test stop sequence extraction from template.

### Integration Tests

- Format a multi-turn conversation with each template and verify structure.
- Test that changing template config changes the prompt format sent to RKLLM.
- Test custom template file path loading.

### Manual Testing

```bash
# Test with different templates by modifying config
# config/inference_config.json: "default_template": "llama3"

# Verify prompt format in debug mode
export RKLLM_LOG_LEVEL=1
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-0.6b",
    "messages": [
      {"role": "system", "content": "You are helpful."},
      {"role": "user", "content": "Hello"}
    ]
  }'
# Check server logs for the formatted prompt
```

## References

- [Hugging Face Chat Templates](https://huggingface.co/docs/transformers/main/en/chat_templating)
- [OpenAI Chat Format](https://platform.openai.com/docs/guides/text-generation/chat-completions-api)
- RKLLM Chat Template API: `external/rknn-llm/rkllm-runtime/Linux/librkllm_api/include/rkllm.h` (lines 367-380)
- rknn-llm v1.2.3 release: "Added support for loading chat template from an external file"
- Current hardcoded formatting: `src/api/openai_routes.py` (lines ~110-170)
- Existing disabled code: `src/models/rkllm_model.py` (lines ~503-537)
- RKLLM SDK Documentation: `external/rknn-llm/doc/Rockchip_RKLLM_SDK_EN_1.2.3.pdf`
