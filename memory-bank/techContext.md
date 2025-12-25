# Tech Context

## Backend Stack
- Python 3.10+, FastAPI, SQLAlchemy ORM
- Celery (Redis broker/backend) for async processing
- boto3 for MinIO/S3 integration
- OpenCV for frame extraction, FFmpeg for audio
- OpenAI SDK for Whisper/Vision/GPT-4o

## Database
- PostgreSQL (via DATABASE_URL env)
- Tables: Media (aliased as Video), Transcript, Keyframe, Analysis, APIConfig, ProcessingLog

## Storage
- MinIO (S3-compatible) with configurable endpoints
- Env vars: MINIO_ENDPOINT, MINIO_PUBLIC_ENDPOINT, MINIO_BUCKET, MINIO_ACCESS_KEY, MINIO_SECRET_KEY

## Async Processing
- Celery tasks: `process_video_task`, `process_audio_task`
- Worker initializes AIAnalyzer + MinIOStorage at startup

## Frontend Stack
- Next.js 13+ with App Router
- Tailwind CSS for styling
- axios for API calls (`/frontend/lib/api.ts`)
- lucide-react for icons
- Custom hooks in `/frontend/lib/hooks.ts`

## Exports
- PDF: generated with HTML templates + styling
- ZIP: bundles analysis, keyframes, diagrams, README
- HTML/Markdown: template-based generation
- Diagrams: Mermaid syntax rendered via Kroki.io

## Development Environment
- docker-compose for Postgres, Redis, MinIO, web, worker, frontend
- FFmpeg required on host for video/audio processing
- Logging to app.log and worker console
- Hot reload enabled for frontend (Turbopack)

## Key Environment Variables
- DATABASE_URL, REDIS_URL
- OPENAI_API_KEY (or stored in APIConfig table)
- MINIO_* vars for storage
- CELERY_BROKER_URL, CELERY_RESULT_BACKEND
