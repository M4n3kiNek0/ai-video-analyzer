
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Video, APIConfig
import os

DATABASE_URL = "postgresql://video_user:video_password@localhost:5432/video_analyzer"

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    with open("db_status.txt", "w") as f:
        f.write("-" * 50 + "\n")
        f.write("Latest Videos:\n")
        videos = db.query(Video).order_by(Video.created_at.desc()).limit(5).all()
        for v in videos:
            f.write(f"ID: {v.id}, File: {v.filename}, Status: {v.status}\n")
            if v.status == 'failed':
                # Check for context or other clues
                pass 

        f.write("-" * 50 + "\n")
        f.write("Active API Config:\n")
        config = db.query(APIConfig).filter(APIConfig.is_active == True).first()
        if config:
            f.write(f"Name: {config.config_name}\n")
            f.write(f"Transcription: {config.transcription_provider} ({config.transcription_model})\n")
            f.write(f"Vision: {config.vision_provider} ({config.vision_model})\n")
        else:
            f.write("No active API config found!\n")
    
    db.close()
    print("Done writing to db_status.txt")
except Exception as e:
    with open("db_status.txt", "w") as f:
        f.write(f"Error: {e}")
    print(f"Error: {e}")
