"""
Videos Routes - Video listing, detail, and deletion endpoints.
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from models import Video, Transcript, Keyframe, Analysis, ProcessingLog, get_db

# Import Celery tasks for retry functionality
from processing_pipeline import process_video_task, process_audio_task

# Configure logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/videos", tags=["videos"])

# Global reference to storage (set by main.py)
_storage = None

def set_storage(storage):
    """Set the global storage reference."""
    global _storage
    _storage = storage


@router.get("/{video_id}")
async def get_video_analysis(video_id: int, db: Session = Depends(get_db)):
    """
    Get complete analysis for a video.
    
    Returns video metadata, transcription, keyframes, and structured analysis.
    """
    # Fetch video
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Fetch related data
    transcript = db.query(Transcript).filter(Transcript.video_id == video_id).first()
    keyframes = db.query(Keyframe).filter(Keyframe.video_id == video_id).order_by(Keyframe.timestamp).all()
    analysis = db.query(Analysis).filter(Analysis.video_id == video_id).first()
    
    # Determine media type
    media_type = video.media_type if hasattr(video, 'media_type') else 'video'
    analysis_type = video.analysis_type if hasattr(video, 'analysis_type') else 'descriptive'
    
    # Build response based on media type
    response_data = {
        "video": {
            "id": video.id,
            "filename": video.filename,
            "status": video.status,
            "media_type": media_type,
            "analysis_type": analysis_type,
            "duration": video.duration_seconds,
            "file_size_bytes": video.file_size_bytes,
            "created_at": video.created_at.isoformat() if video.created_at else None,
            "updated_at": video.updated_at.isoformat() if video.updated_at else None
        },
        "transcript": {
            "full_text": transcript.full_text if transcript else None,
            "segments": transcript.segments if transcript else None,
            "language": transcript.language if transcript else None
        } if transcript else None,
        "keyframes": [
            {
                "id": kf.id,
                "timestamp": kf.timestamp,
                "frame_number": kf.frame_number,
                "s3_url": kf.s3_url,
                "description": kf.visual_description,
                "scene_change_score": kf.scene_change_score
            } for kf in keyframes
        ] if media_type == 'video' else [],  # Empty keyframes for audio
        "analysis": analysis.output_format if analysis else None
    }
    
    # Add audio-specific fields if available
    if media_type == 'audio' and analysis:
        response_data["audio_analysis"] = {
            "speakers": analysis.speakers if hasattr(analysis, 'speakers') else None,
            "action_items": analysis.action_items if hasattr(analysis, 'action_items') else None,
            "decisions": analysis.decisions if hasattr(analysis, 'decisions') else None,
            "topics": analysis.topics if hasattr(analysis, 'topics') else None
        }
    
    return JSONResponse(response_data)


@router.get("/{video_id}/logs")
async def get_video_logs(video_id: int, db: Session = Depends(get_db)):
    """
    Get processing logs for a video.
    """
    logs = db.query(ProcessingLog).filter(ProcessingLog.video_id == video_id).order_by(ProcessingLog.timestamp).all()
    
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "level": log.level,
            "message": log.message
        }
        for log in logs
    ]


@router.get("")
async def list_videos(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List all uploaded videos with optional status filter.
    
    Query params:
    - status: Filter by status (pending, processing, completed, failed)
    - limit: Max results (default 50)
    - offset: Pagination offset
    """
    query = db.query(Video)
    
    if status:
        query = query.filter(Video.status == status)
    
    total = query.count()
    videos = query.order_by(Video.created_at.desc()).offset(offset).limit(limit).all()
    
    # Build response with thumbnail and summary for each video
    videos_data = []
    for v in videos:
        media_type = v.media_type if hasattr(v, 'media_type') else 'video'
        
        # Get first keyframe as thumbnail (only for videos)
        thumbnail_url = None
        if media_type == 'video':
            first_keyframe = db.query(Keyframe).filter(
                Keyframe.video_id == v.id
            ).order_by(Keyframe.timestamp).first()
            if first_keyframe:
                thumbnail_url = first_keyframe.s3_url
        
        # Get summary from analysis
        summary = None
        analysis = db.query(Analysis).filter(Analysis.video_id == v.id).first()
        if analysis and analysis.output_format:
            summary = analysis.output_format.get('summary', None)
        
        videos_data.append({
            "id": v.id,
            "filename": v.filename,
            "status": v.status,
            "media_type": media_type,
            "analysis_type": v.analysis_type if hasattr(v, 'analysis_type') else 'descriptive',
            "duration": v.duration_seconds,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "thumbnail_url": thumbnail_url,
            "summary": summary
        })
    
    return JSONResponse({
        "total": total,
        "limit": limit,
        "offset": offset,
        "videos": videos_data
    })


