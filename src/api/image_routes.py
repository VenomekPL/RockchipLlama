from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
import time
import base64
import io
import os
import logging
from models.model_manager import ModelManager
from config.settings import Settings

router = APIRouter()
logger = logging.getLogger(__name__)

class ImageGenerationRequest(BaseModel):
    prompt: str
    model: Optional[str] = "dall-e-2" # OpenAI compatibility
    n: Optional[int] = 1
    size: Optional[str] = "512x512"
    response_format: Optional[Literal["url", "b64_json"]] = "b64_json"
    quality: Optional[str] = "standard"
    style: Optional[str] = "natural"
    
    # Extended parameters
    num_inference_steps: Optional[int] = 4
    guidance_scale: Optional[float] = 8.0
    seed: Optional[int] = None

class ImageObject(BaseModel):
    b64_json: Optional[str] = None
    url: Optional[str] = None
    revised_prompt: Optional[str] = None

class ImageGenerationResponse(BaseModel):
    created: int
    data: List[ImageObject]

# Dependency to get ModelManager (singleton)
def get_model_manager():
    from src.main import model_manager
    return model_manager

@router.post("/images/generations", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest,
    manager: ModelManager = Depends(get_model_manager)
):
    """
    Generate images using Stable Diffusion on NPU.
    Compatible with OpenAI API.
    """
    logger.info(f"Image generation request: {request.prompt}")
    
    if request.n > 1:
        raise HTTPException(status_code=400, detail="Only n=1 is supported for now")
        
    if request.size != "512x512":
        raise HTTPException(status_code=400, detail="Only 512x512 resolution is supported")

    try:
        # Get SD model
        sd_model = await manager.get_stable_diffusion_model()
        if not sd_model:
             raise HTTPException(status_code=503, detail="Stable Diffusion model not available")

        # Generate
        image = await sd_model.generate(
            prompt=request.prompt,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed
        )
        
        # Save image to SDimages folder
        sd_images_dir = "SDimages"
        if not os.path.exists(sd_images_dir):
            os.makedirs(sd_images_dir)
            
        timestamp = int(time.time())
        filename = f"gen_{timestamp}.png"
        filepath = os.path.join(sd_images_dir, filename)
        image.save(filepath)
        logger.info(f"Saved generated image to {filepath}")
        
        # Convert to response format
        response_data = []
        
        if request.response_format == "b64_json":
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            response_data.append(ImageObject(b64_json=img_str, revised_prompt=request.prompt))
        else:
            # Return URL pointing to the saved file
            # Note: You might need to mount SDimages as a static directory in main.py to serve these
            url = f"/SDimages/{filename}"
            response_data.append(ImageObject(url=url, revised_prompt=request.prompt))

        return ImageGenerationResponse(
            created=int(time.time()),
            data=response_data
        )

    except Exception as e:
        logger.error(f"Image generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
