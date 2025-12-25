<div align="center">

# 🎬 Video Analyzer

### AI-Powered Video & Audio Analysis Platform

Transform videos and audio recordings into comprehensive, structured documentation with AI-powered transcription, visual analysis, and intelligent insights.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/yourusername/video-analyzer/issues)

[Features](#-features) • [Demo](#-demo) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎤 Intelligent Transcription
- Full audio transcription using OpenAI Whisper
- Timestamped segments for easy navigation
- Support for multiple languages

</td>
<td width="50%">

### 🖼️ Visual Analysis
- Automatic keyframe extraction with scene detection
- AI-powered visual descriptions using GPT-4 Vision
- Smart deduplication to capture unique moments

</td>
</tr>
<tr>
<td width="50%">

### 📊 Structured Reports
- Automatic module/feature detection
- User flow mapping
- Issue identification & recommendations
- Recreation instructions for app demos

</td>
<td width="50%">

### 📤 Flexible Exports
- **PDF** – Professional reports with diagrams
- **ZIP** – Complete package with all assets
- **HTML/Markdown** – Web-ready documentation
- **Mermaid Diagrams** – User flows & sequences

</td>
</tr>
</table>

---

## 🖥️ Demo

<!-- 
Add your screenshots here! 
Replace the placeholder paths with actual screenshot URLs after capturing them.
Recommended sizes: Dashboard (1200x800), Upload (800x600), Analysis (1200x800)
-->

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)
*Video library with search, filtering, and status indicators*

### Upload Interface
![Upload](docs/screenshots/upload.png)
*Drag & drop upload with optional context for better AI analysis*

### Analysis View
![Analysis](docs/screenshots/analysis.png)
*Interactive video player with synchronized transcript and AI analysis*

### Processing Logs
![Processing](docs/screenshots/processing.png)
*Real-time processing logs with SSE streaming*

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│                         Next.js + Tailwind CSS                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ REST API
┌────────────────────────────────▼────────────────────────────────────────┐
│                              BACKEND                                     │
│                    FastAPI + SQLAlchemy + Celery                        │
└───────┬─────────────┬─────────────┬─────────────┬─────────────┬────────┘
        │             │             │             │             │
   ┌────▼────┐  ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
   │PostgreSQL│  │   Redis   │ │   MinIO   │ │  FFmpeg   │ │  OpenAI   │
   │ Database │  │  (Celery) │ │    (S3)   │ │  (Media)  │ │   APIs    │
   └──────────┘  └───────────┘ └───────────┘ └───────────┘ └───────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** – Container orchestration