@router.delete("/{video_id}")
async def delete_video(video_id: int, db: Session = Depends(get_db)):
    """
    Delete a video and all associated data.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Delete from S3/MinIO
    if _storage:
        try:
            _storage.delete_video_assets(video_id)
        except Exception as e:
            logger.warning(f"Failed to delete S3 assets: {e}")
    
    # Delete local file if it exists
    if video.upload_path and os.path.exists(video.upload_path):
        try:
            os.remove(video.upload_path)
            logger.info(f"Local file deleted: {video.upload_path}")
        except Exception as e:
            logger.warning(f"Failed to delete local file {video.upload_path}: {e}")
    
    # Delete from database (cascades to related tables)
    filename = video.filename
    db.delete(video)
    db.commit()
    
    logger.info(f"Video {video_id} deleted")
    
    return JSONResponse({
        "status": "deleted",
        "video_id": video_id,
        "message": f"Video '{filename}' and all associated data deleted"
    })


@router.post("/{video_id}/retry")
async def retry_video_analysis(video_id: int, db: Session = Depends(get_db)):
    """
    Retry analysis for a failed or stuck video.
    
    This will:
    1. Clear any existing analysis data
    2. Reset status to 'processing'
    3. Re-queue the Celery task
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video.status not in ['failed', 'processing']:
        raise HTTPException(
            status_code=400, 
            detail=f"Can only retry failed or stuck videos. Current status: {video.status}"
        )
    
    # Check if upload path still exists
    if not video.upload_path:
        raise HTTPException(
            status_code=400, 
            detail="Original video file path not available. Please re-upload."
        )
    
    import os
    if not os.path.exists(video.upload_path):
        # Update status to failed to reflect the error
        video.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=400, 
            detail="Original video file no longer exists on server (likely cleaned up). Please delete and re-upload the video."
        )
    
    # Clear existing analysis data
    db.query(Transcript).filter(Transcript.video_id == video_id).delete()
    db.query(Keyframe).filter(Keyframe.video_id == video_id).delete()
    db.query(Analysis).filter(Analysis.video_id == video_id).delete()
    
    # Reset status
    video.status = "processing"
    db.commit()
    
    # Determine task based on media type
    media_type = video.media_type if hasattr(video, 'media_type') else 'video'
    context = video.context if hasattr(video, 'context') else None
    analysis_type = video.analysis_type if hasattr(video, 'analysis_type') else 'auto'
    
    # Get temp directory from upload path
    import os
    temp_dir = os.path.dirname(video.upload_path)
    
    # Re-queue the task
    if media_type == 'audio':
        process_audio_task.delay(
            video_id,
            video.upload_path,
            temp_dir,
            context,
            analysis_type
        )
    else:
        process_video_task.delay(
            video_id,
            video.upload_path,
            temp_dir,
            context,
            analysis_type
        )
    
    logger.info(f"Video {video_id} retry queued")
    
    return JSONResponse({
        "status": "processing",
        "video_id": video_id,
        "message": f"Analysis retry started for '{video.filename}'"
    })
