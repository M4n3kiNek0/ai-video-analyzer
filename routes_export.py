"""
Export Routes - PDF, ZIP, HTML, and Markdown export endpoints.
"""

import os
import io
import json
import zipfile
import logging
from datetime import datetime
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from models import Video, Transcript, Keyframe, Analysis, get_db
from pdf_generator import generate_video_report
from html_report_generator import generate_html_report
from diagram_generator import DiagramGenerator
from description_parser import DescriptionParser
from export_templates import EXPORT_TEMPLATES, get_template

# Configure logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/videos", tags=["export"])


def _get_video_data(video: Video) -> dict:
    """Helper to build video data dict for exports."""
    return {
        "id": video.id,
        "filename": video.filename,
        "status": video.status,
        "media_type": video.media_type if hasattr(video, 'media_type') else 'video',
        "analysis_type": video.analysis_type if hasattr(video, 'analysis_type') else 'auto',
        "duration": video.duration_seconds,
        "created_at": video.created_at.isoformat() if video.created_at else None
    }


def _get_transcript_data(transcript: Optional[Transcript]) -> Optional[dict]:
    """Helper to build transcript data dict for exports."""
    if not transcript:
        return None
    return {
        "full_text": transcript.full_text,
        "segments": transcript.segments,
        "language": transcript.language,
        "semantic_summary": getattr(transcript, 'semantic_summary', None),
        "topics": getattr(transcript, 'topics', None),
        "tone": getattr(transcript, 'tone', None),
        "speaking_style": getattr(transcript, 'speaking_style', None)
    }


def _get_keyframes_data(keyframes: list) -> list:
    """Helper to build keyframes data list for exports."""
    return [
        {
            "timestamp": kf.timestamp,
            "frame_number": kf.frame_number,
            "s3_url": kf.s3_url,
            "description": kf.visual_description
        } for kf in keyframes
    ]


def _generate_readme_for_template(video, template_type: str, keyframes_count: int, analysis) -> str:
    """Generate template-specific README content."""
    
    # Get template config
    template_config = None
    template_name = "Analisi"
    try:
        if template_type and template_type in EXPORT_TEMPLATES:
            template_config = EXPORT_TEMPLATES[template_type]
            template_name = template_config.get("name", "Analisi")
    except:
        pass
    
    media_type = video.media_type if hasattr(video, 'media_type') else 'video'
    duration_mins = video.duration_seconds // 60 if video.duration_seconds else 0
    duration_secs = video.duration_seconds % 60 if video.duration_seconds else 0
    
    # Template-specific file descriptions
    files_table = _get_template_files_table(template_type, media_type, keyframes_count)
    usage_section = _get_template_usage_section(template_type, analysis)
    
    readme = f"""# {template_name}: {video.filename}

Questo archivio contiene l'analisi completa generata da Media Analyzer.

**Tipo di Analisi:** {template_name}
**Tipo Media:** {media_type.upper()}

## Contenuto

{files_table}

## Informazioni Media

- **Nome:** {video.filename}
- **Durata:** {duration_mins}:{duration_secs:02d}
- **Tipo:** {media_type.upper()}
- **Template:** {template_name}
- **Keyframes:** {keyframes_count if media_type == 'video' else 'N/A'}
- **Data Export:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

{usage_section}

---
Generato da Media Analyzer
"""
    return readme


def _get_template_files_table(template_type: str, media_type: str, keyframes_count: int) -> str:
    """Generate files table based on template type."""
    
    base_files = """| File/Cartella | Descrizione |
|---------------|-------------|
| `report.pdf` | Report PDF completo con copertina e indice |
| `transcript.txt` | Trascrizione audio completa |
| `analysis.json` | Dati di analisi in formato JSON |"""
    
    if template_type == "reverse_engineering":
        return base_files + """
| `descriptions.txt` | Descrizioni dettagliate di ogni keyframe |
| `data_model.md` | Modello dati inferito |
| `api_spec.md` | Specifiche API dedotte |
| `images/` | Screenshot keyframe estratti |
| `diagrams/` | Diagrammi Mermaid |"""
    
    elif template_type == "meeting":
        return base_files + """
| `action_items.md` | Lista action items con responsabili |
| `decisions.md` | Decisioni prese durante il meeting |
| `meeting_minutes.md` | Verbale completo della riunione |"""
    
    elif template_type == "debrief":
        return base_files + """
| `lessons_learned.md` | Lezioni apprese |
| `recommendations.md` | Raccomandazioni per il futuro |
| `improvements.md` | Proposte di miglioramento |"""
    
    elif template_type == "brainstorming":
        return base_files + """
| `ideas.md` | Tutte le idee raccolte |
| `ideas_by_category.md` | Idee organizzate per categoria |
| `ideas_matrix.csv` | Matrice fattibilità/impatto |"""
    
    elif template_type == "notes":
        return base_files + """
| `notes.md` | Note strutturate |
| `key_points.md` | Punti chiave estratti |"""
    
    else:
        # Generic
        if media_type == "video" and keyframes_count > 0:
            return base_files + """
| `descriptions.txt` | Descrizioni keyframe |
| `images/` | Screenshot estratti |
| `diagrams/` | Diagrammi generati |"""
        else:
            return base_files


