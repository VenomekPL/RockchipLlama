import os
import time
import logging
import numpy as np
from PIL import Image
import asyncio
from typing import List, Optional, Union, Tuple

# Import diffusers for scheduler (Import BEFORE rknnlite to avoid logging conflict)
try:
    from diffusers import LCMScheduler
    from transformers import CLIPTokenizer
except ImportError:
    logging.warning("diffusers or transformers not installed. Stable Diffusion will not work.")
    LCMScheduler = None
    CLIPTokenizer = None

# Try to import rknn_lite, mock if not available (for dev/testing)
try:
    from rknnlite.api import RKNNLite
except ImportError:
    class RKNNLite:
        def __init__(self, verbose=False, verbose_file=''): pass
        def load_rknn(self, path): return 0
        def init_runtime(self, core_mask=0): return 0
        def inference(self, inputs): return [np.zeros((1, 4, 64, 64))] # Mock output
        def release(self): pass

logger = logging.getLogger(__name__)

class StableDiffusionRKNN:
    """
    Stable Diffusion 1.5 LCM implementation for RK3588 NPU using RKNN-Lite.
    """
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.height = 512
        self.width = 512
        self.is_loaded = False
        
        # RKNN Contexts
        self.rknn_text_encoder = None
        self.rknn_unet = None
        self.rknn_vae_decoder = None
        
        # Tokenizer & Scheduler
        self.tokenizer = None
        self.scheduler = None
        
        # Paths
        self.encoder_path = os.path.join(model_dir, "text_encoder.rknn")
        self.unet_path = os.path.join(model_dir, "unet_lcm_512.rknn") # Assuming 512x512
        self.vae_path = os.path.join(model_dir, "vae_decoder.rknn")
        self.vocab_path = os.path.join(model_dir, "tokenizer") # Folder containing vocab.json/merges.txt

    def load(self):
        """Load all models into NPU memory"""
        if self.is_loaded:
            return

        logger.info(f"Loading Stable Diffusion models from {self.model_dir}...")
        
        if not os.path.exists(self.model_dir):
            raise FileNotFoundError(f"Model directory not found: {self.model_dir}")

        # 1. Load Tokenizer & Scheduler
        try:
            # We use the standard CLIP tokenizer. 
            # If local files exist in 'tokenizer' subdir, use them, else download/cache
            if os.path.exists(self.vocab_path):
                logger.info(f"Loading tokenizer from local path: {self.vocab_path}")
                self.tokenizer = CLIPTokenizer.from_pretrained(self.vocab_path)
            else:
                logger.info("Loading tokenizer from huggingface (openai/clip-vit-large-patch14)")
                self.tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-large-patch14")
                
            self.scheduler = LCMScheduler(
                beta_start=0.00085,
                beta_end=0.012,
                beta_schedule="scaled_linear",
                original_inference_steps=50,
                clip_sample=False,
                set_alpha_to_one=False,
            )
        except Exception as e:
            logger.error(f"Failed to load tokenizer/scheduler: {e}")
            raise

        # 2. Load RKNN Models
        self.rknn_text_encoder = self._load_rknn_model(self.encoder_path, "Text Encoder", core_mask=RKNNLite.NPU_CORE_0)
        # U-Net is heavy. Reference script says multi-core causes kernel crash, so use AUTO or single core.
        self.rknn_unet = self._load_rknn_model(self.unet_path, "U-Net", core_mask=RKNNLite.NPU_CORE_AUTO) 
        self.rknn_vae_decoder = self._load_rknn_model(self.vae_path, "VAE Decoder", core_mask=RKNNLite.NPU_CORE_0)

        self.is_loaded = True
        logger.info("✅ Stable Diffusion models loaded successfully")

    def _load_rknn_model(self, path: str, name: str, core_mask: int = 0) -> RKNNLite:
        if not os.path.exists(path):
            raise FileNotFoundError(f"{name} model not found at {path}")
            
        logger.info(f"Loading {name}...")
        rknn = RKNNLite(verbose=False)
        
        ret = rknn.load_rknn(path)
        if ret != 0:
            raise RuntimeError(f"Load {name} failed!")
            
        ret = rknn.init_runtime(core_mask=core_mask)
        if ret != 0:
            raise RuntimeError(f"Init {name} runtime failed!")
            
        return rknn

    def unload(self):
        """Release NPU resources"""
        if self.rknn_text_encoder: self.rknn_text_encoder.release()
        if self.rknn_unet: self.rknn_unet.release()
        if self.rknn_vae_decoder: self.rknn_vae_decoder.release()
        self.is_loaded = False
        logger.info("Stable Diffusion models unloaded")

    async def generate(
        self, 
        prompt: str, 
        num_inference_steps: int = 4, 
        guidance_scale: float = 8.0,
        seed: Optional[int] = None
    ) -> Image.Image:
        """
        Generate an image from text prompt
        """
        if not self.is_loaded:
            self.load()

        loop = asyncio.get_running_loop()
        
        # Run inference in a separate thread to avoid blocking the async loop
        # (RKNN inference is blocking)
        return await loop.run_in_executor(
            None, 
            self._generate_sync, 
            prompt, 
            num_inference_steps, 
            guidance_scale, 
            seed
        )

    def get_guidance_scale_embedding(self, w, embedding_dim=256, dtype=np.float32):
        """
        Generate sinusoidal embedding for guidance scale.
        """
        w = w * 1000.0
        half_dim = embedding_dim // 2
        emb = np.log(10000.0) / (half_dim - 1)
        emb = np.exp(np.arange(half_dim, dtype=dtype) * -emb)
        emb = w[:, None] * emb[None, :]
        emb = np.concatenate([np.sin(emb), np.cos(emb)], axis=1)

        if embedding_dim % 2 == 1:  # zero pad
            emb = np.pad(emb, [(0, 0), (0, 1)])

        return emb.astype(dtype)

    def _generate_sync(self, prompt: str, num_inference_steps: int, guidance_scale: float, seed: Optional[int]) -> Image.Image:
        start_time = time.time()
        
        # 1. Text Embeddings
        logger.debug("Encoding text prompt...")
        text_inputs = self.tokenizer(
            prompt,
            padding="max_length",
            max_length=77,
            truncation=True,
            return_tensors="np"
        )
        input_ids = text_inputs.input_ids.astype(np.int32)
        
        # Run Text Encoder RKNN
        # Output shape: [1, 77, 768]
        encoder_outputs = self.rknn_text_encoder.inference(inputs=[input_ids])
        prompt_embeds = encoder_outputs[0]
        
        # Release Text Encoder to save memory
        self.rknn_text_encoder.release()
        self.rknn_text_encoder = None
        logger.info("Released Text Encoder")

        # 2. Latents Initialization
        if seed is None:
            seed = int(time.time())
        np.random.seed(seed)
        
        # Shape: [1, 4, 64, 64] for 512x512 image
        latents = np.random.randn(1, 4, 64, 64).astype(np.float32)
        
        self.scheduler.set_timesteps(num_inference_steps)
        timesteps = self.scheduler.timesteps
        
        # 3. Denoising Loop (U-Net)
        logger.info(f"Starting U-Net inference ({num_inference_steps} steps)...")
        
        # Guidance scale embedding (w)
        # LCM uses guidance embedding: w = (guidance_scale - 1)
        # Embedding dim is 256 based on error "model input size(1024)" (256 * 4 bytes)
        w = np.array([guidance_scale - 1.0], dtype=np.float32)
        guidance_scale_embedding = self.get_guidance_scale_embedding(w, embedding_dim=256, dtype=np.float32)
        
        for i, t in enumerate(timesteps):
            step_start = time.time()
            
            # Prepare inputs
            # U-Net inputs:
            # 0: sample (latents) - [1, 4, 64, 64]
            # 1: timestep - [1]
            # 2: encoder_hidden_states - [1, 77, 768]
            # 3: timestep_cond (guidance) - [1, 256]
            
            # Try int64 as per reference
            timestep_tensor = np.array([t], dtype=np.int64) 
            
            # Ensure all are float32 (except timestep if int)
            latents = latents.astype(np.float32)
            prompt_embeds = prompt_embeds.astype(np.float32)
            guidance_scale_embedding = guidance_scale_embedding.astype(np.float32)

            # Run U-Net RKNN
            unet_inputs = [
                latents,
                timestep_tensor,
                prompt_embeds,
                guidance_scale_embedding
            ]
            
            noise_pred = self.rknn_unet.inference(inputs=unet_inputs)[0]
            
            # Scheduler step
            import torch
            latents_tensor = torch.from_numpy(latents)
            noise_pred_tensor = torch.from_numpy(noise_pred)
            
            # LCM Scheduler Step
            latents_tensor = self.scheduler.step(
                noise_pred_tensor, 
                t, 
                latents_tensor, 
                return_dict=False
            )[0]
            
            latents = latents_tensor.numpy()
            
            logger.debug(f"Step {i+1}/{num_inference_steps} took {time.time() - step_start:.2f}s")

        # 4. VAE Decode
        logger.debug("Decoding latents...")
        # Scale latents
        latents = latents / 0.18215
        
        # Run VAE Decoder RKNN
        # Input: [1, 4, 64, 64]
        vae_outputs = self.rknn_vae_decoder.inference(inputs=[latents])
        image_data = vae_outputs[0] # [1, 3, 512, 512]
        
        # Post-process image
        # NCHW -> HWC
        image_data = np.transpose(image_data, (0, 2, 3, 1))
        # Denormalize (approximate, depends on VAE training)
        # Usually VAE output is [-1, 1] or [0, 1]. 
        # Standard SD VAE output is roughly [-1, 1].
        image_data = (image_data / 2 + 0.5).clip(0, 1)
        image_data = (image_data * 255).astype(np.uint8)
        
        image = Image.fromarray(image_data[0])
        
        total_time = time.time() - start_time
        logger.info(f"Image generation complete in {total_time:.2f}s")
        
        return image
