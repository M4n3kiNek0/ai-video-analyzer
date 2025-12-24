
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Video, Keyframe
import json

DATABASE_URL = "postgresql://video_user:video_password@localhost:5432/video_analyzer"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Get the latest video
video = db.query(Video).order_by(Video.created_at.desc()).first()

# Write to file directly to avoid shell encoding issues
with open("description_dump.txt", "w", encoding="utf-8") as f:
    if video:
        f.write(f"Checking Video ID: {video.id} ({video.filename})\n")
        keyframes = db.query(Keyframe).filter(Keyframe.video_id == video.id).order_by(Keyframe.timestamp).all()
        
        f.write(f"Found {len(keyframes)} keyframes.\n")
        f.write("-" * 50 + "\n")
        
        count_missing = 0
        for kf in keyframes:
            desc = kf.visual_description
            status = "OK"
            if not desc:
                status = "EMPTY"
                count_missing += 1
            elif len(desc) < 20:
                 status = "TOO SHORT"
                 count_missing += 1
            
            # Print full content for analysis
            preview = desc.replace("\n", " ") if desc else "None"
            f.write(f"[{kf.timestamp}s] Status: {status} | Content: {preview}\n\n")

        f.write("-" * 50 + "\n")
        f.write(f"Total Keyframes: {len(keyframes)}\n")
        f.write(f"Potentially Missing: {count_missing}\n")
    else:
        f.write("No video found.\n")

db.close()