def _get_template_usage_section(template_type: str, analysis) -> str:
    """Generate usage section based on template type."""
    
    base_usage = """## Utilizzo

### Report PDF
Apri `report.pdf` per una visione completa dell'analisi.

### Dati Programmabili
Usa `analysis.json` per importare i dati in altri strumenti."""
    
    if template_type == "meeting":
        action_count = len(analysis.action_items) if analysis and analysis.action_items else 0
        decision_count = len(analysis.decisions) if analysis and analysis.decisions else 0
        return base_usage + f"""

### Action Items
{action_count} action item estratti. Consulta `action_items.md` per la lista completa.

### Decisioni
{decision_count} decisioni registrate. Vedi `decisions.md` per i dettagli."""
    
    elif template_type == "brainstorming":
        return base_usage + """

### Idee
Tutte le idee sono in `ideas.md`. Per una visione organizzata, consulta `ideas_by_category.md`.

### Valutazione
La matrice in `ideas_matrix.csv` può essere importata in Excel per analisi."""
    
    elif template_type == "debrief":
        return base_usage + """

### Lessons Learned
Consulta `lessons_learned.md` per le lezioni apprese da questa sessione.

### Piano d'Azione
Le raccomandazioni in `recommendations.md` possono guidare i prossimi passi."""
    
    elif template_type == "reverse_engineering":
        return base_usage + """

### Per Sviluppatori
- `data_model.md` contiene lo schema dati inferito
- `api_spec.md` elenca gli endpoint dedotti
- I diagrammi in `diagrams/` mostrano flussi e architettura

### Immagini
Gli screenshot in `images/` sono nominati cronologicamente."""
    
    else:
        return base_usage


def _add_template_specific_files(zip_file, template_type: str, analysis, video) -> None:
    """Add template-specific markdown files to the ZIP export."""
    
    if not analysis or not analysis.output_format:
        return
    
    output = analysis.output_format
    
    if template_type == "meeting":
        # Action Items
        action_items = output.get("action_items", []) or (analysis.action_items if analysis.action_items else [])
        if action_items:
            content = _generate_action_items_md(action_items, video.filename)
            zip_file.writestr("action_items.md", content.encode('utf-8'))
            logger.info(f"Added action_items.md with {len(action_items)} items")
        
        # Decisions
        decisions = output.get("decisions", []) or (analysis.decisions if analysis.decisions else [])
        if decisions:
            content = _generate_decisions_md(decisions, video.filename)
            zip_file.writestr("decisions.md", content.encode('utf-8'))
            logger.info(f"Added decisions.md with {len(decisions)} decisions")
        
        # Meeting Minutes
        content = _generate_meeting_minutes_md(output, video)
        zip_file.writestr("meeting_minutes.md", content.encode('utf-8'))
        logger.info("Added meeting_minutes.md")
    
    elif template_type == "brainstorming":
        # All Ideas
        ideas = output.get("ideas_collected", [])
        if ideas:
            content = _generate_ideas_md(ideas, video.filename)
            zip_file.writestr("ideas.md", content.encode('utf-8'))
            logger.info(f"Added ideas.md with {len(ideas)} ideas")
        
        # Ideas by Category
        categories = output.get("ideas_by_category", [])
        if categories:
            content = _generate_ideas_by_category_md(categories, video.filename)
            zip_file.writestr("ideas_by_category.md", content.encode('utf-8'))
            logger.info(f"Added ideas_by_category.md")
        
        # Ideas Matrix CSV
        top_ideas = output.get("top_ideas", []) or output.get("feasibility_analysis", [])
        if top_ideas:
            content = _generate_ideas_matrix_csv(top_ideas)
            zip_file.writestr("ideas_matrix.csv", content.encode('utf-8'))
            logger.info(f"Added ideas_matrix.csv")
    
    elif template_type == "debrief":
        # Lessons Learned
        lessons = output.get("lessons_learned", [])
        if lessons:
            content = _generate_lessons_learned_md(lessons, video.filename)
            zip_file.writestr("lessons_learned.md", content.encode('utf-8'))
            logger.info(f"Added lessons_learned.md with {len(lessons)} lessons")
        
        # Recommendations
        recommendations = output.get("recommendations", [])
        if recommendations:
            content = _generate_recommendations_md(recommendations, video.filename)
            zip_file.writestr("recommendations.md", content.encode('utf-8'))
            logger.info(f"Added recommendations.md")
        
        # Improvements
        improvements = output.get("improvements", [])
        if improvements:
            content = _generate_improvements_md(improvements, video.filename)
            zip_file.writestr("improvements.md", content.encode('utf-8'))
            logger.info(f"Added improvements.md")
    
    elif template_type == "notes":
        # Notes
        content = _generate_notes_md(output, video)
        zip_file.writestr("notes.md", content.encode('utf-8'))
        logger.info("Added notes.md")
        
        # Key Points
        key_points = output.get("key_points", [])
        if key_points:
            content = _generate_key_points_md(key_points, video.filename)
            zip_file.writestr("key_points.md", content.encode('utf-8'))
            logger.info(f"Added key_points.md")
    
    elif template_type == "reverse_engineering":
        # Data Model
        data_model = output.get("data_model", {})
        if data_model:
            content = _generate_data_model_md(data_model, video.filename)
            zip_file.writestr("data_model.md", content.encode('utf-8'))
            logger.info("Added data_model.md")
        
        # API Spec
        api_spec = output.get("api_specification", {})
        if api_spec:
            content = _generate_api_spec_md(api_spec, video.filename)
            zip_file.writestr("api_spec.md", content.encode('utf-8'))
            logger.info("Added api_spec.md")
        
        # Tech Stack
        tech_stack = output.get("technology_stack", {})
        if tech_stack:
            content = _generate_tech_stack_md(tech_stack, video.filename)
            zip_file.writestr("tech_stack.md", content.encode('utf-8'))
            logger.info("Added tech_stack.md")


