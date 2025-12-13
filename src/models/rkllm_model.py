"""
RKLLM Model Wrapper - REAL NPU IMPLEMENTATION
Handles RKLLM runtime integration and inference using actual ctypes bindings
"""
import ctypes
import os
import logging
import asyncio
from typing import Optional, Callable, List
from pathlib import Path
import threading
from utils.cache_manager import PromptCacheManager
from utils.system_prompt_generator import SystemPromptGenerator

logger = logging.getLogger(__name__)

# Load RKLLM library
try:
    rkllm_lib = ctypes.CDLL('/usr/lib/librkllmrt.so')
    logger.info("RKLLM library loaded successfully")
except Exception as e:
    logger.error(f"Failed to load RKLLM library: {e}")
    raise

# Define handles and types
RKLLM_Handle_t = ctypes.c_void_p

# Define enums
class LLMCallState:
    RKLLM_RUN_NORMAL  = 0
    RKLLM_RUN_WAITING  = 1
    RKLLM_RUN_FINISH  = 2
    RKLLM_RUN_ERROR   = 3

class RKLLMInputType:
    RKLLM_INPUT_PROMPT      = 0
    RKLLM_INPUT_TOKEN       = 1
    RKLLM_INPUT_EMBED       = 2
    RKLLM_INPUT_MULTIMODAL  = 3

class RKLLMInferMode:
    RKLLM_INFER_GENERATE = 0
    RKLLM_INFER_GET_LAST_HIDDEN_LAYER = 1
    RKLLM_INFER_GET_LOGITS = 2

# Define structures
class RKLLMExtendParam(ctypes.Structure):
    _fields_ = [
        ("base_domain_id", ctypes.c_int32),
        ("embed_flash", ctypes.c_int8),
        ("enabled_cpus_num", ctypes.c_int8),
        ("enabled_cpus_mask", ctypes.c_uint32),
        ("n_batch", ctypes.c_uint8),
        ("use_cross_attn", ctypes.c_int8),
        ("reserved", ctypes.c_uint8 * 104)
    ]

class RKLLMParam(ctypes.Structure):
    _fields_ = [
        ("model_path", ctypes.c_char_p),
        ("max_context_len", ctypes.c_int32),
        ("max_new_tokens", ctypes.c_int32),
        ("top_k", ctypes.c_int32),
        ("n_keep", ctypes.c_int32),
        ("top_p", ctypes.c_float),
        ("temperature", ctypes.c_float),
        ("repeat_penalty", ctypes.c_float),
        ("frequency_penalty", ctypes.c_float),
        ("presence_penalty", ctypes.c_float),
        ("mirostat", ctypes.c_int32),
        ("mirostat_tau", ctypes.c_float),
        ("mirostat_eta", ctypes.c_float),
        ("skip_special_token", ctypes.c_bool),
        ("is_async", ctypes.c_bool),
        ("img_start", ctypes.c_char_p),
        ("img_end", ctypes.c_char_p),
        ("img_content", ctypes.c_char_p),
        ("extend_param", RKLLMExtendParam),
    ]

class RKLLMTokenInput(ctypes.Structure):
    _fields_ = [
        ("input_ids", ctypes.POINTER(ctypes.c_int32)),
        ("n_tokens", ctypes.c_size_t)
    ]

class RKLLMInputUnion(ctypes.Union):
    _fields_ = [
        ("prompt_input", ctypes.c_char_p),
        ("token_input", RKLLMTokenInput),
    ]

class RKLLMInput(ctypes.Structure):
    _fields_ = [
        ("role", ctypes.c_char_p),
        ("enable_thinking", ctypes.c_bool),
        ("input_type", ctypes.c_int),
        ("input_data", RKLLMInputUnion)
    ]

class RKLLMPromptCacheParam(ctypes.Structure):
    """RKLLM Prompt Cache Parameter - for binary NPU state caching
    
    MUST match official rkllm.h structure:
    typedef struct {
        int save_prompt_cache;          // 0=don't save, 1=save
        const char* prompt_cache_path;  // Path to cache file
    } RKLLMPromptCacheParam;
    """
    _fields_ = [
        ("save_prompt_cache", ctypes.c_int),     # 1=save, 0=load (FIRST!)
        ("prompt_cache_path", ctypes.c_char_p)   # Path to binary cache file (SECOND!)
    ]

