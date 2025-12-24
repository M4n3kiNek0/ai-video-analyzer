"""
Database models for Video Analyzer System.
Uses SQLAlchemy ORM with PostgreSQL.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://video_user:video_password@localhost:5432/video_analyzer")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Media(Base):
    """
    Media (Video/Audio) metadata and processing status.
    Supports both video files and audio-only files.
    """
    __tablename__ = "videos"  # Keep table name for backward compatibility

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, nullable=False)
    upload_path = Column(String(500))
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    media_type = Column(String(20), default="video")  # video, audio
    analysis_type = Column(String(50), default="descriptive")  # descriptive, brainstorming, reverse_engineering, meeting_notes
    duration_seconds = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    context = Column(Text, nullable=True)  # User-provided context for better AI analysis
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transcript = relationship("Transcript", back_populates="media", uselist=False, cascade="all, delete-orphan")
    keyframes = relationship("Keyframe", back_populates="media", cascade="all, delete-orphan")
    analysis = relationship("Analysis", back_populates="media", uselist=False, cascade="all, delete-orphan")
    logs = relationship("ProcessingLog", back_populates="media", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Media(id={self.id}, filename='{self.filename}', type='{self.media_type}', status='{self.status}')>"


# Alias for backward compatibility
Video = Media


class Transcript(Base):
    """
    Audio transcription with segmented timestamps.
    Works for both video and audio-only files.
    """
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, unique=True)  # Keep column name for compatibility
    full_text = Column(Text)
    segments = Column(JSON)  # [{"start": 0.0, "end": 30.0, "text": "..."}, ...]
    language = Column(String(10), default="it")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    media = relationship("Media", back_populates="transcript")

    @property
    def media_id(self):
        """Alias for video_id for semantic clarity."""
        return self.video_id

    def __repr__(self):
        return f"<Transcript(id={self.id}, media_id={self.video_id})>"


class Keyframe(Base):
    """
    Extracted keyframes with visual descriptions.
    Only applicable to video files, not audio-only.
    """
    __tablename__ = "keyframes"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)  # Keep column name for compatibility
    timestamp = Column(Integer)  # seconds
    frame_number = Column(Integer)
    s3_url = Column(String(500))  # URL screenshot on S3/MinIO
    visual_description = Column(Text)  # OpenAI Vision description
    scene_change_score = Column(Integer, nullable=True)  # How different from previous frame
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    media = relationship("Media", back_populates="keyframes")

    @property
    def media_id(self):
        """Alias for video_id for semantic clarity."""
        return self.video_id

    def __repr__(self):
        return f"<Keyframe(id={self.id}, media_id={self.video_id}, timestamp={self.timestamp}s)>"


class Analysis(Base):
    """
    Full structured analysis output with diagrams.
    Works for both video and audio-only files.
    """
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, unique=True)  # Keep column name for compatibility
    summary = Column(Text)
    app_type = Column(String(50))  # web, mobile, desktop (for video) or meeting, podcast, brainstorm (for audio)
    modules = Column(JSON)  # [{name, description, screens, key_features}, ...]
    user_flows = Column(JSON)  # [{name, steps: [{step, action, timestamp, outcome}], actors}, ...]
    issues = Column(JSON)  # [{type, description, timestamp, severity}, ...]
    technology_hints = Column(JSON)  # ["React", "PostgreSQL", ...] or audio-specific hints
    recommendations = Column(JSON)  # ["...", "..."]
    output_format = Column(JSON)  # Full structured output as returned by GPT-4
    
    # Diagram fields (primarily for video, but can be used for audio flow diagrams)
    sequence_diagram = Column(Text, nullable=True)     # Mermaid syntax for sequence diagram
    user_flow_diagram = Column(Text, nullable=True)    # Mermaid syntax for user flow / conversation flow
    wireframes = Column(JSON, nullable=True)           # List of ASCII wireframes per frame (video only)
    
    # Audio-specific fields
    speakers = Column(JSON, nullable=True)             # Detected speakers [{name, segments, speaking_time}]
    action_items = Column(JSON, nullable=True)         # Extracted action items [{item, assignee, deadline}]
    decisions = Column(JSON, nullable=True)            # Key decisions made [{decision, timestamp, context}]
    topics = Column(JSON, nullable=True)               # Topics discussed [{topic, start_time, end_time, summary}]
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    media = relationship("Media", back_populates="analysis")

    @property
    def media_id(self):
        """Alias for video_id for semantic clarity."""
        return self.video_id

    def __repr__(self):
        return f"<Analysis(id={self.id}, media_id={self.video_id})>"


class APIConfig(Base):
    """
    API Configuration for AI providers.
    Stores provider settings, models, API keys, and metadata.
    """
    __tablename__ = "api_config"

    id = Column(Integer, primary_key=True, index=True)
    config_name = Column(String(100), unique=True, nullable=False)  # "default", "accurate", "economical", etc.
    is_active = Column(Boolean, default=False)  # Solo una config attiva
    
    # Provider settings
    transcription_provider = Column(String(50))  # "openai", "groq", "local_whisper"
    transcription_model = Column(String(100))  # "whisper-1", "llama-3.1-70b", "local"
    transcription_api_key = Column(Text, nullable=True)  # Encrypted in production
    transcription_base_url = Column(String(500), nullable=True)  # Per provider locali
    
    vision_provider = Column(String(50))  # "openai", "groq", "ollama", "together", "google"
    vision_model = Column(String(100))
    vision_api_key = Column(Text, nullable=True)
    vision_base_url = Column(String(500), nullable=True)  # Per Ollama locale
    
    analysis_provider = Column(String(50))
    analysis_model = Column(String(100))
    analysis_api_key = Column(Text, nullable=True)
    analysis_base_url = Column(String(500), nullable=True)
    
    enrichment_provider = Column(String(50))
    enrichment_model = Column(String(100))
    enrichment_api_key = Column(Text, nullable=True)
    enrichment_base_url = Column(String(500), nullable=True)
    
    # Metadata
    quality_rating = Column(String(20))  # "high", "medium", "low"
    estimated_cost_per_video = Column(String(50))  # "$0.50", "Free", etc.
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<APIConfig(id={self.id}, name='{self.config_name}', active={self.is_active})>"


class ProcessingLog(Base):
    """
    Real-time processing logs for feedback to the user.
    """
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(20), default="INFO")
    message = Column(Text, nullable=False)
    
    # Relationship
    media = relationship("Media", back_populates="logs")

    def __repr__(self):
        return f"<ProcessingLog(id={self.id}, video_id={self.video_id}, message='{self.message[:30]}...')>"


def init_db():
    """
    Initialize database tables.
    Call this function to create all tables.
    """
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


def get_db():
    """
    Dependency for FastAPI to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    # Create tables when run directly
    init_db()