def _generate_action_items_md(action_items: list, filename: str) -> str:
    """Generate action items markdown file."""
    lines = [f"# Action Items - {filename}", "", f"Estratti il {datetime.now().strftime('%d/%m/%Y %H:%M')}", ""]
    
    for idx, item in enumerate(action_items, 1):
        item_text = item.get("item", item.get("description", ""))
        assignee = item.get("assignee", "Non assegnato")
        deadline = item.get("deadline", "Non specificata")
        priority = item.get("priority", "medium").upper()
        timestamp = item.get("timestamp", "")
        
        lines.append(f"## {idx}. [{priority}] {item_text}")
        lines.append("")
        lines.append(f"- **Responsabile:** {assignee}")
        lines.append(f"- **Scadenza:** {deadline}")
        if timestamp:
            lines.append(f"- **Discusso a:** {timestamp}")
        lines.append("")
    
    return "\n".join(lines)


def _generate_decisions_md(decisions: list, filename: str) -> str:
    """Generate decisions markdown file."""
    lines = [f"# Decisioni - {filename}", "", f"Registrate il {datetime.now().strftime('%d/%m/%Y %H:%M')}", ""]
    
    for idx, dec in enumerate(decisions, 1):
        decision = dec.get("decision", "")
        made_by = dec.get("made_by", "Non specificato")
        rationale = dec.get("rationale", "")
        timestamp = dec.get("timestamp", "")
        
        lines.append(f"## {idx}. {decision}")
        lines.append("")
        lines.append(f"- **Deciso da:** {made_by}")
        if rationale:
            lines.append(f"- **Motivazione:** {rationale}")
        if timestamp:
            lines.append(f"- **Timestamp:** {timestamp}")
        lines.append("")
    
    return "\n".join(lines)


def _generate_meeting_minutes_md(output: dict, video) -> str:
    """Generate complete meeting minutes."""
    lines = [f"# Verbale Riunione - {video.filename}", ""]
    
    # Meeting info
    lines.append("## Informazioni")
    lines.append(f"- **Data:** {datetime.now().strftime('%d/%m/%Y')}")
    if video.duration_seconds:
        lines.append(f"- **Durata:** {video.duration_seconds // 60}:{video.duration_seconds % 60:02d}")
    lines.append("")
    
    # Summary
    if output.get("summary"):
        lines.append("## Riepilogo")
        lines.append(output["summary"])
        lines.append("")
    
    # Participants
    participants = output.get("participants", output.get("speakers", []))
    if participants:
        lines.append("## Partecipanti")
        for p in participants:
            name = p.get("name", p.get("inferred_name", "Partecipante"))
            role = p.get("role", "")
            lines.append(f"- {name}" + (f" ({role})" if role else ""))
        lines.append("")
    
    # Topics
    topics = output.get("agenda_topics", output.get("topics", []))
    if topics:
        lines.append("## Argomenti Discussi")
        for t in topics:
            topic_name = t.get("topic", t.get("name", ""))
            summary = t.get("summary", "")
            lines.append(f"### {topic_name}")
            if summary:
                lines.append(summary)
            lines.append("")
    
    return "\n".join(lines)


def _generate_ideas_md(ideas: list, filename: str) -> str:
    """Generate all ideas markdown file."""
    lines = [f"# Idee Raccolte - {filename}", "", f"Sessione del {datetime.now().strftime('%d/%m/%Y')}", ""]
    
    for idx, idea in enumerate(ideas, 1):
        idea_text = idea.get("idea", "")
        proposed_by = idea.get("proposed_by", "")
        timestamp = idea.get("timestamp", "")
        
        lines.append(f"## Idea {idx}")
        lines.append(idea_text)
        if proposed_by:
            lines.append(f"*Proposta da: {proposed_by}*")
        if timestamp:
            lines.append(f"*Timestamp: {timestamp}*")
        lines.append("")
    
    return "\n".join(lines)


def _generate_ideas_by_category_md(categories: list, filename: str) -> str:
    """Generate ideas by category markdown file."""
    lines = [f"# Idee per Categoria - {filename}", ""]
    
    for cat in categories:
        cat_name = cat.get("category", "Altro")
        description = cat.get("description", "")
        idea_ids = cat.get("idea_ids", [])
        
        lines.append(f"## {cat_name}")
        if description:
            lines.append(description)
        lines.append(f"*{len(idea_ids)} idee in questa categoria*")
        lines.append("")
    
    return "\n".join(lines)


def _generate_ideas_matrix_csv(top_ideas: list) -> str:
    """Generate ideas feasibility/impact matrix CSV."""
    lines = ["Idea,Fattibilita,Impatto,Effort,Quick Win"]
    
    for idea in top_ideas:
        idea_text = idea.get("idea", idea.get("idea_summary", "")).replace(",", ";")[:100]
        feasibility = idea.get("feasibility_score", idea.get("feasibility", ""))
        impact = idea.get("impact_score", idea.get("potential_impact", ""))
        effort = idea.get("effort_estimate", "")
        quick_win = "Si" if idea.get("quick_win", False) else "No"
        
        lines.append(f'"{idea_text}",{feasibility},{impact},{effort},{quick_win}')
    
    return "\n".join(lines)


