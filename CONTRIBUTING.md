# Contributing to Video Analyzer

First off, thank you for considering contributing to Video Analyzer! 🎉

It's people like you that make Video Analyzer such a great tool. We welcome contributions of all kinds – from bug fixes to new features, documentation improvements to design suggestions.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our commitment to creating a welcoming environment. We expect everyone to:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

## Getting Started

### Good First Issues

New to the project? Look for issues labeled:

- `good first issue` – Simple tasks for newcomers
- `help wanted` – We'd love your help on these
- `documentation` – Help improve our docs

### Before You Start

1. **Check existing issues** – Someone might already be working on it
2. **Open a discussion** – For major changes, discuss first
3. **Keep it focused** – One feature/fix per PR

## How to Contribute

### Reporting Bugs 🐛

Great bug reports help us improve! Include:

```markdown
**Environment:**
- OS: [e.g., Windows 11, macOS 14, Ubuntu 22.04]
- Docker version: [e.g., 24.0.7]
- Browser: [e.g., Chrome 120]

**Steps to Reproduce:**
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

**Expected Behavior:**
What you expected to happen.

**Actual Behavior:**
What actually happened.

**Screenshots/Logs:**
If applicable, add screenshots or log output.
```

### Suggesting Features 💡

We love new ideas! When proposing a feature:

1. **Explain the problem** – What user need does this address?
2. **Describe the solution** – How would it work?
3. **Consider alternatives** – What other approaches exist?
4. **Scope it** – Is this a small tweak or major feature?

### Contributing Code 🔧

1. Fork the repository
2. Create a feature branch from `main`
3. Write your code (and tests!)
4. Submit a Pull Request

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- FFmpeg
- Git

### Quick Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/video-analyzer.git
cd video-analyzer

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Start infrastructure
docker-compose up -d postgres redis minio minio-init

# Run backend (Terminal 1)
python main.py

# Run Celery worker (Terminal 2)
celery -A celery_app worker --loglevel=info

# Run frontend (Terminal 3)
cd frontend && npm run dev
```

### Running Tests

```bash
# Backend tests
pytest tests/

# Frontend tests (when available)
cd frontend && npm test
```

## Pull Request Process

### Before Submitting

- [ ] Code follows the project style guidelines
- [ ] Self-reviewed my code
- [ ] Added comments for complex logic
- [ ] Updated documentation if needed
- [ ] Added tests for new functionality
- [ ] All tests pass locally
- [ ] No linting errors

### PR Title Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add video thumbnail generation
fix: resolve SSE connection timeout
docs: update API documentation
style: format code with black
refactor: simplify keyframe extraction
test: add unit tests for ai_analyzer
chore: update dependencies
```

### Review Process

1. **Automated checks** – CI runs tests and linting
2. **Code review** – Maintainers review your changes
3. **Feedback** – Address any requested changes
4. **Merge** – Once approved, we'll merge your PR!

## Style Guidelines

### Python (Backend)

- Use **Black** for formatting
- Follow **PEP 8** conventions
- Type hints for function signatures
- Docstrings for public functions

```python
def process_video(video_id: int, context: str | None = None) -> dict:
    """
    Process a video file and extract analysis.
    
    Args:
        video_id: The database ID of the video
        context: Optional context to guide AI analysis
        
    Returns:
        Dictionary containing analysis results
    """
    ...
```

### TypeScript/React (Frontend)

- Use **Prettier** for formatting
- Follow existing component patterns
- Prefer functional components with hooks
- Type all props and state

```tsx
interface VideoCardProps {
  id: number;
  title: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  onDelete?: (id: number) => void;
}

export function VideoCard({ id, title, status, onDelete }: VideoCardProps) {
  // ...
}
```

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Keep first line under 72 characters
- Reference issues when relevant

```
feat: add PDF export with diagrams

- Integrate Kroki for diagram rendering
- Add report template with styling
- Support Mermaid syntax in analysis

Closes #123
```

### Documentation

- Keep README.md up to date
- Document new API endpoints
- Add JSDoc/docstrings for public functions
- Include code examples where helpful

## Project Structure

```
video-analyzer/
├── Backend (FastAPI)
│   ├── main.py              # API routes and app setup
│   ├── models.py            # SQLAlchemy database models
│   ├── processing_pipeline.py # Celery async tasks
│   ├── ai_analyzer.py       # OpenAI integration
│   ├── ai_providers.py      # Pluggable AI backends
│   ├── video_processor.py   # FFmpeg/OpenCV processing
│   ├── storage.py           # MinIO/S3 operations
│   └── routes_*.py          # Route modules
│
├── Frontend (Next.js)
│   ├── app/                 # Pages and routes
│   ├── components/          # React components
│   │   ├── ui/              # Base UI components
│   │   ├── features/        # Feature-specific components
│   │   └── layout/          # Layout components
│   ├── lib/                 # Utilities and API client
│   └── types/               # TypeScript definitions
│
└── Infrastructure
    ├── docker-compose.yml   # Local development stack
    ├── Dockerfile           # Backend container
    └── frontend/Dockerfile  # Frontend container
```

## Community

### Getting Help

- **Issues** – For bugs and feature requests
- **Discussions** – For questions and ideas
- **Discord** – Real-time chat (coming soon!)

### Recognition

All contributors are recognized in our:
- README acknowledgments
- Release notes
- Contributors page

---

## Thank You! 🙏

Every contribution, no matter how small, makes a difference. Whether you're fixing a typo, reporting a bug, or implementing a major feature – **thank you for being part of Video Analyzer!**

Happy coding! 🚀

