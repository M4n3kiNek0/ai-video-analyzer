"""
Upload Routes - Video and Audio upload endpoints.
"""

import os
import tempfile
import shutil
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session

from models import Video, Media, get_db
from schemas import UploadResponse, AudioUploadResponse, OptimizePromptRequest, OptimizePromptResponse
from audio_processor import SUPPORTED_AUDIO_FORMATS
# Import Celery tasks
from processing_pipeline import process_video_task, process_audio_task

# Configure logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(tags=["upload"])

# Global reference to analyzer (set by main.py)
_analyzer = None

def set_analyzer(analyzer):
    """Set the global analyzer reference."""
    global _analyzer
    _analyzer = analyzer


@router.post("/optimize-prompt", response_model=OptimizePromptResponse)
async def optimize_prompt(request: OptimizePromptRequest):
    """
    Ottimizza la descrizione fornita dall'utente per migliorare la qualità dell'analisi.
    Usa AI per suggerire una versione migliorata del prompt mantenendo il significato originale.
    """
    if not _analyzer:
        raise HTTPException(status_code=500, detail="AI Analyzer not initialized")
    
    original = request.context.strip()
    
    if len(original) < 20:
        raise HTTPException(status_code=400, detail="Descrizione troppo breve (minimo 20 caratteri)")
    
    try:
        result = _analyzer.optimize_context_prompt(original)
        return OptimizePromptResponse(
            original_context=original,
            optimized_context=result.get("optimized_text", original),
            improvements=result.get("improvements", [])
        )
    except Exception as e:
        logger.error(f"Prompt optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ottimizzazione fallita: {str(e)}")


@router.post("/upload", response_model=UploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    context: Optional[str] = Form(None),
    analysis_type: Optional[str] = Form("auto"),
    db: Session = Depends(get_db)
):
    """
    Upload a video file and start async processing.
    
    Supported formats: MP4, MOV, AVI, MKV, WEBM
    
    Optional context: A description of the video content to improve AI analysis.
    
    Analysis types:
    - auto: AI determines the best type (default)
    - reverse_engineering: Technical app demo analysis
    - meeting: Meeting notes with action items
    - debrief: Post-event analysis
    - brainstorming: Creative session
    - notes: General notes
    
    Processing pipeline:
    1. Extract audio → Transcribe with Whisper
    2. Extract keyframes → Deduplicate with perceptual hash
    3. Analyze frames with GPT-4 Vision (contextual)
    4. Generate structured analysis with GPT-4 Turbo
    """
    # Validate file type
    allowed_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.txt', '.md'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate analysis type
    valid_analysis_types = {"auto", "reverse_engineering", "meeting", "debrief", "brainstorming", "notes"}
    if analysis_type not in valid_analysis_types:
        analysis_type = "auto"
    
    # Check if filename already exists
    existing = db.query(Video).filter(Video.filename == file.filename).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Video with filename '{file.filename}' already exists (ID: {existing.id})"
        )
    
    # Create temp directory for this upload in a shared location
    base_temp_dir = "temp_uploads"
    os.makedirs(base_temp_dir, exist_ok=True)
    temp_dir = tempfile.mkdtemp(prefix="video_analyzer_", dir=base_temp_dir)
    
    try:
        # First creating the record to get the ID
        video_record = Video(
            filename=file.filename,
            upload_path="", # Placeholder, will update
            status="uploading",
            media_type="video",
            analysis_type=analysis_type,
            file_size_bytes=0,
            context=context.strip() if context else None
        )
        db.add(video_record)
        db.commit()
        db.refresh(video_record)
        video_id = video_record.id
        
        # Save to static/videos for playback
        static_dir = "static/videos"
        os.makedirs(static_dir, exist_ok=True)
        video_filename = f"{video_id}.mp4"
        video_path = os.path.join(static_dir, video_filename)
        
        # Save uploaded file
        with open(video_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        file_size = os.path.getsize(video_path)
        
        # Update record
        video_record.upload_path = video_path
        video_record.file_size_bytes = file_size
        video_record.status = "processing"
        db.commit()
        
        logger.info(f"Video uploaded: ID={video_id}, filename={file.filename}, path={video_path}")
        
        # Schedule async processing with Celery
        process_video_task.delay(
            video_id,
            video_path,
            temp_dir,
            context,
            analysis_type
        )
        
        return UploadResponse(
            video_id=video_id,
            status="processing",
            message="Video caricato con successo. Analisi in corso..."
        )
        
    except Exception as e:
        # Cleanup on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-audio", response_model=AudioUploadResponse)
async def upload_audio(
    file: UploadFile = File(...),
    context: Optional[str] = Form(None),
    analysis_type: Optional[str] = Form("auto"),
    db: Session = Depends(get_db)
):
    """
    Upload an audio file and start async processing.
    
    Supported formats: MP3, WAV, M4A, OGG, FLAC, WEBM, AAC
    
    Optional context: A description of the audio content to improve AI analysis.
    
    Analysis types:
    - descriptive: General analysis (default)
    - meeting_notes: Focus on action items and decisions
    - brainstorming: Focus on ideas and proposals
    - reverse_engineering: Technical analysis
    
    Processing pipeline:
    1. Validate and extract metadata
    2. Transcribe with Whisper
    3. Enrich transcription with semantic analysis
    4. Generate structured analysis with GPT-4
    """
    # Get supported extensions
    allowed_extensions = set(SUPPORTED_AUDIO_FORMATS.keys())
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Allowed: {', '.join(sorted(allowed_extensions))}"
        )
    
    # Validate analysis type (support both old and new naming)
    valid_analysis_types = {"auto", "descriptive", "meeting", "meeting_notes", "debrief", "brainstorming", "reverse_engineering", "notes"}
    if analysis_type not in valid_analysis_types:
        analysis_type = "auto"
    
    # Map old names to new names
    if analysis_type == "descriptive":
        analysis_type = "notes"
    elif analysis_type == "meeting_notes":
        analysis_type = "meeting"
    
    # Check if filename already exists
    existing = db.query(Media).filter(Media.filename == file.filename).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"File with name '{file.filename}' already exists (ID: {existing.id})"
        )
    
    # Create temp directory for this upload
    temp_dir = tempfile.mkdtemp(prefix="audio_analyzer_")
    audio_path = os.path.join(temp_dir, file.filename)
    
    try:
        # Save uploaded file
        with open(audio_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        file_size = os.path.getsize(audio_path)
        
        # Create database record
        audio_record = Media(
            filename=file.filename,
            upload_path=audio_path,
            status="processing",
            media_type="audio",
            analysis_type=analysis_type,
            file_size_bytes=file_size,
            context=context.strip() if context else None
        )
        db.add(audio_record)
        db.commit()
        db.refresh(audio_record)
        
        audio_id = audio_record.id
        logger.info(f"Audio uploaded: ID={audio_id}, filename={file.filename}, size={file_size} bytes, type={analysis_type}")
        
        # Schedule async processing with Celery
        process_audio_task.delay(
            audio_id,
            audio_path,
            temp_dir,
            context,
            analysis_type
        )
        
        return AudioUploadResponse(
            audio_id=audio_id,
            status="processing",
            message="Audio caricato con successo. Analisi in corso...",
            media_type="audio"
        )
        
    except Exception as e:
        # Cleanup on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.error(f"Audio upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