def _generate_lessons_learned_md(lessons: list, filename: str) -> str:
    """Generate lessons learned markdown file."""
    lines = [f"# Lessons Learned - {filename}", ""]
    
    for idx, lesson in enumerate(lessons, 1):
        lesson_text = lesson.get("lesson", "")
        category = lesson.get("category", "")
        priority = lesson.get("priority", "medium").upper()
        action = lesson.get("action", "")
        
        lines.append(f"## {idx}. [{priority}] {lesson_text}")
        if category:
            lines.append(f"*Categoria: {category}*")
        if action:
            lines.append(f"**Azione:** {action}")
        lines.append("")
    
    return "\n".join(lines)


def _generate_recommendations_md(recommendations: list, filename: str) -> str:
    """Generate recommendations markdown file."""
    lines = [f"# Raccomandazioni - {filename}", ""]
    
    for idx, rec in enumerate(recommendations, 1):
        if isinstance(rec, str):
            lines.append(f"{idx}. {rec}")
        else:
            rec_text = rec.get("recommendation", rec.get("description", ""))
            priority = rec.get("priority", "").upper()
            rationale = rec.get("rationale", "")
            
            lines.append(f"## {idx}. {rec_text}")
            if priority:
                lines.append(f"*Priorità: {priority}*")
            if rationale:
                lines.append(f"*Motivazione: {rationale}*")
        lines.append("")
    
    return "\n".join(lines)


def _generate_improvements_md(improvements: list, filename: str) -> str:
    """Generate improvements markdown file."""
    lines = [f"# Proposte di Miglioramento - {filename}", ""]
    
    for idx, imp in enumerate(improvements, 1):
        area = imp.get("area", "")
        current = imp.get("current_state", "")
        desired = imp.get("desired_state", "")
        actions = imp.get("proposed_actions", [])
        
        lines.append(f"## {idx}. {area}")
        if current:
            lines.append(f"**Stato attuale:** {current}")
        if desired:
            lines.append(f"**Stato desiderato:** {desired}")
        if actions:
            lines.append("**Azioni proposte:**")
            for a in actions:
                lines.append(f"- {a}")
        lines.append("")
    
    return "\n".join(lines)


def _generate_notes_md(output: dict, video) -> str:
    """Generate general notes markdown file."""
    lines = [f"# Note - {video.filename}", "", f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ""]
    
    # Summary
    if output.get("summary"):
        lines.append("## Riassunto")
        lines.append(output["summary"])
        lines.append("")
    
    # Key Points
    key_points = output.get("key_points", [])
    if key_points:
        lines.append("## Punti Chiave")
        for kp in key_points:
            point = kp.get("point", kp) if isinstance(kp, dict) else kp
            lines.append(f"- {point}")
        lines.append("")
    
    # Topics
    topics = output.get("topics", [])
    if topics:
        lines.append("## Argomenti")
        for t in topics:
            topic = t.get("topic", t.get("name", "")) if isinstance(t, dict) else t
            lines.append(f"- {topic}")
        lines.append("")
    
    return "\n".join(lines)


def _generate_key_points_md(key_points: list, filename: str) -> str:
    """Generate key points markdown file."""
    lines = [f"# Punti Chiave - {filename}", ""]
    
    for idx, kp in enumerate(key_points, 1):
        if isinstance(kp, dict):
            point = kp.get("point", "")
            importance = kp.get("importance", "").upper()
            timestamp = kp.get("timestamp", "")
            
            lines.append(f"## {idx}. {point}")
            if importance:
                lines.append(f"*Importanza: {importance}*")
            if timestamp:
                lines.append(f"*Timestamp: {timestamp}*")
        else:
            lines.append(f"{idx}. {kp}")
        lines.append("")
    
    return "\n".join(lines)


def _generate_data_model_md(data_model: dict, filename: str) -> str:
    """Generate data model markdown file."""
    lines = [f"# Modello Dati Inferito - {filename}", ""]
    
    entities = data_model.get("entities", [])
    for entity in entities:
        name = entity.get("name", "Entity")
        description = entity.get("description", "")
        
        lines.append(f"## {name}")
        if description:
            lines.append(description)
        lines.append("")
        
        fields = entity.get("fields", [])
        if fields:
            lines.append("### Campi")
            lines.append("| Campo | Tipo | Descrizione |")
            lines.append("|-------|------|-------------|")
            for f in fields:
                fname = f.get("name", "")
                ftype = f.get("type", "")
                fdesc = f.get("description", "")
                lines.append(f"| {fname} | {ftype} | {fdesc} |")
            lines.append("")
    
    return "\n".join(lines)


def _generate_api_spec_md(api_spec: dict, filename: str) -> str:
    """Generate API specification markdown file."""
    lines = [f"# Specifiche API Inferite - {filename}", ""]
    
    base_url = api_spec.get("base_url", "/api")
    lines.append(f"**Base URL:** `{base_url}`")
    lines.append("")
    
    endpoints = api_spec.get("endpoints", [])
    for ep in endpoints:
        method = ep.get("method", "GET")
        path = ep.get("path", "/")
        description = ep.get("description", "")
        
        lines.append(f"## `{method} {path}`")
        if description:
            lines.append(description)
        lines.append("")
    
    return "\n".join(lines)


