# Feature: Function Calling / Tool Use

## Overview

Function calling (also known as "tool use") allows the LLM to recognize when a user's request requires calling an external function, generate a structured JSON call specification, and then incorporate the function result back into its response. This is a critical feature for building AI agents and integrating LLMs with external APIs, databases, and services.

## Current Status

**Not Implemented** — RockchipLlama does not currently support function calling.

- The `MessageRole` enum in `src/api/schemas.py` defines a `tool = "tool"` role, but it is never used in request processing.
- No endpoint parses tool/function specifications from requests.
- No logic extracts `<tool_call>` blocks from model output.
- No mechanism injects tool results back into the conversation context.
- The RKLLM runtime (v1.2.1+) fully supports function calling via `rkllm_set_function_tools()`.

## rknn-llm Reference Implementation

The rknn-llm submodule provides a complete reference implementation in:

- **Server**: `external/rknn-llm/examples/rkllm_server_demo/rkllm_server/flask_server.py`
- **Client**: `external/rknn-llm/examples/rkllm_server_demo/chat_api_flask.py`
- **C API**: `rkllm_set_function_tools()` in `external/rknn-llm/rkllm-runtime/Linux/librkllm_api/include/rkllm.h` (line 392)

### Key C API

```c
// Sets function calling configuration for the LLM
// system_prompt: context prompt for the model
// tools: JSON string defining available functions
// tool_response_str: marker tag for tokenizer to recognize tool outputs
int rkllm_set_function_tools(LLMHandle handle, const char* system_prompt,
                              const char* tools, const char* tool_response_str);
```

### Reference Client Code (from `chat_api_flask.py`)

```python
TOOLS = [
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
                        "description": "The location to get the temperature for."
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit. Defaults to celsius."
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# Send request with tools
data = {
    "model": "qwen3-0.6b",
    "messages": messages,
    "stream": False,
    "enable_thinking": False,
    "tools": TOOLS
}
response = session.post(server_url, json=data)

# Parse tool calls from response
server_answer = response.json()["choices"][-1]["message"]["content"]
matches = re.findall(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", server_answer, re.DOTALL)
tool_calls = [json.loads(match) for match in matches]

# Execute functions and send results back
for call in tool_calls:
    fn_result = execute_function(call["name"], call["arguments"])
    messages.append({"role": "tool", "name": call["name"], "content": json.dumps(fn_result)})
```

### Reference Server Code (from `flask_server.py`)

```python
# Server-side: configure function tools before inference
if TOOLS is not None:
    rkllm_model.set_function_tools(
        system_prompt=system_prompt,
        tools=json.dumps(TOOLS),
        tool_response_str="tool_response"
    )

# Process tool role messages
if message['role'] == 'tool':
    input_prompt.append(message['content'])
```

## Implementation Plan

### Step 1: Extend Pydantic Schemas

Add tool-related fields to request/response schemas in `src/api/schemas.py`:

```python
class FunctionDefinition(BaseModel):
    name: str
    description: str
    parameters: dict

class ToolDefinition(BaseModel):
    type: str = "function"
    function: FunctionDefinition

class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: dict  # {"name": str, "arguments": str}

# Add to ChatCompletionRequest:
class ChatCompletionRequest(BaseModel):
    # ... existing fields ...
    tools: Optional[List[ToolDefinition]] = None
    tool_choice: Optional[str] = None  # "auto", "none", or specific function

# Add to response message:
class ChatMessage(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
```

### Step 2: Bind `rkllm_set_function_tools` in RKLLM Wrapper

In `src/models/rkllm_model.py`, add the ctypes binding:

