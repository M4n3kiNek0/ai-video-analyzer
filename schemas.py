"""
Pydantic models for API requests and responses.
"""

from typing import List, Optional
from pydantic import BaseModel


class VideoResponse(BaseModel):
    id: int
    filename: str
    status: str
    duration: Optional[int] = None
    created_at: str


class TranscriptResponse(BaseModel):
    full_text: Optional[str] = None
    segments: Optional[List[dict]] = None


class KeyframeResponse(BaseModel):
    timestamp: int
    s3_url: str
    description: Optional[str] = None


class AnalysisResponse(BaseModel):
    video: VideoResponse
    transcript: Optional[TranscriptResponse] = None
    keyframes: List[KeyframeResponse] = []
    analysis: Optional[dict] = None


class UploadResponse(BaseModel):
    video_id: int
    status: str
    message: str
    media_type: str = "video"


class AudioUploadResponse(BaseModel):
    audio_id: int
    status: str
    message: str
    media_type: str = "audio"


class OptimizePromptRequest(BaseModel):
    context: str


class OptimizePromptResponse(BaseModel):
    original_context: str
    optimized_context: str
    improvements: List[str]

