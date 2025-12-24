# Video Analysis System – Project Brief

## Obiettivo
Creare un sistema di analisi automatica di video (MP4, MOV, AVI) che estrae trascrizione, descrizioni visive e genera un rapporto strutturato con mappa funzionalità, flussi utente e issue rilevate. Ideale per documentare demo video di applicazioni.

## Stack Tecnologico
- **Backend**: FastAPI (Python 3.10+)
- **AI/ML**: OpenAI APIs (Whisper per trascrizione, GPT-4 Vision per analisi visiva, GPT-4 Turbo per sintesi)
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Storage**: S3 / MinIO (screenshot keyframe)
- **Processing**: OpenCV + FFmpeg (estrazione audio, keyframe)
- **Task Async**: Background tasks FastAPI (scalare a Celery se necessario)

## Componenti da Implementare

### 1. Video Processing (`video_processor.py`)
- Estrazione audio con FFmpeg in WAV/MP3
- Keyframe extraction basato su scene change detection (istogramma correlazione)
- Parametri: threshold (25.0), max_frames (10)

### 2. AI Integration (`ai_analyzer.py`)
- **Whisper API**: Trascrizione audio italiano con timestamp segmentati
- **GPT-4 Vision**: Analisi frame-by-frame (componenti UI, layout, dati visibili)
- **GPT-4 Turbo**: Sintesi flusso completo → JSON strutturato (summary, modules, user_flows, issues, recommendations)

### 3. Database (`models.py`)
- **Video**: metadata video (filename, status, duration, created_at)
- **Transcript**: testo completo + segmenti con timestamp
- **Keyframe**: frame estratti con timestamp, URL S3, descrizione visiva
- **Analysis**: output finale strutturato (moduli, flussi, issue, raccomandazioni)

### 4. Storage (`storage.py`)
- Upload keyframe su S3/MinIO
- URL pubblico per accesso via API
- Gestione credenziali da `.env`

### 5. REST API (`main.py`)
- `POST /upload`: Carica video, avvia processing asincrono
- `GET /videos/{id}`: Ritorna analisi completa (video, trascrizione, keyframe, analisi JSON)
- `GET /videos`: Lista video processati

### 6. Workflow Completo
1. Upload video → crea record DB, lancia background task
2. Estrai audio + trascrivi (Whisper) → salva Transcript DB
3. Estrai keyframe + upload S3 → salva Keyframe DB con descrizione Vision
4. Analizza flusso (GPT-4 Turbo: testo + descrizioni visive) → salva Analysis DB
5. Ritorna JSON strutturato con: summary, modules, user_flows, issues, recommendations

## Output Atteso
```json
{
  "summary": "Descrizione app",
  "modules": [{"name": "...", "screens": [...], "key_features": [...]}],
  "user_flows": [{"name": "...", "steps": [{"step": 1, "action": "...", "timestamp": "X:XXs"}]}],
  "issues_and_observations": [{"type": "UI/UX/Bug", "description": "...", "severity": "low/medium/high"}],
  "recommendations": ["..."]
}
```

## Environment Variables (`.env`)
```
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:password@localhost:5432/video_analyzer
S3_BUCKET=video-screenshots
S3_ENDPOINT=https://s3.amazonaws.com  # o http://localhost:9000 per MinIO
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

## Dipendenze Python
```
fastapi
uvicorn
python-dotenv
openai
opencv-python
pillow
numpy
scipy
ffmpeg-python
moviepy
psycopg2-binary
sqlalchemy
boto3
pydantic
```

## Structure Progetto
```
video-analyzer/
├── main.py              # FastAPI app + endpoints
├── models.py            # SQLAlchemy DB models
├── video_processor.py   # Estrazione audio, keyframe
├── ai_analyzer.py       # OpenAI integration (Whisper, Vision, Turbo)
├── storage.py           # S3/MinIO upload
├── requirements.txt     # Dipendenze
├── .env.example         # Variabili ambiente template
├── docker-compose.yml   # PostgreSQL + MinIO (opzionale)
└── README.md           # Documentazione
```

## Flusso di Utilizzo
1. **Setup**: Configura `.env` con credenziali OpenAI, DB, S3
2. **Run**: `python main.py` (FastAPI su localhost:8000)
3. **Upload**: POST `/upload` con file video
4. **Poll**: GET `/videos/{id}` finché status != "completed"
5. **Result**: Scarica JSON analisi con screenshot, trascrizione, flussi

## Prossimi Passi (Fase 2)
- Containerizzazione Docker + docker-compose
- Frontend React/Vue dashboard
- WebSocket per real-time progress
- Celery per processing parallelo
- JWT auth per API
