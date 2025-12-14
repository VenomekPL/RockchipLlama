# RockchipLlama Design Document

## 📋 Documentation Guidelines for AI Assistants

**IMPORTANT: All documentation files MUST be kept in the `docs/` folder.**

### Critical Development Environment Rules:
1. ⚠️ **ALWAYS activate virtual environment before running Python scripts**
   ```bash
   source venv/bin/activate
   # Then run: python scripts/benchmark.py, etc.
   ```
2. 🛑 **DO NOT START THE SERVER AUTOMATICALLY**
   - Never run `./start_server.sh` or `python src/main.py` via tool/command.
   - **ALWAYS ask the user to start the server** in a separate terminal.
   - The server is long-running and blocks the terminal, interfering with other agent tasks.
3. ⚠️ **Use `python` not `python3` when venv is activated**
4. ⚠️ **Check if venv is active: prompt shows `(venv)` prefix**

### Documentation Organization Rules:
1. ✅ **Keep all `.md` documentation files in `docs/` folder**
2. ✅ **Update existing documentation rather than creating new phase files**
3. ✅ **Use `copilot.md` as the central design document and session log**
4. ✅ **Update session notes at the end of each work session**
5. ❌ **Do NOT create separate PHASE*.md files - consolidate into copilot.md**
6. ❌ **Do NOT create separate SUMMARY.md files - update copilot.md instead**

### Existing Documentation Structure:
```
docs/
├── copilot.md              # Central design doc + session notes (THIS FILE)
├── rkllm.md                # RKLLM runtime API documentation
├── QUICKSTART.md           # Getting started guide
├── MODEL_MANAGEMENT.md     # Model lifecycle management
├── BENCHMARKING.md         # Performance benchmarking guide
├── BENCHMARK_QUICKREF.md   # Quick reference for benchmarks
└── benchmark_prompts.json  # Test prompts library
```

### When to Update Which File:
- **copilot.md**: Design decisions, session notes, phase progress, architecture changes
- **QUICKSTART.md**: User-facing setup and first-run instructions
- **MODEL_MANAGEMENT.md**: How to use model management APIs
- **BENCHMARKING.md**: How to run benchmarks and interpret results
- **rkllm.md**: Technical RKLLM runtime documentation

## Quick Links
- 📖 [RKLLM Runtime Documentation](./rkllm.md) - Detailed analysis of RKLLM API, parameters, and capabilities
- 🔗 [External Repository](../external/rknn-llm/) - Rockchip RKNN-LLM submodule
- 📝 [Project README](../README.md) - Project overview and getting started
- 🚀 [Quickstart Guide](./QUICKSTART.md) - Getting started
- 🔧 [Model Management](./MODEL_MANAGEMENT.md) - Model lifecycle
- 📊 [Benchmarking](./BENCHMARKING.md) - Performance testing

## Project Synopsis

RockchipLlama is a Docker-centric REST API server designed to provide OpenAI and Ollama API compatibility while leveraging Rockchip's Neural Processing Unit (NPU) capabilities for efficient large language model inference on ARM64 architecture.

### Core Objectives
- Provide REST API compatibility with OpenAI and Ollama specifications
- Optimize performance using Rockchip RK3588 and RKNN-LLM based NPU acceleration
- Containerized deployment for easy distribution and scaling
- ARM64 architecture optimization
- Seamless integration with existing LLM applications

## Repository Structure

```
RockchipLlama/
├── .git/
├── .gitignore
├── .gitmodules          # Git submodule configuration
├── README.md            # Project overview
├── docs/                # ALL DOCUMENTATION GOES HERE
│   ├── copilot.md              # This design document + session notes
│   ├── rkllm.md                # RKLLM runtime API documentation
│   ├── QUICKSTART.md           # Getting started guide
│   ├── MODEL_MANAGEMENT.md     # Model management guide
│   ├── BENCHMARKING.md         # Benchmarking guide
│   └── BENCHMARK_QUICKREF.md   # Benchmark quick reference
├── external/           # External dependencies
│   └── rknn-llm/       # Rockchip RKNN-LLM submodule
│       ├── examples/
│       │   ├── rkllm_server_demo/
│       │   │   ├── chat_api_flask.py
│       │   │   └── chat_api_gradio.py
│       │   ├── rkllm_api_demo/
│       │   └── multimodal_model_demo/
│       ├── rkllm-runtime/
│       ├── rkllm-toolkit/
│       └── rknpu-driver/
├── models/             # Model storage directory
│   ├── Qwen_Qwen3-0.6B-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm
│   ├── gemma-3-1b-it_w8a8.rkllm
│   └── google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm
├── src/                # FastAPI application source
│   ├── main.py         # FastAPI entry point
│   ├── api/
│   │   ├── openai_routes.py    # OpenAI-compatible endpoints
│   │   ├── model_routes.py     # Model management API
│   │   └── schemas.py          # Pydantic data models
│   ├── models/
│   │   ├── model_manager.py    # Singleton model manager
│   │   └── rkllm_model.py      # RKLLM runtime wrapper
│   └── config/
│       ├── settings.py         # Configuration management
│       └── benchmark_prompts.json # Test prompts library
├── scripts/            # Test and benchmark scripts
│   ├── benchmark.py            # Comprehensive benchmark suite
│   ├── test_benchmark.py       # Quick benchmark test
│   ├── test_api.py             # API endpoint tests
│   └── test_model_management.py    # Model management tests
├── start_server.sh     # Server startup script
├── venv/               # Python virtual environment
├── requirements.txt    # Python dependencies
└── Dockerfile          # Docker configuration (Phase 5)
```

## Implementation Plan

### Phase 1: Foundation and Setup
- [x] Repository initialization
- [x] Basic project structure
- [x] Documentation framework
- [x] External repository integration (drivers, runtime, examples)
  - Added rknn-llm as git submodule in `/external/rknn-llm/`
  - Includes: runtime libraries, toolkit, NPU drivers, Flask/Gradio example servers
- [x] Created `/models/` folder for model storage
- [x] RKLLM runtime analysis and documentation
  - Analyzed Flask and Gradio server implementations from examples
  - Reviewed official SDK documentation (v1.2.2 PDF)
  - Documented complete API structure, parameters, and capabilities
  - Identified key v1.2.1/v1.2.2 features:
    - Multi-instance inference (multiple models simultaneously)
    - Multi-batch inference (concurrent request processing)
    - Thinking mode for reasoning models
    - Function calling with OpenAI-style tool definitions
    - GPU prefill acceleration option
    - Custom model conversion support
    - PC simulation and accuracy testing
  - See [RKLLM Documentation](./rkllm.md) for comprehensive analysis
