Video Analysis Hybrid Solution – Python Implementation
Architecture Overview
Components:
1.	Video Ingestion & Processing – FFmpeg per estrazione audio, OpenAI Whisper API per trascrizione
2.	Keyframe Extraction – Algoritmo basato su scene change detection + content-aware sampling
3.	Screenshot Generation – Salvataggio frame su S3/MinIO con metadata
4.	AI Analysis – OpenAI Vision + GPT-4 per descrizione visiva e riassunto strutturato
5.	Database – PostgreSQL per metadata, trascrizioni, analisi
6.	REST API – FastAPI per orchestrazione flusso
________________________________________
1. Setup Ambiente
Dipendenze Python
pip install fastapi uvicorn python-dotenv
pip install openai
pip install opencv-python pillow numpy scipy
pip install ffmpeg-python moviepy
pip install psycopg2-binary sqlalchemy
pip install boto3 # per AWS S3 / MinIO
pip install pydantic
Variabili ambiente (.env)
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:password@localhost:5432/video_analyzer
S3_BUCKET=video-screenshots
S3_ENDPOINT=https://s3.amazonaws.com # o MinIO locale
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
________________________________________
2. Database Schema (SQLAlchemy)
models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
class Video(Base):
tablename = "videos"
id = Column(Integer, primary_key=True)
filename = Column(String, unique=True, nullable=False)
upload_path = Column(String)
status = Column(String, default="pending") # pending, processing, completed, failed
duration_seconds = Column(Integer)
created_at = Column(DateTime, default=datetime.utcnow)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class Transcript(Base):
tablename = "transcripts"
id = Column(Integer, primary_key=True)
video_id = Column(Integer, nullable=False)
segments = Column(JSON) # [{"start": 0, "end": 30, "text": "..."}, ...]
full_text = Column(Text)
created_at = Column(DateTime, default=datetime.utcnow)
class Keyframe(Base):
tablename = "keyframes"
id = Column(Integer, primary_key=True)
video_id = Column(Integer, nullable=False)
timestamp = Column(Integer) # secondi
frame_number = Column(Integer)
s3_url = Column(String) # URL screenshot su S3/MinIO
visual_description = Column(Text) # descrizione OpenAI Vision
created_at = Column(DateTime, default=datetime.utcnow)
class Analysis(Base):
tablename = "analyses"
id = Column(Integer, primary_key=True)
video_id = Column(Integer, nullable=False)
summary = Column(Text)
modules = Column(JSON) # [{name, description, screens, flows}, ...]
flows = Column(JSON) # [{step, action, timestamp, screenshot}, ...]
issues = Column(JSON) # [{description, timestamp, severity}, ...]
output_format = Column(JSON) # full structured output
created_at = Column(DateTime, default=datetime.utcnow)
Crea le tabelle
Base.metadata.create_all(engine)
________________________________________
3. Video Processing Service
video_processor.py
import subprocess
import os
from pathlib import Path
import cv2
import numpy as np
from typing import List, Dict, Tuple
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name)
class VideoProcessor:
def init(self, video_path: str):
self.video_path = video_path
self.cap = cv2.VideoCapture(video_path)
self.fps = self.cap.get(cv2.CAP_PROP_FPS)
self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
self.duration = self.total_frames / self.fps
def extract_audio(self, output_audio_path: str) -> str:
    """Estrae audio da video con ffmpeg"""
    cmd = [
        "ffmpeg", "-i", self.video_path,
        "-q:a", "0", "-map", "a",
        output_audio_path, "-y"
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    logger.info(f"Audio estratto in {output_audio_path}")
    return output_audio_path

def extract_keyframes_scene_detection(
    self, 
    output_dir: str,
    threshold: float = 25.0,
    max_frames: int = 10
) -> List[Dict[str, any]]:
    """
    Estrae keyframe basato su scene change detection (variazione luminanza).
    Ritorna lista di frame con timestamp e path.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    keyframes = []
    prev_frame = None
    frame_count = 0
    keyframe_count = 0
    
    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    while True:
        ret, frame = self.cap.read()
        if not ret:
            break
        
        # Converti a scala di grigi per calcolo differenza
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calcola differenza istogramma rispetto al frame precedente
        if prev_frame is not None:
            hist_curr = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist_prev = cv2.calcHist([prev_frame], [0], None, [256], [0, 256])
            
            # Normalizza istogrammi
            hist_curr = cv2.normalize(hist_curr, hist_curr).flatten()
            hist_prev = cv2.normalize(hist_prev, hist_prev).flatten()
            
            # Calcola correlazione (0 = diverso, 1 = identico)
            correlation = cv2.compareHist(
                hist_curr, hist_prev, cv2.HISTCMP_CORREL
            )
            scene_change = (1 - correlation) * 100
            
            # Se differenza > threshold, è un keyframe
            if scene_change > threshold and keyframe_count < max_frames:
                timestamp = frame_count / self.fps
                frame_path = os.path.join(
                    output_dir, f"keyframe_{keyframe_count:03d}.jpg"
                )
                cv2.imwrite(frame_path, frame)
                
                keyframes.append({
                    "frame_number": frame_count,
                    "timestamp": round(timestamp, 2),
                    "path": frame_path,
                    "scene_change_score": round(scene_change, 2)
                })
                keyframe_count += 1
                logger.info(
                    f"Keyframe {keyframe_count} a {timestamp:.2f}s "
                    f"(scene_change={scene_change:.2f}%)"
                )
        
        prev_frame = gray
        frame_count += 1
    
    self.cap.release()
    return keyframes

def get_duration(self) -> float:
    """Ritorna durata video in secondi"""
    return self.duration

________________________________________
4. OpenAI Integration
ai_analyzer.py
from openai import OpenAI
import base64
from typing import List, Dict
import json
import logging
logger = logging.getLogger(name)
client = OpenAI()
class AIAnalyzer:
def init(self):
self.model_transcription = "whisper-1"
self.model_vision = "gpt-4-vision-preview" # o gpt-4o
self.model_analysis = "gpt-4-turbo"
def transcribe_audio(self, audio_path: str) -> Dict:
    """
    Trascrive audio usando Whisper API di OpenAI.
    Ritorna: {"text": "...", "segments": [...]}
    """
    logger.info(f"Trascrizione in corso: {audio_path}")
    
    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model=self.model_transcription,
            file=f,
            language="it",  # Italiano
            response_format="verbose_json"  # Ritorna timestamp dettagliati
        )
    
    # Formatta output
    segments = []
    if hasattr(transcript, 'segments'):
        for seg in transcript.segments:
            segments.append({
                "start": round(seg.get("start", 0), 2),
                "end": round(seg.get("end", 0), 2),
                "text": seg.get("text", "")
            })
    
    result = {
        "full_text": transcript.text,
        "segments": segments
    }
    logger.info(f"Trascrizione completata: {len(result['full_text'])} caratteri")
    return result

def describe_frame(self, image_path: str) -> str:
    """
    Analizza un frame immagine e ritorna descrizione strutturata
    usando GPT-4 Vision.
    """
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")
    
    prompt = """Analizza questa schermata di un'applicazione e descrivi:

1.	Componenti UI visibili (bottoni, menu, tabelle, form)
2.	Layout e struttura
3.	Informazioni o dati mostrati
4.	Possibili azioni disponibili
Rispondi in JSON con struttura:
{
"layout": "...",
"components": [...],
"data_visible": {...},
"possible_actions": [...]
}
"""
    response = client.messages.create(
        model=self.model_vision,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    
    return response.content[0].text

def analyze_full_flow(
    self,
    transcript_text: str,
    keyframes_descriptions: List[Dict],
    video_duration: float
) -> Dict:
    """
    Analizza il flusso completo: trascrizione + screenshot + durata.
    Ritorna: {summary, modules, flows, issues, feature_map}
    """
    
    keyframes_str = "\n".join([
        f"[{kf['timestamp']}s] {kf['description']}" 
        for kf in keyframes_descriptions
    ])
    
    prompt = f"""Analizza questa registrazione video di un'applicazione e genera un rapporto strutturato.

Trascrizione (durata {video_duration:.1f}s):
{transcript_text}
Schermate chiave con timestamp:
{keyframes_str}
Genera un JSON con questa struttura:
{{
"summary": "Descrizione generale dell'app in 2-3 righe",
"app_type": "Tipo di applicazione (web/mobile/desktop)",
"modules": [
{{
"name": "Nome modulo",
"description": "...",
"screens": ["nomi schermate"],
"key_features": ["feature1", "feature2"]
}}
],
"user_flows": [
{{
"name": "Flusso principale",
"steps": [
{{"step": 1, "action": "...", "timestamp": "X:XXs", "outcome": "..."}}
],
"actors": ["chi esegue"]
}}
],
"issues_and_observations": [
{{
"type": "UI/UX/Performance/Bug",
"description": "...",
"timestamp": "X:XXs",
"severity": "low/medium/high"
}}
],
"technology_hints": ["tecnologie dedotte"],
"recommendations": ["suggerimenti di miglioramento"]
}}
Sii specifico, usa i timestamp, riferisciti alle schermate evidenziate.
"""
    logger.info("Analisi completa in corso...")
    
    response = client.messages.create(
        model=self.model_analysis,
        max_tokens=3000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    response_text = response.content[0].text
    
    # Estrai JSON dalla risposta (potrebbe avere markdown fence)
    try:
        if "```json" in response_text:
            json_part = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            json_part = response_text.split("```")[1].split("```")[0]
        else:
            json_part = response_text
        
        analysis_json = json.loads(json_part)
    except json.JSONDecodeError:
        logger.warning("Impossibile parsare JSON, salvataggio raw text")
        analysis_json = {"raw_response": response_text}
    
    logger.info("Analisi completata")
    return analysis_json

________________________________________
5. S3/MinIO Upload
storage.py
import boto3
import os
from typing import Tuple
class S3Storage:
def init(self):
self.s3_client = boto3.client(
"s3",
endpoint_url=os.getenv("S3_ENDPOINT"),
aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
region_name="us-east-1"
)
self.bucket = os.getenv("S3_BUCKET", "video-screenshots")
def upload_keyframe(self, local_path: str, video_id: int, keyframe_num: int) -> str:
    """Carica keyframe su S3, ritorna URL pubblico"""
    s3_key = f"videos/{video_id}/keyframe_{keyframe_num:03d}.jpg"
    
    self.s3_client.upload_file(
        local_path, self.bucket, s3_key,
        ExtraArgs={"ContentType": "image/jpeg"}
    )
    
    # URL pubblico (adatta a MinIO o S3)
    url = f"{os.getenv('S3_ENDPOINT')}/{self.bucket}/{s3_key}"
    return url

def upload_video(self, local_path: str, video_id: int) -> str:
    """Carica video originale, ritorna URL"""
    s3_key = f"videos/{video_id}/original.mp4"
    self.s3_client.upload_file(local_path, self.bucket, s3_key)
    url = f"{os.getenv('S3_ENDPOINT')}/{self.bucket}/{s3_key}"
    return url

________________________________________
6. FastAPI Orchestration
main.py
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from contextlib import contextmanager
import os
import tempfile
import shutil
from models import Video, Transcript, Keyframe, Analysis, SessionLocal
from video_processor import VideoProcessor
from ai_analyzer import AIAnalyzer
from storage import S3Storage
import logging
app = FastAPI(title="Video Analyzer API")
logger = logging.getLogger(name)
@contextmanager
def get_db():
db = SessionLocal()
try:
yield db
finally:
db.close()
analyzer = AIAnalyzer()
storage = S3Storage()
@app.post("/upload")
async def upload_video(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
"""Carica video e avvia processing asincrono"""
# Salva file temporaneamente
temp_dir = tempfile.mkdtemp()
video_path = os.path.join(temp_dir, file.filename)

with open(video_path, "wb") as f:
    f.write(await file.read())

# Crea record DB
db = SessionLocal()
video_record = Video(
    filename=file.filename,
    upload_path=video_path,
    status="processing"
)
db.add(video_record)
db.commit()
video_id = video_record.id
db.close()

# Schedule processing asincrono
if background_tasks:
    background_tasks.add_task(process_video_async, video_id, video_path, temp_dir)

return JSONResponse({
    "video_id": video_id,
    "status": "processing",
    "message": "Video caricato, analisi in corso..."
})

async def process_video_async(video_id: int, video_path: str, temp_dir: str):
"""Task asincrono: processing completo"""
db = SessionLocal()
try:
    logger.info(f"Inizio processing video {video_id}")
    
    # 1. Estrai audio e trascivi
    processor = VideoProcessor(video_path)
    audio_path = os.path.join(temp_dir, "audio.mp3")
    processor.extract_audio(audio_path)
    
    transcript_result = analyzer.transcribe_audio(audio_path)
    
    # Salva trascrizione DB
    transcript = Transcript(
        video_id=video_id,
        full_text=transcript_result["full_text"],
        segments=transcript_result["segments"]
    )
    db.add(transcript)
    db.commit()
    
    # 2. Estrai keyframe
    keyframes_dir = os.path.join(temp_dir, "keyframes")
    keyframes_list = processor.extract_keyframes_scene_detection(
        keyframes_dir, threshold=25.0, max_frames=10
    )
    
    # 3. Analizza ogni keyframe con Vision
    keyframes_with_descriptions = []
    for idx, kf in enumerate(keyframes_list):
        try:
            description = analyzer.describe_frame(kf["path"])
            
            # Upload su S3
            s3_url = storage.upload_keyframe(kf["path"], video_id, idx)
            
            # Salva keyframe DB
            keyframe_db = Keyframe(
                video_id=video_id,
                timestamp=int(kf["timestamp"]),
                frame_number=kf["frame_number"],
                s3_url=s3_url,
                visual_description=description
            )
            db.add(keyframe_db)
            db.commit()
            
            keyframes_with_descriptions.append({
                "timestamp": kf["timestamp"],
                "description": description
            })
        except Exception as e:
            logger.error(f"Errore Vision frame {idx}: {e}")
    
    # 4. Analisi completa
    analysis = analyzer.analyze_full_flow(
        transcript_result["full_text"],
        keyframes_with_descriptions,
        processor.get_duration()
    )
    
    # Salva analisi DB
    analysis_record = Analysis(
        video_id=video_id,
        summary=analysis.get("summary"),
        modules=analysis.get("modules"),
        flows=analysis.get("user_flows"),
        issues=analysis.get("issues_and_observations"),
        output_format=analysis
    )
    db.add(analysis_record)
    
    # Aggiorna status video
    video = db.query(Video).filter(Video.id == video_id).first()
    video.status = "completed"
    video.duration_seconds = int(processor.get_duration())
    db.commit()
    
    logger.info(f"Processing completato per video {video_id}")
    
except Exception as e:
    logger.error(f"Errore processing {video_id}: {e}", exc_info=True)
    video = db.query(Video).filter(Video.id == video_id).first()
    video.status = "failed"
    db.commit()

finally:
    db.close()
    # Pulisci file temporanei
    shutil.rmtree(temp_dir, ignore_errors=True)

@app.get("/videos/{video_id}")
def get_video_analysis(video_id: int):
"""Ritorna analisi completa di un video"""
db = SessionLocal()
video = db.query(Video).filter(Video.id == video_id).first()
transcript = db.query(Transcript).filter(Transcript.video_id == video_id).first()
keyframes = db.query(Keyframe).filter(Keyframe.video_id == video_id).all()
analysis = db.query(Analysis).filter(Analysis.video_id == video_id).first()

db.close()

if not video:
    return JSONResponse({"error": "Video not found"}, status_code=404)

return JSONResponse({
    "video": {
        "id": video.id,
        "filename": video.filename,
        "status": video.status,
        "duration": video.duration_seconds,
        "created_at": video.created_at.isoformat()
    },
    "transcript": {
        "full_text": transcript.full_text if transcript else None,
        "segments": transcript.segments if transcript else None
    },
    "keyframes": [
        {
            "timestamp": kf.timestamp,
            "s3_url": kf.s3_url,
            "description": kf.visual_description
        } for kf in keyframes
    ],
    "analysis": analysis.output_format if analysis else None
})

@app.get("/videos")
def list_videos():
"""Lista tutti i video caricati"""
db = SessionLocal()
videos = db.query(Video).all()
db.close()
return JSONResponse([
    {
        "id": v.id,
        "filename": v.filename,
        "status": v.status,
        "created_at": v.created_at.isoformat()
    } for v in videos
])

if name == "main":
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
________________________________________
7. Esecuzione
Avvia servizio
1. Setup DB
python -c "from models import Base, engine; Base.metadata.create_all(engine)"
2. Avvia API
python main.py
API raggiungibile su http://localhost:8000
Workflow completo
Carica video (ritorna video_id: 1)
curl -X POST -F "file=@demo.mp4" http://localhost:8000/upload
Verifica status (polling ogni 10s)
curl http://localhost:8000/videos/1
Una volta completato, scarica analisi
curl http://localhost:8000/videos/1 | jq '.analysis'
________________________________________
8. Output Esempio
{
"summary": "Applicazione di gestione ordini per ristoranti con dashboard principale, lista tavoli e sistema di pagamento integrato.",
"app_type": "web",
"modules": [
{
"name": "Dashboard principale",
"description": "Panoramica ordini attivi e statistiche",
"screens": ["Home", "Statistiche giornaliere"],
"key_features": ["Visualizzazione ordini", "Filtri per stato", "Esportazione report"]
},
{
"name": "Gestione tavoli",
"description": "Layout tavoli con ordini associati",
"screens": ["Mappa tavoli", "Dettaglio tavolo"],
"key_features": ["Drag-drop ordini", "Modifica portate", "Note tavolo"]
}
],
"user_flows": [
{
"name": "Ciclo ordine completo",
"steps": [
{"step": 1, "action": "Accesso dashboard", "timestamp": "0:05s", "outcome": "Visualizzazione ordini"},
{"step": 2, "action": "Click tavolo #5", "timestamp": "0:32s", "outcome": "Apertura dettagli"},
{"step": 3, "action": "Aggiunta portate", "timestamp": "1:15s", "outcome": "Ordine confermato"}
]
}
],
"issues_and_observations": [
{
"type": "UX",
"description": "Pulsante 'Salva' poco visibile, potrebbe causare confusione",
"timestamp": "2:10s",
"severity": "medium"
}
]
}

