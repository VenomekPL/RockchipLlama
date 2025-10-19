"""
Model Management API Routes
Endpoints for loading, unloading, and listing models
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from models.model_manager import model_manager

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/v1/models", tags=["Model Management"])


class LoadModelRequest(BaseModel):
    """Request to load a model"""
    model: str = Field(..., description="Name of model to load (with or without .rkllm extension)")
    max_context_len: Optional[int] = Field(None, description="Maximum context length")
    num_npu_core: Optional[int] = Field(None, description="Number of NPU cores to use")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "gemma-3-270m",
                "max_context_len": 512,
                "num_npu_core": 3
            }
        }


class LoadModelResponse(BaseModel):
    """Response from loading a model"""
    success: bool
    message: str
    model_name: str
    loaded: bool = True


class UnloadModelResponse(BaseModel):
    """Response from unloading a model"""
    success: bool
    message: str


class LoadedModelResponse(BaseModel):
    """Response showing currently loaded model"""
    loaded: bool
    model_name: Optional[str] = None
    model_path: Optional[str] = None


class AvailableModel(BaseModel):
    """Information about an available model"""
    name: str
    filename: str
    path: str
    size_mb: float
    loaded: bool


class AvailableModelsResponse(BaseModel):
    """List of available models"""
    models: List[AvailableModel]
    total: int
    loaded_model: Optional[str] = None


@router.post("/load", response_model=LoadModelResponse)
async def load_model(request: LoadModelRequest):
    """
    Load a model into memory for inference
    
    This must be called before using /v1/chat/completions with a model.
    Loading a new model will unload the currently loaded model.
    
    Endpoint: POST /v1/models/load
    """
    try:
        logger.info(f"Request to load model: {request.model}")
        
        # Attempt to load model
        success = model_manager.load_model(
            model_name=request.model,
            max_context_len=request.max_context_len,
            num_npu_core=request.num_npu_core
        )
        
        if success:
            return LoadModelResponse(
                success=True,
                message=f"Model {request.model} loaded successfully",
                model_name=model_manager.get_loaded_model_name(),
                loaded=True
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to load model"
            )
            
    except ValueError as e:
        # Model not found
        logger.error(f"Model not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
        
    except RuntimeError as e:
        # Loading failed
        logger.error(f"Failed to load model: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error loading model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/unload", response_model=UnloadModelResponse)
async def unload_model():
    """
    Unload the currently loaded model from memory
    
    This frees up memory and NPU resources.
    
    Endpoint: POST /v1/models/unload
    """
    try:
        if not model_manager.is_model_loaded():
            return UnloadModelResponse(
                success=False,
                message="No model is currently loaded"
            )
        
        model_name = model_manager.get_loaded_model_name()
        success = model_manager.unload_model()
        
        if success:
            return UnloadModelResponse(
                success=True,
                message=f"Model {model_name} unloaded successfully"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to unload model"
            )
            
    except Exception as e:
        logger.error(f"Error unloading model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loaded", response_model=LoadedModelResponse)
async def get_loaded_model():
    """
    Get information about the currently loaded model
    
    Endpoint: GET /v1/models/loaded
    """
    try:
        model_info = model_manager.get_model_info()
        
        if model_info:
            return LoadedModelResponse(
                loaded=True,
                model_name=model_info['name'],
                model_path=model_info['path']
            )
        else:
            return LoadedModelResponse(loaded=False)
            
    except Exception as e:
        logger.error(f"Error getting loaded model info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available", response_model=AvailableModelsResponse)
async def list_available_models():
    """
    List all available models in the models directory
    
    Shows model name, size, and whether it's currently loaded.
    
    Endpoint: GET /v1/models/available
    """
    try:
        models = model_manager.list_available_models()
        loaded_model = model_manager.get_loaded_model_name()
        
        return AvailableModelsResponse(
            models=[AvailableModel(**m) for m in models],
            total=len(models),
            loaded_model=loaded_model
        )
        
    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
