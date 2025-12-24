"""
Export Templates Configuration.
Defines template configurations for different content types:
- Reverse Engineering (app demos, technical videos)
- Meeting Notes (structured meetings with action items)
- Debrief (post-event analysis)
- Brainstorming (creative sessions)
- Notes (general notes/summaries)
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class TemplateType(str, Enum):
    """Enum for template types."""
    AUTO = "auto"
    REVERSE_ENGINEERING = "reverse_engineering"
    MEETING = "meeting"
    DEBRIEF = "debrief"
    BRAINSTORMING = "brainstorming"
    NOTES = "notes"


@dataclass
class TemplateConfig:
    """Configuration for an export template."""
    name: str
    description: str
    icon: str
    color_primary: str
    color_secondary: str
    pdf_sections: List[str]
    export_files: List[str]
    readme_template: str
    suitable_for: List[str]  # video, audio, or both


# Template configurations
EXPORT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "reverse_engineering": {
        "name": "Reverse Engineering",
        "description": "Analisi tecnica di applicazioni software da video demo",
        "icon": "code",
        "color_primary": "#6366f1",  # Indigo
        "color_secondary": "#818cf8",
        "pdf_sections": [
            "cover",
            "toc",
            "summary",
            "architecture_overview",
            "modules",
            "data_model",
            "api_specification",
            "user_flows",
            "technology_stack",
            "issues_and_observations",
            "recommendations",
            "reconstruction_guide",
            "diagrams",
            "keyframes",
            "transcript"
        ],
        "export_files": [
            "report.pdf",
            "analysis.json",
            "descriptions.txt",
            "transcript.txt",
            "data_model.md",
            "api_spec.md",
            "tech_stack.md",
            "README.md"
        ],
        "export_folders": ["diagrams", "media/images", "docs", "data"],
        "readme_template": "reverse_engineering",
        "suitable_for": ["video"],
        "pdf_subtitle": "Report di Reverse Engineering",
        "toc_items": [
            ("1. Riepilogo Esecutivo", "Panoramica dell'applicazione analizzata"),
            ("2. Architettura", "Struttura e organizzazione del sistema"),
            ("3. Moduli e Funzionalità", "Componenti principali identificati"),
            ("4. Modello Dati", "Entità e relazioni inferite"),
            ("5. Specifiche API", "Endpoint e operazioni rilevate"),
            ("6. Flussi Utente", "Percorsi e interazioni nell'applicazione"),
            ("7. Stack Tecnologico", "Tecnologie e framework identificati"),
            ("8. Issue e Osservazioni", "Problemi e aree di miglioramento"),
            ("9. Raccomandazioni", "Suggerimenti per l'implementazione"),
            ("10. Guida alla Ricostruzione", "Passi per replicare l'applicazione"),
            ("11. Diagrammi", "Sequence e flow diagram"),
            ("12. Keyframe Estratti", "Screenshot con analisi visiva"),
        ]
    },
    
    "meeting": {
        "name": "Meeting Notes",
        "description": "Note strutturate di riunioni con action items e decisioni",
        "icon": "users",
        "color_primary": "#10b981",  # Green/Emerald
        "color_secondary": "#34d399",
        "pdf_sections": [
            "cover",
            "toc",
            "summary",
            "meeting_info",
            "participants",
            "agenda_topics",
            "action_items",
            "decisions",
            "topics_timeline",
            "open_issues",
            "next_steps",
            "key_quotes",
            "transcript"
        ],
        "export_files": [
            "report.pdf",
            "analysis.json",
            "action_items.md",
            "decisions.md",
            "meeting_minutes.md",
            "transcript.txt",
            "README.md"
        ],
        "export_folders": [],
        "readme_template": "meeting",
        "suitable_for": ["audio", "video"],
        "pdf_subtitle": "Verbale di Riunione",
        "toc_items": [
            ("1. Riepilogo", "Sintesi della riunione"),
            ("2. Informazioni Meeting", "Data, durata, partecipanti"),
            ("3. Partecipanti", "Chi ha partecipato e ruoli"),
            ("4. Argomenti Discussi", "Agenda e punti trattati"),
            ("5. Action Items", "Task assegnati con responsabili"),
            ("6. Decisioni", "Decisioni prese durante il meeting"),
            ("7. Timeline Argomenti", "Cronologia della discussione"),
            ("8. Questioni Aperte", "Punti da risolvere"),
            ("9. Prossimi Passi", "Follow-up e azioni future"),
            ("10. Citazioni Chiave", "Affermazioni importanti"),
            ("11. Trascrizione", "Testo completo della registrazione"),
        ]
    },
    
    "debrief": {
        "name": "Debrief",
        "description": "Analisi post-evento con lessons learned e miglioramenti",
        "icon": "clipboard-check",
        "color_primary": "#f59e0b",  # Amber
        "color_secondary": "#fbbf24",
        "pdf_sections": [
            "cover",
            "toc",
            "executive_summary",
            "event_overview",
            "key_findings",
            "what_worked",
            "what_didnt_work",
            "lessons_learned",
            "improvements",
            "action_items",
            "recommendations",
            "timeline",
            "transcript"
        ],
        "export_files": [
            "report.pdf",
            "analysis.json",
            "lessons_learned.md",
            "recommendations.md",
            "improvements.md",
            "transcript.txt",
            "README.md"
        ],
        "export_folders": [],
        "readme_template": "debrief",
        "suitable_for": ["audio", "video"],
        "pdf_subtitle": "Report di Debrief",
        "toc_items": [
            ("1. Executive Summary", "Sintesi dell'analisi"),
            ("2. Panoramica Evento", "Contesto e obiettivi"),
            ("3. Risultati Chiave", "Principali scoperte"),
            ("4. Cosa ha Funzionato", "Successi e punti di forza"),
            ("5. Cosa Migliorare", "Aree critiche"),
            ("6. Lessons Learned", "Insegnamenti per il futuro"),
            ("7. Proposte di Miglioramento", "Azioni correttive"),
            ("8. Action Items", "Task da completare"),
            ("9. Raccomandazioni", "Suggerimenti strategici"),
            ("10. Timeline", "Cronologia della discussione"),
            ("11. Trascrizione", "Testo completo"),
        ]
    },
    
    "brainstorming": {
        "name": "Brainstorming",
        "description": "Sessione creativa con raccolta e categorizzazione idee",
        "icon": "lightbulb",
        "color_primary": "#8b5cf6",  # Purple/Violet
        "color_secondary": "#a78bfa",
        "pdf_sections": [
            "cover",
            "toc",
            "session_overview",
            "participants",
            "ideas_collected",
            "ideas_by_category",
            "top_ideas",
            "feasibility_analysis",
            "idea_connections",
            "next_steps",
            "parking_lot",
            "transcript"
        ],
        "export_files": [
            "report.pdf",
            "analysis.json",
            "ideas.md",
            "ideas_by_category.md",
            "ideas_matrix.csv",
            "transcript.txt",
            "README.md"
        ],
        "export_folders": [],
        "readme_template": "brainstorming",
        "suitable_for": ["audio", "video"],
        "pdf_subtitle": "Report Sessione di Brainstorming",
        "toc_items": [
            ("1. Panoramica Sessione", "Obiettivi e contesto"),
            ("2. Partecipanti", "Chi ha contribuito"),
            ("3. Idee Raccolte", "Tutte le idee emerse"),
            ("4. Idee per Categoria", "Organizzazione tematica"),
            ("5. Top Idee", "Le proposte più promettenti"),
            ("6. Analisi Fattibilità", "Valutazione realizzabilità"),
            ("7. Connessioni tra Idee", "Pattern e sinergie"),
            ("8. Prossimi Passi", "Come procedere"),
            ("9. Parking Lot", "Idee da approfondire"),
            ("10. Trascrizione", "Testo completo della sessione"),
        ]
    },
    
    "notes": {
        "name": "Note",
        "description": "Appunti semplificati con punti chiave e riassunto",
        "icon": "file-text",
        "color_primary": "#64748b",  # Slate
        "color_secondary": "#94a3b8",
        "pdf_sections": [
            "cover",
            "toc",
            "summary",
            "key_points",
            "topics",
            "important_mentions",
            "quotes",
            "references",
            "transcript"
        ],
        "export_files": [
            "report.pdf",
            "notes.md",
            "key_points.md",
            "transcript.txt",
            "README.md"
        ],
        "export_folders": [],
        "readme_template": "notes",
        "suitable_for": ["audio", "video"],
        "pdf_subtitle": "Note e Appunti",
        "toc_items": [
            ("1. Riassunto", "Sintesi del contenuto"),
            ("2. Punti Chiave", "Informazioni principali"),
            ("3. Argomenti", "Temi trattati"),
            ("4. Menzioni Importanti", "Riferimenti rilevanti"),
            ("5. Citazioni", "Frasi significative"),
            ("6. Riferimenti", "Link e risorse"),
            ("7. Trascrizione", "Testo completo"),
        ]
    }
}


def get_template(template_type: str) -> Dict[str, Any]:
    """
    Get template configuration by type.
    
    Args:
        template_type: One of the TemplateType values
        
    Returns:
        Template configuration dictionary
        
    Raises:
        ValueError: If template_type is not valid
    """
    if template_type == "auto":
        raise ValueError("Cannot get template for 'auto' - must infer type first")
    
    if template_type not in EXPORT_TEMPLATES:
        raise ValueError(f"Unknown template type: {template_type}. Valid types: {list(EXPORT_TEMPLATES.keys())}")
    
    return EXPORT_TEMPLATES[template_type]


def get_template_for_media(media_type: str, template_type: str = None) -> Dict[str, Any]:
    """
    Get appropriate template for media type.
    
    Args:
        media_type: 'video' or 'audio'
        template_type: Optional specific template type
        
    Returns:
        Template configuration
    """
    if template_type and template_type != "auto":
        template = get_template(template_type)
        if media_type not in template["suitable_for"]:
            # Fallback to default for media type
            if media_type == "video":
                return get_template("reverse_engineering")
            else:
                return get_template("notes")
        return template
    
    # Default templates by media type
    if media_type == "video":
        return get_template("reverse_engineering")
    else:
        return get_template("notes")


def get_all_template_types() -> List[Dict[str, str]]:
    """
    Get list of all available template types for UI.
    
    Returns:
        List of dicts with id, name, description, icon
    """
    return [
        {
            "id": "auto",
            "name": "Auto-detect",
            "description": "L'AI determinerà automaticamente il tipo più appropriato",
            "icon": "sparkles"
        }
    ] + [
        {
            "id": key,
            "name": config["name"],
            "description": config["description"],
            "icon": config["icon"]
        }
        for key, config in EXPORT_TEMPLATES.items()
    ]


def get_suitable_templates_for_media(media_type: str) -> List[Dict[str, str]]:
    """
    Get templates suitable for a specific media type.
    
    Args:
        media_type: 'video' or 'audio'
        
    Returns:
        List of suitable template configurations
    """
    result = [
        {
            "id": "auto",
            "name": "Auto-detect",
            "description": "L'AI determinerà automaticamente il tipo più appropriato",
            "icon": "sparkles"
        }
    ]
    
    for key, config in EXPORT_TEMPLATES.items():
        if media_type in config["suitable_for"]:
            result.append({
                "id": key,
                "name": config["name"],
                "description": config["description"],
                "icon": config["icon"]
            })
    
    return result


# Content type inference keywords (used by AI to help determine type)
CONTENT_TYPE_HINTS = {
    "reverse_engineering": [
        "applicazione", "app", "software", "interfaccia", "UI", "UX",
        "schermata", "bottone", "menu", "form", "database", "API",
        "frontend", "backend", "click", "navigazione", "demo"
    ],
    "meeting": [
        "riunione", "meeting", "call", "agenda", "punto", "discussione",
        "partecipanti", "colleghi", "team", "progetto", "deadline",
        "task", "assegnare", "responsabile", "follow-up"
    ],
    "debrief": [
        "debrief", "retrospettiva", "post-mortem", "analisi",
        "cosa ha funzionato", "cosa migliorare", "lessons learned",
        "insegnamenti", "errori", "successi", "evento", "progetto concluso"
    ],
    "brainstorming": [
        "brainstorming", "idee", "proposta", "creatività", "innovazione",
        "pensare", "ipotesi", "soluzione", "alternativa", "opzione",
        "cosa ne pensate", "potremmo", "e se", "immaginiamo"
    ],
    "notes": [
        "nota", "appunto", "memo", "promemoria", "registrazione",
        "pensiero", "riflessione", "considerazione"
    ]
}


if __name__ == "__main__":
    # Test template loading
    print("Available templates:")
    for t in get_all_template_types():
        print(f"  - {t['id']}: {t['name']}")
    
    print("\nTemplates for video:")
    for t in get_suitable_templates_for_media("video"):
        print(f"  - {t['id']}: {t['name']}")
    
    print("\nTemplates for audio:")
    for t in get_suitable_templates_for_media("audio"):
        print(f"  - {t['id']}: {t['name']}")
