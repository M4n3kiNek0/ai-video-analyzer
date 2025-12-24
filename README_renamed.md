# Video Analyzer System

Sistema di analisi automatica di video che estrae trascrizioni, descrizioni visive e genera report strutturati con mappa funzionalità, flussi utente e issue rilevate. Ideale per documentare demo video di applicazioni.

## Funzionalità

- **Trascrizione Audio**: Estrazione e trascrizione automatica con OpenAI Whisper
- **Keyframe Detection**: Rilevamento scene change con OpenCV per estrarre frame significativi
- **Analisi Visiva**: Descrizione componenti UI con GPT-4 Vision
- **Report Strutturato**: Generazione automatica di JSON con moduli, flussi utente, issue e raccomandazioni

## Architettura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Client/API    │────▶│   FastAPI        │────▶│   PostgreSQL    │
│   (Upload)      │     │   Backend        │     │   Database      │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐ ┌────▼────┐ ┌─────▼─────┐
              │  FFmpeg   │ │ OpenCV  │ │  MinIO    │
              │  (Audio)  │ │(Frames) │ │  (S3)     │
              └─────┬─────┘ └────┬────┘ └───────────┘
                    │            │
              ┌─────▼─────┐ ┌────▼────┐
              │  Whisper  │ │ GPT-4   │
              │   API     │ │ Vision  │
              └─────┬─────┘ └────┬────┘
                    │            │
                    └─────┬──────┘
                          │
                    ┌─────▼─────┐
                    │  GPT-4    │
                    │  Turbo    │
                    └───────────┘
```

## Requisiti

- Python 3.10+
- Docker & Docker Compose
- FFmpeg
- OpenAI API Key

## Quick Start

### 1. Clona e configura

```bash
# Copia il file di configurazione
cp .env.example .env

# Modifica .env con la tua API key OpenAI
# OPENAI_API_KEY=sk-your-key-here
```

### 2. Installa FFmpeg

**Windows (PowerShell):**
```powershell
winget install FFmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

### 3. Avvia i servizi Docker

```bash
# Avvia PostgreSQL e MinIO
docker-compose up -d

# Verifica che i container siano attivi
docker-compose ps
```

I servizi saranno disponibili su:
- **PostgreSQL**: `localhost:5432`
- **MinIO API**: `localhost:9000`
- **MinIO Console**: `localhost:9001` (user: `minioadmin`, password: `minioadmin123`)

### 4. Setup Python

```bash
# Crea virtual environment
python -m venv venv

# Attiva venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt
```

### 5. Inizializza Database

```bash
python -c "from models import init_db; init_db()"
```

### 6. Avvia l'API

```bash
python main.py
```

L'API sarà disponibile su:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Utilizzo API

### Upload Video

```bash
curl -X POST -F "file=@demo.mp4" http://localhost:8000/upload
```

Risposta:
```json
{
    "video_id": 1,
    "status": "processing",
    "message": "Video caricato con successo. Analisi in corso..."
}
```

### Verifica Stato

```bash
curl http://localhost:8000/videos/1
```

### Lista Video

```bash
curl http://localhost:8000/videos
```

### Elimina Video

```bash
curl -X DELETE http://localhost:8000/videos/1
```

## Output Analisi

```json
{
    "video": {
        "id": 1,
        "filename": "demo.mp4",
        "status": "completed",
        "duration": 120
    },
    "transcript": {
        "full_text": "Trascrizione completa...",
        "segments": [
            {"start": 0.0, "end": 5.2, "text": "Benvenuti..."}
        ]
    },
    "keyframes": [
        {
            "timestamp": 0,
            "s3_url": "http://localhost:9000/video-screenshots/videos/1/keyframes/keyframe_000.jpg",
            "description": "{...}"
        }
    ],
    "analysis": {
        "summary": "Applicazione web per gestione ordini...",
        "app_type": "web",
        "modules": [...],
        "user_flows": [...],
        "issues_and_observations": [...],
        "recommendations": [...]
    }
}
```

## Struttura Progetto

```
video-analyzer/
├── main.py              # FastAPI app + endpoints
├── models.py            # SQLAlchemy DB models
├── video_processor.py   # Estrazione audio, keyframe
├── ai_analyzer.py       # OpenAI integration
├── storage.py           # MinIO upload
├── requirements.txt     # Dipendenze Python
├── docker-compose.yml   # PostgreSQL + MinIO
├── .env.example         # Template variabili ambiente
└── README.md            # Documentazione
```

## Configurazione

### Variabili Ambiente (.env)

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `OPENAI_API_KEY` | API key OpenAI | (required) |
| `DATABASE_URL` | Connection string PostgreSQL | `postgresql://video_user:video_password@localhost:5432/video_analyzer` |
| `MINIO_ENDPOINT` | Endpoint MinIO locale | `http://localhost:9000` |
| `MINIO_BUCKET` | Nome bucket | `video-screenshots` |
| `MINIO_ACCESS_KEY` | Access key MinIO | `minioadmin` |
| `MINIO_SECRET_KEY` | Secret key MinIO | `minioadmin123` |

### Parametri Video Processing

In `video_processor.py`:
- `threshold`: Sensibilità scene detection (default: 25.0)
- `max_frames`: Massimo keyframe da estrarre (default: 10)
- `min_interval_seconds`: Intervallo minimo tra keyframe (default: 2.0)

## Troubleshooting

### FFmpeg non trovato

```
RuntimeError: FFmpeg not found
```

Soluzione: Installa FFmpeg e assicurati che sia nel PATH:
```powershell
winget install FFmpeg
# Riavvia il terminale
```

### Connessione Database fallita

```
sqlalchemy.exc.OperationalError: could not connect to server
```

Soluzione: Verifica che PostgreSQL sia attivo:
```bash
docker-compose ps
docker-compose up -d postgres
```

### MinIO non raggiungibile

```
botocore.exceptions.EndpointConnectionError
```

Soluzione: Verifica che MinIO sia attivo:
```bash
docker-compose up -d minio
# Attendi 30 secondi per l'inizializzazione
```

### OpenAI API Error

```
openai.AuthenticationError: Incorrect API key
```

Soluzione: Verifica la API key nel file `.env`

## Sviluppo

### Test API Connection

```bash
# Test OpenAI
python -c "from ai_analyzer import test_api_connection; print(test_api_connection())"

# Test Storage
python -c "from storage import test_storage_connection; print(test_storage_connection())"

# Test FFmpeg
python -c "from video_processor import check_ffmpeg_installed; print(check_ffmpeg_installed())"
```

### Log Dettagliati

I log sono configurati a livello INFO. Per debug più dettagliato, modifica in `main.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Roadmap (Fase 2)

- [ ] Frontend React/Vue dashboard
- [ ] WebSocket per progress real-time
- [ ] Celery per processing parallelo
- [ ] JWT authentication
- [ ] Export PDF/Word del report
- [ ] Supporto multi-lingua

## License

MIT License

