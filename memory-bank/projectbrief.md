# Video Analysis System – Project Brief

Obiettivo: sistema automatico per analizzare video (e audio) generando trascrizioni, descrizioni visive e report strutturati con moduli, flussi utente, issue e raccomandazioni.

Output atteso (JSON): summary, modules, user_flows, issues_and_observations, how to recreate in case is an application.

Stack previsto: FastAPI (Python), OpenAI (Whisper, Vision, GPT-4o), PostgreSQL + SQLAlchemy, S3/MinIO per keyframe, OpenCV/FFmpeg per audio/keyframe, Celery per task async, frontend Next.js/Tailwind per dashboard.

Workflow alto livello:
1) Upload video/audio → crea record.
2) Estrai audio + trascrivi (Whisper).
3) Estrai keyframe (scene detection/adaptive) + descrizione visiva (Vision) + upload S3.
4) Analisi completa (GPT-4o) → JSON strutturato + diagrammi/wireframe.
5) API/Frontend mostrano stato, log, download/export (PDF/ZIP/HTML/MD).

