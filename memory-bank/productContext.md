# Product Context

## Purpose
Rapidly document demos, app recordings, meetings, and debriefs by generating a navigable dossier (JSON/PDF/ZIP/HTML/MD) with:
- Full transcription
- Key screenshots/frames
- User flows and modules
- Issues and observations
- Recreation instructions (for apps)

Reduces manual analysis and reporting work significantly.

## Target Users
- **Product/UX teams**: Analyze demo recordings and user sessions
- **QA teams**: Document bugs and testing sessions
- **Consultants**: Create client deliverables from meeting recordings
- **Developers**: Reverse engineer app demos
- **Operations**: Generate meeting summaries and action items

## User Experience Goals
1. **Simple Upload**: Drag & drop video/audio with optional context field to guide AI
2. **Clear Progress**: Real-time logs during processing (SSE + polling fallback)
3. **Rich Results**: Structured analysis viewable in tabs (Transcript, Analysis, Logs)
4. **Flexible Export**: Download in multiple formats (PDF, ZIP, HTML, Markdown)
5. **Library Management**: Search and filter uploaded content by name/status

## Current Status
- Core flow fully functional (upload → process → view → export)
- Dashboard with video library
- Video detail page with all tabs working
- Settings for API key configuration
- Reports page planned for future analytics
