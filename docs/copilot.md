# RockchipLlama Design Document

## 📋 Documentation Guidelines for AI Assistants

**IMPORTANT: All documentation files MUST be kept in the `docs/` folder.**

### Critical Development Environment Rules:
1. ⚠️ **ALWAYS activate virtual environment before running Python scripts**
   ```bash
   source venv/bin/activate
   # Then run: python scripts/benchmark.py, etc.
   ```
2. ⚠️ **Server must be run from venv to avoid import errors**
   ```bash
   source venv/bin/activate
   ./start_server.sh
   ```
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
│   ├── BENCHMARK_QUICKREF.md   # Benchmark quick reference
│   └── benchmark_prompts.json  # Test prompts library
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
│       └── settings.py         # Configuration management
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

### Phase 4: Advanced Features (CURRENT - October 20, 2025)

**Short-term Goals:**

#### 4.1: Prompt Caching System ⭐ (Highest Priority)
- [ ] Design prompt cache architecture
  - [ ] Implement prompt hash-based cache key generation
  - [ ] Model-specific cache directories (`cache/{model_name}/`)
  - [ ] Cache metadata tracking (hit rate, size, age)
- [ ] RKLLM KV cache integration
  - [ ] Research RKLLM prompt cache API (if available)
  - [ ] Implement prefill cache save/load
  - [ ] Handle cache invalidation on parameter changes
- [ ] Cache management
  - [ ] LRU eviction policy for size limits
  - [ ] Cache warming for common system prompts
  - [ ] Cache statistics endpoint
- [ ] Testing and validation
  - [ ] Benchmark TTFT before/after caching
  - [ ] Test cache hit/miss scenarios
  - [ ] Measure memory overhead
  - [ ] Document cache configuration
- **Expected Impact**: 50-70% TTFT reduction for repeated system prompts

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

**Phase 4 Success Criteria:**
- ✅ Prompt caching reduces TTFT by ≥50% for cached prompts
- ✅ Multi-batch increases throughput by ≥2x under load
- ✅ LongRoPE enables ≥32K context without quality degradation
- ✅ All features documented and benchmarked
- ✅ Production-ready with configuration examples

### Phase 5: Docker Containerization
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
- **Version**: v1.2.1 / v1.2.2
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
- ✅ Added benchmark prompts library (`docs/benchmark_prompts.json`)
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

```