- **FFmpeg** – Media processing ([Installation Guide](#installing-ffmpeg))
- **OpenAI API Key** – For AI features

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/video-analyzer.git
cd video-analyzer
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### 3. Launch with Docker

```bash
# Start all services (database, redis, minio, backend, worker, frontend)
docker-compose up -d

# Watch the logs
docker-compose logs -f
```

### 4. Access the Application

| Service | URL | Description |
|---------|-----|-------------|
| 🌐 **Frontend** | http://localhost:3000 | Main application |
| 📡 **API Docs** | http://localhost:8000/docs | Swagger documentation |
| 🗄️ **MinIO Console** | http://localhost:9001 | Object storage UI |

---

## 📦 Installation (Manual Setup)

<details>
<summary><strong>Click to expand manual installation steps</strong></summary>

### Installing FFmpeg

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

### Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Start Services Individually

```bash
# Terminal 1: Start infrastructure
docker-compose up -d postgres redis minio minio-init

# Terminal 2: Start backend API
python main.py

# Terminal 3: Start Celery worker
celery -A celery_app worker --loglevel=info

# Terminal 4: Start frontend
cd frontend && npm install && npm run dev
```

</details>

---

## 📖 Documentation

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload video for analysis |
| `POST` | `/upload-audio` | Upload audio for analysis |
| `GET` | `/videos` | List all videos (supports `?q=` search and `?status=` filter) |
| `GET` | `/videos/{id}` | Get video details with analysis |
| `GET` | `/videos/{id}/logs` | Get processing logs |
| `GET` | `/videos/{id}/logs/stream` | SSE endpoint for real-time logs |
| `GET` | `/videos/{id}/export/{format}` | Export as pdf, zip, html, or markdown |
| `DELETE` | `/videos/{id}` | Delete video and all associated data |
| `POST` | `/videos/{id}/retry` | Retry failed analysis |
| `GET` | `/health` | Health check with DB connectivity |

### Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | *Required* |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://video_user:video_password@localhost:5432/video_analyzer` |
| `MINIO_ENDPOINT` | MinIO/S3 endpoint | `http://localhost:9000` |
| `MINIO_BUCKET` | Storage bucket name | `video-screenshots` |
| `CELERY_BROKER_URL` | Redis broker URL | `redis://localhost:6379/0` |

### Project Structure

```
video-analyzer/
├── 🐍 Backend (Python/FastAPI)
│   ├── main.py              # FastAPI application & routes
│   ├── processing_pipeline.py # Celery tasks for async processing
│   ├── ai_analyzer.py       # OpenAI integration
│   ├── video_processor.py   # FFmpeg & OpenCV processing
│   ├── storage.py           # MinIO/S3 integration
│   └── models.py            # SQLAlchemy models
│
├── ⚛️ Frontend (Next.js)
│   ├── app/                 # App Router pages
│   ├── components/          # React components
│   └── lib/                 # Utilities & API client
│
├── 🐳 Infrastructure
│   ├── docker-compose.yml   # Full stack orchestration
│   └── Dockerfile           # Backend container
│
└── 📚 Documentation
    └── memory-bank/         # Project context & progress
```

---

## 🤝 Contributing

We love contributions! Video Analyzer is an open-source project and we welcome developers of all skill levels.

### 🌟 Ways to Contribute

| Type | Description |
|------|-------------|
| 🐛 **Bug Reports** | Found a bug? [Open an issue](https://github.com/yourusername/video-analyzer/issues/new?template=bug_report.md) |
| 💡 **Feature Requests** | Have an idea? [Start a discussion](https://github.com/yourusername/video-analyzer/discussions) |
| 📝 **Documentation** | Help improve our docs |
| 🧪 **Testing** | Write tests or improve coverage |
| 🎨 **UI/UX** | Enhance the frontend experience |
| 🔧 **Code** | Fix bugs or implement features |

### 🏁 Getting Started

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create** a feature branch: `git checkout -b feature/amazing-feature`
4. **Make** your changes
5. **Test** your changes thoroughly
6. **Commit** with clear messages: `git commit -m "feat: add amazing feature"`
7. **Push** to your branch: `git push origin feature/amazing-feature`
8. **Open** a Pull Request

### 📋 Priority Areas

We're especially looking for help with:

- [ ] **Authentication System** – JWT/OAuth implementation
- [ ] **Multi-language Support** – i18n for frontend and transcription
- [ ] **Additional AI Providers** – Anthropic Claude, local LLMs
- [ ] **Real Analytics Dashboard** – Processing metrics & insights
- [ ] **Kubernetes Deployment** – Helm charts & manifests
- [ ] **Test Coverage** – Unit & integration tests
- [ ] **Performance Optimization** – Faster processing pipeline
- [ ] **Mobile Responsiveness** – Better mobile UI

### 💻 Development Guidelines

- Follow existing code style and conventions
- Write meaningful commit messages ([Conventional Commits](https://conventionalcommits.org/))
- Add tests for new features
- Update documentation as needed
- Keep PRs focused and reasonably sized

---

## 📊 Roadmap

| Phase | Status | Features |
|-------|--------|----------|
| **Phase 1** | ✅ Complete | Core upload, processing, analysis, exports |
| **Phase 2** | ✅ Complete | Next.js frontend, SSE logs, search & filters |
| **Phase 3** | 🚧 In Progress | UI polish, error handling, thumbnails |
| **Phase 4** | 📋 Planned | Authentication, user management |
| **Phase 5** | 📋 Planned | Analytics dashboard, multi-tenant |

---

## ❓ Troubleshooting

<details>
<summary><strong>FFmpeg not found</strong></summary>

```
RuntimeError: FFmpeg not found
```

Install FFmpeg and ensure it's in your PATH:
```bash
# Verify installation
ffmpeg -version
```
</details>

<details>
<summary><strong>Database connection failed</strong></summary>

```
sqlalchemy.exc.OperationalError: could not connect to server
```

Check PostgreSQL is running:
```bash
docker-compose ps
docker-compose up -d postgres
```
</details>

<details>
<summary><strong>OpenAI API errors</strong></summary>

```
openai.AuthenticationError: Incorrect API key
```

Verify your `.env` file has a valid `OPENAI_API_KEY`
</details>

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** – see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [OpenAI](https://openai.com/) – Whisper, GPT-4, Vision APIs
- [FastAPI](https://fastapi.tiangolo.com/) – Modern Python web framework
- [Next.js](https://nextjs.org/) – React framework
- [Tailwind CSS](https://tailwindcss.com/) – Utility-first CSS
- [Celery](https://docs.celeryq.dev/) – Distributed task queue
- [MinIO](https://min.io/) – S3-compatible object storage
- [Kroki](https://kroki.io/) – Diagram rendering service

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ by contributors around the world



</div>

