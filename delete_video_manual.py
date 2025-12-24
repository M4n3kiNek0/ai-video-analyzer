
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Video, Transcript, Keyframe, Analysis, APIConfig
import os

DATABASE_URL = "postgresql://video_user:video_password@localhost:5432/video_analyzer"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

VIDEO_ID = 33

try:
    print(f"Attempting to delete video {VIDEO_ID}...")
    video = db.query(Video).filter(Video.id == VIDEO_ID).first()
    if not video:
        print("Video not found.")
    else:
        # Manually delete related records first just in case cascades fail (though they shouldn't)
        db.query(Transcript).filter(Transcript.video_id == VIDEO_ID).delete()
        db.query(Keyframe).filter(Keyframe.video_id == VIDEO_ID).delete()
        db.query(Analysis).filter(Analysis.video_id == VIDEO_ID).delete()
        
        db.delete(video)
        db.commit()
        print(f"Successfully deleted video {VIDEO_ID} and its data.")

except Exception as e:
    print(f"Error deleting video: {e}")
finally:
    db.close()