class RKLLMInferParam(ctypes.Structure):
    _fields_ = [
        ("mode", ctypes.c_int),
        ("lora_params", ctypes.c_void_p),
        ("prompt_cache_params", ctypes.c_void_p),
        ("keep_history", ctypes.c_int)
    ]

class RKLLMPerfStat(ctypes.Structure):
    _fields_ = [
        ("prefill_time_ms", ctypes.c_float),
        ("prefill_tokens", ctypes.c_int),
        ("generate_time_ms", ctypes.c_float),
        ("generate_tokens", ctypes.c_int),
        ("memory_usage_mb", ctypes.c_float)
    ]

class RKLLMResultLastHiddenLayer(ctypes.Structure):
    _fields_ = [
        ("hidden_states", ctypes.POINTER(ctypes.c_float)),
        ("embd_size", ctypes.c_int),
        ("num_tokens", ctypes.c_int)
    ]

class RKLLMResultLogits(ctypes.Structure):
    _fields_ = [
        ("logits", ctypes.POINTER(ctypes.c_float)),
        ("vocab_size", ctypes.c_int),
        ("num_tokens", ctypes.c_int)
    ]

class RKLLMResult(ctypes.Structure):
    _fields_ = [
        ("text", ctypes.c_char_p),
        ("token_id", ctypes.c_int),
        ("last_hidden_layer", RKLLMResultLastHiddenLayer),
        ("logits", RKLLMResultLogits),
        ("perf", RKLLMPerfStat)
    ]


