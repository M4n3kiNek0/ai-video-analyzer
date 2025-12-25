# System Patterns

## Architecture
- **Backend**: FastAPI + Celery worker (Redis broker), PostgreSQL via SQLAlchemy, MinIO/S3 for assets
- **AI Providers**: OpenAI/Groq/etc. via provider factory (`ai_providers/`)
- **Frontend**: Next.js 13+ (app dir) with axios API client, Tailwind CSS

## Video Processing Pipeline
1. Upload → create DB record (Media/Video) → enqueue Celery task
2. Extract audio (FFmpeg) → transcribe (Whisper provider) → semantic enrichment
3. Extract keyframes (scene detection + adaptive sampling + perceptual hash deduplication)
4. Describe frames (GPT-4 Vision with contextual prompts)
5. Full analysis (GPT-4o) → structured JSON + diagrams/wireframes
6. Save Analysis record → update status to completed/failed
7. Log progress to ProcessingLog table throughout

## Audio Processing Pipeline
- Similar to video but skips keyframe extraction
- Analysis tailored for meeting/brainstorming content

## Storage Pattern
- `MinIOStorage` wrapper uses bucket `video-screenshots`
- Paths organized as `videos/{id}/keyframes/`, `videos/{id}/original/`
- Generates public URLs via MINIO_PUBLIC_ENDPOINT

## API Patterns
- RESTful endpoints under `/videos`, `/upload`, `/config`
- SSE endpoint `/videos/{id}/logs/stream` for real-time logs
- Export endpoints `/videos/{id}/export/{format}` for PDF/ZIP/HTML/MD

## Frontend Patterns
- Dashboard polls every 10s for processing videos
- ProgressTerminal uses SSE with polling fallback
- Debounced search input (400ms delay)
- Status filter dropdown wired to backend `?status=` param