def _generate_tech_stack_md(tech_stack: dict, filename: str) -> str:
    """Generate technology stack markdown file."""
    lines = [f"# Stack Tecnologico - {filename}", ""]
    
    if tech_stack.get("frontend_framework"):
        lines.append(f"- **Frontend Framework:** {tech_stack['frontend_framework']}")
    if tech_stack.get("ui_library"):
        lines.append(f"- **UI Library:** {tech_stack['ui_library']}")
    if tech_stack.get("state_management"):
        lines.append(f"- **State Management:** {tech_stack['state_management']}")
    if tech_stack.get("styling"):
        lines.append(f"- **Styling:** {tech_stack['styling']}")
    if tech_stack.get("platform"):
        lines.append(f"- **Platform:** {tech_stack['platform']}")
    
    return "\n".join(lines)


@router.get("/{video_id}/export/pdf")
async def export_video_pdf(video_id: int, db: Session = Depends(get_db)):
    """
    Export video analysis as a PDF report.
    
    Returns a downloadable PDF file with:
    - Executive summary
    - Enriched transcription
    - User flows
    - Modules and features
    - Issues and recommendations
    - Keyframes timeline
    """
    # Fetch video
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Video analysis not completed. Current status: {video.status}"
        )
    
    # Fetch related data
    transcript = db.query(Transcript).filter(Transcript.video_id == video_id).first()
    keyframes = db.query(Keyframe).filter(Keyframe.video_id == video_id).order_by(Keyframe.timestamp).all()
    analysis = db.query(Analysis).filter(Analysis.video_id == video_id).first()
    
    # Prepare data for PDF
    video_data = _get_video_data(video)
    transcript_data = _get_transcript_data(transcript)
    keyframes_data = _get_keyframes_data(keyframes)
    analysis_data = analysis.output_format if analysis else None
    
    # Render diagrams for PDF
    diagrams_data = None
    if analysis:
        diagram_gen = DiagramGenerator()
        diagrams_data = {}
        
        # Render sequence diagram
        if analysis.sequence_diagram:
            try:
                seq_png = diagram_gen.render_mermaid_to_image_sync(analysis.sequence_diagram, "png")
                if seq_png:
                    diagrams_data['sequence_diagram_image'] = seq_png
                    logger.info("Rendered sequence diagram for PDF")
            except Exception as e:
                logger.warning(f"Failed to render sequence diagram for PDF: {e}")
        
        # Render user flow diagram
        if analysis.user_flow_diagram:
            try:
                flow_png = diagram_gen.render_mermaid_to_image_sync(analysis.user_flow_diagram, "png")
                if flow_png:
                    diagrams_data['user_flow_diagram_image'] = flow_png
                    logger.info("Rendered user flow diagram for PDF")
            except Exception as e:
                logger.warning(f"Failed to render user flow diagram for PDF: {e}")
    
    try:
        # Get template type from video record
        template_type = video.analysis_type if hasattr(video, 'analysis_type') else None
        if template_type == "auto":
            # Use appropriate default based on media type
            template_type = "reverse_engineering" if video.media_type == "video" else "notes"
        
        # Generate PDF with diagrams and template styling
        pdf_content = generate_video_report(
            video_data=video_data,
            transcript_data=transcript_data,
            keyframes_data=keyframes_data,
            analysis_data=analysis_data,
            diagrams_data=diagrams_data,
            template_type=template_type
        )
        
        # Create filename
        safe_filename = "".join(c for c in video.filename if c.isalnum() or c in "._- ").rstrip()
        pdf_filename = f"{safe_filename}_report.pdf"
        
        logger.info(f"PDF report generated for video {video_id} (template: {template_type}): {len(pdf_content)} bytes")
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{pdf_filename}"'
            }
        )
        
    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/{video_id}/export/zip")
