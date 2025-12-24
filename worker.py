"""
Celery Worker Entry Point.
Initializes resources (AI Analyzer, Storage) for the worker process.
"""
import os
import logging
from celery_app import celery_app
from ai_analyzer import AIAnalyzer
from storage import MinIOStorage
import processing_pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize global instances on worker start
@celery_app.on_after_configure.connect
def setup_initial_tasks(sender, **kwargs):
    logger.info("Worker started. Initializing resources...")
    init_resources()

def init_resources():
    """Initialize singleton resources for the worker process."""
    try:
        # Initialize AI Analyzer
        logger.info("Initializing AI Analyzer...")
        analyzer = AIAnalyzer()
        processing_pipeline.set_analyzer(analyzer)
        
        # Initialize Storage
        logger.info("Initializing MinIO Storage...")
        storage = MinIOStorage()
        processing_pipeline.set_storage(storage)
        
        logger.info("Resources initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize resources: {e}")
        # Build robustness: don't crash, tasks might retry
