"""
Video Analyzer API - FastAPI Application.
REST API for uploading, processing, and analyzing video content.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import local modules
from models import init_db
from video_processor import check_ffmpeg_installed
from ai_analyzer import AIAnalyzer
from storage import MinIOStorage

# Import routers
from routes_upload import router as upload_router, set_analyzer as set_upload_analyzer
from routes_videos import router as videos_router, set_storage as set_videos_storage
from routes_export import router as export_router
from routes_config import router as config_router

# Import processing pipeline setters
from processing_pipeline import set_analyzer as set_pipeline_analyzer, set_storage as set_pipeline_storage

# Global analyzer instance (can be reloaded)
_analyzer: Optional[AIAnalyzer] = None

# Configure logging with DEBUG level for more verbosity
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('app.log', mode='a', encoding='utf-8')  # File output
    ]
)

# Reduce noise from third-party libraries
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.INFO)
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def reload_analyzer():
    """
    Reload analyzer with current active configuration.
    Thread-safe reload for runtime configuration changes.
    """
    global _analyzer
    try:
        logger.info("Reloading AI Analyzer with current configuration...")
        _analyzer = AIAnalyzer()  # Loads active config from DB
        set_upload_analyzer(_analyzer)
        set_pipeline_analyzer(_analyzer)
        logger.info("AI Analyzer reloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to reload analyzer: {e}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info("Starting Video Analyzer API...")
    
    # Check FFmpeg
    if not check_ffmpeg_installed():
        logger.warning("FFmpeg not found! Video processing will fail.")
        logger.warning("Install with: winget install FFmpeg")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Initialize AI analyzer
    global _analyzer
    try:
        _analyzer = AIAnalyzer()
        logger.info("AI Analyzer initialized")
    except Exception as e:
        logger.error(f"AI Analyzer initialization failed: {e}")
        _analyzer = None
    
    # Initialize MinIO storage
    storage = None
    try:
        storage = MinIOStorage()
        logger.info("MinIO Storage initialized")
    except Exception as e:
        logger.error(f"MinIO Storage initialization failed: {e}")
    
    # Set global instances for routers
    set_upload_analyzer(_analyzer)
    set_pipeline_analyzer(_analyzer)
    set_pipeline_storage(storage)
    set_videos_storage(storage)
    
    logger.info("Video Analyzer API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Video Analyzer API...")


# Create FastAPI app
app = FastAPI(
    title="Video Analyzer API",
    description="Automated video analysis system with AI-powered transcription, visual analysis, and structured reports.",
    version="1.0.0",
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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(upload_router)
app.include_router(videos_router)
app.include_router(export_router)
app.include_router(config_router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main GUI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api")
async def api_info():
    """API info endpoint."""
    return {
        "status": "online",
        "service": "Video Analyzer API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /upload",
            "get_video": "GET /videos/{video_id}",
            "list_videos": "GET /videos",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "components": {
            "ffmpeg": check_ffmpeg_installed(),
            "database": True,  # Would check connection in production
            "analyzer": _analyzer is not None
        }
    }


@app.post("/api/config/reload")
async def reload_config():
    """Reload analyzer with current active configuration."""
    success = reload_analyzer()
    if success:
        return {"message": "Configuration reloaded successfully", "status": "success"}
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Failed to reload configuration")


if __name__ == "__main__":
    import uvicorn
    
    # Check prerequisites
    print("=" * 50)
    print("Video Analyzer API")
    print("=" * 50)
    
    if not check_ffmpeg_installed():
        print("\n⚠️  WARNING: FFmpeg not found!")
        print("   Install with: winget install FFmpeg")
        print("   Video processing will fail without FFmpeg.\n")
    
    print("\nStarting server on http://localhost:8000")
    print("API docs available at http://localhost:8000/docs\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

# Hot reload trigger: 12/13/2025 17:50:14