class RKLLMModel:
    """Wrapper for REAL RKLLM runtime inference on NPU"""
    
    # Global callback storage
    _callback_storage = {}
    _callback_lock = threading.Lock()
    _unloading = False
    
    # Phase 4.2: Multi-batch inference semaphore
    # Limits concurrent inference requests to match n_batch parameter
    # NOTE: This will be updated in load() based on config n_batch value
    _batch_semaphore = None  # Initialized in load()
    _batch_size = 1  # Current n_batch value
    
    def __init__(self, model_path: str, lib_path: str = "/usr/lib/librkllmrt.so"):
        """
        Initialize RKLLM model
        
        Args:
            model_path: Path to .rkllm model file
            lib_path: Path to librkllmrt.so library
        """
        self.model_path = model_path
        self.lib_path = lib_path
        self.handle = None
        self.lib = rkllm_lib
        
        # Streaming state
        self.current_callback = None
        self.generated_text = []
        self.generation_state = None
        self.perf_stats = None  # Will be populated by callback
        self.current_max_tokens = -1  # No limit by default
        self.current_stop_sequences = [] # Stop sequences
        
        # Cache management
        self.cache_manager = PromptCacheManager()
        self.system_prompt_generator = SystemPromptGenerator()
        self.model_name = None  # Set in load() method
        
        # Initialize state tracking for smart caching
        self.npu_context = ""
        
        # Validate paths
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        if not os.path.exists(lib_path):
            raise FileNotFoundError(f"RKLLM library not found: {lib_path}")
        
        logger.info(f"Initializing REAL RKLLM model: {Path(model_path).name}")
        
    def _callback_impl(self, result, userdata, state):
        """Internal callback for RKLLM - called from C library"""
        try:
            # Check token limit
            if self.current_max_tokens > 0 and len(self.generated_text) >= self.current_max_tokens:
                logger.info(f"🛑 Max tokens reached ({self.current_max_tokens}), stopping generation")
                return 1  # Stop generation

            # Check stop sequences
            if self.current_stop_sequences:
                # We only need to check the last few tokens + new token to be efficient
                # But for simplicity, let's check the tail of the generated text
                # Construct the tail text (enough to cover the longest stop sequence)
                # Assuming max stop sequence is not huge (e.g. < 100 chars)
                tail_len = 200 
                current_tail = "".join(self.generated_text[-tail_len:])
                
                for stop_seq in self.current_stop_sequences:
                    if stop_seq in current_tail:
                        logger.info(f"🛑 Stop sequence '{stop_seq}' found, stopping generation")
                        # return 1 # DISABLED to debug crash
                        pass


            # logger.info(f"🔔 Callback called: state={state}")
            if state == LLMCallState.RKLLM_RUN_FINISH:
                self.generation_state = state
                # Extract final performance stats
                if result and result.contents:
                    perf = result.contents.perf
                    self.perf_stats = {
                        'prefill_time_ms': perf.prefill_time_ms,
                        'prefill_tokens': perf.prefill_tokens,
                        'generate_time_ms': perf.generate_time_ms,
                        'generate_tokens': perf.generate_tokens,
                        'memory_usage_mb': perf.memory_usage_mb
                    }
                    logger.debug(f"Performance stats: {self.perf_stats}")
                logger.debug("Generation finished")
            elif state == LLMCallState.RKLLM_RUN_ERROR:
                self.generation_state = state
                logger.error("❌ Generation error in callback")
            elif state == LLMCallState.RKLLM_RUN_NORMAL:
                self.generation_state = state
                # logger.info(f"📝 RKLLM_RUN_NORMAL: result={result}, contents={result.contents if result else 'None'}")
                if result and result.contents:
                    text_ptr = result.contents.text
                    # logger.info(f"📝 text_ptr={text_ptr}, type={type(text_ptr)}")
                    if text_ptr is not None:
                        text = text_ptr.decode('utf-8') if isinstance(text_ptr, bytes) else str(text_ptr)
                        # logger.info(f"📝 Got text token: {repr(text)} (len={len(text)})")
                        if text:  # Only append if non-empty
                            self.generated_text.append(text)
                            # Call user callback if set
                            if self.current_callback:
                                self.current_callback(text)
                    else:
                        logger.warning("⚠️  RKLLM_RUN_NORMAL but text_ptr is None")
                else:
                    logger.warning("⚠️  RKLLM_RUN_NORMAL but no result or contents")
        except Exception as e:
            logger.error(f"Error in callback: {e}", exc_info=True)
        return 0
        
    def load(self, max_context_len: int = 512, num_npu_core: int = 3):
        """
        Load model into NPU memory
        
        Args:
            max_context_len: Maximum context length
            num_npu_core: Number of NPU cores to use (RK3588 has 3)
        """
        try:
            # Load inference configuration
            from config.settings import inference_config
            
            logger.info(f"Loading REAL RKLLM model: {self.model_path}")
            logger.info(f"  Max context: {max_context_len}, NPU cores: {num_npu_core}")
            
            # Get config params
            model_defaults = inference_config['model_defaults']
            inf_params = inference_config['inference_params']
            hw_params = inference_config['hardware']
            
            logger.info(f"  Using config: top_k={inf_params['top_k']}, repeat_penalty={inf_params['repeat_penalty']}, n_batch={hw_params['n_batch']}")
            
            # Create parameters
            rkllm_param = RKLLMParam()
            rkllm_param.model_path = self.model_path.encode('utf-8')
            
            # Model defaults - RESPECT passed max_context_len over config (already validated by model_manager)
            rkllm_param.max_context_len = max_context_len  # Use passed parameter (model-specific)
            rkllm_param.max_new_tokens = model_defaults.get('max_new_tokens', 4096)
            rkllm_param.skip_special_token = model_defaults.get('skip_special_token', True)
            rkllm_param.n_keep = model_defaults.get('n_keep', -1)
            
            logger.info(f"  📝 max_new_tokens={rkllm_param.max_new_tokens}, max_context_len={rkllm_param.max_context_len}")
            
            # Sampling parameters - from config file
            rkllm_param.top_k = inf_params['top_k']
            rkllm_param.top_p = inf_params['top_p']
            rkllm_param.temperature = inf_params['temperature']
            rkllm_param.repeat_penalty = inf_params['repeat_penalty']
            
            logger.info(f"  🎲 temperature={rkllm_param.temperature}, top_p={rkllm_param.top_p}, top_k={rkllm_param.top_k}")
            rkllm_param.frequency_penalty = inf_params.get('frequency_penalty', 0.0)
            rkllm_param.presence_penalty = inf_params.get('presence_penalty', 0.0)
            
            # Log ignored parameters
            if 'min_p' in inf_params:
                logger.warning(f"⚠️  min_p={inf_params['min_p']} found in config but NOT supported by RKLLM runtime (ignored)")
            if 'seed' in inf_params:
                logger.warning(f"⚠️  seed={inf_params['seed']} found in config but NOT supported by RKLLM runtime (ignored)")
            
            # Mirostat - from config
            rkllm_param.mirostat = inf_params.get('mirostat', 0)
            rkllm_param.mirostat_tau = inf_params.get('mirostat_tau', 5.0)
            rkllm_param.mirostat_eta = inf_params.get('mirostat_eta', 0.1)
            
            # Async mode - from config
            rkllm_param.is_async = model_defaults.get('is_async', False)
            logger.info(f"  🔄 is_async mode: {rkllm_param.is_async}")
            
            # Image parameters (empty for text-only)
            rkllm_param.img_start = b""
            rkllm_param.img_end = b""
            rkllm_param.img_content = b""
            
            # Extended parameters - ALL from config now!
            rkllm_param.extend_param.base_domain_id = hw_params.get('base_domain_id', 0)
            rkllm_param.extend_param.embed_flash = hw_params.get('embed_flash', 1)
            n_batch = hw_params.get('n_batch', 3)
            rkllm_param.extend_param.n_batch = n_batch
            rkllm_param.extend_param.use_cross_attn = hw_params.get('use_cross_attn', 0)
            rkllm_param.extend_param.enabled_cpus_num = hw_params.get('enabled_cpus_num', 4)
            rkllm_param.extend_param.enabled_cpus_mask = hw_params.get('enabled_cpus_mask', 0xF0)
            
            # Initialize batch semaphore based on n_batch from config
            if RKLLMModel._batch_semaphore is None or RKLLMModel._batch_size != n_batch:
                RKLLMModel._batch_size = n_batch
                RKLLMModel._batch_semaphore = asyncio.Semaphore(n_batch)
                logger.info(f"📊 Batch semaphore initialized: {n_batch} concurrent slots")

            
            # Create callback
            callback_type = ctypes.CFUNCTYPE(
                ctypes.c_int, 
                ctypes.POINTER(RKLLMResult), 
                ctypes.c_void_p, 
                ctypes.c_int
            )
            callback = callback_type(self._callback_impl)
            
            # Store callback to prevent garbage collection
            with self._callback_lock:
                self._callback_storage[id(self)] = callback
            
            # Initialize RKLLM
            self.handle = RKLLM_Handle_t()
            
            rkllm_init = self.lib.rkllm_init
            rkllm_init.argtypes = [
                ctypes.POINTER(RKLLM_Handle_t), 
                ctypes.POINTER(RKLLMParam), 
                callback_type
            ]
            rkllm_init.restype = ctypes.c_int
            
            ret = rkllm_init(ctypes.byref(self.handle), ctypes.byref(rkllm_param), callback)
            
            if ret != 0:
                raise RuntimeError(f"rkllm_init failed with code: {ret}")
            
            logger.info(f"✅ REAL RKLLM model loaded successfully on NPU!")
            
            # Initialize chat template function
            try:
                self.rkllm_set_chat_template = self.lib.rkllm_set_chat_template
                self.rkllm_set_chat_template.argtypes = [
                    RKLLM_Handle_t, 
                    ctypes.c_char_p, 
                    ctypes.c_char_p, 
                    ctypes.c_char_p
                ]
                self.rkllm_set_chat_template.restype = ctypes.c_int
            except AttributeError:
                logger.warning("⚠️  rkllm_set_chat_template not found in library (older version?)")

            # Initialize KV cache clear function
            try:
                self.rkllm_clear_kv_cache = self.lib.rkllm_clear_kv_cache
                self.rkllm_clear_kv_cache.argtypes = [
                    RKLLM_Handle_t,
                    ctypes.c_int,
                    ctypes.POINTER(ctypes.c_int),
                    ctypes.POINTER(ctypes.c_int)
                ]
                self.rkllm_clear_kv_cache.restype = ctypes.c_int
                logger.info("✅ rkllm_clear_kv_cache bound successfully")
            except AttributeError:
                logger.warning("⚠️  rkllm_clear_kv_cache not found in library")
                self.rkllm_clear_kv_cache = None

            # DISABLED: We handle chat templating manually in openai_routes.py
                # Calling this disables internal parsing but might also interfere with our manual formatting
                # if not careful. Since we send the full formatted string as a single "prompt",
                # we don't want RKLLM to wrap it again.
                
                # chat_tmpl = inference_config.get('chat_template', {})
                # if chat_tmpl:
                #     self.set_chat_template(
                #         system_prompt=chat_tmpl.get('system_prompt', ''),
                #         prefix=chat_tmpl.get('user_prefix', ''),
                #         postfix=chat_tmpl.get('assistant_prefix', '')
                #     )
            except AttributeError:
                logger.warning("⚠️  rkllm_set_chat_template not found in library (older version?)")
            except Exception as e:
                logger.error(f"Error setting up chat template: {e}")
            
            # Set model name from path (extract folder name)
            self.model_name = Path(self.model_path).parent.name
            logger.info(f"Model name set to: {self.model_name}")
            
            # Auto-generate system prompt cache if it doesn't exist
            self._ensure_system_cache()
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise
    
    def _ensure_system_cache(self):
        """
        Ensure system prompt cache exists for this model.
        If not, generate it from config/system.txt.
        This is a BLOCKING operation - model won't be ready until cache is created.
        
        NOTE: Disabled in favor of manual binary cache creation via API.
        Use POST /v1/cache/{model} to create binary caches.
        """
        # Old text cache auto-generation removed
        # Binary caches must be created explicitly via API for better control
        logger.info(f"System cache auto-generation disabled. Create caches via POST /v1/cache/{self.model_name}")
        return
    
    def set_chat_template(self, system_prompt: str, prefix: str, postfix: str):
        """
        Set the chat template for the LLM.
        
        Args:
            system_prompt: System prompt content
            prefix: User prompt prefix (e.g. "<|user|>\n")
            postfix: User prompt postfix (e.g. "<|assistant|>\n")
        """
        if not self.handle:
            raise RuntimeError("Model not loaded. Call load() first.")
            
        try:
            if not hasattr(self, 'rkllm_set_chat_template'):
                logger.warning("rkllm_set_chat_template not available")
                return

            logger.info(f"Setting chat template: system_len={len(system_prompt)}")
            
            ret = self.rkllm_set_chat_template(
                self.handle,
                system_prompt.encode('utf-8'),
                prefix.encode('utf-8'),
                postfix.encode('utf-8')
            )
            
            if ret != 0:
                logger.error(f"rkllm_set_chat_template failed with code: {ret}")
                raise RuntimeError(f"Failed to set chat template: {ret}")
                
            logger.info("✅ Chat template set successfully")
            
        except Exception as e:
            logger.error(f"Error setting chat template: {e}")
            raise

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.8,
        top_p: float = 0.9,
        top_k: int = 20,  # User preference
        repeat_penalty: float = 1.1,
        callback: Optional[Callable[[str], None]] = None,
        binary_cache_path: Optional[str] = None,
        save_binary_cache: bool = False,
        stop: Optional[List[str]] = None
    ) -> tuple[str, Optional[dict]]:
        """
        Generate text completion using REAL NPU
        
        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter (user set to 20)
            repeat_penalty: Repetition penalty
            callback: Optional streaming callback function
            binary_cache_path: Path to binary cache file (.rkllm_cache)
            save_binary_cache: If True, save NPU state to binary_cache_path after prefill
            stop: Optional list of stop sequences
            
        Returns:
            (Generated text, performance stats dict)
        """
        if not self.handle:
            raise RuntimeError("Model not loaded. Call load() first.")
        
        try:
            logger.info(f"Running REAL NPU inference...")
            logger.debug(f"Prompt length: {len(prompt)} chars")
            
            # Smart Caching Logic
            # Check if the new prompt is a continuation of the current NPU context
            should_clear = True
            input_prompt = prompt
            
            if self.npu_context and prompt.startswith(self.npu_context):
                # Optimization: Only send the new part (delta)
                delta = prompt[len(self.npu_context):]
                if delta:
                    logger.info(f"♻️ Smart Cache Hit: Sending delta ({len(delta)} chars)")
                    input_prompt = delta
                    should_clear = False
                else:
                    # Exact match? Weird but possible. Send empty or just clear to be safe.
                    logger.warning("⚠️ Smart Cache: Exact match with context, clearing to be safe")
            
            if should_clear:
                # Context switch or first run
                if hasattr(self, 'rkllm_clear_kv_cache') and self.rkllm_clear_kv_cache:
                    ret = self.rkllm_clear_kv_cache(self.handle, 0, None, None)
                    if ret == 0:
                        logger.debug("🧹 Smart Cache: Context switch, KV cache cleared")
                        self.npu_context = ""
                    else:
                        logger.warning(f"⚠️  Failed to clear KV cache: {ret}")
            
            if binary_cache_path:
                action = "Saving to" if save_binary_cache else "Loading from"
                logger.info(f"🔥 Binary cache: {action} {binary_cache_path}")
            
            # Reset state
            self.generated_text = []
            self.generation_state = None
            self.current_callback = callback
            self.current_max_tokens = max_new_tokens
            
            # Set stop sequences (default to common ones if not provided)
            self.current_stop_sequences = stop if stop else ["<|im_end|>", "<|endoftext|>"]
            
            # Create input
            rkllm_input = RKLLMInput()
            rkllm_input.role = b"user"
            
            # Enable thinking from config
            from config.settings import inference_config
            enable_thinking = inference_config['model_defaults'].get('enable_thinking', False)
            rkllm_input.enable_thinking = enable_thinking
            if enable_thinking:
                logger.info("🧠 Thinking mode ENABLED")
            
            rkllm_input.input_type = RKLLMInputType.RKLLM_INPUT_PROMPT
            
            # Keep reference to bytes to prevent GC
            self._current_prompt_bytes = input_prompt.encode('utf-8')
            rkllm_input.input_data.prompt_input = self._current_prompt_bytes
            
            # Create infer params
            infer_params = RKLLMInferParam()
            infer_params.mode = RKLLMInferMode.RKLLM_INFER_GENERATE
            infer_params.lora_params = None
            infer_params.keep_history = 0  # Don't keep history
            
            # Setup binary prompt cache if provided
            prompt_cache = None
            self._current_cache_path_bytes = None # Keep ref
            
            if binary_cache_path:
                prompt_cache = RKLLMPromptCacheParam()
                prompt_cache.save_prompt_cache = 1 if save_binary_cache else 0
                self._current_cache_path_bytes = binary_cache_path.encode('utf-8')
                prompt_cache.prompt_cache_path = self._current_cache_path_bytes
                
                infer_params.prompt_cache_params = ctypes.cast(
                    ctypes.pointer(prompt_cache),
                    ctypes.c_void_p
                )
                action = "save" if save_binary_cache else "load"
                logger.info(f"Binary cache: {action} at {binary_cache_path}")
            else:
                infer_params.prompt_cache_params = None
            
            # Run inference - use async if configured
            from config.settings import inference_config
            is_async_mode = inference_config['model_defaults'].get('is_async', False)
            
            if is_async_mode:
                logger.debug("🔄 Using rkllm_run_async (non-blocking)")
                rkllm_run = self.lib.rkllm_run_async
            else:
                logger.debug("🔒 Using rkllm_run (blocking)")
                rkllm_run = self.lib.rkllm_run
            
            rkllm_run.argtypes = [
                RKLLM_Handle_t, 
                ctypes.POINTER(RKLLMInput), 
                ctypes.POINTER(RKLLMInferParam), 
                ctypes.c_void_p
            ]
            rkllm_run.restype = ctypes.c_int
            
            ret = rkllm_run(
                self.handle, 
                ctypes.byref(rkllm_input), 
                ctypes.byref(infer_params), 
                None
            )
            
            if ret != 0:
                raise RuntimeError(f"rkllm_run(_async) failed with code: {ret}")
            
            # If async mode, wait for completion
            if is_async_mode:
                import time
                rkllm_is_running = self.lib.rkllm_is_running
                rkllm_is_running.argtypes = [RKLLM_Handle_t]
                rkllm_is_running.restype = ctypes.c_int
                
                logger.info("⏳ Waiting for async inference to complete...")
                # Give it a moment to start
                time.sleep(0.01)  # 10ms initial delay
                # NOTE: rkllm_is_running returns 1 while running, 0 when done
                poll_count = 0
                while rkllm_is_running(self.handle) == 1:  # 1 = still running
                    time.sleep(0.001)  # Poll every 1ms
                    poll_count += 1
                logger.info(f"✅ Async inference complete (polled {poll_count} times)")
            
            # Log binary cache result
            if binary_cache_path and save_binary_cache:
                if os.path.exists(binary_cache_path):
                    size_mb = os.path.getsize(binary_cache_path) / (1024 * 1024)
                    logger.info(f"✅ Binary cache saved: {size_mb:.2f} MB")
                else:
                    logger.warning(f"⚠️  Binary cache not created at {binary_cache_path}")
            
            # Return generated text and perf stats
            logger.info(f"📦 generated_text list has {len(self.generated_text)} items: {self.generated_text[:5]}")
            result = ''.join(self.generated_text)
            logger.info(f"Generated {len(result)} characters: {repr(result[:100])}")
            
            # Update NPU context for next run
            # The new context is the full prompt + what was just generated
            self.npu_context = prompt + result
            
            # Return tuple: (text, perf_stats)
            return result, self.perf_stats
            
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            raise
    
    async def generate_async(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.8,
        top_p: float = 0.9,
        top_k: int = 20,
        repeat_penalty: float = 1.1,
        callback: Optional[Callable[[str], None]] = None,
        binary_cache_path: Optional[str] = None,
        save_binary_cache: bool = False,
        stop: Optional[List[str]] = None
    ) -> tuple[str, Optional[dict]]:
        """
        Async wrapper for generate() with batch slot queueing
        
        Phase 4.2: Multi-batch inference with automatic queuing.
        Limits concurrent requests to n_batch (configurable, default 3 for RK3588).
        Requests beyond n_batch are automatically queued and processed as slots free.
        
        Args: Same as generate()
        
        Returns: Same as generate() - (Generated text, performance stats dict)
        """
        # Ensure semaphore is initialized (should be done in load(), but safety check)
        if self._batch_semaphore is None:
            raise RuntimeError("Model not loaded. Call load() first to initialize batch semaphore.")
        
        # Acquire batch slot (auto-queues if all slots busy)
        async with self._batch_semaphore:
            # Log queue depth if waiting
            waiting = self._batch_size - self._batch_semaphore._value
            if waiting > 0:
                logger.info(f"📊 Batch slots: {waiting}/{self._batch_size} active")
            
            # Run synchronous generate in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,  # Use default executor
                lambda: self.generate(
                    prompt=prompt,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    repeat_penalty=repeat_penalty,
                    callback=callback,
                    binary_cache_path=binary_cache_path,
                    save_binary_cache=save_binary_cache,
                    stop=stop
                )
            )
            return result
    
    async def get_embeddings(
        self,
        text: str,
        inference_config: dict
    ) -> tuple[list[float], dict]:
        """
        Extract embeddings (hidden states) for the given text
        
        Uses RKLLM_INFER_GET_LAST_HIDDEN_LAYER mode to get the final
        layer's hidden states, then normalizes them to unit vectors.
        
        Args:
            text: Input text to embed
            inference_config: Configuration dict (not heavily used for embeddings)
            
        Returns:
            (embedding_vector, stats_dict) where:
                - embedding_vector is a list of floats (normalized)
                - stats_dict contains tokens_processed, time_ms, embedding_dim
        """
        if not self.handle:
            raise RuntimeError("Model not loaded")
        
        import time
        import math
        
        logger.info(f"🔍 Generating embeddings for text: {text[:100]}...")
        start_time = time.time()
        
        # Storage for hidden states
        hidden_states_result = {"data": None, "dim": 0, "num_tokens": 0}
        
        def embedding_callback(result_ptr, userdata, state):
            """Callback for embedding extraction"""
            if not result_ptr:
                return 0
            
            result = result_ptr.contents
            
            if state == LLMCallState.RKLLM_RUN_FINISH:
                logger.info("✅ Embedding extraction finished")
                # Extract hidden states
                if result.last_hidden_layer.hidden_states:
                    embd_size = result.last_hidden_layer.embd_size
                    num_tokens = result.last_hidden_layer.num_tokens
                    
                    logger.info(f"📊 Hidden layer: {num_tokens} tokens × {embd_size} dimensions")
                    
                    # Copy the last token's hidden state (common for embeddings)
                    # Total size is num_tokens * embd_size
                    # We want the last token: offset = (num_tokens - 1) * embd_size
                    if num_tokens > 0:
                        offset = (num_tokens - 1) * embd_size
                        hidden_states_result["data"] = [
                            result.last_hidden_layer.hidden_states[offset + i]
                            for i in range(embd_size)
                        ]
                        hidden_states_result["dim"] = embd_size
                        hidden_states_result["num_tokens"] = num_tokens
                else:
                    logger.warning("⚠️  No hidden states in result")
            
            elif state == LLMCallState.RKLLM_RUN_ERROR:
                logger.error("❌ Error during embedding extraction")
            
            return 0
        
        # Register callback
        callback_type = ctypes.CFUNCTYPE(
            ctypes.c_int,
            ctypes.POINTER(RKLLMResult),
            ctypes.c_void_p,
            ctypes.c_int
        )
        callback_c = callback_type(embedding_callback)
        with self._callback_lock:
            self._callback_storage[id(self)] = callback_c
        
        try:
            # Set up input
            rkllm_input = RKLLMInput()
            rkllm_input.role = b"user"
            rkllm_input.enable_thinking = False
            rkllm_input.input_type = RKLLMInputType.RKLLM_INPUT_PROMPT
            rkllm_input.input_data.prompt_input = text.encode('utf-8')
            
            # Set up inference parameters for embedding mode
            infer_params = RKLLMInferParam()
            infer_params.mode = RKLLMInferMode.RKLLM_INFER_GET_LAST_HIDDEN_LAYER
            infer_params.lora_params = None
            infer_params.prompt_cache_params = None
            infer_params.keep_history = 0  # Don't keep history for embeddings
            
            # ALWAYS use sync mode for embeddings (async can cause crashes with embedding models)
            is_async_mode = False
            logger.debug("🔒 Using rkllm_run (sync) for embeddings")
            rkllm_run = self.lib.rkllm_run
            
            rkllm_run.argtypes = [
                RKLLM_Handle_t,
                ctypes.POINTER(RKLLMInput),
                ctypes.POINTER(RKLLMInferParam),
                ctypes.c_void_p
            ]
            rkllm_run.restype = ctypes.c_int
            
            # Run the embedding extraction
            logger.info("⏳ Running embedding extraction...")
            ret = rkllm_run(
                self.handle,
                ctypes.byref(rkllm_input),
                ctypes.byref(infer_params),
                None
            )
            
            if ret != 0:
                raise RuntimeError(f"rkllm_run failed with code {ret}")
            
            # Wait for async completion if needed
            if is_async_mode:
                rkllm_is_running = self.lib.rkllm_is_running
                rkllm_is_running.argtypes = [RKLLM_Handle_t]
                rkllm_is_running.restype = ctypes.c_int
                
                logger.info("⏳ Waiting for async embedding extraction...")
                time.sleep(0.01)  # Initial delay
                poll_count = 0
                while rkllm_is_running(self.handle) == 1:
                    time.sleep(0.001)
                    poll_count += 1
                logger.info(f"✅ Embedding extraction complete (polled {poll_count} times)")
            
            # Check if we got hidden states
            if hidden_states_result["data"] is None:
                raise RuntimeError("Failed to extract hidden states")
            
            # Normalize to unit vector (L2 normalization)
            embedding = hidden_states_result["data"]
            norm = math.sqrt(sum(x * x for x in embedding))
            if norm > 0:
                embedding = [x / norm for x in embedding]
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            stats = {
                "tokens_processed": hidden_states_result["num_tokens"],
                "time_ms": elapsed_ms,
                "embedding_dim": hidden_states_result["dim"]
            }
            
            logger.info(f"✅ Generated {len(embedding)}-dim embedding in {elapsed_ms:.1f}ms")
            
            return embedding, stats
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def unload(self):
        """Unload model and free NPU resources
        
        WARNING: Based on official RKLLM examples, rkllm_destroy() should only 
        be called on server shutdown, not during runtime. Calling it during runtime
        can cause hanging issues. Model swapping is not officially supported.
        """
        if self.handle:
            try:
                logger.warning("Attempting to unload RKLLM model - this may cause issues!")
                logger.warning("Official RKLLM pattern: one model per server lifetime")
                
                # Set a flag to prevent new inference calls
                self._unloading = True
                
                rkllm_destroy = self.lib.rkllm_destroy
                rkllm_destroy.argtypes = [RKLLM_Handle_t]
                rkllm_destroy.restype = ctypes.c_int
                
                logger.info("Calling rkllm_destroy...")
                ret = rkllm_destroy(self.handle)
                
                if ret == 0:
                    logger.info("Model unloaded successfully")
                else:
                    logger.warning(f"rkllm_destroy returned: {ret}")
                
                # Clean up callback
                with self._callback_lock:
                    if id(self) in self._callback_storage:
                        del self._callback_storage[id(self)]
                
                self.handle = None
                self._unloading = False
            except Exception as e:
                logger.error(f"Error during unload: {e}")
                self._unloading = False
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.unload()