async def export_video_zip(video_id: int, db: Session = Depends(get_db)):
    """
    Export video analysis as a ZIP containing:
    - All keyframe images renamed as {video_title}_{number}.jpg
    - A descriptions.txt file with image list and descriptions
    - The PDF report
    
    File structure:
    - {video_name}_export/
      - images/
        - {video_name}_001.jpg
        - {video_name}_002.jpg
        - ...
      - descriptions.txt
      - report.pdf
    """
    # Fetch video
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Video analysis not completed. Current status: {video.status}"
        )
    
    # Fetch related data
    transcript = db.query(Transcript).filter(Transcript.video_id == video_id).first()
    keyframes = db.query(Keyframe).filter(Keyframe.video_id == video_id).order_by(Keyframe.timestamp).all()
    analysis = db.query(Analysis).filter(Analysis.video_id == video_id).first()
    
    # Create safe video name for files
    safe_name = "".join(c for c in os.path.splitext(video.filename)[0] if c.isalnum() or c in "._- ").rstrip()
    safe_name = safe_name.replace(" ", "_")
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    
    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Download and add each keyframe image
            for idx, kf in enumerate(keyframes, start=1):
                image_filename = f"{safe_name}_{idx:03d}.jpg"
                image_path_in_zip = f"images/{image_filename}"
                
                # Try to download image from MinIO/S3
                if kf.s3_url:
                    try:
                        # Translate public URL to internal Docker network URL
                        # Public URL (for browser): http://localhost:9000/...
                        # Internal URL (for server): http://minio:9000/...
                        public_endpoint = os.getenv('MINIO_PUBLIC_ENDPOINT', 'http://localhost:9000')
                        internal_endpoint = os.getenv('MINIO_ENDPOINT', 'http://minio:9000')
                        internal_url = kf.s3_url.replace(public_endpoint, internal_endpoint)
                        
                        response = requests.get(internal_url, timeout=10)
                        if response.status_code == 200:
                            zip_file.writestr(image_path_in_zip, response.content)
                            logger.info(f"Added keyframe {idx} to ZIP: {image_filename}")
                        else:
                            logger.warning(f"Failed to download keyframe {idx} from {internal_url}: HTTP {response.status_code}")
                    except Exception as e:
                        logger.warning(f"Failed to download keyframe {idx}: {e}")
            
            # Generate descriptions.txt using the new DescriptionParser
            keyframes_for_parser = [
                {
                    "timestamp": kf.timestamp,
                    "frame_number": kf.frame_number,
                    "s3_url": kf.s3_url,
                    "visual_description": kf.visual_description
                } for kf in keyframes
            ]
            
            descriptions_content = DescriptionParser.format_descriptions_file(
                video_filename=video.filename,
                video_duration=video.duration_seconds,
                video_context=video.context,
                keyframes=keyframes_for_parser,
                transcript_text=transcript.full_text if transcript else None,
                analysis_data=analysis.output_format if analysis else None
            )
            
            zip_file.writestr("descriptions.txt", descriptions_content)
            
            # Add transcript.txt as separate file
            if transcript and transcript.full_text:
                transcript_content = f"""# Trascrizione Audio
# Video: {video.filename}
# Generato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 60}

{transcript.full_text}
"""
                zip_file.writestr("transcript.txt", transcript_content.encode('utf-8'))
                logger.info("Added transcript.txt to ZIP")
            
            # Add analysis.json for programmatic access
            if analysis and analysis.output_format:
                analysis_json = {
                    "video_id": video.id,
                    "filename": video.filename,
                    "duration_seconds": video.duration_seconds,
                    "analysis": analysis.output_format,
                    "generated_at": datetime.now().isoformat()
                }
                zip_file.writestr(
                    "analysis.json", 
                    json.dumps(analysis_json, indent=2, ensure_ascii=False).encode('utf-8')
                )
                logger.info("Added analysis.json to ZIP")
            
            # Get template type for styling
            template_type = video.analysis_type if hasattr(video, 'analysis_type') else None
            if template_type == "auto":
                template_type = "reverse_engineering" if video.media_type == "video" else "notes"
            
            # Generate and add PDF with template styling
            try:
                video_data = _get_video_data(video)
                transcript_data = _get_transcript_data(transcript)
                keyframes_data = _get_keyframes_data(keyframes)
                
                pdf_content = generate_video_report(
                    video_data=video_data,
                    transcript_data=transcript_data,
                    keyframes_data=keyframes_data,
                    analysis_data=analysis.output_format if analysis else None,
                    template_type=template_type
                )
                
                zip_file.writestr("report.pdf", pdf_content)
                logger.info(f"Added PDF report to ZIP (template: {template_type})")
                
            except Exception as e:
                logger.warning(f"Failed to generate PDF for ZIP: {e}")
            
            # Add diagrams if available
            diagram_gen = DiagramGenerator()
            
            if analysis:
                # Sequence Diagram
                if analysis.sequence_diagram:
                    zip_file.writestr(
                        "diagrams/sequence_diagram.mmd", 
                        analysis.sequence_diagram.encode('utf-8')
                    )
                    logger.info("Added sequence diagram .mmd to ZIP")
                    
                    # Render to PNG
                    try:
                        png_data = diagram_gen.render_mermaid_to_image_sync(analysis.sequence_diagram, "png")
                        if png_data:
                            zip_file.writestr("diagrams/sequence_diagram.png", png_data)
                            logger.info("Added sequence diagram .png to ZIP")
                    except Exception as render_err:
                        logger.warning(f"Failed to render sequence diagram PNG: {render_err}")
                
                # User Flow Diagram
                if analysis.user_flow_diagram:
                    zip_file.writestr(
                        "diagrams/user_flow_diagram.mmd",
                        analysis.user_flow_diagram.encode('utf-8')
                    )
                    logger.info("Added user flow diagram .mmd to ZIP")
                    
                    # Render to PNG
                    try:
                        png_data = diagram_gen.render_mermaid_to_image_sync(analysis.user_flow_diagram, "png")
                        if png_data:
                            zip_file.writestr("diagrams/user_flow_diagram.png", png_data)
                            logger.info("Added user flow diagram .png to ZIP")
                    except Exception as render_err:
                        logger.warning(f"Failed to render user flow diagram PNG: {render_err}")
                
                # Wireframes
                if analysis.wireframes:
                    wireframes_content = []
                    wireframes_content.append("# WIREFRAMES ASCII")
                    wireframes_content.append("# Rappresentazioni semplificate delle schermate")
                    wireframes_content.append("=" * 60)
                    wireframes_content.append("")
                    
                    for idx, wf in enumerate(analysis.wireframes, 1):
                        ts = wf.get('timestamp', 0)
                        mins = int(ts // 60)
                        secs = int(ts % 60)
                        wireframe_ascii = wf.get('wireframe', '')
                        
                        wireframes_content.append(f"WIREFRAME #{idx} - Timestamp: {mins}:{secs:02d}")
                        wireframes_content.append("-" * 60)
                        wireframes_content.append(wireframe_ascii)
                        wireframes_content.append("")
                        wireframes_content.append("")
                    
                    zip_file.writestr(
                        "diagrams/wireframes.txt",
                        "\n".join(wireframes_content).encode('utf-8')
                    )
                    logger.info(f"Added {len(analysis.wireframes)} wireframes to ZIP")
                
                # Create a diagrams README
                diagrams_readme = """# Diagrammi Generati

Questa cartella contiene i diagrammi generati automaticamente dall'analisi del video.

## File inclusi:

### sequence_diagram.mmd / sequence_diagram.png
Diagramma di sequenza che mostra l'interazione tra utente e applicazione.
- Il file `.mmd` contiene il codice Mermaid sorgente
- Il file `.png` è l'immagine renderizzata pronta all'uso

### user_flow_diagram.mmd / user_flow_diagram.png
Diagramma di flusso utente che mostra i percorsi principali nell'applicazione.

### wireframes.txt
Wireframe ASCII delle schermate principali - rappresentazioni semplificate della UI.

## Come usare i file .mmd:

1. **Mermaid Live Editor**: https://mermaid.live
2. **VS Code**: Installa l'estensione "Markdown Preview Mermaid Support"
3. **GitHub**: I file .mmd vengono renderizzati automaticamente nei README

"""
                zip_file.writestr("diagrams/README.md", diagrams_readme.encode('utf-8'))
            
            # Add template-specific export files
            _add_template_specific_files(zip_file, template_type, analysis, video)
            
            # Add root README.md based on template type
            root_readme = _generate_readme_for_template(
                video=video,
                template_type=template_type,
                keyframes_count=len(keyframes),
                analysis=analysis
            )
            zip_file.writestr("README.md", root_readme.encode('utf-8'))
            logger.info(f"Added README.md to ZIP (template: {template_type})")
        
    except Exception as zip_err:
        logger.error(f"ZIP creation failed: {zip_err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ZIP creation failed: {str(zip_err)}")
    
    # Prepare response
    zip_buffer.seek(0)
    zip_filename = f"{safe_name}_export.zip"
    
    logger.info(f"ZIP export generated for video {video_id}: {len(keyframes)} images")
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"'
        }
    )


