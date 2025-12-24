"""
Description Parser for Video Analyzer.
Handles parsing of JSON descriptions from keyframes and formatting for export.
"""

import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DescriptionParser:
    """
    Parses and formats keyframe descriptions from JSON to clean text.
    Handles various JSON formats and provides robust fallback.
    """
    
    @staticmethod
    def extract_json_from_text(text: str) -> str:
        """
        Robustly extract JSON object from mixed text.
        Finds the first '{' and the last '}' that form a valid JSON structure.
        """
        if not text:
            return ""
            
        text = text.strip()
        
        # Remove markdown code block wrappers first
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Find all opening and closing braces
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return text[start_idx:end_idx+1]
            
        return text

    @staticmethod
    def parse_description(raw_description: str) -> Dict[str, Any]:
        """
        Parse a keyframe description, handling both JSON and plain text.
        
        Args:
            raw_description: Raw description string (may be JSON or plain text)
            
        Returns:
            Dictionary with parsed fields
        """
        if not raw_description:
            return {"summary": "Nessuna descrizione AI disponibile per questo frame", "parse_error": True}
        
        # Try to extract and clean JSON
        cleaned = DescriptionParser.extract_json_from_text(raw_description)
        
        try:
            data = json.loads(cleaned)
            return DescriptionParser._normalize_parsed_data(data)
        except json.JSONDecodeError:
            # If standard parsing fails, try to repair common issues
            # sometimes LLMs output single quotes instead of double quotes
            try:
                # Very basic repair attempt
                repaired = cleaned.replace("'", '"') 
                data = json.loads(repaired)
                return DescriptionParser._normalize_parsed_data(data)
            except json.JSONDecodeError:
                pass
                
            # Treat as plain text fallback
            return {
                "summary": raw_description.strip()[:1000],  # Increased limit
                "parse_error": True,
                "visual_description": raw_description.strip()[:1000] # Duplicate for robustness
            }
        
    @staticmethod
    def _normalize_parsed_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize parsed JSON data to a consistent structure.
        """
        if not isinstance(data, dict):
            return {
                "summary": str(data)[:1000] if data else "Descrizione non disponibile",
                "screen_type": "",
                "audio_correlation": "",
                "parse_error": True
            }
        
        result = {}
        
        # Summary - Robust fallback chain
        summary = None
        
        # Direct keys
        for key in ["summary", "visual_description", "description", "screen_summary", "screen_description"]:
            if data.get(key):
                summary = data.get(key)
                break
        
        # Nested keys
        if not summary:
            # check screen.narration or screen.summary
            if isinstance(data.get("screen"), dict):
                summary = data["screen"].get("narration") or data["screen"].get("summary")
            
            # check audio_narration
            if not summary:
                audio_nar = data.get("audio_narration")
                if isinstance(audio_nar, str):
                    summary = audio_nar
                elif isinstance(audio_nar, dict):
                    summary = audio_nar.get("context") or audio_nar.get("narration")
                    
            # check previous_frame (as last resort fallback)
            if not summary:
                summary = data.get("previous_frame_summary")
                if not summary and isinstance(data.get("previous_frame"), dict):
                     summary = data["previous_frame"].get("summary")
        
        # Synthesize from title/elements if still missing
        if not summary:
            title = data.get("screen_title") or data.get("title")
            if title:
                summary = f"Schermata: {title}"
                if data.get("elements"):
                    summary += ". Elementi rilevati."
        
        result["summary"] = summary or "Descrizione non disponibile"
        
        # Screen type
        layout = data.get("layout")
        if isinstance(layout, dict):
            layout_type = layout.get("type")
        else:
            layout_type = None
        
        result["screen_type"] = (
            data.get("screen_type") or 
            layout_type or 
            data.get("screen_type_hint") or
            ""
        )
        
        # Audio correlation
        result["audio_correlation"] = (
            data.get("audio_correlation") or 
            data.get("audio_narration") if isinstance(data.get("audio_narration"), str) else ""
        )
        
        # Actions
        action_data = data.get("current_action", {})
        if isinstance(action_data, dict):
            result["action"] = action_data.get("action", "")
            result["action_target"] = action_data.get("target_element", "")
            result["action_step"] = action_data.get("step_in_flow", "")
            result["next_action"] = action_data.get("next_likely_action", "")
        else:
            result["action"] = str(action_data) if action_data else ""
            result["action_target"] = ""
            result["action_step"] = ""
            result["next_action"] = ""

        # Components
        components = data.get("components", [])
        result["components"] = []
        for comp in components[:10]:
            if isinstance(comp, dict):
                name = comp.get("name") or comp.get("type") or comp.get("element", "")
                desc = comp.get("description", "")
                if name:
                    result["components"].append({"name": name, "description": desc})
            elif isinstance(comp, str):
                result["components"].append({"name": comp, "description": ""})
        
        # OCR extracted texts
        ocr_data = data.get("ocr_extracted_texts", {})
        if not isinstance(ocr_data, dict):
            ocr_data = {}
        result["ocr"] = {
            "buttons": ocr_data.get("buttons", [])[:10] if ocr_data else [],
            "headers": ocr_data.get("headers", [])[:5] if ocr_data else [],
            "labels": ocr_data.get("labels", [])[:10] if ocr_data else [],
            "menu_items": ocr_data.get("menu_items", [])[:10] if ocr_data else [],
            "visible_data": ocr_data.get("visible_data", [])[:5] if ocr_data else []
        }
        
        # Layout info
        layout = data.get("layout", {})
        if not isinstance(layout, dict):
            layout = {}
        result["layout"] = {
            "header": layout.get("header", ""),
            "navigation": layout.get("navigation", ""),
            "main_content": layout.get("main_content", ""),
            "sidebar": layout.get("sidebar", ""),
            "footer": layout.get("footer", "")
        }
        
        # UI observations
        result["ui_observations"] = data.get("ui_observations", [])[:5]
        
        # Data elements visible
        result["data_elements"] = data.get("data_elements", [])[:5]
        
        return result
    
    @staticmethod
    def format_timestamp(seconds: int) -> str:
        """Format seconds to MM:SS string."""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"
    
    @staticmethod
    def format_keyframe_description(
        index: int,
        filename: str,
        timestamp: int,
        raw_description: str
    ) -> str:
        """
        Format a single keyframe description for the descriptions.txt file.
        
        Args:
            index: Keyframe index (1-based)
            filename: Image filename
            timestamp: Timestamp in seconds
            raw_description: Raw description from database
            
        Returns:
            Formatted description block
        """
        parsed = DescriptionParser.parse_description(raw_description)
        time_str = DescriptionParser.format_timestamp(timestamp)
        screen_type = parsed.get("screen_type", "")
        
        lines = []
        
        # Header line
        header_parts = [f"[{index:03d}] {filename}", f"Timestamp: {time_str}"]
        if screen_type:
            header_parts.append(f"Tipo: {screen_type}")
        
        lines.append("=" * 80)
        lines.append(" | ".join(header_parts))
        lines.append("=" * 80)
        lines.append("")
        
        # Summary/Description
        summary = parsed.get("summary", "Descrizione non disponibile")
        if (not summary or summary == "Descrizione non disponibile") and not raw_description:
            summary = f"Nessuna descrizione AI disponibile per il frame {index} ({time_str}). Usa transcript o screenshot per contesto."
        lines.append("DESCRIZIONE:")
        lines.append(summary)
        lines.append("")
        if parsed.get("parse_error") and raw_description:
            lines.append("_Nota: descrizione originale non strutturata; è stata usata una versione semplificata._")
            lines.append("")
        
        # Audio correlation
        audio_corr = parsed.get("audio_correlation", "")
        if audio_corr:
            lines.append("CORRELAZIONE AUDIO:")
            lines.append(audio_corr)
            lines.append("")
        
        # User action
        action = parsed.get("action", "")
        action_target = parsed.get("action_target", "")
        action_step = parsed.get("action_step", "")
        
        if action or action_target:
            lines.append("AZIONE UTENTE:")
            action_line = action
            if action_target:
                action_line += f" → {action_target}"
            if action_step:
                action_line += f" ({action_step})"
            lines.append(action_line)
            lines.append("")
        
        # Next likely action
        next_action = parsed.get("next_action", "")
        if next_action:
            lines.append("PROSSIMA AZIONE PROBABILE:")
            lines.append(next_action)
            lines.append("")
        
        # Components
        components = parsed.get("components", [])
        if components:
            lines.append("COMPONENTI UI:")
            for comp in components:
                name = comp.get("name", "")
                desc = comp.get("description", "")
                if desc:
                    lines.append(f"  • {name}: {desc}")
                else:
                    lines.append(f"  • {name}")
            lines.append("")
        
        # OCR texts
        ocr = parsed.get("ocr", {})
        has_ocr = any([
            ocr.get("buttons"),
            ocr.get("headers"),
            ocr.get("labels"),
            ocr.get("menu_items")
        ])
        
        if has_ocr:
            lines.append("TESTI VISIBILI (OCR):")
            
            if ocr.get("headers"):
                lines.append(f"  Titoli: {', '.join(ocr['headers'])}")
            if ocr.get("buttons"):
                buttons_str = ", ".join([f"[{b}]" for b in ocr["buttons"]])
                lines.append(f"  Bottoni: {buttons_str}")
            if ocr.get("menu_items"):
                lines.append(f"  Menu: {', '.join(ocr['menu_items'])}")
            if ocr.get("labels"):
                lines.append(f"  Etichette: {', '.join(ocr['labels'])}")
            if ocr.get("visible_data"):
                lines.append(f"  Dati: {', '.join(ocr['visible_data'])}")
            lines.append("")
        
        # Layout info (if meaningful)
        layout = parsed.get("layout", {})
        if not isinstance(layout, dict):
            layout = {}
        layout_parts = []
        header_val = layout.get("header", "")
        if header_val and isinstance(header_val, str):
            layout_parts.append(f"Header: {header_val[:50]}")
        nav_val = layout.get("navigation", "")
        if nav_val and isinstance(nav_val, str):
            layout_parts.append(f"Nav: {nav_val[:50]}")
        content_val = layout.get("main_content", "")
        if content_val and isinstance(content_val, str):
            layout_parts.append(f"Content: {content_val[:50]}")
        
        if layout_parts:
            lines.append("LAYOUT:")
            for part in layout_parts:
                lines.append(f"  • {part}")
            lines.append("")
        
        # UI observations
        observations = parsed.get("ui_observations", [])
        if observations:
            lines.append("OSSERVAZIONI UI:")
            for obs in observations:
                lines.append(f"  • {obs}")
            lines.append("")
        
        # Footer separator
        lines.append("-" * 80)
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_descriptions_file(
        video_filename: str,
        video_duration: Optional[int],
        video_context: Optional[str],
        keyframes: List[Dict[str, Any]],
        transcript_text: Optional[str] = None,
        analysis_data: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Generate the complete descriptions.txt file content.
        
        Args:
            video_filename: Original video filename
            video_duration: Video duration in seconds
            video_context: User-provided context
            keyframes: List of keyframe dictionaries
            transcript_text: Full transcript text
            analysis_data: Analysis output dictionary
            
        Returns:
            UTF-8 encoded bytes with BOM for Windows compatibility
        """
        lines = []
        
        # File header with BOM will be added at encoding stage
        lines.append("╔" + "═" * 78 + "╗")
        lines.append("║" + f" REPORT ANALISI VIDEO: {video_filename}".ljust(78) + "║")
        lines.append("╚" + "═" * 78 + "╝")
        lines.append("")
        lines.append(f"Data Export: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if video_duration:
            duration_str = DescriptionParser.format_timestamp(video_duration)
            lines.append(f"Durata Video: {duration_str}")
        
        if video_context:
            lines.append("")
            lines.append("Contesto Fornito:")
            # Word wrap context at ~75 chars
            context_wrapped = DescriptionParser._word_wrap(video_context, 75)
            for line in context_wrapped:
                lines.append(f"  {line}")
        
        lines.append("")
        lines.append("")
        
        # Analysis summary section
        if analysis_data:
            lines.append("╔" + "═" * 78 + "╗")
            lines.append("║" + " RIEPILOGO ANALISI AI".ljust(78) + "║")
            lines.append("╚" + "═" * 78 + "╝")
            lines.append("")
            
            app_type = analysis_data.get("app_type", "N/A")
            lines.append(f"Tipo Applicazione: {app_type.upper() if app_type else 'N/A'}")
            lines.append("")
            
            summary = analysis_data.get("summary", "")
            if summary:
                lines.append("Sommario:")
                for line in DescriptionParser._word_wrap(summary, 75):
                    lines.append(f"  {line}")
                lines.append("")
            
            # Technology hints
            tech_hints = analysis_data.get("technology_hints", [])
            if tech_hints:
                lines.append(f"Tecnologie Rilevate: {', '.join(tech_hints)}")
                lines.append("")
            
            # Modules
            modules = analysis_data.get("modules", [])
            if modules:
                lines.append("Moduli Identificati:")
                for mod in modules[:10]:
                    mod_name = mod.get("name", "N/A")
                    mod_desc = mod.get("description", "")[:80]
                    lines.append(f"  • {mod_name}")
                    if mod_desc:
                        lines.append(f"    {mod_desc}")
                lines.append("")
            
            # User flows summary
            flows = analysis_data.get("user_flows", [])
            if flows:
                lines.append("Flussi Utente Identificati:")
                for flow in flows[:5]:
                    flow_name = flow.get("name", "N/A")
                    steps_count = len(flow.get("steps", []))
                    lines.append(f"  • {flow_name} ({steps_count} step)")
                lines.append("")
            
            # Issues
            issues = analysis_data.get("issues_and_observations", [])
            if issues:
                lines.append("Issue e Osservazioni:")
                for issue in issues[:10]:
                    issue_type = issue.get("type", "")
                    severity = issue.get("severity", "").upper()
                    desc = issue.get("description", "")[:100]
                    lines.append(f"  [{severity}] {issue_type}: {desc}")
                lines.append("")
            
            # Recommendations
            recommendations = analysis_data.get("recommendations", [])
            if recommendations:
                lines.append("Raccomandazioni:")
                for i, rec in enumerate(recommendations[:10], 1):
                    lines.append(f"  {i}. {rec}")
                lines.append("")
            
            lines.append("")
        
        # Keyframes section
        lines.append("╔" + "═" * 78 + "╗")
        lines.append("║" + f" ELENCO IMMAGINI ESTRATTE ({len(keyframes)} keyframe)".ljust(78) + "║")
        lines.append("╚" + "═" * 78 + "╝")
        lines.append("")
        
        # Create safe filename base
        safe_name = "".join(
            c for c in video_filename.rsplit(".", 1)[0] 
            if c.isalnum() or c in "._- "
        ).rstrip().replace(" ", "_")
        
        for idx, kf in enumerate(keyframes, start=1):
            image_filename = f"{safe_name}_{idx:03d}.jpg"
            timestamp = kf.get("timestamp", 0)
            raw_desc = kf.get("visual_description", "")
            
            formatted = DescriptionParser.format_keyframe_description(
                index=idx,
                filename=image_filename,
                timestamp=timestamp,
                raw_description=raw_desc
            )
            lines.append(formatted)
        
        # Transcript section
        if transcript_text:
            lines.append("")
            lines.append("╔" + "═" * 78 + "╗")
            lines.append("║" + " TRASCRIZIONE AUDIO COMPLETA".ljust(78) + "║")
            lines.append("╚" + "═" * 78 + "╝")
            lines.append("")
            
            # Word wrap transcript
            for line in DescriptionParser._word_wrap(transcript_text, 78):
                lines.append(line)
            lines.append("")
        
        # Footer
        lines.append("")
        lines.append("═" * 80)
        lines.append("Fine del report")
        lines.append(f"Generato da Video Analyzer - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("═" * 80)
        
        # Join and encode with UTF-8 BOM for Windows compatibility
        content = "\n".join(lines)
        return b'\xef\xbb\xbf' + content.encode('utf-8')
    
    @staticmethod
    def _word_wrap(text: str, max_width: int) -> List[str]:
        """
        Wrap text to specified width, preserving words.
        
        Args:
            text: Text to wrap
            max_width: Maximum line width
            
        Returns:
            List of wrapped lines
        """
        if not text:
            return []
        
        # Replace newlines with spaces, then split into words
        text = text.replace('\n', ' ').replace('\r', '')
        words = text.split()
        
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_len = len(word)
            
            if current_length + word_len + len(current_line) <= max_width:
                current_line.append(word)
                current_length += word_len
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_len
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines


# Utility function for external use
def parse_and_format_description(raw_description: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse and return both structured data and formatted text.
    
    Args:
        raw_description: Raw description string
        
    Returns:
        Tuple of (parsed_dict, formatted_text)
    """
    parsed = DescriptionParser.parse_description(raw_description)
    
    # Create a simple formatted text version
    lines = []
    lines.append(parsed.get("summary", "N/A"))
    
    if parsed.get("audio_correlation"):
        lines.append(f"Audio: {parsed['audio_correlation']}")
    
    if parsed.get("action"):
        action_line = parsed["action"]
        if parsed.get("action_target"):
            action_line += f" → {parsed['action_target']}"
        lines.append(f"Azione: {action_line}")
    
    return parsed, "\n".join(lines)


if __name__ == "__main__":
    # Test the parser
    test_json = '''```json
{
    "summary": "Test screen showing a dashboard",
    "screen_type": "dashboard",
    "audio_correlation": "The audio describes navigation",
    "current_action": {
        "action": "clicking button",
        "target_element": "Save button"
    },
    "components": [
        {"name": "Header", "description": "Top navigation bar"},
        {"name": "Sidebar", "description": "Left menu"}
    ],
    "ocr_extracted_texts": {
        "buttons": ["Save", "Cancel", "Edit"],
        "headers": ["Dashboard", "Settings"]
    }
}
```'''
    
    parsed = DescriptionParser.parse_description(test_json)
    print("Parsed data:")
    print(json.dumps(parsed, indent=2, ensure_ascii=False))
    
    formatted = DescriptionParser.format_keyframe_description(
        index=1,
        filename="test_001.jpg",
        timestamp=65,
        raw_description=test_json
    )
    print("\nFormatted output:")
    print(formatted)
