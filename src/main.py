"""
RockchipLlama FastAPI Server
Main entry point for the OpenAI-compatible API server
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from api.openai_routes import router as openai_router
from api.model_routes import router as model_router
from api.ollama_routes import router as ollama_router
from api.image_routes import router as image_router
from config.settings import settings
from models.rkllm_model import RKLLMModel
from models.model_manager import model_manager

from contextlib import asynccontextmanager

# Configure logging
log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup and cleanup on shutdown"""
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 RockchipLlama Server Starting")
    logger.info("=" * 60)
    logger.info(f"Models directory: {settings.models_dir}")
    logger.info(f"Default model: {settings.default_model}")
    logger.info(f"NPU cores: {settings.num_npu_core}")
    logger.info(f"RKLLM library: {settings.rkllm_lib_path}")
    
    # Check if models directory exists
    if not os.path.exists(settings.models_dir):
        logger.warning(f"Models directory not found: {settings.models_dir}")
    else:
        # List available models using ModelManager
        available_models = model_manager.list_available_models()
        logger.info(f"Available models: {len(available_models)}")
        for model in available_models:
            logger.info(f"  - {model['name']} ({model['filename']})")
    
    logger.info("✅ Server initialization complete")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("🛑 Server shutting down...")
    # TODO: Cleanup loaded models

# Create FastAPI app
app = FastAPI(
    title="RockchipLlama API",
    description="OpenAI-compatible API server for Rockchip NPU acceleration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

# Include routers
app.include_router(openai_router)
app.include_router(model_router)
app.include_router(ollama_router)
app.include_router(image_router, prefix="/v1") # Mount at /v1/images/generations

# Mount SDimages directory for static access
sd_images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "SDimages")
if not os.path.exists(sd_images_dir):
    os.makedirs(sd_images_dir)
app.mount("/SDimages", StaticFiles(directory=sd_images_dir), name="SDimages")


@app.get("/")
async def root():
    """Root endpoint with server information"""
    loaded_model = model_manager.get_loaded_model_name()
    
    return {
        "name": "RockchipLlama API",
        "version": "0.1.0",
        "status": "running",
        "loaded_model": loaded_model,
        "endpoints": {
            "openai_chat": "/v1/chat/completions",
            "openai_models": "/v1/models",
            "ollama_generate": "/api/generate",
            "ollama_chat": "/api/chat",
            "ollama_tags": "/api/tags",
            "model_management": {
                "load": "/v1/models/load",
                "unload": "/v1/models/unload",
                "loaded": "/v1/models/loaded",
                "available": "/v1/models/available"
            },
            "health": "/v1/health",
            "docs": "/docs"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": str(exc),
                "type": "internal_server_error"
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=False  # Disable auto-reload for stable operation
    )