@router.get("/{video_id}/export/html")
async def export_video_html(video_id: int, db: Session = Depends(get_db)):
    """
    Export video analysis as an interactive HTML report.
    
    Features:
    - Single-file HTML with embedded images (base64)
    - Tab navigation between sections
    - Mermaid diagrams rendered in browser
    - Lightbox for keyframe images
    - Dark/Light mode toggle
    - Text search functionality
    - Fully responsive design
    """
    # Fetch video
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Video analysis not completed. Current status: {video.status}"
        )
    
    # Fetch related data
    transcript = db.query(Transcript).filter(Transcript.video_id == video_id).first()
    keyframes = db.query(Keyframe).filter(Keyframe.video_id == video_id).order_by(Keyframe.timestamp).all()
    analysis = db.query(Analysis).filter(Analysis.video_id == video_id).first()
    
    # Prepare data
    video_data = _get_video_data(video)
    transcript_data = {
        "full_text": transcript.full_text if transcript else None,
        "segments": transcript.segments if transcript else None,
        "language": transcript.language if transcript else None,
    } if transcript else None
    keyframes_data = _get_keyframes_data(keyframes)
    
    # Prepare diagrams data
    diagrams_data = None
    if analysis:
        diagrams_data = {
            "sequence_diagram": analysis.sequence_diagram,
            "user_flow_diagram": analysis.user_flow_diagram
        }
    
    try:
        # Generate HTML
        html_content = generate_html_report(
            video_data=video_data,
            transcript_data=transcript_data,
            keyframes_data=keyframes_data,
            analysis_data=analysis.output_format if analysis else None,
            diagrams_data=diagrams_data
        )
        
        # Create filename
        safe_filename = "".join(c for c in video.filename if c.isalnum() or c in "._- ").rstrip()
        html_filename = f"{safe_filename}_report.html"
        
        logger.info(f"HTML report generated for video {video_id}: {len(html_content)} characters")
        
        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Content-Disposition": f'attachment; filename="{html_filename}"'
            }
        )
        
    except Exception as e:
        logger.error(f"HTML generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"HTML generation failed: {str(e)}")


@router.get("/{video_id}/export/markdown")
async def export_video_markdown(video_id: int, db: Session = Depends(get_db)):
    """
    Export video analysis as a Markdown document.
    
    Ideal for:
    - Importing into Notion, Obsidian, Confluence
    - Version control with Git
    - Converting to other formats
    """
    # Fetch video
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Video analysis not completed. Current status: {video.status}"
        )
    
    # Fetch related data
    transcript = db.query(Transcript).filter(Transcript.video_id == video_id).first()
    keyframes = db.query(Keyframe).filter(Keyframe.video_id == video_id).order_by(Keyframe.timestamp).all()
    analysis = db.query(Analysis).filter(Analysis.video_id == video_id).first()
    
    # Build Markdown content
    duration = video.duration_seconds or 0
    duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
    
    md_lines = [
        f"# {video.filename}",
        "",
        "> Report di Analisi Video Automatizzata",
        "",
        "## Informazioni Video",
        "",
        f"| Proprietà | Valore |",
        f"|-----------|--------|",
        f"| **Durata** | {duration_str} |",
        f"| **Keyframes** | {len(keyframes)} |",
        f"| **Data Generazione** | {datetime.now().strftime('%d/%m/%Y %H:%M')} |",
        f"| **ID Video** | {video.id} |",
        "",
    ]
    
    # Summary
    if analysis and analysis.output_format:
        analysis_data = analysis.output_format
        
        md_lines.extend([
            "## 📋 Riepilogo Esecutivo",
            "",
            analysis_data.get('summary', 'Nessun riepilogo disponibile.'),
            "",
        ])
        
        if analysis_data.get('app_type'):
            md_lines.append(f"**Tipo Applicazione:** {analysis_data['app_type'].upper()}")
            md_lines.append("")
        
        if analysis_data.get('technology_hints'):
            md_lines.append(f"**Tecnologie Rilevate:** {', '.join(analysis_data['technology_hints'])}")
            md_lines.append("")
        
        # Modules
        if analysis_data.get('modules'):
            md_lines.extend([
                "## 📦 Moduli e Funzionalità",
                "",
            ])
            for mod in analysis_data['modules']:
                mod_name = mod.get('name', 'Modulo')
                mod_desc = mod.get('description', '')
                features = mod.get('key_features', [])
                
                md_lines.append(f"### {mod_name}")
                md_lines.append("")
                if mod_desc:
                    md_lines.append(mod_desc)
                    md_lines.append("")
                if features:
                    md_lines.append("**Features:**")
                    for f in features:
                        md_lines.append(f"- {f}")
                    md_lines.append("")
        
        # User flows
        if analysis_data.get('user_flows'):
            md_lines.extend([
                "## 🔄 Flussi Utente",
                "",
            ])
            for flow in analysis_data['user_flows']:
                flow_name = flow.get('name', 'Flusso')
                steps = flow.get('steps', [])
                
                md_lines.append(f"### {flow_name}")
                md_lines.append("")
                for step in steps:
                    step_num = step.get('step', '')
                    action = step.get('action', '')
                    timestamp = step.get('timestamp', '')
                    outcome = step.get('outcome', '')
                    
                    step_line = f"{step_num}. {action}"
                    if timestamp:
                        step_line += f" `[{timestamp}]`"
                    if outcome:
                        step_line += f" → {outcome}"
                    md_lines.append(step_line)
                md_lines.append("")
        
        # Issues
        if analysis_data.get('issues_and_observations'):
            md_lines.extend([
                "## ⚠️ Osservazioni e Issue",
                "",
            ])
            for issue in analysis_data['issues_and_observations']:
                issue_type = issue.get('type', 'Osservazione')
                desc = issue.get('description', '')
                severity = issue.get('severity', 'medium').upper()
                
                md_lines.append(f"### [{severity}] {issue_type}")
                md_lines.append("")
                md_lines.append(desc)
                md_lines.append("")
        
        # Recommendations
        if analysis_data.get('recommendations'):
            md_lines.extend([
                "## 💡 Raccomandazioni",
                "",
            ])
            for i, rec in enumerate(analysis_data['recommendations'], 1):
                if isinstance(rec, str):
                    md_lines.append(f"{i}. {rec}")
                elif isinstance(rec, dict):
                    md_lines.append(f"{i}. {rec.get('description', str(rec))}")
            md_lines.append("")
    
    # Transcript
    if transcript and transcript.full_text:
        md_lines.extend([
            "## 📝 Trascrizione Audio",
            "",
            "```",
            transcript.full_text,
            "```",
            "",
        ])
    
    # Keyframes
    if keyframes:
        md_lines.extend([
            f"## 🖼️ Keyframes ({len(keyframes)} estratti)",
            "",
        ])
        for idx, kf in enumerate(keyframes, 1):
            timestamp = kf.timestamp
            mins = int(timestamp // 60)
            secs = int(timestamp % 60)
            
            # Parse description
            desc_text = "Descrizione non disponibile"
            if kf.visual_description:
                try:
                    raw = kf.visual_description.strip()
                    if raw.startswith("```json"):
                        raw = raw[7:]
                    if raw.endswith("```"):
                        raw = raw[:-3]
                    desc_data = json.loads(raw.strip())
                    desc_text = desc_data.get('summary', desc_data.get('visual_description', ''))[:200]
                except:
                    desc_text = kf.visual_description[:200] if kf.visual_description else ""
            
            md_lines.append(f"### Frame {idx} - `{mins}:{secs:02d}`")
            md_lines.append("")
            if kf.s3_url:
                md_lines.append(f"![Frame {idx}]({kf.s3_url})")
                md_lines.append("")
            md_lines.append(desc_text)
            md_lines.append("")
    
    # Diagrams
    if analysis and (analysis.sequence_diagram or analysis.user_flow_diagram):
        md_lines.extend([
            "## 📊 Diagrammi",
            "",
        ])
        
        if analysis.sequence_diagram:
            md_lines.extend([
                "### Diagramma di Sequenza",
                "",
                "```mermaid",
                analysis.sequence_diagram,
                "```",
                "",
            ])
        
        if analysis.user_flow_diagram:
            md_lines.extend([
                "### Diagramma Flusso Utente",
                "",
                "```mermaid",
                analysis.user_flow_diagram,
                "```",
                "",
            ])
    
    # Footer
    md_lines.extend([
        "---",
        "",
        f"*Generato da Video Analyzer - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
    ])
    
    # Join and return
    markdown_content = "\n".join(md_lines)
    
    # Create filename
    safe_filename = "".join(c for c in video.filename if c.isalnum() or c in "._- ").rstrip()
    md_filename = f"{safe_filename}_report.md"
    
    logger.info(f"Markdown report generated for video {video_id}: {len(markdown_content)} characters")
    
    return Response(
        content=markdown_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{md_filename}"'
        }
    )

