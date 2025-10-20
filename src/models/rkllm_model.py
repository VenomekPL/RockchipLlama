"""
RKLLM Model Wrapper - REAL NPU IMPLEMENTATION
Handles RKLLM runtime integration and inference using actual ctypes bindings
"""
import ctypes
import os
import logging
from typing import Optional, Callable, List
from pathlib import Path
import threading

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
        
        # Validate paths
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        if not os.path.exists(lib_path):
            raise FileNotFoundError(f"RKLLM library not found: {lib_path}")
        
        logger.info(f"Initializing REAL RKLLM model: {Path(model_path).name}")
        
    def _callback_impl(self, result, userdata, state):
        """Internal callback for RKLLM - called from C library"""
        try:
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
                logger.error("Generation error")
            elif state == LLMCallState.RKLLM_RUN_NORMAL:
                self.generation_state = state
                if result.contents.text:
                    text = result.contents.text.decode('utf-8')
                    self.generated_text.append(text)
                    # Call user callback if set
                    if self.current_callback:
                        self.current_callback(text)
        except Exception as e:
            logger.error(f"Error in callback: {e}")
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
            inf_params = inference_config['inference_params']
            hw_params = inference_config['hardware']
            
            logger.info(f"  Using config: top_k={inf_params['top_k']}, repeat_penalty={inf_params['repeat_penalty']}")
            
            # Create parameters
            rkllm_param = RKLLMParam()
            rkllm_param.model_path = self.model_path.encode('utf-8')
            rkllm_param.max_context_len = inf_params.get('max_context_len', max_context_len)
            rkllm_param.max_new_tokens = inf_params.get('max_new_tokens', 4096)
            rkllm_param.skip_special_token = inf_params.get('skip_special_token', True)
            rkllm_param.n_keep = -1
            
            # Sampling parameters - from config file
            rkllm_param.top_k = inf_params['top_k']
            rkllm_param.top_p = inf_params['top_p']
            rkllm_param.temperature = inf_params['temperature']
            rkllm_param.repeat_penalty = inf_params['repeat_penalty']
            rkllm_param.frequency_penalty = inf_params.get('frequency_penalty', 0.0)
            rkllm_param.presence_penalty = inf_params.get('presence_penalty', 0.0)
            
            # Mirostat - from config
            rkllm_param.mirostat = inf_params.get('mirostat', 0)
            rkllm_param.mirostat_tau = inf_params.get('mirostat_tau', 5.0)
            rkllm_param.mirostat_eta = inf_params.get('mirostat_eta', 0.1)
            
            # Async mode - from config
            rkllm_param.is_async = inf_params.get('is_async', False)
            
            # Image parameters (empty for text-only)
            rkllm_param.img_start = b""
            rkllm_param.img_end = b""
            rkllm_param.img_content = b""
            
            # Extended parameters - from config
            rkllm_param.extend_param.base_domain_id = 0
            rkllm_param.extend_param.embed_flash = 1  # Store embeddings in flash
            rkllm_param.extend_param.n_batch = 1
            rkllm_param.extend_param.use_cross_attn = 0
            rkllm_param.extend_param.enabled_cpus_num = hw_params.get('num_threads', 4)
            # Use CPU mask from config (default: RK3588 big cores 4-7)
            rkllm_param.extend_param.enabled_cpus_mask = hw_params.get('enabled_cpus_mask', 0xF0)
            
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
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.8,
        top_p: float = 0.9,
        top_k: int = 20,  # User preference
        repeat_penalty: float = 1.1,
        callback: Optional[Callable[[str], None]] = None
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
            
        Returns:
            Generated text
        """
        if not self.handle:
            raise RuntimeError("Model not loaded. Call load() first.")
        
        try:
            logger.info(f"Running REAL NPU inference...")
            logger.debug(f"Prompt length: {len(prompt)} chars")
            
            # Reset state
            self.generated_text = []
            self.generation_state = None
            self.current_callback = callback
            
            # Create input
            rkllm_input = RKLLMInput()
            rkllm_input.role = b"user"
            rkllm_input.enable_thinking = False
            rkllm_input.input_type = RKLLMInputType.RKLLM_INPUT_PROMPT
            rkllm_input.input_data.prompt_input = prompt.encode('utf-8')
            
            # Create infer params
            infer_params = RKLLMInferParam()
            infer_params.mode = RKLLMInferMode.RKLLM_INFER_GENERATE
            infer_params.lora_params = None
            infer_params.prompt_cache_params = None
            infer_params.keep_history = 0  # Don't keep history
            
            # Run inference
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
                raise RuntimeError(f"rkllm_run failed with code: {ret}")
            
            # Return generated text and perf stats
            result = ''.join(self.generated_text)
            logger.info(f"Generated {len(result)} characters")
            
            # Return tuple: (text, perf_stats)
            return result, self.perf_stats
            
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
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
