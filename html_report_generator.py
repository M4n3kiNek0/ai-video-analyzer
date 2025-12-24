"""
HTML Report Generator for Media Analyzer.
Creates interactive single-file HTML reports with embedded images and diagrams.
Features: Tabs navigation, lightbox, Mermaid diagrams, dark mode, search, responsive.
Supports both video (with keyframes) and audio-only analysis.
"""

import base64
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from report_base import BaseReportGenerator

# Configure logging
logger = logging.getLogger(__name__)


class HTMLReportGenerator(BaseReportGenerator):
    """
    Generates interactive HTML reports from video analysis data.
    All assets are embedded for single-file portability.
    Inherits common utilities from BaseReportGenerator.
    """
    
    def __init__(self):
        """Initialize HTML generator."""
        super().__init__()
    
    def generate_report(
        self,
        video_data: Dict[str, Any],
        transcript_data: Optional[Dict[str, Any]],
        keyframes_data: List[Dict[str, Any]],
        analysis_data: Optional[Dict[str, Any]],
        diagrams_data: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate an interactive HTML report.
        
        Args:
            video_data: Media metadata (supports both video and audio)
            transcript_data: Transcription data
            keyframes_data: Keyframes with descriptions (empty for audio)
            analysis_data: Analysis results
            diagrams_data: Mermaid diagram strings
            output_path: Optional path to save HTML file
            
        Returns:
            HTML content as string
        """
        media_type = video_data.get('media_type', 'video')
        logger.info(f"Generating HTML report for {media_type}: {video_data.get('filename', 'unknown')}")
        
        # Build HTML document
        html = self._build_html_document(
            video_data=video_data,
            transcript_data=transcript_data,
            keyframes_data=keyframes_data,
            analysis_data=analysis_data,
            diagrams_data=diagrams_data
        )
        
        # Optionally save to file
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"HTML saved to: {output_path}")
        
        logger.info(f"HTML report generated: {len(html)} characters")
        return html
    
    def _build_html_document(
        self,
        video_data: Dict[str, Any],
        transcript_data: Optional[Dict[str, Any]],
        keyframes_data: List[Dict[str, Any]],
        analysis_data: Optional[Dict[str, Any]],
        diagrams_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build complete HTML document."""
        
        # Detect media type
        media_type = video_data.get('media_type', 'video')
        is_audio = media_type == 'audio'
        
        title = video_data.get('filename', 'Media Analysis Report')
        if '.' in title:
            title = title.rsplit('.', 1)[0]
        
        duration = video_data.get('duration', 0)
        duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "N/A"
        
        # Prepare sections content
        summary_html = self._build_summary_section(analysis_data, is_audio)
        transcript_html = self._build_transcript_section(transcript_data)
        
        # Audio-specific sections
        if is_audio:
            speakers_html = self._build_speakers_section(analysis_data)
            topics_html = self._build_topics_section(analysis_data)
            action_items_html = self._build_action_items_section(analysis_data)
            decisions_html = self._build_decisions_section(analysis_data)
            ideas_html = self._build_ideas_section(analysis_data)
        else:
            flows_html = self._build_flows_section(analysis_data)
            modules_html = self._build_modules_section(analysis_data)
            keyframes_html = self._build_keyframes_section(keyframes_data)
        
        issues_html = self._build_issues_section(analysis_data)
        recommendations_html = self._build_recommendations_section(analysis_data)
        diagrams_html = self._build_diagrams_section(diagrams_data)
        
        # Build tabs based on media type
        if is_audio:
            tabs_html = '''
            <button class="tab active" data-tab="summary">📋 Riepilogo</button>
            <button class="tab" data-tab="speakers">👥 Partecipanti</button>
            <button class="tab" data-tab="topics">📌 Argomenti</button>
            <button class="tab" data-tab="actions">✅ Action Items</button>
            <button class="tab" data-tab="decisions">🎯 Decisioni</button>
            <button class="tab" data-tab="transcript">📝 Trascrizione</button>
            <button class="tab" data-tab="diagrams">📊 Diagrammi</button>
            '''
            
            content_html = f'''
            <section id="summary" class="tab-content active">
                {summary_html}
            </section>
            
            <section id="speakers" class="tab-content">
                {speakers_html}
            </section>
            
            <section id="topics" class="tab-content">
                {topics_html}
            </section>
            
            <section id="actions" class="tab-content">
                {action_items_html}
                {decisions_html}
                {ideas_html}
            </section>
            
            <section id="decisions" class="tab-content">
                {issues_html}
                {recommendations_html}
            </section>
            
            <section id="transcript" class="tab-content">
                {transcript_html}
            </section>
            
            <section id="diagrams" class="tab-content">
                {diagrams_html}
            </section>
            '''
            
            meta_html = f'''
                <span><strong>Durata:</strong> {duration_str}</span>
                <span><strong>Tipo:</strong> AUDIO</span>
                <span><strong>Generato:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
            '''
            subtitle = "Report di Analisi Audio Automatizzata"
        else:
            tabs_html = '''
            <button class="tab active" data-tab="summary">📋 Riepilogo</button>
            <button class="tab" data-tab="transcript">📝 Trascrizione</button>
            <button class="tab" data-tab="flows">🔄 Flussi</button>
            <button class="tab" data-tab="modules">📦 Moduli</button>
            <button class="tab" data-tab="issues">⚠️ Issue</button>
            <button class="tab" data-tab="keyframes">🖼️ Keyframes</button>
            <button class="tab" data-tab="diagrams">📊 Diagrammi</button>
            '''
            
            content_html = f'''
            <section id="summary" class="tab-content active">
                {summary_html}
            </section>
            
            <section id="transcript" class="tab-content">
                {transcript_html}
            </section>
            
            <section id="flows" class="tab-content">
                {flows_html}
            </section>
            
            <section id="modules" class="tab-content">
                {modules_html}
            </section>
            
            <section id="issues" class="tab-content">
                {issues_html}
                {recommendations_html}
            </section>
            
            <section id="keyframes" class="tab-content">
                {keyframes_html}
            </section>
            
            <section id="diagrams" class="tab-content">
                {diagrams_html}
            </section>
            '''
            
            meta_html = f'''
                <span><strong>Durata:</strong> {duration_str}</span>
                <span><strong>Keyframes:</strong> {len(keyframes_data)}</span>
                <span><strong>Generato:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
            '''
            subtitle = "Report di Analisi Video Automatizzata"
        
        # Build complete HTML
        html = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(title)} - {"Audio" if is_audio else "Video"} Analysis Report</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="header-content">
                <h1>{self._escape_html(title)}</h1>
                <p class="subtitle">{subtitle}</p>
                <div class="meta-info">
                    {meta_html}
                </div>
            </div>
            <div class="header-controls">
                <button id="themeToggle" class="btn-icon" title="Cambia tema">
                    <span class="icon-sun">☀️</span>
                    <span class="icon-moon" style="display:none">🌙</span>
                </button>
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Cerca nel report...">
                </div>
            </div>
        </header>
        
        <!-- Navigation Tabs -->
        <nav class="tabs">
            {tabs_html}
        </nav>
        
        <!-- Content Sections -->
        <main class="content">
            {content_html}
        </main>
        
        <!-- Lightbox for images -->
        <div id="lightbox" class="lightbox">
            <span class="lightbox-close">&times;</span>
            <img class="lightbox-content" id="lightbox-img">
            <div id="lightbox-caption"></div>
        </div>
        
        <!-- Footer -->
        <footer class="footer">
            <p>Generato da Media Analyzer • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>
    
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>'''
        
        return html
    
    def _get_css_styles(self) -> str:
        """Return CSS styles for the HTML report.
        Tries to load from external file, falls back to embedded styles.
        """
        # Try to load from external file
        css_path = os.path.join(os.path.dirname(__file__), 'static', 'report_styles.css')
        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (FileNotFoundError, IOError):
            logger.warning(f"Could not load external CSS from {css_path}, using embedded styles")
        
        # Fallback to embedded styles
        return '''
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --bg-tertiary: #f1f5f9;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --accent: #6366f1;
    --accent-light: #e0e7ff;
    --border: #e2e8f0;
    --shadow: 0 1px 3px rgba(0,0,0,0.1);
    --radius: 8px;
}
[data-theme="dark"] {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --accent: #818cf8;
    --accent-light: #312e81;
    --border: #334155;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg-primary); color: var(--text-primary); line-height: 1.6; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
.header { display: flex; justify-content: space-between; padding: 30px; background: linear-gradient(135deg, var(--accent), #8b5cf6); color: white; border-radius: var(--radius); margin-bottom: 20px; flex-wrap: wrap; gap: 20px; }
.header h1 { font-size: 2rem; }
.tabs { display: flex; gap: 5px; background: var(--bg-secondary); padding: 10px; border-radius: var(--radius); margin-bottom: 20px; }
.tab { padding: 10px 20px; border: none; background: transparent; color: var(--text-secondary); cursor: pointer; border-radius: var(--radius); }
.tab.active { background: var(--accent); color: white; }
.content { background: var(--bg-secondary); padding: 30px; border-radius: var(--radius); min-height: 400px; }
.tab-content { display: none; }
.tab-content.active { display: block; }
.section-title { font-size: 1.5rem; color: var(--accent); margin-bottom: 20px; border-bottom: 2px solid var(--border); padding-bottom: 10px; }
.card { background: var(--bg-primary); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 15px; }
.keyframes-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }
.keyframe-card { background: var(--bg-primary); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.keyframe-image { width: 100%; height: 200px; object-fit: cover; cursor: pointer; }
.keyframe-info { padding: 15px; }
.lightbox { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); justify-content: center; align-items: center; }
.lightbox.active { display: flex; }
.footer { text-align: center; padding: 20px; color: var(--text-secondary); }
'''
    
    def _get_javascript(self) -> str:
        """Return JavaScript for interactivity.
        Tries to load from external file, falls back to embedded script.
        """
        # Try to load from external file
        js_path = os.path.join(os.path.dirname(__file__), 'static', 'report_scripts.js')
        try:
            with open(js_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (FileNotFoundError, IOError):
            logger.warning(f"Could not load external JS from {js_path}, using embedded script")
        
        # Fallback to embedded script
        return '''
mermaid.initialize({ startOnLoad: true, theme: 'default', securityLevel: 'loose' });
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.getAttribute('data-tab')).classList.add('active');
    });
});
const themeToggle = document.getElementById('themeToggle');
if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
    });
}
const lightbox = document.getElementById('lightbox');
document.querySelectorAll('.keyframe-image').forEach(img => {
    img.addEventListener('click', () => {
        if (lightbox) { lightbox.classList.add('active'); document.getElementById('lightbox-img').src = img.src; }
    });
});
if (document.querySelector('.lightbox-close')) {
    document.querySelector('.lightbox-close').addEventListener('click', () => lightbox.classList.remove('active'));
}
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && lightbox) lightbox.classList.remove('active'); });
'''
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters. Alias for _escape_text from base class."""
        return self._escape_text(text)
    
    def _download_and_encode_image(self, url: str) -> Optional[str]:
        """Download image and return base64 encoded data URL."""
        if not url:
            return None
        
        # Check if we already have a cached data URL
        cache_key = f"data_url_{url}"
        if cache_key in self.image_cache:
            cached = self.image_cache[cache_key]
            if isinstance(cached, str):
                return cached
        
        # Use base class method to download
        img_data = self._download_image(url)
        if img_data:
            try:
                img_data.seek(0)
                content = img_data.read()
                base64_data = base64.b64encode(content).decode('utf-8')
                data_url = f"data:image/jpeg;base64,{base64_data}"
                self.image_cache[cache_key] = data_url
                return data_url
            except Exception as e:
                logger.warning(f"Failed to encode image from {url}: {e}")
        
        return None
    
    def _build_summary_section(self, analysis_data: Optional[Dict[str, Any]], is_audio: bool = False) -> str:
        """Build summary section HTML."""
        if not analysis_data:
            return '<p>Nessun riepilogo disponibile.</p>'
        
        summary = analysis_data.get('summary', 'Nessun riepilogo disponibile.')
        
        html = f'''
        <h2 class="section-title">📋 Riepilogo Esecutivo</h2>
        <div class="card">
            <p>{self._escape_html(summary)}</p>
        </div>
        '''
        
        if is_audio:
            # Audio-specific metadata
            audio_type = analysis_data.get('audio_type', '')
            tags = analysis_data.get('tags', [])
            metadata = analysis_data.get('metadata', {})
            
            html += '<div class="card">'
            if audio_type:
                html += f'<p><strong>Tipo Audio:</strong> {self._escape_html(audio_type.upper())}</p>'
            if metadata.get('speakers_count'):
                html += f'<p><strong>Partecipanti:</strong> {metadata["speakers_count"]}</p>'
            if metadata.get('tone'):
                html += f'<p><strong>Tono:</strong> {self._escape_html(metadata["tone"])}</p>'
            if tags:
                html += f'<p><strong>Tags:</strong> {self._escape_html(", ".join(tags[:10]))}</p>'
            html += '</div>'
        else:
            # Video metadata
            app_type = analysis_data.get('app_type', '')
            tech_hints = analysis_data.get('technology_hints', [])
            
            if app_type or tech_hints:
                html += '<div class="card">'
                if app_type:
                    html += f'<p><strong>Tipo Applicazione:</strong> {self._escape_html(app_type.upper())}</p>'
                if tech_hints:
                    html += f'<p><strong>Tecnologie Rilevate:</strong> {self._escape_html(", ".join(tech_hints))}</p>'
                html += '</div>'
        
        return html
    
    def _build_speakers_section(self, analysis_data: Optional[Dict[str, Any]]) -> str:
        """Build speakers section HTML for audio analysis."""
        if not analysis_data or not analysis_data.get('speakers'):
            return '<p>Nessun partecipante identificato.</p>'
        
        speakers = analysis_data['speakers']
        html = '<h2 class="section-title">👥 Partecipanti</h2>'
        
        for speaker in speakers:
            name = speaker.get('inferred_name', speaker.get('id', 'Speaker'))
            role = speaker.get('role', '')
            percentage = speaker.get('speaking_percentage', 0)
            characteristics = speaker.get('characteristics', '')
            contributions = speaker.get('key_contributions', [])
            
            html += f'''
            <div class="card">
                <h3>{self._escape_html(name)}</h3>
                {f'<p class="badge badge-low">{self._escape_html(role)}</p>' if role else ''}
                {f'<p><strong>Tempo di parola:</strong> {percentage}%</p>' if percentage else ''}
                {f'<p>{self._escape_html(characteristics)}</p>' if characteristics else ''}
            '''
            
            if contributions:
                html += '<p><strong>Contributi chiave:</strong></p><ul>'
                for contrib in contributions[:5]:
                    html += f'<li>{self._escape_html(contrib)}</li>'
                html += '</ul>'
            
            html += '</div>'
        
        return html
    
    def _build_topics_section(self, analysis_data: Optional[Dict[str, Any]]) -> str:
        """Build topics section HTML for audio analysis."""
        if not analysis_data or not analysis_data.get('topics'):
            return '<p>Nessun argomento identificato.</p>'
        
        topics = analysis_data['topics']
        html = '<h2 class="section-title">📌 Argomenti Discussi</h2>'
        html += '<div class="timeline">'
        
        for topic in topics:
            name = topic.get('name', topic.get('topic', 'Argomento'))
            start = topic.get('start_time', 0)
            end = topic.get('end_time', 0)
            summary = topic.get('summary', '')
            key_points = topic.get('key_points', [])
            
            time_str = f"{int(start//60)}:{int(start%60):02d} - {int(end//60)}:{int(end%60):02d}"
            
            html += f'''
            <div class="timeline-item">
                <strong>{self._escape_html(name)}</strong>
                <span class="badge badge-low">{time_str}</span>
                {f'<p>{self._escape_html(summary)}</p>' if summary else ''}
            '''
            
            if key_points:
                html += '<ul>'
                for point in key_points[:5]:
                    html += f'<li>{self._escape_html(point)}</li>'
                html += '</ul>'
            
            html += '</div>'
        
        html += '</div>'
        return html
    
    def _build_action_items_section(self, analysis_data: Optional[Dict[str, Any]]) -> str:
        """Build action items section HTML for audio analysis."""
        if not analysis_data or not analysis_data.get('action_items'):
            return '<p>Nessun action item identificato.</p>'
        
        items = analysis_data['action_items']
        html = '<h2 class="section-title">✅ Action Items</h2>'
        
        for idx, item in enumerate(items, 1):
            item_text = item.get('item', item.get('description', ''))
            assignee = item.get('assignee', '')
            deadline = item.get('deadline', '')
            priority = item.get('priority', 'medium')
            timestamp = item.get('timestamp', '')
            
            priority_class = 'badge-high' if priority == 'high' else ('badge-low' if priority == 'low' else 'badge-medium')
            
            html += f'''
            <div class="card">
                <p>
                    <strong>{idx}.</strong>
                    <span class="badge {priority_class}">{self._escape_html(priority.upper())}</span>
                    {self._escape_html(item_text)}
                </p>
                {f'<p><em>Assegnato a: {self._escape_html(assignee)}</em></p>' if assignee else ''}
                {f'<p><em>Scadenza: {self._escape_html(deadline)}</em></p>' if deadline else ''}
                {f'<span class="badge badge-low">{self._escape_html(timestamp)}</span>' if timestamp else ''}
            </div>
            '''
        
        return html
    
    def _build_decisions_section(self, analysis_data: Optional[Dict[str, Any]]) -> str:
        """Build decisions section HTML for audio analysis."""
        if not analysis_data or not analysis_data.get('decisions'):
            return ''
        
        decisions = analysis_data['decisions']
        html = '<h2 class="section-title">🎯 Decisioni Chiave</h2>'
        
        for idx, decision in enumerate(decisions, 1):
            decision_text = decision.get('decision', '')
            made_by = decision.get('made_by', '')
            timestamp = decision.get('timestamp', '')
            rationale = decision.get('rationale', '')
            
            html += f'''
            <div class="card">
                <p><strong>{idx}.</strong> {self._escape_html(decision_text)}</p>
                {f'<p><em>Deciso da: {self._escape_html(made_by)}</em></p>' if made_by else ''}
                {f'<p><em>Motivazione: {self._escape_html(rationale)}</em></p>' if rationale else ''}
                {f'<span class="badge badge-low">{self._escape_html(timestamp)}</span>' if timestamp else ''}
            </div>
            '''
        
        return html
    
    def _build_ideas_section(self, analysis_data: Optional[Dict[str, Any]]) -> str:
        """Build ideas section HTML for audio analysis."""
        if not analysis_data or not analysis_data.get('ideas_and_proposals'):
            return ''
        
        ideas = analysis_data['ideas_and_proposals']
        html = '<h2 class="section-title">💡 Idee e Proposte</h2>'
        
        for idea in ideas:
            idea_text = idea.get('idea', '')
            proposed_by = idea.get('proposed_by', '')
            reception = idea.get('reception', '')
            timestamp = idea.get('timestamp', '')
            
            html += f'''
            <div class="card">
                <p>{self._escape_html(idea_text)}</p>
                {f'<p><em>Proposto da: {self._escape_html(proposed_by)}</em></p>' if proposed_by else ''}
                {f'<span class="badge badge-medium">{self._escape_html(reception.upper())}</span>' if reception else ''}
                {f'<span class="badge badge-low">{self._escape_html(timestamp)}</span>' if timestamp else ''}
            </div>
            '''
        
        return html
    
    def _build_transcript_section(self, transcript_data: Optional[Dict[str, Any]]) -> str:
        """Build transcript section HTML."""
        if not transcript_data:
            return '<p>Nessuna trascrizione disponibile.</p>'
        
        full_text = transcript_data.get('full_text', '')
        topics = transcript_data.get('topics', [])
        tone = transcript_data.get('tone', '')
        
        html = '<h2 class="section-title">📝 Trascrizione Audio</h2>'
        
        # Topics
        if topics:
            html += '<h3 class="subsection-title">Argomenti Identificati</h3>'
            html += '<div class="timeline">'
            for topic in topics[:10]:
                topic_name = topic.get('topic', 'Argomento')
                start = topic.get('start_time', 0)
                end = topic.get('end_time', 0)
                desc = topic.get('description', '')
                
                time_str = f"{int(start//60)}:{int(start%60):02d} - {int(end//60)}:{int(end%60):02d}"
                html += f'''
                <div class="timeline-item">
                    <strong>{self._escape_html(topic_name)}</strong>
                    <span class="badge badge-low">{time_str}</span>
                    <p>{self._escape_html(desc)}</p>
                </div>
                '''
            html += '</div>'
        
        # Tone
        if tone:
            html += f'<div class="card"><strong>Tono:</strong> {self._escape_html(tone)}</div>'
        
        # Full transcript
        if full_text:
            html += '<h3 class="subsection-title">Trascrizione Completa</h3>'
            html += f'<div class="transcript-box">{self._escape_html(full_text)}</div>'
        
        return html
    
    def _build_flows_section(self, analysis_data: Optional[Dict[str, Any]]) -> str:
        """Build user flows section HTML."""
        if not analysis_data or not analysis_data.get('user_flows'):
            return '<p>Nessun flusso utente identificato.</p>'
        
        flows = analysis_data['user_flows']
        html = '<h2 class="section-title">🔄 Flussi Utente</h2>'
        
        for flow in flows:
            flow_name = flow.get('name', 'Flusso')
            steps = flow.get('steps', [])
            
            html += f'<h3 class="subsection-title">{self._escape_html(flow_name)}</h3>'
            html += '<div class="timeline">'
            
            for step in steps:
                step_num = step.get('step', '')
                action = step.get('action', '')
                timestamp = step.get('timestamp', '')
                outcome = step.get('outcome', '')
                
                html += f'''
                <div class="timeline-item">
                    <strong>Step {step_num}:</strong> {self._escape_html(action)}
                    {f'<span class="badge badge-low">{timestamp}</span>' if timestamp else ''}
                    {f'<p>→ {self._escape_html(outcome)}</p>' if outcome else ''}
                </div>
                '''
            
            html += '</div>'
        
        return html
    
    def _build_modules_section(self, analysis_data: Optional[Dict[str, Any]]) -> str:
        """Build modules section HTML."""
        if not analysis_data or not analysis_data.get('modules'):
            return '<p>Nessun modulo identificato.</p>'
        
        modules = analysis_data['modules']
        html = '<h2 class="section-title">📦 Moduli e Funzionalità</h2>'
        
        for module in modules:
            mod_name = module.get('name', 'Modulo')
            description = module.get('description', '')
            features = module.get('key_features', [])
            
            html += f'''
            <div class="card">
                <div class="card-header">{self._escape_html(mod_name)}</div>
                {f'<p>{self._escape_html(description)}</p>' if description else ''}
                {f'<p><strong>Features:</strong> {self._escape_html(", ".join(features))}</p>' if features else ''}
            </div>
            '''
        
        return html
    
    def _build_issues_section(self, analysis_data: Optional[Dict[str, Any]]) -> str:
        """Build issues section HTML."""
        if not analysis_data or not analysis_data.get('issues_and_observations'):
            return '<p>Nessuna issue identificata.</p>'
        
        issues = analysis_data['issues_and_observations']
        html = '<h2 class="section-title">⚠️ Osservazioni e Issue</h2>'
        
        for issue in issues:
            issue_type = issue.get('type', 'Osservazione')
            description = issue.get('description', '')
            severity = issue.get('severity', 'medium').lower()
            
            badge_class = f'badge-{severity}'
            
            html += f'''
            <div class="card">
                <div class="card-header">
                    <span class="badge {badge_class}">{severity.upper()}</span>
                    {self._escape_html(issue_type)}
                </div>
                <p>{self._escape_html(description)}</p>
            </div>
            '''
        
        return html
    
    def _build_recommendations_section(self, analysis_data: Optional[Dict[str, Any]]) -> str:
        """Build recommendations section HTML."""
        if not analysis_data or not analysis_data.get('recommendations'):
            return ''
        
        recommendations = analysis_data['recommendations']
        html = '<h2 class="section-title">💡 Raccomandazioni</h2>'
        
        for i, rec in enumerate(recommendations, 1):
            if isinstance(rec, str):
                rec_text = rec
            elif isinstance(rec, dict):
                rec_text = rec.get('description', str(rec))
            else:
                rec_text = str(rec)
            
            html += f'''
            <div class="card">
                <div class="card-header">{i}. Raccomandazione</div>
                <p>{self._escape_html(rec_text)}</p>
            </div>
            '''
        
        return html
    
    def _build_keyframes_section(self, keyframes_data: List[Dict[str, Any]]) -> str:
        """Build keyframes gallery section HTML."""
        if not keyframes_data:
            return '<p>Nessun keyframe estratto.</p>'
        
        html = f'''
        <h2 class="section-title">🖼️ Keyframe Estratti ({len(keyframes_data)} frame)</h2>
        <div class="keyframes-grid">
        '''
        
        for idx, kf in enumerate(keyframes_data, start=1):
            timestamp = kf.get('timestamp', 0)
            mins = int(timestamp // 60)
            secs = int(timestamp % 60)
            time_str = f"{mins}:{secs:02d}"
            
            # Parse description
            desc_data = self._parse_description(kf.get('description', ''))
            summary = desc_data.get('summary', desc_data.get('visual_description', 'Descrizione non disponibile'))
            screen_type = desc_data.get('screen_type', '')
            
            # Get image
            s3_url = kf.get('s3_url', '')
            img_src = self._download_and_encode_image(s3_url) if s3_url else ''
            
            if img_src:
                html += f'''
                <div class="keyframe-card">
                    <img class="keyframe-image" src="{img_src}" alt="Frame {idx} - {time_str}: {self._escape_html(summary[:100])}">
                    <div class="keyframe-info">
                        <span class="keyframe-timestamp">⏱️ {time_str}</span>
                        {f'<span class="badge badge-low">{self._escape_html(screen_type)}</span>' if screen_type else ''}
                        <p class="keyframe-description">{self._escape_html(summary[:200])}</p>
                    </div>
                </div>
                '''
            else:
                html += f'''
                <div class="keyframe-card">
                    <div class="keyframe-image" style="display:flex;align-items:center;justify-content:center;color:var(--text-secondary);">
                        🖼️ Immagine non disponibile
                    </div>
                    <div class="keyframe-info">
                        <span class="keyframe-timestamp">⏱️ {time_str}</span>
                        <p class="keyframe-description">{self._escape_html(summary[:200])}</p>
                    </div>
                </div>
                '''
        
        html += '</div>'
        return html
    
    def _build_diagrams_section(self, diagrams_data: Optional[Dict[str, Any]]) -> str:
        """Build diagrams section with Mermaid rendering."""
        if not diagrams_data:
            return '<p>Nessun diagramma disponibile.</p>'
        
        html = '<h2 class="section-title">📊 Diagrammi</h2>'
        
        # Sequence diagram
        seq_diagram = diagrams_data.get('sequence_diagram', '')
        if seq_diagram:
            html += '''
            <h3 class="subsection-title">Diagramma di Sequenza</h3>
            <div class="diagram-container">
                <div class="mermaid">
            '''
            html += seq_diagram
            html += '''
                </div>
            </div>
            '''
        
        # User flow diagram
        flow_diagram = diagrams_data.get('user_flow_diagram', '')
        if flow_diagram:
            html += '''
            <h3 class="subsection-title">Diagramma Flusso Utente</h3>
            <div class="diagram-container">
                <div class="mermaid">
            '''
            html += flow_diagram
            html += '''
                </div>
            </div>
            '''
        
        return html


def generate_html_report(
    video_data: Dict[str, Any],
    transcript_data: Optional[Dict[str, Any]],
    keyframes_data: List[Dict[str, Any]],
    analysis_data: Optional[Dict[str, Any]],
    diagrams_data: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Convenience function to generate an HTML report.
    
    Args:
        video_data: Video metadata
        transcript_data: Transcription data
        keyframes_data: Keyframes data
        analysis_data: Analysis data
        diagrams_data: Mermaid diagram strings
        output_path: Optional output file path
        
    Returns:
        HTML content as string
    """
    generator = HTMLReportGenerator()
    return generator.generate_report(
        video_data,
        transcript_data,
        keyframes_data,
        analysis_data,
        diagrams_data,
        output_path
    )


if __name__ == "__main__":
    print("HTML Report Generator module loaded successfully.")
    print("Use generate_html_report() to create HTML reports.")