```python
# In RKLLMModel.__init__ or load():
self._set_function_tools = self.lib.rkllm_set_function_tools
self._set_function_tools.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                      ctypes.c_char_p, ctypes.c_char_p]
self._set_function_tools.restype = ctypes.c_int

def set_function_tools(self, system_prompt: str, tools_json: str,
                        tool_response_str: str = "tool_response"):
    ret = self._set_function_tools(
        self.handle,
        system_prompt.encode('utf-8'),
        tools_json.encode('utf-8'),
        tool_response_str.encode('utf-8')
    )
    if ret != 0:
        raise RuntimeError(f"rkllm_set_function_tools failed with code {ret}")
```

### Step 3: Add Tool Call Extraction Logic

Create a utility to parse `<tool_call>` blocks from model output:

```python
import re
import json

def extract_tool_calls(content: str) -> list[dict]:
    """Extract tool calls from model output containing <tool_call> blocks."""
    matches = re.findall(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", content, re.DOTALL)
    tool_calls = []
    for i, match in enumerate(matches):
        parsed = json.loads(match)
        tool_calls.append({
            "id": f"call_{i}",
            "type": "function",
            "function": {
                "name": parsed["name"],
                "arguments": json.dumps(parsed.get("arguments", {}))
            }
        })
    return tool_calls
```

### Step 4: Update OpenAI Routes

In `src/api/openai_routes.py`, modify the chat completion endpoint:

1. Extract tools from request and call `set_function_tools()` before inference.
2. After inference, check if response contains `<tool_call>` blocks.
3. If tool calls found, return them in OpenAI-compatible format with `finish_reason: "tool_calls"`.
4. Handle `tool` role messages in follow-up requests.

### Step 5: Update Ollama Routes

Mirror the function calling support in `src/api/ollama_routes.py` using Ollama's tool format.

## Goals

1. Full OpenAI-compatible function calling via `/v1/chat/completions`.
2. Support for multiple tools per request.
3. Support for multi-step tool use (call → result → continue).
4. Streaming support with tool call chunks.
5. Ollama API tool calling parity.

## Definition of Done

- [ ] `tools` parameter accepted in chat completion requests.
- [ ] `rkllm_set_function_tools()` called before inference when tools are provided.
- [ ] Model output containing `<tool_call>` blocks is parsed and returned as structured `tool_calls` in the response.
- [ ] `finish_reason` is set to `"tool_calls"` when the model requests function calls.
- [ ] `tool` role messages are correctly forwarded to the model in follow-up requests.
- [ ] Multi-turn tool use works (user → tool_call → tool_result → final answer).
- [ ] Streaming responses correctly handle tool call chunks.
- [ ] Both OpenAI and Ollama endpoints support function calling.
- [ ] Error handling for malformed tool definitions and invalid tool responses.

## Test Approach

### Unit Tests

- Test `extract_tool_calls()` with various model output formats (single call, multi-call, malformed).
- Test schema validation for `ToolDefinition` and `ToolCall` models.
- Test prompt formatting with tool specifications.

### Integration Tests

- Send a request with tools and verify `rkllm_set_function_tools()` is called.
- Mock RKLLM output containing `<tool_call>` blocks and verify parsed response.
- Test full multi-turn flow: user query → tool call response → tool result → final answer.
- Test streaming with tool calls.

### Manual Testing

```bash
# Test function calling
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-0.6b",
    "messages": [{"role": "user", "content": "What is the weather in Paris?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
          "type": "object",
          "properties": {"location": {"type": "string"}},
          "required": ["location"]
        }
      }
    }]
  }'
```

## References

- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [OpenAI Chat Completions API - Tools](https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools)
- rknn-llm flask client: `external/rknn-llm/examples/rkllm_server_demo/chat_api_flask.py`
- rknn-llm flask server: `external/rknn-llm/examples/rkllm_server_demo/rkllm_server/flask_server.py`
- RKLLM C API: `external/rknn-llm/rkllm-runtime/Linux/librkllm_api/include/rkllm.h` (lines 382-392)
- RKLLM SDK Documentation: `external/rknn-llm/doc/Rockchip_RKLLM_SDK_EN_1.2.3.pdf`
