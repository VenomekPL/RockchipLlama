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
from config.settings import settings
from models.rkllm_model import RKLLMModel
from models.model_manager import model_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RockchipLlama API",
    description="OpenAI-compatible API server for Rockchip NPU acceleration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(openai_router)
app.include_router(model_router)
app.include_router(ollama_router)


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
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
        # List available models
        model_files = [f for f in os.listdir(settings.models_dir) if f.endswith('.rkllm')]
        logger.info(f"Available models: {len(model_files)}")
        for model_file in model_files:
            logger.info(f"  - {model_file}")
    
    # TODO: Initialize default model
    # For now, we'll load models on-demand
    logger.info("✅ Server initialization complete")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("🛑 Server shutting down...")
    # TODO: Cleanup loaded models


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