- [x] Technology stack decisions
  - Selected FastAPI for REST API framework
  - See [Technology Decisions](#technology-decisions-finalized) for rationale
- [x] Model acquisition
  - ✅ Downloaded 3 production-ready models to `/models/`
  - ✅ Qwen3-0.6B (w8a8-opt0-hybrid0-npu3-ctx16384) - 16K context!
  - ✅ Gemma-3-1B-it (w8a8) - Instruction-tuned variant
  - ✅ Gemma-3-270M (w8a8-opt0-hybrid0-npu3-ctx16384) - Blazing fast, 16K context!
- [ ] Development environment configuration
  - Strategy decided: Hybrid approach (venv now, Docker later)
  - See [Development Strategy](#development-strategy-hybrid-approach) below
- [ ] Docker environment setup (deferred to Phase 2)

### Phase 2: FastAPI Server Development (COMPLETED ✅)
- [x] Python virtual environment setup
- [x] FastAPI project structure creation
- [x] OpenAI-compatible schemas (Pydantic models)
- [x] Basic /v1/chat/completions endpoint (placeholder responses)
- [x] /v1/models endpoint (lists 3 downloaded models)
- [x] /v1/health endpoint
- [x] RKLLM model wrapper skeleton created
- [x] Error handling and logging
- [x] Test script created and validated
- [x] Interactive API docs at /docs
- [x] Modular structure: separate routing (main.py) and API logic (openai_routes.py)
- **Status**: Server running successfully on port 8080
- **Next**: RKLLM runtime integration for real inference

### Phase 3: RKLLM Runtime Integration (COMPLETED ✅)
- [x] Study Flask reference implementation
- [x] Extract RKLLM ctypes bindings from Flask example
- [x] Implement rkllm_init() in rkllm_model.py
- [x] Implement rkllm_run() for inference
- [x] Add streaming callback support
- [x] Test with Gemma-3-270M model (REMOVED - quality failure)
- [x] Test with Qwen3-0.6B model (15.59 tok/s - PRODUCTION READY)
- [x] Test with Gemma3-1B model (13.50 tok/s - USABLE)
- [x] Test with Qwen3-4B model (3.13 tok/s - research only)
- [x] Performance benchmarking system implemented
- [x] Friendly model names with dynamic context detection
- [x] Automatic model swapping
- [x] Configurable inference parameters
- **Status**: Real NPU inference working, production-ready models validated

### Phase 4.1: Prompt Caching System (COMPLETED ✅ - October 20, 2025)
- [x] Cache infrastructure implementation
  - [x] Folder-based organization: `cache/{model_name}/{cache_name}.bin`
  - [x] CacheManager singleton with CRUD operations
  - [x] Metadata tracking: version, timestamps, size, source
  - [x] System cache support (always loaded first)
- [x] Multi-cache support
  - [x] Single and array syntax in API requests
  - [x] Application-layer concatenation (RKLLM supports only one cache path)
  - [x] Cache loading order: system → user caches → user message
  - [x] Response tracking in usage metadata
- [x] Cache overwrite system
  - [x] Automatic detection via file existence check
  - [x] Version increment on each overwrite (v1 → v2 → v3...)
  - [x] Size comparison logging (old vs new)
  - [x] Timestamp preservation (created_at + updated_at)
  - [x] Optional protection (`allow_overwrite=false` → 409 error)
- [x] API endpoints
  - [x] `POST /v1/cache/{model_name}` - Create/update cache with validation
  - [x] `GET /v1/cache/{model_name}` - List all caches with metadata
  - [x] `GET /v1/cache/{model_name}/{cache_name}` - Get cache content
  - [x] `DELETE /v1/cache/{model_name}/{cache_name}` - Delete cache
  - [x] System cache protection (403 error on manual overwrite attempts)
- [x] Testing and validation
  - [x] Created test caches: coding_rules (221 chars), project_context (214 chars)
  - [x] Validated single cache loading: system + coding_rules
  - [x] Validated multi-cache: system + coding_rules + project_context (1765 chars)
  - [x] Tested overwrite: test_cache v1 (54 chars) → v2 (71 chars)
  - [x] Verified protection: 409 error when allow_overwrite=false
  - [x] Confirmed metadata tracking: version, created_at, updated_at
- [x] Documentation
  - [x] CACHE_USAGE_GUIDE.md - Comprehensive user guide (8KB)
  - [x] MULTI_CACHE_TEST_RESULTS.md - Test validation (12KB)
  - [x] CACHE_OVERWRITE_TEST.md - Overwrite feature tests (10KB)
- **Status**: Text-based prompt caching complete and production-ready
- **Next**: Binary cache generation with RKLLM native caching for actual TTFT reduction

### Phase 4: Advanced Features (IN PROGRESS - October 20, 2025)

**Completed:**
- ✅ **Phase 4.1**: Binary prompt caching with RKLLM native NPU state caching - **COMPLETE!**

**Short-term Goals:**

#### 4.1: Prompt Caching System ⭐ (COMPLETED ✅ - October 20, 2025)
- [x] Binary cache infrastructure
  - [x] **CRITICAL FIX**: Corrected RKLLMPromptCacheParam structure to match official RKLLM API
  - [x] Fixed field order: save_prompt_cache FIRST, prompt_cache_path SECOND  
  - [x] Removed non-existent num_input field that caused segmentation faults
  - [x] Verified against external/rknn-llm/examples/ official implementations
  - [x] Model-specific cache directories (`cache/{model_name}/`)
- [x] Cache creation and loading
  - [x] POST /v1/cache/{model} - Create binary NPU state cache
  - [x] GET /v1/cache/{model} - List available caches
  - [x] DELETE /v1/cache/{model}/{cache_name} - Remove cache
  - [x] use_cache parameter in chat completions for loading
- [x] Performance validation
  - [x] Cache creation: 33MB binary file for 1326-char system prompt
  - [x] TTFT without cache: 1775ms (full prefill computation)
  - [x] TTFT with cache: 75.2ms (instant NPU state restoration)
  - [x] **Achievement: 23.5x speedup (95.8% TTFT reduction!)**
  - [x] Cache loading confirmed with cache_hit=true metadata
- [x] Documentation
  - [x] CACHE_BUG_FIX.md - Root cause analysis and solution
  - [x] RKLLM_CACHE_BUG_INVESTIGATION.md - Initial debugging journey
  - [x] Updated API documentation with cache endpoints
- **Achieved Impact**: 95.8% TTFT reduction - far exceeds 50-70% expectation!
- **Status**: Production-ready binary caching fully operational

#### 4.2: Multi-Batch Inference 🚀 (Throughput)
- [ ] Request queue implementation
  - [ ] Thread-safe request queue
  - [ ] Batch size configuration (`n_batch` parameter)
  - [ ] Dynamic batching based on queue depth
- [ ] Batch processing
  - [ ] Group requests by model and parameters
  - [ ] Parallel inference with RKLLM multi-batch
  - [ ] Response routing to correct clients
- [ ] Performance optimization
  - [ ] Optimal batch size tuning
  - [ ] Latency vs throughput trade-offs
  - [ ] Queue timeout handling
- [ ] Testing and benchmarking
  - [ ] Concurrent request load testing
  - [ ] Throughput measurement (requests/sec)
  - [ ] Latency distribution analysis
  - [ ] Document multi-batch configuration
- **Expected Impact**: 2-3x throughput improvement for concurrent requests

#### 4.3: LongRoPE Support 📏 (Extended Context)
- [ ] RKLLM 1.2.2 upgrade preparation
  - [ ] Check current RKLLM version (currently 1.2.1)
  - [ ] Download/install RKLLM 1.2.2 runtime
  - [ ] Verify LongRoPE API availability
- [ ] Model reconversion with LongRoPE
  - [ ] Convert Qwen3-0.6B with `--longrope` flag
  - [ ] Convert Gemma3-1B with extended context + LongRoPE
  - [ ] Test 32K-64K context windows
- [ ] Extended context testing
  - [ ] Create long-context benchmark prompts (8K-64K tokens)
  - [ ] Measure TTFT and memory at various context lengths
  - [ ] Validate output quality at max context
  - [ ] Document context window capabilities
- [ ] System requirements validation
  - [ ] Confirm 16GB RAM sufficient for 64K contexts
  - [ ] Monitor memory usage during long-context inference
  - [ ] Test context length limits
- **Expected Impact**: 32K-64K context support (up from current 16K max)
- **Blocked on**: Rockchip RKLLM 1.2.2 release

#### 4.4: Hugging Face Model Integration 🤗 (Auto-Download & Conversion)
- [ ] Hugging Face Hub integration
  - [ ] Install huggingface_hub library
  - [ ] Implement model download from HF
  - [ ] Support authentication for gated models
  - [ ] Progress tracking for large downloads
- [ ] Automatic model conversion
  - [ ] Trigger RKLLM conversion after download
  - [ ] Support common model architectures (Qwen, Gemma, Llama, etc.)
  - [ ] Configurable conversion parameters (w8a8, context length, etc.)
  - [ ] Error handling and validation
- [ ] Model registry
  - [ ] Database of supported HF models
  - [ ] Model metadata (size, architecture, recommended settings)
  - [ ] Version tracking
- [ ] API endpoints
  - [ ] POST /v1/models/download - Download and convert from HF
  - [ ] GET /v1/models/registry - List supported HF models
  - [ ] Progress tracking endpoint
- **Goal**: One-click model deployment from Hugging Face
- **Impact**: Users don't need manual model conversion

#### 4.5: Ollama API Compatibility 🦙 (COMPLETED ✅ - October 21, 2025)
- [x] Ollama API endpoint implementation
  - [x] POST /api/generate - Text generation (Ollama format)
  - [x] POST /api/chat - Chat completion with streaming
  - [x] GET /api/tags - List available models
  - [x] POST /api/show - Show model information
  - [x] POST /api/pull - Model management (placeholder)
  - [x] DELETE /api/delete - Remove model
- [x] Format translation
  - [x] Ollama request → Internal format adapters
  - [x] Internal response → Ollama format adapters
  - [x] Streaming response support
  - [x] Temperature/top_p/top_k/repeat_penalty mapping
- [x] Model name aliasing
  - [x] Support Ollama model naming patterns
  - [x] Map to internal model files
  - [x] Friendly name resolution
- [x] Testing and validation
  - [x] Tested with curl commands
  - [x] Validated streaming responses
  - [x] Documented Ollama endpoint usage
- **Status**: Full Ollama API compatibility achieved
- **Impact**: Universal local LLM server (OpenAI AND Ollama compatible)

#### 4.6: Embeddings API 📊 (POSTPONED - October 22, 2025)
**Status**: Implementation complete but disabled due to model incompatibility.

**What Was Built:**
- [x] Complete embedding API implementation
  - [x] POST /v1/embeddings - OpenAI format (batch support)
  - [x] POST /api/embed, /api/embeddings - Ollama format
  - [x] Embedding schemas and adapters
  - [x] get_embeddings() method in RKLLMModel
  - [x] Auto-loading of embedding model
  - [x] Test suite (scripts/test_embeddings.py preserved)

**The Problem:**
- Qwen3-Embedding-0.6B model crashes with current RKLLM runtime (1.2.2)
- Segmentation fault in clear_kv_cache() call
- rkllm_run returns error -1 with RKLLM_INFER_GET_LAST_HIDDEN_LAYER mode
- Both our implementation AND HuggingFace example crash identically
- Likely model conversion issue or runtime version incompatibility

**Current State:**
- ✅ Endpoints commented out (not removed) in openai_routes.py and ollama_routes.py
- ✅ Test scripts preserved in scripts/ for future validation
- ✅ Implementation ready to re-enable when compatible model available
- ✅ Cleaned up temp/ folder (removed outdated HF example scripts)

**Next Steps:**
- [ ] Wait for verified compatible embedding model
- [ ] Test with different RKLLM runtime version if available
- [ ] Or: Implement CPU-based fallback (sentence-transformers)

**Decision**: Skip embeddings until model compatibility verified. All code preserved for future use.

#### 4.7: RKLLM v1.2.3 Upgrade & Chat Templates 💬 (COMPLETED ✅ - December 10, 2025)
- [x] Upgrade `external/rknn-llm` to v1.2.3
  - [x] Verified new features: Qwen3-VL, DeepSeek-OCR, Auto-Cache
- [x] Chat Template Implementation
  - [x] Bind `rkllm_set_chat_template` in `rkllm_model.py`
  - [x] Add `chat_template` section to `inference_config.json`
  - [x] Auto-apply templates on model load
- [x] Automatic Cache Reuse Analysis
  - [x] Investigated v1.2.3 "Automatic Cache Reuse"
  - [x] Finding: Applies to `RKLLM_INPUT_EMBED` only
  - [x] Decision: Continue using manual binary cache for text generation
- **Status**: Project fully updated to latest runtime with enhanced configuration

#### 4.8: Comprehensive Testing & Validation 🧪 (COMPLETED ✅ - December 13, 2025)
- [x] Design Test Plan
  - [x] Created `docs/tests.md` with scenarios for RK3588
  - [x] Defined success criteria for all major features
- [x] Execute Test Suite
  - [x] Created automated script `scripts/tests.sh`
  - [x] **Smoke Test**: Verified basic inference (Passed)
  - [x] **Chat Templates**: Verified "Pirate Mode" (Passed - Model adopted persona)
  - [x] **Ollama**: Verified `/api/generate` and `/api/chat` (Passed)
  - [x] **Concurrency**: Verified queue stability
  - [x] **Caching**: Verified TTFT reduction
- [x] Stability Verification
  - [x] **Context Leakage Fix**: Implemented "Smart Caching" to isolate requests
  - [x] **Thinking Mode**: Enabled and tuned for Qwen models
  - [x] **Penalty Tuning**: Optimized to prevent garbage output in long-chain reasoning

#### 4.9: Hugging Face Integration & Default Model Fix 🛠️ (COMPLETED ✅ - December 10, 2025)
- [x] Fix Default Model
  - [x] Updated `config/settings.py` to point to `qwen3-0.6b` (existing model)
- [x] Hugging Face Integration
  - [x] Added `huggingface_hub` dependency
  - [x] Implemented `_discover_hf_models` in `ModelManager`
  - [x] Scans `HF_HOME` (default: `~/.cache/huggingface/hub`) for `.rkllm` files
  - [x] Auto-registers discovered models with `hf-` prefix (or friendly name)
  - [x] Enables Docker volume mounting of HF cache for shared model storage

#### 4.10: Thinking Mode & Stability Optimization 🧠 (COMPLETED ✅ - December 13, 2025)
- [x] **Context Leakage Fix**:
  - [x] Diagnosed NPU KV cache persistence causing hallucinations across requests
  - [x] Implemented `rkllm_clear_kv_cache` binding in `rkllm_model.py`
  - [x] Added "Smart Caching" logic: Clear cache if prompt context changes, keep if extending
- [x] **Thinking Mode Implementation**:
  - [x] Added `enable_thinking` flag to `inference_config.json`
  - [x] Passed flag to RKLLM runtime for Qwen/DeepSeek models
  - [x] Verified `<think>` tag generation in output
- [x] **Stability Tuning**:
  - [x] Diagnosed "garbage output" issue caused by high `presence_penalty` fighting with long Chain-of-Thought
  - [x] Tuned penalties: `frequency_penalty=0.1`, `presence_penalty=0.1`
  - [x] Validated with 10/10 pass rate on full benchmark suite

**Phase 4 Success Criteria:**
- ✅ **Phase 4.1 COMPLETE**: Binary prompt caching (23.5x speedup achieved!)
  - ✅ Binary cache creation with NPU state saving
  - ✅ Cache loading with instant restoration
  - ✅ 95.8% TTFT reduction validated
- ✅ **Phase 4.2 COMPLETE**: Queue-based concurrency (stable parallel requests)
- ✅ **Phase 4.5 COMPLETE**: Ollama API compatibility (universal server)
- ✅ **Phase 4.7 COMPLETE**: RKLLM v1.2.3 & Chat Templates
- ✅ **Phase 4.8 COMPLETE**: Comprehensive Testing & Validation
- ✅ **Phase 4.10 COMPLETE**: Thinking Mode & Stability Optimization
- ⏸️ **Phase 4.6 POSTPONED**: Embeddings API (model incompatibility, code preserved)
- [ ] **Phase 4.3**: LongRoPE support (32K-64K context) - requires model rebuild
- [ ] **Phase 4.4**: Hugging Face integration (auto-download & convert)
- ✅ All working features documented and benchmarked
- ✅ Production-ready with configuration examples

### Phase 5: Multimodal Support (Vision-Language) 👁️ (IN PROGRESS)
- [x] **Architecture Design**:
  - [x] "Split Brain" architecture: Python wrapper + C++ `imgenc` binary
  - [x] Documented in `docs/multimodal_architecture.md`
- [x] **Core Implementation**:
  - [x] Updated `RKLLMModel` to handle `image_data`
  - [x] Implemented `_encode_image` using `subprocess` to call `imgenc`
  - [x] Added `RKLLMMultiModalInput` ctypes structure

### Phase 6: Image Generation (Stable Diffusion) 🎨 (IN PROGRESS)
- [x] **Initial Setup**:
  - [x] Downloaded `unet_lcm_512.rknn` and related components
  - [x] Created `scripts/run_rknn-lcm.py` pipeline script
- [x] **Investigation & Debugging**:
  - [x] **Issue**: `Segmentation fault` during `rknn.inference()`
  - [x] **Root Cause Analysis**:
    - Verified input signature: 4 inputs (`sample`, `timestep`, `encoder_hidden_states`, `timestep_cond`)
    - Verified memory alignment: NPU driver requires 4096-byte alignment
    - Created C reproduction tool (`test_unet_mem.c`) to bypass Python
    - **Conclusion**: Model file `unet_lcm_512.rknn` is likely incompatible with current NPU driver (v0.9.7) or Runtime (v2.3.2)
- [ ] **Next Steps**:
  - [ ] **Driver Update**: Check for newer NPU drivers in `external/rknn-llm`
  - [ ] **Model Strategy**: Find alternative pre-converted models or perform local conversion
  - [ ] **Integration**: Once stable, integrate into `/v1/images/generations` endpoint

## Session Notes (December 14, 2025)
- **Stable Diffusion Debugging**:
  - Spent significant time debugging a Segfault in the UNet inference.
  - Confirmed the model requires 4 inputs, not 3.
  - Even with perfect memory alignment (using `posix_memalign` in C), the crash persists inside the NPU driver execution.
  - This strongly suggests a binary incompatibility between the `.rknn` model and the installed driver/runtime.
- **Plan**:
  1. Check/Update NPU Driver.
  2. Search for a better/compatible model file.
  3. If all else fails, use the user's x86 Strix Halo machine to convert models manually.
- [x] **API Integration**:
  - [x] Updated `openai_routes.py` to parse `image_url` in messages
  - [x] Implemented ChatML vision token injection (`<|vision_start|>`, etc.)
  - [x] **Fix**: Switched to `<image>` tag for RKLLM runtime compatibility
- [x] **Client Tools**:
  - [x] Created `examples/multimodal_request.py` for testing
- [ ] **Debugging & Validation**:
  - [ ] **Issue**: Model returns single token "The" and stops immediately.
  - [ ] **Attempts**: Fixed `<image>` tag, added newlines, forced `max_new_tokens`.
  - [ ] **Next**: Verify `imgenc` binary compatibility and runtime signals.
  - [ ] Benchmark multimodal performance

### Phase 6: Docker Containerization
- [ ] Create Dockerfile for ARM64
- [ ] Generate requirements.txt from working venv
- [ ] Multi-stage Docker build optimization
- [ ] Volume mount configuration
- [ ] Docker Compose setup
- [ ] Container testing and validation
- [ ] Production deployment guide

### Phase 6: Advanced Model Management
- [ ] Dynamic model loading and unloading
- [ ] Model caching and warm-up strategies
- [ ] Memory management for NPU operations
- [ ] Multi-model support (parallel instances)
- [ ] Model switching mechanisms
- [ ] LoRA adapter support

### Phase 7: Performance Optimization
- [ ] NPU utilization optimization
- [ ] Concurrent request handling (multi-batch)
- [ ] Memory efficiency improvements (embed_flash)
- [ ] Response time optimization (GPU prefill)
- [ ] CPU affinity tuning (big cores 4-7)
- [ ] Throughput maximization

### Phase 8: Testing and Validation
- [ ] Unit testing framework (pytest)
- [ ] Integration testing with real models
- [ ] API compatibility testing (OpenAI/Ollama clients)
- [ ] Performance benchmarking
- [ ] Load testing and stress testing
- [ ] Hardware-specific testing on RK3588

### Phase 9: Documentation and Deployment
- [ ] API documentation (auto-generated via FastAPI)
- [ ] Deployment guides
- [ ] Configuration documentation
- [ ] Performance tuning guides
- [ ] Troubleshooting documentation
- [ ] Model conversion guides

## Technical Architecture

> **📖 For detailed RKLLM runtime analysis, see [RKLLM Documentation](./rkllm.md)**

### System Components

#### 1. API Gateway Layer
- **Purpose**: Handle incoming REST requests
- **Technology**: TBD (FastAPI/Flask consideration)
- **Responsibilities**:
  - Request validation
  - Authentication/authorization
  - Rate limiting
  - Response formatting
  - OpenAI/Ollama API compatibility translation

#### 2. Model Management Layer
- **Purpose**: Handle model lifecycle and operations
- **Responsibilities**:
  - Model loading/unloading
  - RKNN model conversion
  - Model caching
  - Memory management

#### 3. NPU Interface Layer
- **Purpose**: Abstract NPU operations
- **Responsibilities**:
  - NPU detection and initialization
  - RKNN runtime management
  - Hardware abstraction
  - Error handling

#### 4. Compatibility Layer
- **Purpose**: Ensure API compatibility
- **Responsibilities**:
  - OpenAI API translation
  - Ollama API translation
  - Request/response transformation
  - Feature mapping

### Data Flow

```
Client Request → API Gateway → Compatibility Layer → Model Management → NPU Interface → RKNN Runtime → NPU Hardware
```

### Container Architecture

#### Base Container Requirements
- ARM64 compatible base image
- RKNN runtime libraries
- Python runtime environment
- Required system dependencies

#### Multi-stage Build Strategy
1. **Build Stage**: Compile dependencies, prepare runtime
2. **Runtime Stage**: Minimal container with only runtime requirements
3. **Development Stage**: Additional tools for development/debugging

## External Dependencies

### Integrated External Repository
- **Repository**: [airockchip/rknn-llm](https://github.com/airockchip/rknn-llm.git)
- **Integration Method**: Git submodule at `/external/rknn-llm/`
- **Date Integrated**: October 19, 2025
- **Version**: v1.2.3
- **Components Available**:
  - `rkllm-runtime/` - RKNN LLM runtime libraries (`librkllmrt.so`)
    - Linux/Android support
    - Platform: RK3588, RK3576, RK3562, RV1126B
  - `rkllm-toolkit/` - RKNN LLM toolkit for model conversion and optimization
  - `rknpu-driver/` - NPU driver files and documentation
  - `examples/rkllm_server_demo/` - Reference Flask and Gradio server implementations
    - `flask_server.py` - OpenAI-compatible Flask server with streaming support
    - `gradio_server.py` - Interactive Gradio web interface
    - `chat_api_flask.py` - Client API examples
    - `chat_api_gradio.py` - Gradio client examples
  - `examples/rkllm_api_demo/` - C++ and Python API usage examples
  - `examples/multimodal_model_demo/` - Multimodal (vision + LLM) model demonstrations
- **Key Features Identified**:
  - Multi-instance inference support (v1.2.2)
  - Multi-batch inference (v1.2.1)
  - Function calling capability (v1.2.1)
  - Thinking mode for reasoning models (v1.2.1)
  - LongRoPE for extended context (v1.2.2)
  - Optimized KV cache management (v1.2.1)
  - Cross-attention inference (v1.2.1)
  - Performance statistics tracking (v1.2.1)
  - Automatic Cache Reuse for Embeddings (v1.2.3)
  - External Chat Template Support (v1.2.3)

### Required External Repository
- **Rockchip RKNN Toolkit**: Drivers, runtime, and examples
- **Integration Strategy**: Git submodule or download during build
- **Components Needed**:
  - NPU drivers
  - RKNN runtime libraries
  - Reference implementations
  - Example models

### Python Dependencies (Preliminary)
- FastAPI or Flask (API framework decision pending)
- Pydantic (data validation)
- asyncio (asynchronous operations)
- numpy (numerical operations)
- Additional RKNN Python bindings

## Configuration Management

### Configuration Categories
1. **Hardware Configuration**: NPU settings, memory allocation
2. **API Configuration**: Port, authentication, rate limits
3. **Model Configuration**: Default models, conversion settings
4. **Runtime Configuration**: Logging, debugging, performance tuning

### Configuration Methods
- Environment variables
- Configuration files (YAML/JSON)
- Command-line arguments
- Runtime API endpoints

## Deployment Strategy

### Docker Deployment
- Single container with all dependencies
- Volume mounts for models and configuration
- Environment-based configuration
- Health checks and monitoring

### Hardware Requirements
- ARM64 architecture
- Rockchip RK3588 or compatible RKNN-LLM chip
- Minimum RAM: TBD based on model requirements
- NPU drivers properly installed

## API Compatibility Specifications

### OpenAI API Endpoints (Target)
- `/v1/completions`
- `/v1/chat/completions`
- `/v1/models`
- Additional endpoints as required

### Ollama API Endpoints (Target)
- `/api/generate`
- `/api/chat`
- `/api/tags`
- Additional endpoints as required

## Performance Considerations

### Optimization Targets
- Minimize latency for inference requests
- Maximize throughput for concurrent requests
- Efficient memory utilization
- NPU utilization optimization

### Monitoring Metrics
- Request/response times
- NPU utilization
- Memory usage
- Throughput rates
- Error rates

## Development Guidelines

### Code Organization
- Modular architecture
- Clear separation of concerns
- Testable components
- Documentation requirements

### Quality Assurance
- Unit testing for all components
- Integration testing with real hardware
- Performance testing and benchmarking
- Code review requirements

## Future Considerations

### Potential Enhancements
- Multi-node clustering
- Model fine-tuning capabilities
- Advanced caching strategies
- Extended API compatibility
- Monitoring and analytics dashboard

### Scalability Planning
- Horizontal scaling support
- Load balancing strategies
- Distributed model serving
- Resource management optimization

## Development Strategy: Hybrid Approach

### Phase 1: Rapid Prototyping (CURRENT)
**Goal**: Working FastAPI server with basic inference in 1-2 hours

**Steps**:
1. Create Python venv for isolation
2. Install FastAPI, uvicorn, RKLLM Python bindings
3. Build minimal `/v1/chat/completions` endpoint
4. Test with downloaded models (Qwen3-0.6B, Gemma-3-270M, Gemma-3-1B)
5. Iterate rapidly on API logic
6. Generate `requirements.txt` from working setup

**Benefits**:
- ✅ Real NPU hardware access from day 1
- ✅ Fast iteration cycles (no container rebuilds)
- ✅ Easy debugging with immediate feedback
- ✅ Learn RKLLM runtime quirks early

### Phase 2: Containerization (AFTER IT WORKS)
**Goal**: Production-ready Docker container in 30 minutes

**Steps**:
1. Create Dockerfile based on working venv
2. Use `pip freeze > requirements.txt`
3. Test container on same hardware
4. Fine-tune for production deployment

**Benefits**:
- ✅ Environment parity guaranteed
- ✅ Perfect requirements.txt from tested setup
- ✅ Minimal rework (copy working code)

### Network Configuration
- **Samba Server**: ✅ Configured on 192.168.10.53
  - Share: `\\192.168.10.53\AI` (access to `/home/angeiv/AI`)
  - Enables easy file transfer and remote development

## Decision Log

### Technology Decisions (Finalized)
1. **API Framework**: ✅ **FastAPI** (Selected)
   - **Rationale**: 
     - ~3x faster than Flask with async/await native support
     - ~10% lower memory usage via async architecture
     - Auto-generated OpenAPI/Swagger documentation
     - Pydantic type safety reduces runtime errors
     - Perfect for I/O-bound NPU workloads
     - Modern, production-proven (Microsoft, Uber, Netflix)
   - **Trade-off**: +10MB Docker image vs Flask (acceptable)
   - **Migration**: Similar structure to Flask reference code (~2-4 hours)
   - **Date Decided**: October 19, 2025

2. **Development Strategy**: ✅ **Hybrid Approach** (Selected)
   - **Rationale**:
     - Fastest path to working prototype (native development)
     - Real hardware NPU access essential for RKLLM testing
     - Clean transition to Docker after validation
     - Requirements generated from proven setup
   - **Timeline**: 1-2 hours to first inference, 30 min to containerize
   - **Date Decided**: October 19, 2025

3. **Model Selection**: ✅ **Downloaded Models**
   - **Qwen3-0.6B**: Primary model, 16K context, w8a8 quantization
   - **Gemma-3-270M**: Ultra-fast testing model, 16K context
   - **Gemma-3-1B-it**: Instruction-tuned, general testing
   - **Date Acquired**: October 19, 2025

4. **Cache Strategy**: ✅ **Manual Binary Cache** (Selected)
   - **Rationale**: RKLLM v1.2.3 "Automatic Cache Reuse" only applies to embedding inputs. For text generation, manual binary caching (saving/loading NPU state) remains the most effective way to reduce TTFT.
   - **Date Decided**: December 10, 2025

### Technology Decisions (Pending)
2. **Container Base Image**: Specific ARM64 image selection
3. **Configuration Format**: YAML vs JSON vs TOML
4. **Logging Framework**: Selection and configuration
5. **Testing Framework**: pytest vs unittest selection

### Architecture Decisions (Pending)
1. **Model Loading Strategy**: Lazy vs eager loading
   - **Context**: RKLLM initialization is synchronous and blocking
2. **Memory Management**: Allocation strategies
   - **Context**: RKLLM supports embed_flash for memory optimization
3. **Concurrent Processing**: Threading vs async approach
   - **Context**: RKLLM inference is single-threaded per handle, requires locking
4. **Error Handling**: Strategy and implementation
5. **Monitoring Integration**: Built-in vs external tools
   - **Context**: RKLLM v1.2.1+ provides performance statistics (prefill/generate time, memory)

### RKLLM Runtime Insights
- **Threading Model**: Single-threaded inference per handle requires explicit locking for server
- **Batch Processing**: Multi-batch support (n_batch parameter) can improve throughput
- **Multi-Instance**: Multiple model instances possible with separate handles (v1.2.2)
- **Memory**: embed_flash=1 stores embeddings in flash to reduce RAM usage
- **CPU Affinity**: Should use big cores (4-7) on RK3588 for best performance
- **Context Management**: Supports up to 16K tokens with LongRoPE (v1.2.2)

## Key Insights from SDK Analysis

### Performance Optimization Opportunities
1. **GPU Prefill Acceleration**: RK3588/3576 support GPU-accelerated prefill stage
2. **Multi-Batch Processing**: Single model can handle multiple requests concurrently (n_batch parameter)
3. **CPU Core Affinity**: Big cores (4-7) on RK3588 provide best performance
4. **Embed Flash**: Store embeddings in flash memory to save RAM
5. **Prompt Cache**: Reuse prefill computation for common system prompts

### Deployment Considerations
1. **Thread Safety**: RKLLM requires explicit locking per handle (single-threaded inference)
2. **Resource Limits**: Should increase file descriptor limits for server deployment
3. **Frequency Scaling**: Use provided scripts to fix CPU/NPU frequencies
4. **Logging**: Enable RKLLM_LOG_LEVEL for performance monitoring

### API Compatibility
1. **OpenAI Format**: Reference Flask implementation already provides OpenAI-compatible endpoints
2. **Function Calling**: Full tool/function calling support with JSON schema definitions
3. **Streaming**: Callback-based streaming with UTF-8 character completion
4. **Message Roles**: system/user/assistant/tool roles properly handled

### Development Tools
1. **PC Simulation**: Test models on PC before deployment (toolkit)
2. **Accuracy Testing**: PPL evaluation on Wikitext dataset (toolkit)
3. **Model Update**: Convert v1.0.2 models to latest version
4. **Custom Models**: JSON configuration for non-standard architectures

### Limitations Identified
1. **Single-threaded per handle**: Requires careful concurrency management
2. **Memory constraints**: Model size + KV cache must fit in RAM
3. **Context window**: 16K max with LongRoPE, less for smaller models
4. **Quantization only**: No FP16/FP32 NPU inference, only W8A8/W4A16

## Session Notes

### Session: October 20, 2025 - CRITICAL FIX: Binary Cache Structure Corrected! 🎉

#### The Bug Hunt That Led to Victory

**Initial Problem:**
- Binary cache creation consistently segfaulted
- No `.rkllm_cache` files ever created
- Suspected RKLLM library bug

**The Investigation:**
User suggestion: "check if the external/rknn-llm examples have some implementation of caching"

**The Discovery:**
Found official examples in `/external/rknn-llm/examples/rkllm_server_demo/rkllm_server/gradio_server.py`

**Official Structure (from rkllm.h):**
```c
typedef struct {
    int save_prompt_cache;          // FIRST field
    const char* prompt_cache_path;  // SECOND field
} RKLLMPromptCacheParam;
```

**Our WRONG Structure:**
```python
class RKLLMPromptCacheParam(ctypes.Structure):
    _fields_ = [
        ("prompt_cache_path", ctypes.c_char_p),  # WRONG ORDER!
        ("save_prompt_cache", ctypes.c_int),     # WRONG ORDER!
        ("num_input", ctypes.c_int)              # DOESN'T EXIST!
    ]
```

**The Fix:**
```python
class RKLLMPromptCacheParam(ctypes.Structure):
    _fields_ = [
        ("save_prompt_cache", ctypes.c_int),     # FIRST (correct!)
        ("prompt_cache_path", ctypes.c_char_p)   # SECOND (correct!)
    ]
```

**The Results:**
- ✅ Cache creation: SUCCESS - 33MB `system.rkllm_cache` created
- ✅ Cache loading: SUCCESS - `cache_hit: true` confirmed
- ✅ Performance: **TTFT 75.2ms** (was 1775ms) = **23.5x faster!**
- ✅ Real NPU state caching working perfectly

**Key Lesson:**
ALWAYS check official examples when ctypes bindings fail. Structure field order matters!

**Files Modified:**
- `src/models/rkllm_model.py` - Corrected RKLLMPromptCacheParam structure
- `docs/CACHE_BUG_FIX.md` - Detailed root cause analysis
- `docs/RKLLM_CACHE_BUG_INVESTIGATION.md` - Investigation journey
- `docs/DISK_USAGE_ANALYSIS.md` - Repository size breakdown
- `docs/GIT_CLEANUP_SUCCESS.md` - Git history cleanup documentation

**Performance Achievement:**
- Without cache: 1775ms TTFT (full prefill)
- With cache: 75.2ms TTFT (instant NPU restore)
- Improvement: 95.8% reduction (23.5x speedup!)
- Cache size: 33MB for 1326-char system prompt

**Repository Cleanup Achievement:**
- Removed 5GB model file from git history using git filter-branch
- .git size: 4.6 GB → 391 MB (mostly submodule, only 314 KB actual code)
- Pack size: 4.14 GB → 314 KB (99.99% reduction!)
- Push size: 311 KB (instead of 4.14 GB!)
- Updated .gitignore: Added `*.rkllm`, `*.rkllm_cache` patterns
- Fast clones: Repository now lightweight and efficient

**Commits Made:**
- `6dd4181` - fix: Correct RKLLMPromptCacheParam structure to match official API
- `857bf51` - fix: Add overwrite protection + document RKLLM segfault bug
- `5ebab0e` - chore: Update .gitignore to exclude binary cache files
- `0e7e61a` - docs: Add git repository size analysis and cleanup documentation
- `6d3e550` - docs: Document successful git history cleanup (4.6GB → 391MB)
- `318425a` - docs: Celebrate Phase 4.1 completion - Binary caching working!

**Status:** Phase 4.1 Binary Caching - **COMPLETE AND WORKING!** 🎉  
**Status:** Repository Optimization - **COMPLETE!** Ready for fast distribution.

---

### Session: October 20, 2025 - Phase 4.1 Prompt Caching Complete

#### Prompt Caching Implementation (COMPLETED ✅)

**Multi-Cache Support:**
- ✅ Single cache syntax: `"cache_prompts": "coding_rules"`
- ✅ Array syntax: `"cache_prompts": ["coding_rules", "project_context"]`
- ✅ Application-layer concatenation (system → user caches → message)
- ✅ Response metadata tracking: `cached_prompts`, `cache_hit`
- ✅ RKLLM limitation workaround: Only supports one cache path, we concatenate at app layer

**Cache Overwrite System:**
- ✅ Automatic detection via `bin_path.exists()`
- ✅ Version tracking (increments on each overwrite)
- ✅ Size comparison logging (old vs new)
- ✅ Timestamp preservation (`created_at` + `updated_at`)
- ✅ Optional protection (`allow_overwrite=false` → 409 error)
- ✅ System cache protection (403 error on manual overwrite)

**API Endpoints:**
- ✅ `POST /v1/cache/{model_name}` - Create/update cache
- ✅ `GET /v1/cache/{model_name}` - List caches
- ✅ `GET /v1/cache/{model_name}/{cache_name}` - Get content
- ✅ `DELETE /v1/cache/{model_name}/{cache_name}` - Delete cache

**Testing Results:**
- ✅ Created test caches: coding_rules (221 chars), project_context (214 chars)
- ✅ Multi-cache loading: system + coding_rules + project_context = 1765 chars
- ✅ Overwrite test: test_cache v1 (54 chars) → v2 (71 chars)
- ✅ Protection test: 409 error when allow_overwrite=false
- ✅ All metadata tracking verified

**Documentation Created:**
- ✅ `CACHE_USAGE_GUIDE.md` - 8KB comprehensive guide
- ✅ `MULTI_CACHE_TEST_RESULTS.md` - 12KB test validation
- ✅ `CACHE_OVERWRITE_TEST.md` - 10KB overwrite tests

**Files Modified:**
- `src/api/schemas.py` - Added cache_prompts, cached_prompts, cache_hit
- `src/utils/cache_manager.py` - Complete cache CRUD with overwrite support
- `src/api/openai_routes.py` - Multi-cache integration + POST endpoint

**Current State:**
Text-based prompt caching is production-ready. System cache always loads first, user caches concatenate in order, user message appends last. Overwrite system tracks versions and sizes with optional protection.

**Next Phase:**
Binary cache generation using RKLLM's native `RKLLMPromptCacheParam` to achieve actual TTFT reduction (target: 50-70%).

---

### Session: October 19, 2025 - Complete Phase 2 Implementation + Model Management + Benchmarking

#### Phase 1: Foundation (Completed Earlier)
- ✅ Repository initialization with git submodules
- ✅ Added rknn-llm as submodule (1191 objects, 390 MB)
- ✅ Analyzed RKLLM runtime capabilities
- ✅ Created comprehensive RKLLM documentation (docs/rkllm.md)
- ✅ Selected FastAPI over Flask (3x performance benefit)
- ✅ Downloaded 3 models: Qwen3-0.6B (909MB), Gemma-3-270M (616MB), Gemma-3-1B (1.5GB)
- ✅ Set up Samba server on 192.168.10.53 for network access

#### Phase 2: FastAPI Server (Completed)
- ✅ Created Python venv with all dependencies
- ✅ Installed FastAPI 0.104.1, uvicorn 0.24.0, pydantic 2.5.0, numpy 2.3.4
- ✅ Built modular structure: main.py (routing) + openai_routes.py (API logic)
- ✅ Created comprehensive Pydantic schemas for OpenAI compatibility
- ✅ Implemented OpenAI-compatible endpoints:
  - `GET /` - Root endpoint with API info
  - `GET /v1/health` - Health check
  - `GET /v1/models` - List models (OpenAI format)
  - `POST /v1/chat/completions` - Chat completions (streaming & non-streaming)
- ✅ Created test suite (test_api.py)
- ✅ Created startup script (start_server.sh)
- ✅ Server running on port 8080, accessible at 192.168.10.53:8080
- ✅ All endpoints tested and validated with placeholder responses

**Files Created (Phase 2):**
- `requirements.txt` - Python dependencies
- `src/main.py` - FastAPI entry point
- `src/api/schemas.py` - Pydantic models
- `src/api/openai_routes.py` - OpenAI endpoints
- `src/models/rkllm_model.py` - RKLLM wrapper (placeholder)
- `src/config/settings.py` - Configuration management
- `test_api.py` - API test suite
- `start_server.sh` - Quick start script
- `docs/QUICKSTART.md` - User guide

#### Model Management Implementation (Completed)
- ✅ Created ModelManager singleton service (`src/models/model_manager.py`)
- ✅ Implemented thread-safe model lifecycle:
  - `load_model()` - Load with NPU configuration
  - `unload_model()` - Cleanup and memory release
  - `get_current_model()` - Returns loaded instance
  - `list_available_models()` - Scans /models/ directory
- ✅ Created Model Management API (`src/api/model_routes.py`):
  - `POST /v1/models/load` - Load specific model
  - `POST /v1/models/unload` - Unload current model
  - `GET /v1/models/loaded` - Show currently loaded model
  - `GET /v1/models/available` - List all models with sizes
- ✅ Updated chat endpoint to validate model is loaded (returns 400 if not)
- ✅ Created comprehensive test suite (`test_model_management.py`)
- ✅ Created usage documentation (`docs/MODEL_MANAGEMENT.md`)

**Key Architecture Decisions:**
- **Manual load vs Auto-load**: Chose manual load for predictable performance
- **Single model at a time**: Loading new model automatically unloads current one
- **Path resolution**: Automatic detection from configured models_dir
- **Thread safety**: Using threading.Lock for singleton pattern
- **Error handling**: Graceful errors with helpful messages

**Test Results:**
- ✅ Model listing: All 3 models detected (616MB, 909MB, 1.5GB)
- ✅ Model loading: Successfully simulated (pending RKLLM integration)
- ✅ Model unloading: Working correctly
- ✅ Chat without model: Returns proper 400 error
- ✅ Health check: Reports loaded model status

#### Benchmarking System Implementation (Completed)
- ✅ Created comprehensive benchmark suite (`benchmark.py`)
- ✅ Created quick benchmark test (`test_benchmark.py`)
- ✅ Added benchmark prompts library (`config/benchmark_prompts.json`)
- ✅ Created benchmarking guide (`docs/BENCHMARKING.md`)
- ✅ Created quick reference (`docs/BENCHMARK_QUICKREF.md`)
- ✅ Updated README.md with benchmark information

**Benchmark Features:**
- Performance metrics: TTFT, tokens/sec, input processing speed, memory usage
- Two test suites:
  - Performance tests: 5 quick prompts for speed measurement
  - Quality tests: 5 detailed prompts for output assessment
- Comprehensive statistics: mean, median, min, max for all metrics
- Detailed JSON output for long-term tracking
- Comparison with expected RK3588 performance values
- Support for multiple runs for statistical accuracy
- Command-line interface with flexible options

**Metrics Measured:**
1. **TTFT (Time To First Token)**: Prefill/input processing time
2. **Tokens per Second**: Generation speed during output phase
3. **Input Processing Speed**: Tokens/sec during prefill
4. **Total Inference Time**: End-to-end request time
5. **Memory Usage**: RAM consumption (when available)
6. **Token Counts**: Input, output, and total tokens

**Usage Examples:**
```bash
# Quick test (3 requests)
python scripts/test_benchmark.py

# Full performance suite
python scripts/benchmark.py --type performance

# Quality assessment
python scripts/benchmark.py --type quality

# Complete benchmark with multiple runs
python scripts/benchmark.py --type all --runs 3

# Test specific model
python scripts/benchmark.py --model google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588
```

#### Documentation Cleanup (October 19, 2025)
- ✅ Moved all documentation to `docs/` folder:
  - `QUICKSTART.md` → `docs/QUICKSTART.md`
  - `MODEL_MANAGEMENT.md` → `docs/MODEL_MANAGEMENT.md`
  - `PHASE2_SUMMARY.md` → `docs/PHASE2_SUMMARY.md`
  - `BENCHMARK_SUMMARY.md` → `docs/BENCHMARK_SUMMARY.md`
  - `BENCHMARK_QUICKREF.md` → `docs/BENCHMARK_QUICKREF.md`
- ✅ Moved all scripts to `scripts/` folder:
  - `benchmark.py` → `scripts/benchmark.py`
  - `test_api.py` → `scripts/test_api.py`
  - `test_benchmark.py` → `scripts/test_benchmark.py`
  - `test_model_management.py` → `scripts/test_model_management.py`
- ✅ Kept `start_server.sh` in root for easy access
- ✅ Updated all documentation references with new paths
- ✅ Created `docs/DOCUMENTATION_INDEX.md` - documentation overview
- ✅ Created `scripts/README.md` - scripts documentation
- ✅ Added documentation guidelines to copilot.md
- ✅ Consolidated all phase information into copilot.md

**Documentation Guidelines Established:**
1. All `.md` documentation files kept in `docs/` folder
2. All test and benchmark scripts kept in `scripts/` folder
3. Only `start_server.sh` stays in root for convenience
4. Update existing documentation rather than creating new phase files
5. Use `copilot.md` as central design document and session log
6. Do NOT create separate PHASE*.md or SUMMARY.md files

**Current State:**
- Clean root directory with only essential files
- All documentation organized in `docs/`
- All scripts organized in `scripts/`
- Server fully operational with model management
- All endpoints tested and working
- Comprehensive benchmarking system ready
- Documentation organized and consolidated
- **CRITICAL**: Using placeholder/mock responses - NEED TO IMPLEMENT REAL RKLLM!

**Hardware Available:**
- Orange Pi 5 Max with 16GB RAM
- Rockchip RK3588 NPU onboard
- RKLLM runtime library installed: `/usr/lib/librkllmrt.so` (7.2MB)
- RKLLM drivers already installed and working
- 3 real .rkllm models downloaded and ready

**Next Steps (Phase 3 - IN PROGRESS):**
1. ~~Study Flask reference~~ (Already analyzed)
2. **IMPLEMENT REAL RKLLM ctypes bindings** (CURRENT TASK)
3. Implement actual `rkllm_init()` in RKLLMModel.load()
4. Implement actual `rkllm_run()` in RKLLMModel.generate()
5. Add streaming callback support
6. Test with real Gemma-3-270M model on NPU
7. **Benchmark real NPU performance** using benchmark tools
8. Compare actual vs expected performance (32-45 tokens/sec for 0.5-0.6B models)

### Session: October 20, 2025 - Real RKLLM Implementation

#### RKLLM Configuration from Official Examples
**Key Performance Settings from gradio_server.py:**
```python
# GPU Acceleration + Big Core Optimization for RK3588
rkllm_param.extend_param.base_domain_id = 0  # GPU prefill acceleration
rkllm_param.extend_param.embed_flash = 1     # Store embeddings in flash (saves RAM)
rkllm_param.extend_param.n_batch = 1         # Batch size
rkllm_param.extend_param.enabled_cpus_num = 4  # Use 4 threads
rkllm_param.extend_param.enabled_cpus_mask = 0xF0  # RK3588 big cores 4-7: (1<<4)|(1<<5)|(1<<6)|(1<<7)

# Inference parameters
top_k = 1 (or 20 per user preference)
top_p = 0.9
temperature = 0.8
repeat_penalty = 1.1
```

#### Implementation Progress
- ✅ Created complete RKLLM ctypes wrapper (`src/models/rkllm_model.py`)
- ✅ Copied all structures from official Gradio example
- ✅ Implemented GPU acceleration (base_domain_id = 0)
- ✅ Configured 4-thread big core optimization (cores 4-7, mask 0xF0)
- ✅ Enabled flash embedding storage (embed_flash = 1)
- ✅ Set user preference: top_k = 20
- ✅ Updated API routes with correct parameters
- ✅ Server running with real RKLLM implementation

**Current Status**: ✅ **REAL NPU INFERENCE WORKING!**

**Breakthrough**: First successful NPU generation on October 20, 2025 00:33:10
- ✅ Model loads successfully on NPU (1.2 seconds)
- ✅ RKLLM runtime 1.2.1 + NPU driver 0.9.7 operational
- ✅ Big cores [4, 5, 6, 7] engaged correctly
- ✅ Generated 5934 characters in ~52 seconds
- ✅ HTTP 200 response returned

**CRITICAL ISSUES FOUND**:

**Issue 1: Garbage Output** ✅ FIXED!
- ~~NPU generates text but it's **complete nonsense**~~
- ~~Example: Asked about "AI and ML", got "Fire Department hiring" and "New Orleans Saints"~~
- **Root Cause**: Wrong sampling parameters (`top_k=20` was too high for small models)
- **Solution Implemented**:
  - ✅ Created configurable `config/inference_config.json` at project root
  - ✅ User can now easily adjust `top_k`, `top_p`, `temperature`, `repeat_penalty`
  - ✅ Model loading automatically uses config parameters
  - ✅ Tested with `top_k=20`, `top_p=0.95`, `temperature=0.6` → **coherent output!**
- **Result**: NPU now generates coherent, on-topic responses with user's preferred parameters

**Issue 2: Token Counting Wrong** ✅ FIXED!
- ~~Problem: We calculated `tokens/sec = output_tokens / total_time_ms`~~
- ~~WRONG! Should use: `tokens/sec = generate_tokens / generate_time_ms`~~
- **Solution Implemented**:
  - ✅ Extract `RKLLMPerfStat` from callback in `_callback_impl()`
  - ✅ Return tuple `(text, perf_stats)` from `generate()`
  - ✅ Send perf stats in final streaming chunk
  - ✅ Benchmark extracts real metrics from usage data
  - ✅ Calculate accurate tokens/sec using `generate_tokens / (generate_time_ms / 1000)`

**Issue 3: Model Reload Hanging** ✅ FIXED!
- **Problem**: Calling model load API when same model already loaded caused `rkllm_destroy()` to hang indefinitely
- **Root Cause**: RKLLM library's destroy function blocks if called during active operations
- **Solution Implemented**:
  - ✅ Added check in `model_manager.load_model()` to skip reload if same model already loaded
  - ✅ Only unloads and reloads when switching to a different model
  - ✅ Logs "Model already loaded, skipping reload" message
- **Result**: No more hanging on repeated load calls, benchmark can run without timeouts

**Issue 4: Streaming Performance Stats Missing** ✅ FIXED!
- **Problem**: Usage field with RKLLM perf stats wasn't being sent in streaming final chunk
- **Root Cause**: `ChatCompletionChunk` schema missing `usage` field
- **Solution Implemented**:
  - ✅ Added `usage: Optional[Dict[str, Any]] = None` to `ChatCompletionChunk` schema
  - ✅ Final streaming chunk now includes all RKLLM performance data
  - ✅ Benchmark can extract accurate metrics from streaming responses
- **Result**: Full performance visibility in both streaming and non-streaming modes

**RKLLM Performance Metrics Now Available**:
- `prefill_time_ms` - **TTFT** (input processing time)
- `prefill_tokens` - Actual input token count from NPU
- `generate_time_ms` - Pure generation time (excludes TTFT)
- `generate_tokens` - Actual output tokens generated
- `memory_usage_mb` - NPU memory usage

**Accurate Speed Calculations**:
```python
# Input processing speed
input_tokens_per_sec = prefill_tokens / (prefill_time_ms / 1000)

# Output generation speed  
output_tokens_per_sec = generate_tokens / (generate_time_ms / 1000)

# Total throughput
total_tokens_per_sec = (prefill_tokens + generate_tokens) / ((prefill_time_ms + generate_time_ms) / 1000)
```

**Benchmark Results**:
- File: `benchmarks/benchmark_google_gemma_3_270m_w8a8_opt0__20251020_eke9ii.md`
- 10 tests completed with old metrics (inaccurate)
- Next run will have accurate RKLLM performance data

**Next Actions**:
1. ✅ DONE: Fix perf stat extraction
2. ✅ DONE: Create configurable inference parameters (config/inference_config.json)
3. ✅ DONE: Fix model reload hanging issue
4. ✅ DONE: Add streaming performance stats
5. ✅ DONE: Move config folder to project root
6. 🔄 TODO: Run full benchmark suite with Qwen3-0.6B
7. 🔄 TODO: Test with different parameter configurations
8. ⏳ TODO: Implement chat templates (later with prompt caching)
9. ⏳ TODO: Add system prompt support for better instruction following

#### Recent Session Improvements (October 20, 2025)

**Configuration System**:
- ✅ Created `config/inference_config.json` at project root for easy parameter tuning
- ✅ All RKLLM parameters now configurable: top_k, top_p, temperature, repeat_penalty, etc.
- ✅ Hardware settings configurable: NPU cores, CPU mask, thread count
- ✅ Settings automatically loaded during model initialization
- ✅ User can modify parameters without code changes

**Smart Model Loading**:
- ✅ Model manager now checks if requested model is already loaded
- ✅ Skips unnecessary reload operations (prevents hanging)
- ✅ Only unloads and reloads when switching between different models
- ✅ Eliminated `rkllm_destroy()` hanging issue

**Performance Monitoring**:
- ✅ Streaming responses now include RKLLM performance stats in final chunk
- ✅ Benchmark script fixed to not overwrite RKLLM's generate_time_ms
- ✅ Accurate tokens/sec calculations from NPU's real timing data

**Output Quality**:
- ✅ Tested with user's preferred parameters (top_k=20, top_p=0.95, temp=0.6)
- ✅ Confirmed coherent, on-topic output generation
- ✅ Qwen3-0.6B producing good quality responses (~23 tok/s)

#### Benchmark System Improvements
- ✅ Fixed model name in benchmark filenames (now includes model name)
- ✅ Fixed prompt capture (added `prompt_text` field to PerformanceMetrics)
- ✅ Implemented auto-loading of models (API auto-loads if no model loaded)
- ✅ Added 5-second stabilization wait after model load
- ✅ Fixed streaming token generation (was accumulating but not yielding)
- ✅ Updated RKLLM parameter defaults (top_k, repeat_penalty)
- ✅ Added virtual environment activation reminders to docs

#### Critical Realization: We Have REAL Hardware!
**Issue**: Was using mock/placeholder responses despite having:
- ✅ Real Orange Pi 5 Max hardware (16GB RAM)
- ✅ Real Rockchip RK3588 NPU
- ✅ RKLLM runtime library installed (`/usr/lib/librkllmrt.so`)
- ✅ RKLLM drivers functional
- ✅ 3 real .rkllm models ready to use

**Decision**: STOP using mocks, implement REAL RKLLM integration NOW!

#### RKLLM Parameters Clarification
- User corrected: `top_k should be 20` (not 1 as in docs)
- Need to verify actual recommended defaults vs documentation defaults
- Current understanding from docs:
  - `top_k = 1` (greedy in docs, but user says 20)
  - `top_p = 0.9`
  - `temperature = 0.8`
  - `repeat_penalty = 1.1`

**Next Immediate Action**: Implement real RKLLM ctypes bindings for actual NPU inference

## Notes

- This document will be continuously updated as development progresses
- All major decisions should be documented in the Decision Log
- Implementation details will be refined based on testing and performance analysis
- Developer has final authority on all technical implementation decisions
- Refer to official SDK documentation at `/external/rknn-llm/doc/` for detailed specifications
### Session: October 20, 2025 - Friendly Names + Context Detection + Model Swapping

#### Friendly Model Names Implementation
- ✅ Implemented friendly name system for better UX
- ✅ Created model cache with multiple lookup keys
- ✅ Friendly names: `qwen3-0.6b`, `gemma3-270m`, `gemma3-1b`
- ✅ Dynamic context detection from filename (ctx16384 → 16K, no ctx → 4K)
- ✅ Flexible model lookup: accepts friendly name, filename, or normalized name
- ✅ `/v1/models` endpoint now returns friendly names
- ✅ All APIs accept friendly names for model loading

**Implementation Details:**
- `_create_friendly_name()` - Maps long filenames to short names
- `_extract_context_size()` - Extracts ctx from filename, defaults to 4096
- `_discover_models()` - Builds cache on startup
- `find_model_path()` - O(1) lookup by any identifier
- `get_model_details()` - Returns full model info including context_size

#### Automatic Model Swapping
- ✅ Updated `load_model()` to automatically unload old model
- ✅ Seamless swapping: load new model → old model destroyed first
- ✅ Still skips reload if same model requested
- ✅ No more "model already loaded" errors when switching models

#### RoPE and Context Analysis
- ✅ Created comprehensive RoPE documentation (`docs/rope_and_context.md`)
- ✅ Confirmed context size is BAKED INTO .rkllm file at conversion time
- ✅ Cannot change context at runtime - must reconvert models
- ✅ Current models:
  - qwen3-0.6b: 16K context ✅
  - gemma3-270m: 16K context ✅
  - gemma3-1b: 4K context ⚠️ (needs reconversion)
- ✅ System has 16GB RAM - can easily handle 32K-64K contexts
- ✅ LongRoPE support requires RKLLM 1.2.2 upgrade + model reconversion

#### Gemma3-270m Benchmark Results
- ✅ Ran comprehensive 10-test benchmark suite
- ✅ Generated detailed report (`benchmarks/benchmark_report_gemma3_270m.md`)
- **Performance**: 29.80 tokens/sec average (excellent for 270M model!)
- **Context**: Full 16K context available
- **Memory**: 602 MB RAM usage
- **TTFT**: 85.67ms average
- **Success Rate**: 100% (10/10 tests passed)
- **Note**: Some tests hit 4095 token limit (max_tokens parameter, not model limit)

**Comparison Summary:**
| Model | Speed | Context | Memory | Notes |
|-------|-------|---------|--------|-------|
| **Qwen3-0.6B** | 15.59 tok/s | 16K | 890 MB | Quality-focused |
| **Gemma3-270m** | 29.80 tok/s | 16K | 602 MB | **Fastest!** |
| **Gemma3-1B** | 13.50 tok/s | 4K | 1243 MB | Needs reconversion |

#### Documentation Updates
- ✅ Created `docs/friendly_names_implementation.md` - Complete implementation guide
- ✅ Created `docs/rope_and_context.md` - RoPE and context extension guide
- ✅ Updated README.md with:
  - New phase status (Friendly Names + Dynamic Context)
  - Benchmark results for all 3 models
  - Current focus and next steps
- ✅ Updated copilot.md with session notes

#### Repository Commit
- ✅ All changes ready for commit
- ✅ Documentation up to date
- ✅ Benchmarks completed
- ✅ Server stable and tested

**Files Modified:**
- `src/models/model_manager.py` - Friendly names + auto model swapping
- `src/api/openai_routes.py` - Use friendly names in API
- `src/main.py` - Disabled auto-reload for stability
- `README.md` - Updated project status and benchmarks
- `docs/copilot.md` - Session notes (this file)

**Files Created:**
- `docs/friendly_names_implementation.md` - Implementation documentation
- `docs/rope_and_context.md` - RoPE and context guide
- `benchmarks/benchmark_gemma3_270m_unlimited_20251020_140855.json` - Raw benchmark data
- `benchmarks/benchmark_report_gemma3_270m.md` - Comprehensive report (79KB)

**Next Steps:**
1. ⏳ Commit all changes to repository
2. ⏳ Implement prompt caching system (Phase 4)
3. ⏳ Explore LongRoPE support (requires RKLLM 1.2.2)
4. ⏳ Reconvert gemma3-1b with 16K context
5. ⏳ Test multi-instance model serving

#### Model Quality Issue - Gemma3-270m REMOVED (October 20, 2025)

**Critical Finding:**
- ✅ Gemma3-270m showed excellent performance metrics (29.80 tok/s, 602 MB)
- ❌ **Output quality completely broken** - produces repetitive garbage
- ❌ Gets stuck in repetition loops
- ❌ Degrades into word salad ("Machine Machine Machine...")
- ❌ 0/10 benchmark tests produced usable output

**Example Failure:**
Prompt: "Artificial intelligence and machine learning are revolutionizing..."
Output: Repeats input 20+ times, then degrades to nonsense

**Root Cause:**
Likely poor w8a8 quantization or model conversion issues. Some models don't convert well to NPU.

**Action Taken:**
- ✅ Model file removed from /models/
- ✅ Benchmarks moved to /benchmarks/removed/
- ✅ Documentation updated to warn against this model
- ✅ Created quality assessment: docs/MODEL_QUALITY_GEMMA3_270M_FAILURE.md

**Lesson Learned:**
**Speed metrics are meaningless if output is garbage.** Always validate quality, not just performance.

**Current Working Models:**
- ✅ **Qwen3-0.6B**: 15.59 tok/s, excellent quality - **RECOMMENDED**
- ✅ **Gemma3-1B**: 13.50 tok/s, good quality (needs 16K reconversion)

#### Qwen3-4B Benchmark Timeout Investigation (October 20, 2025 - Evening)

**Issue Discovered:**
- User noticed tests 7-10 failed with timeout during Qwen3-4B benchmark
- **Root Cause**: Default timeout was **300 seconds (5 minutes)**
- Qwen3-4B generates at ~3 tok/s (5x slower than 0.6B)
- Longer prompts + thorough responses exceeded 5-minute limit

**Timeout Configuration:**
```python
# scripts/benchmark.py - Line 135
def __init__(self, base_url: str = "http://localhost:8080", timeout: int = 300):
    self.timeout = timeout  # Default: 5 minutes
```

**Solution Implemented:**
- ✅ Re-running benchmark with `--timeout 3600` (1 hour)
- ✅ Started at 17:03:30 (October 20, 2025)
- ✅ Process ID: 219359
- ✅ Output file: `benchmarks/benchmark_qwen3_4b_no_timeout_20251020_170330.json`

**Expected Results:**
- All 10 tests should complete (including previous 7-10 failures)
- Total runtime: 40-60 minutes estimated
- Quality validation for all test types
- Complete performance metrics

**Friendly Name Verification:**
- ✅ `qwen3-0.6b` - Correctly identifies 0.6B model
- ✅ `qwen3-4b` - Correctly identifies 4B model (NEW!)
- ✅ `gemma3-1b` - Correctly identifies 1B model
- ✅ Names already properly distinguished in model cache

**Status**: 
- 🔄 Benchmark running in background (nohup)
- ⏱️ Expected completion: ~18:00-18:30
- 📊 Will provide complete quality assessment when finished

#### Qwen3-4B Production Feasibility Assessment (October 20, 2025 - 18:00)

**Conclusion: NOT PRODUCTION VIABLE**

**Performance Analysis:**
- **Speed**: 3.13 tokens/sec (RK3588 @ max frequency)
- **Minimum Required**: 5 tokens/sec for acceptable UX
- **Gap**: 60% too slow (1.6x below minimum threshold)

**Hardware Already Optimized:**
- ✅ NPU: 1.0 GHz (max frequency locked)
- ✅ CPU Big Cores: 2.3 GHz (max frequency locked)
- ✅ GPU: 1.0 GHz (max frequency locked)
- ✅ DDR: 2.1 GHz (max frequency locked)
- ✅ Frequency script already applied permanently

**Quality vs Speed Trade-off:**
- **Qwen3-4B**: Excellent quality, genuine reasoning ⭐⭐⭐ BUT 3.13 tok/s ❌
- **Qwen3-0.6B**: Good quality, fast inference ⭐⭐ AND 15.59 tok/s ✅
- **Verdict**: 5x speed gain worth minor quality drop for production

**Model Size vs Performance (RK3588):**
```
Model Size    Speed (tok/s)    Production Viable
---------     -------------    -----------------
0.5-0.6B      30-45            ✅ EXCELLENT (too fast to utilize)
0.6-1.1B      15-24            ✅ GOOD (recommended range)
1.5-2.0B      8-16             ✅ ACCEPTABLE (upper limit)
4.0B          3.13             ❌ TOO SLOW (<5 tok/s minimum)
```

**Recommendation:**
- **Production**: Stick with Qwen3-0.6B (15.59 tok/s) or Gemma3-1B (13.50 tok/s)
- **Development**: Can use Qwen3-4B for quality research/testing
- **Sweet Spot**: 1.5B-2B models if available (balance quality + speed)

**Action Items:**
- ✅ Benchmark cancelled (no need to complete with 1hr timeout)
- ✅ Qwen3-4B marked as "research only" in documentation
- ✅ Focus shifted back to optimizing 0.6B-1.5B model range
- ⏳ Consider finding/converting 1.5B or 2B models for testing

**Files to Update:**
- README.md - Mark Qwen3-4B as "TOO SLOW for production"
- Model status docs - Add production viability assessment

---

### Session: October 22, 2025 - Embeddings Postponed + Code Cleanup

#### Embeddings Implementation Attempt

**What Was Built:**
- ✅ Complete embedding API implementation (OpenAI + Ollama endpoints)
- ✅ Schemas: EmbeddingRequest/Response, OllamaEmbeddingRequest/Response
- ✅ Adapters: 4 bidirectional conversion functions (openai/ollama ↔ internal)
- ✅ Model method: get_embeddings() with RKLLM_INFER_GET_LAST_HIDDEN_LAYER mode
- ✅ Auto-loading: Both APIs auto-load "qwen3-0.6b-embedding" model
- ✅ Test suite: scripts/test_embeddings.py with comprehensive validation
- ✅ Context fix: Respects model's 4096 limit (not config's 16384)

**The Problem:**
- Qwen3-Embedding-0.6B_w8a8.rkllm model crashes with RKLLM runtime 1.2.2
- **Symptom 1**: Segmentation fault when calling `clear_kv_cache(False)`
- **Symptom 2**: `rkllm_run` returns error -1 even when avoiding segfault
- **Critical**: Both our server AND HuggingFace example script crash identically
- **Root cause**: Model incompatibility with current runtime (not our code)

**Diagnostic Steps Taken:**
1. ✅ Fixed context length handling (used model's 4096 limit, not config 16384)
2. ✅ Switched to sync mode (disabled is_async to avoid potential issues)
3. ✅ Updated HF example script to use our runtime paths and safe params
4. ✅ Removed segfaulting clear_kv_cache() call
5. ❌ Still failed: rkllm_run returned -1 with RKLLM_INFER_GET_LAST_HIDDEN_LAYER mode

**User Insight:**
- Same embedding model works in user's TechnoCore project
- Suggests environment/setup difference, not model file corruption
- Models are backward compatible (user ran 1.2 models on 1.2.1 runtime successfully)
- Likely model was converted incorrectly or has specific requirements

**Decision: Skip embeddings until verified model available**

**Cleanup Actions Taken:**
- ✅ Commented out embedding endpoints in openai_routes.py (lines 471-575)
- ✅ Commented out embedding endpoints in ollama_routes.py (lines 255-332)
- ✅ Added clear documentation comments explaining why disabled
- ✅ Preserved test scripts in scripts/test_embeddings.py for future validation
- ✅ Removed temp/ folder (outdated HF example scripts)
- ✅ Updated README.md - Removed embedding feature, added to "Next Steps"
- ✅ Updated copilot.md - Documented Phase 4.6 status, marked as POSTPONED

**Current Project Status:**

**✅ Working Features:**
- OpenAI-compatible API (/v1/chat/completions, /v1/models)
- Ollama-compatible API (/api/generate, /api/chat, /api/tags)
- Binary prompt caching (23.5x TTFT speedup)
- Queue-based concurrency (stable parallel requests)
- Config-based inference parameters
- Model management (load, unload, auto-switching)
- Friendly model names with auto-detection

**⏸️ Postponed Features:**
- Embeddings API (model incompatibility, code preserved for future)

**📋 Next Priorities:**
1. LongRoPE implementation (requires model rebuild with toolkit --longrope flag)
2. HuggingFace integration (auto-download & convert)
3. Embeddings (when verified compatible model available)

**Files Modified:**
- src/api/openai_routes.py - Commented out /embeddings endpoint
- src/api/ollama_routes.py - Commented out /embed and /embeddings endpoints
- README.md - Updated features and next steps
- docs/copilot.md - Updated Phase 4 status, added session notes

**Repository State:**
- Clean: temp/ folder removed
- Organized: All embedding code commented (not deleted) for future use
- Documented: Clear explanation of why embeddings disabled
- Ready: For next development phase (LongRoPE or HF integration)

## Phase 6: Performance Optimization (Current)
- **Investigation**:
  - Current performance: ~12 t/s (Qwen3-0.6B opt0-hybrid0).
  - Expected performance: ~32 t/s (per `external/rknn-llm/benchmark.md`).
  - Potential bottlenecks: Optimization level (`opt0` vs `opt1`), Hybrid mode (`hybrid0` vs `hybrid1`), Frequency scaling.
- **Actions**:
  - Downloaded optimized model variants to `models/qwen3-0.6b-variants/`:
    - `opt1`: `Qwen_Qwen3-0.6B-w8a8-opt1-hybrid0-npu3-ctx16384-rk3588.rkllm`
    - `hybrid1`: `Qwen_Qwen3-0.6B-w8a8-opt0-hybrid1-npu3-ctx16384-rk3588.rkllm`
    - `g128`: `Qwen_Qwen3-0.6B-w8a8_g128-opt0-hybrid0-npu3-ctx16384-rk3588.rkllm`
- **Next Steps**:
  - Run benchmarks on new models.
  - Ensure `scripts/fix_freq_rk3588.sh` is run on the device.

### Session: December 14, 2025 - Driver Update Investigation

- **Driver Status**:
  - **Current Version**: 0.9.7 (verified via logs/system).
  - **Available Update**: Found `rknpu_driver_0.9.8_20241009.tar.bz2` in `external/rknn-llm/rknpu-driver/`.
  - **Format**: Source code only (requires kernel compilation).
- **Analysis**:
  - The `rknn-llm` submodule provides the *source code* for the NPU driver, not pre-compiled kernel modules (`.ko` files).
  - Updating the driver requires compiling this source against the specific Linux kernel headers running on the Orange Pi 5.
  - **CRITICAL FINDING**: The current NPU driver is **built-in** to the kernel (`CONFIG_ROCKCHIP_RKNPU=y`), not a loadable module. It cannot be replaced without recompiling the entire kernel image.
  - **Version Mismatch Confirmed**:
    - Kernel Driver: v0.9.7
    - Runtime Library (`librknnrt.so`): v2.3.2
    - Python Toolkit (`rknn-toolkit-lite2`): v2.3.2
    - **Result**: Runtime v2.3.2 sends commands incompatible with Driver v0.9.7, causing the Segfault.
- **Decision**:
  - **Driver Update**: IMPOSSIBLE (requires OS/Kernel update).
  - **Resolution Strategy**: User must update the OS/Kernel to a version with Driver 0.9.8+, OR downgrade the runtime libraries to match Driver 0.9.7 (approx v1.6.0/v2.0.0).
  - **Action**: Document findings and advise user to perform system update (`sudo apt upgrade` or flash newer image).

### Session: December 14, 2025 - System Upgrade Decision

- **Situation**: 
  - Stable Diffusion (UNet) Segfaults confirmed to be caused by Driver (v0.9.7) vs Runtime (v2.3.2) mismatch.
  - Driver v0.9.8 is required but is built-in to the kernel, preventing manual update.
  - `apt full-upgrade` did not bring the newer kernel/driver.
- **Decision**: 
  - **Flash New OS**: User will flash **Ubuntu 22.04 for Orange Pi 5 Max** (Joshua Riek v2.4.0) which supports the hardware and likely contains the updated BSP/Drivers.
  - **Backup**: Code committed to git. Models will be re-downloaded or restored from backup after flashing.
- **Next Steps (After Flash)**:
  1. Clone repository.
  2. Run `scripts/download_models.py` (or copy from backup).
  3. Verify `dmesg | grep rknpu` shows version 0.9.8+.
  4. Resume Stable Diffusion testing.


