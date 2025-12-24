"""
PDF Report Generator for Media Analyzer.
Creates structured PDF reports from video and audio analysis results with embedded images.
Features: Cover page, Table of Contents, Page numbers, Professional styling.
Supports both video (with keyframes) and audio-only analysis.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from io import BytesIO
from functools import partial

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas

from report_base import BaseReportGenerator
from export_templates import EXPORT_TEMPLATES, get_template

# Configure logging
logger = logging.getLogger(__name__)

# Default template colors (fallback)
DEFAULT_TEMPLATE_COLOR = "#6366f1"


class NumberedCanvas(canvas.Canvas):
    """Canvas that tracks page numbers for footer."""
    
    def __init__(self, *args, video_title: str = "", **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        self._video_title = video_title
        
    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
        
    def save(self):
        """Add page numbers and footer to each page."""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
        
    def draw_page_footer(self, page_count):
        """Draw footer with page number and video title."""
        page_num = self._pageNumber
        
        # Skip footer on cover page (page 1)
        if page_num == 1:
            return
            
        self.saveState()
        
        # Footer line
        self.setStrokeColor(colors.HexColor('#e5e7eb'))
        self.setLineWidth(0.5)
        self.line(2*cm, 1.5*cm, A4[0] - 2*cm, 1.5*cm)
        
        # Page number on right
        self.setFont('Helvetica', 9)
        self.setFillColor(colors.HexColor('#6b7280'))
        page_text = f"Pagina {page_num - 1} di {page_count - 1}"  # Exclude cover from count
        self.drawRightString(A4[0] - 2*cm, 1.1*cm, page_text)
        
        # Video title on left
        title = self._video_title[:50] + "..." if len(self._video_title) > 50 else self._video_title
        self.drawString(2*cm, 1.1*cm, title)
        
        self.restoreState()


class PDFReportGenerator(BaseReportGenerator):
    """
    Generates PDF reports from video analysis data.
    Features cover page, table of contents, and page footers.
    Inherits common utilities from BaseReportGenerator.
    Supports template-based styling for different content types.
    """

    def __init__(self, template_type: str = None, analyzer = None):
        """
        Initialize PDF generator with custom styles.
        
        Args:
            template_type: Optional template type for styling (reverse_engineering, meeting, etc.)
            analyzer: Optional AIAnalyzer instance for enhanced summary generation
        """
        super().__init__()  # Initialize BaseReportGenerator (image_cache, etc.)
        self.styles = getSampleStyleSheet()
        self.analyzer = analyzer
        
        # Get template configuration for colors
        self.template_type = template_type
        self.template_config = None
        self.primary_color = DEFAULT_TEMPLATE_COLOR
        self.secondary_color = "#818cf8"
        
        if template_type and template_type != "auto":
            try:
                self.template_config = get_template(template_type)
                self.primary_color = self.template_config.get("color_primary", DEFAULT_TEMPLATE_COLOR)
                self.secondary_color = self.template_config.get("color_secondary", "#818cf8")
                logger.info(f"Using template '{template_type}' with color {self.primary_color}")
            except ValueError:
                logger.warning(f"Unknown template type: {template_type}, using default colors")
        
        self._create_custom_styles()
        self.toc_entries = []  # Track sections for TOC
        
    def _create_custom_styles(self):
        """Create custom paragraph styles for the report using template colors."""
        # Use template colors
        accent_color = colors.HexColor(self.primary_color)
        
        # Cover title style
        self.styles.add(ParagraphStyle(
            name='CoverTitle',
            parent=self.styles['Heading1'],
            fontSize=32,
            spaceAfter=20,
            textColor=colors.HexColor('#1a1a2e'),
            alignment=TA_CENTER,
            leading=38
        ))
        
        # Cover subtitle - uses template color
        self.styles.add(ParagraphStyle(
            name='CoverSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=accent_color,
            alignment=TA_CENTER,
            spaceBefore=10,
            spaceAfter=30
        ))
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1a1a2e'),
            alignment=TA_CENTER
        ))
        
        # Section header (for TOC) - uses template color
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=accent_color,
            borderPadding=(0, 0, 5, 0)
        ))
        
        # Subsection header
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#374151')
        ))
        
        # Body text
        self.styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            spaceBefore=6,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))
        
        # Metadata text
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6b7280'),
            spaceAfter=3
        ))
        
        # Quote/transcript style
        self.styles.add(ParagraphStyle(
            name='Transcript',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=13,
            leftIndent=10,
            rightIndent=10,
            spaceBefore=10,
            spaceAfter=10,
            backColor=colors.HexColor('#f3f4f6'),
            borderPadding=10
        ))
        
        # List item style
        self.styles.add(ParagraphStyle(
            name='ListItem',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            leftIndent=15,
            spaceBefore=3,
            spaceAfter=3
        ))
        
        # TOC entry styles
        self.styles.add(ParagraphStyle(
            name='TOCHeading',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceBefore=30,
            spaceAfter=20,
            textColor=colors.HexColor('#1a1a2e'),
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='TOCEntry',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=22,
            leftIndent=0,
            spaceBefore=3,
            spaceAfter=3,
            textColor=colors.HexColor('#374151')
        ))

    def generate_report(
        self,
        video_data: Dict[str, Any],
        transcript_data: Optional[Dict[str, Any]],
        keyframes_data: List[Dict[str, Any]],
        analysis_data: Optional[Dict[str, Any]],
        output_path: Optional[str] = None,
        diagrams_data: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Generate a PDF report from video or audio analysis data.
        
        Args:
            video_data: Media metadata (id, filename, duration, media_type, etc.)
            transcript_data: Transcription with enrichment data
            keyframes_data: List of keyframe information (empty for audio)
            analysis_data: Full analysis results
            output_path: Optional path to save PDF file
            diagrams_data: Optional diagrams (sequence, flow, wireframes)
            
        Returns:
            PDF content as bytes
        """
        # Detect media type
        media_type = video_data.get('media_type', 'video')
        is_audio = media_type == 'audio'
        
        logger.info(f"Generating PDF report for {media_type}: {video_data.get('filename', 'unknown')}")
        
        # Reset TOC entries
        self.toc_entries = []
        
        # Create PDF buffer
        buffer = BytesIO()
        video_title = video_data.get('filename', 'Video Analysis Report')
        
        # Create document with custom canvas for page numbers
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2.5*cm  # Extra space for footer
        )
        
        # Build content
        story = []
        
        # Cover page
        story.extend(self._build_cover_page(video_data, keyframes_data, analysis_data, is_audio))
        story.append(PageBreak())
        
        # Table of Contents placeholder
        story.extend(self._build_toc_placeholder(is_audio))
        story.append(PageBreak())
        
        # Executive summary (Standard)
        if analysis_data:
            story.extend(self._build_summary(
                analysis_data, 
                is_audio,
            ))
            story.append(Spacer(1, 15))

        # Integrated Analysis (New Page as requested)
        if self.analyzer and not is_audio:
            # Generate integrated analysis if not already present or generating on fly
            integrated_text = None
            try:
                # Reuse the enhanced summary generation for this deep dive
                user_context = analysis_data.get('user_context') or analysis_data.get('context')
                integrated_text = self.analyzer.generate_enhanced_executive_summary(
                    existing_summary="", # Force generation of new content focused on synthesis
                    transcript_data=transcript_data,
                    keyframes_data=keyframes_data or [],
                    analysis_data=analysis_data,
                    user_context=user_context
                )
            except Exception as e:
                logger.warning(f"Integrated analysis generation failed: {e}")

            if integrated_text:
                story.append(PageBreak())
                story.extend(self._build_integrated_analysis_section(integrated_text))
        
        # Audio-specific sections
        if is_audio and analysis_data:
            # Speakers
            if analysis_data.get('speakers'):
                story.extend(self._build_speakers_section(analysis_data['speakers']))
            
            # Topics with timeline
            if analysis_data.get('topics'):
                story.extend(self._build_topics_section(analysis_data['topics']))
            
            # Action Items
            if analysis_data.get('action_items'):
                story.extend(self._build_action_items_section(analysis_data['action_items']))
            
            # Decisions
            if analysis_data.get('decisions'):
                story.extend(self._build_decisions_section(analysis_data['decisions']))
            
            # Ideas and Proposals
            if analysis_data.get('ideas_and_proposals'):
                story.extend(self._build_ideas_section(analysis_data['ideas_and_proposals']))
            
            # Key Quotes
            if analysis_data.get('key_quotes'):
                story.extend(self._build_quotes_section(analysis_data['key_quotes']))
        
        # Video-specific sections
        if not is_audio:
            # User flows
            if analysis_data and analysis_data.get('user_flows'):
                story.extend(self._build_flows_section(analysis_data['user_flows']))
            
            # Modules and features
            if analysis_data and analysis_data.get('modules'):
                story.extend(self._build_modules_section(analysis_data['modules']))
        
        # Common sections
        # Issues and observations
        if analysis_data and analysis_data.get('issues_and_observations'):
            story.extend(self._build_issues_section(analysis_data['issues_and_observations']))
        
        # Open issues (audio) / Issues (video)
        if is_audio and analysis_data and analysis_data.get('open_issues'):
            story.extend(self._build_open_issues_section(analysis_data['open_issues']))
        
        # Recommendations
        if analysis_data and analysis_data.get('recommendations'):
            story.extend(self._build_recommendations_section(analysis_data['recommendations']))
        
        # Next steps (audio)
        if is_audio and analysis_data and analysis_data.get('next_steps'):
            story.extend(self._build_next_steps_section(analysis_data['next_steps']))
        
        # Video-specific: Data Model, API, Reconstruction
        if not is_audio:
            if analysis_data and analysis_data.get('data_model'):
                story.extend(self._build_data_model_section(analysis_data['data_model']))
            
            if analysis_data and analysis_data.get('api_specification'):
                story.extend(self._build_api_section(analysis_data['api_specification']))
            
            # Technology stack section removed - focus on context and information extraction instead
            
            if analysis_data and analysis_data.get('reconstruction_guide'):
                story.extend(self._build_reconstruction_guide_section(analysis_data['reconstruction_guide']))
        
        # Diagrams section (if provided)
        if diagrams_data:
            story.extend(self._build_diagrams_section(diagrams_data))
        
        # Keyframes summary (video only)
        if keyframes_data and not is_audio:
            story.extend(self._build_keyframes_section(keyframes_data, transcript_data))
        
        # Trascrizione completa - ALLA FINE del documento
        if transcript_data:
            story.extend(self._build_transcription_section(transcript_data))
        
        # Build PDF with custom canvas
        canvas_maker = partial(NumberedCanvas, video_title=video_title)
        doc.build(story, canvasmaker=canvas_maker)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Optionally save to file
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_content)
            logger.info(f"PDF saved to: {output_path}")
        
        logger.info(f"PDF report generated: {len(pdf_content)} bytes")
        return pdf_content

    def _build_cover_page(
        self, 
        video_data: Dict[str, Any], 
        keyframes_data: List[Dict[str, Any]],
        analysis_data: Optional[Dict[str, Any]],
        is_audio: bool = False
    ) -> List:
        """Build professional cover page."""
        elements = []
        
        # Top spacing
        elements.append(Spacer(1, 3*cm))
        
        # Main title
        title = video_data.get('filename', 'Media Analysis Report')
        # Remove extension for cleaner display
        if '.' in title:
            title = title.rsplit('.', 1)[0]
        elements.append(Paragraph(title, self.styles['CoverTitle']))
        
        # Subtitle
        subtitle = "Report di Analisi Audio Automatizzata" if is_audio else "Report di Analisi Video Automatizzata"
        elements.append(Paragraph(subtitle, self.styles['CoverSubtitle']))
        
        # Decorative line
        line_table = Table([['']], colWidths=[10*cm])
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (0, 0), 2, colors.HexColor('#6366f1')),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 1*cm))
        
        # Cover thumbnail (first keyframe if available)
        if keyframes_data and keyframes_data[0].get('s3_url'):
            img_data = self._download_image(keyframes_data[0]['s3_url'])
            if img_data:
                try:
                    img_width, img_height = self._get_image_size_keeping_aspect_ratio(
                        img_data, max_width=12*cm, max_height=8*cm
                    )
                    cover_img = Image(img_data, width=img_width, height=img_height)
                    
                    # Center the image in a table
                    img_table = Table([[cover_img]], colWidths=[16.5*cm])
                    img_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
                        ('BOX', (0, 0), (0, 0), 1, colors.HexColor('#e5e7eb')),
                        ('TOPPADDING', (0, 0), (0, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (0, 0), 10),
                    ]))
                    elements.append(img_table)
                    elements.append(Spacer(1, 1*cm))
                except Exception as e:
                    logger.warning(f"Failed to add cover image: {e}")
        
        # Metadata box
        duration = video_data.get('duration', 0)
        duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "N/A"
        
        keyframes_count = len(keyframes_data) if keyframes_data else 0
        
        # Get type based on media type
        if is_audio:
            audio_type = analysis_data.get('audio_type', 'N/A') if analysis_data else 'N/A'
            type_label = 'Tipo Audio:'
            type_value = audio_type.upper() if audio_type else 'N/A'
        else:
            app_type = analysis_data.get('app_type', 'N/A') if analysis_data else 'N/A'
            type_label = 'Tipo Applicazione:'
            type_value = app_type.upper() if app_type else 'N/A'
        
        metadata = [
            ['Data Generazione:', datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Durata:', duration_str],
            ['Tipo Media:', 'AUDIO' if is_audio else 'VIDEO'],
            [type_label, type_value],
            ['ID:', str(video_data.get('id', 'N/A'))],
        ]
        
        # Add keyframes count only for video
        if not is_audio:
            metadata.insert(3, ['Keyframes Estratti:', str(keyframes_count)])
        
        meta_table = Table(metadata, colWidths=[6*cm, 10*cm])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1a1a2e')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(meta_table)
        
        # Footer text
        elements.append(Spacer(1, 2*cm))
        elements.append(Paragraph(
            "Generato automaticamente da Video Analyzer",
            ParagraphStyle(
                'CoverFooter',
                parent=self.styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#9ca3af'),
                alignment=TA_CENTER
            )
        ))
        
        return elements

    def _build_toc_placeholder(self, is_audio: bool = False) -> List:
        """Build table of contents section."""
        elements = []
        
        elements.append(Paragraph("Indice", self.styles['TOCHeading']))
        elements.append(Spacer(1, 1*cm))
        
        # Static TOC entries based on media type
        if is_audio:
            toc_items = [
                ("1. Riepilogo Esecutivo", "Sintesi dell'analisi audio"),
                ("2. Partecipanti", "Speaker identificati nella registrazione"),
                ("3. Argomenti Discussi", "Timeline degli argomenti trattati"),
                ("4. Action Items", "Attività e task estratti"),
                ("5. Decisioni", "Decisioni chiave prese"),
                ("6. Idee e Proposte", "Proposte emerse dalla discussione"),
                ("7. Raccomandazioni", "Suggerimenti e prossimi passi"),
                ("8. Trascrizione", "Trascrizione completa dell'audio"),
            ]
        else:
            toc_items = [
                ("1. Riepilogo Esecutivo", "Sintesi dell'analisi video"),
                ("2. Analisi Audio", "Trascrizione e argomenti identificati"),
                ("3. Flussi Utente", "Percorsi e interazioni nell'applicazione"),
                ("4. Moduli e Funzionalità", "Componenti principali identificati"),
                ("5. Osservazioni e Issue", "Problemi e aree di miglioramento"),
                ("6. Raccomandazioni", "Suggerimenti per l'ottimizzazione"),
                ("7. Keyframe Estratti", "Screenshot con analisi visiva"),
            ]
        
        for title, description in toc_items:
            elements.append(Paragraph(
                f"<b>{title}</b><br/><font size='9' color='#6b7280'>{description}</font>",
                self.styles['TOCEntry']
            ))
            
            # Dotted line separator
            elements.append(Spacer(1, 3))
        
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph(
            "<i>Nota: Le sezioni presenti dipendono dai dati disponibili nell'analisi.</i>",
            self.styles['Metadata']
        ))
        
        return elements

    def _build_integrated_analysis_section(self, text: str) -> List:
        """Build integrated analysis section on a new page."""
        elements = []
        
        elements.append(Paragraph("🔍 Analisi Integrata Audio-Video", self.styles['SectionHeader']))
        
        elements.append(Paragraph(
            "Questa sezione fornisce un'elaborazione approfondita basata sulla correlazione tra la narrazione audio e l'analisi visiva delle schermate.",
            self.styles['Metadata']
        ))
        elements.append(Spacer(1, 15))
        
        # Split text into paragraphs
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                # Check if it's a list item
                if para.strip().startswith('- ') or para.strip().startswith('• '):
                    elements.append(Paragraph(para.strip(), self.styles['ListItem']))
                elif para.strip().startswith('###') or para.strip().startswith('**'):
                     # Handle subheaders roughly
                    clean_text = para.replace('#', '').replace('*', '').strip()
                    elements.append(Paragraph(clean_text, self.styles['SubsectionHeader']))
                else:
                    elements.append(Paragraph(para.strip(), self.styles['CustomBodyText']))
                    elements.append(Spacer(1, 8))
                    
        return elements

    def _build_summary(
        self, 
        analysis_data: Dict[str, Any], 
        is_audio: bool = False,
    ) -> List:
        """Build executive summary section."""
        elements = []
        
        elements.append(Paragraph("📋 Riepilogo Esecutivo", self.styles['SectionHeader']))
        
        # Check for analysis errors
        if analysis_data.get('error'):
            elements.append(Paragraph(
                f"⚠️ Errore durante l'analisi: {analysis_data.get('error')}",
                self.styles['CustomBodyText']
            ))
            elements.append(Spacer(1, 15))
            return elements
        
        # Use existing summary
        summary = analysis_data.get('summary') or 'Nessun riepilogo disponibile.'
        
        elements.append(Paragraph(summary, self.styles['CustomBodyText']))
        
        if is_audio:
            # Audio-specific metadata
            audio_type = analysis_data.get('audio_type', '')
            tags = analysis_data.get('tags', [])
            metadata = analysis_data.get('metadata', {})
            
            elements.append(Spacer(1, 10))
            
            if audio_type:
                elements.append(Paragraph(
                    f"<b>Tipo Audio:</b> {audio_type.upper()}",
                    self.styles['CustomBodyText']
                ))
            
            if metadata.get('speakers_count'):
                elements.append(Paragraph(
                    f"<b>Partecipanti:</b> {metadata['speakers_count']}",
                    self.styles['CustomBodyText']
                ))
            
            if metadata.get('tone'):
                elements.append(Paragraph(
                    f"<b>Tono:</b> {metadata['tone']}",
                    self.styles['CustomBodyText']
                ))
            
            if tags:
                elements.append(Paragraph(
                    f"<b>Tags:</b> {', '.join(tags[:10])}",
                    self.styles['CustomBodyText']
                ))
        else:
            # Video-specific metadata
            app_type = analysis_data.get('app_type', 'N/A')
            tech_hints = analysis_data.get('technology_hints', [])
            
            if app_type or tech_hints:
                elements.append(Spacer(1, 10))
                
                if app_type:
                    elements.append(Paragraph(
                        f"<b>Tipo Applicazione:</b> {app_type.upper()}",
                        self.styles['CustomBodyText']
                    ))
                
                if tech_hints:
                    elements.append(Paragraph(
                        f"<b>Tecnologie Rilevate:</b> {', '.join(tech_hints)}",
                        self.styles['CustomBodyText']
                    ))
        
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _build_speakers_section(self, speakers: List[Dict[str, Any]]) -> List:
        """Build speakers section for audio analysis."""
        elements = []
        
        elements.append(Paragraph("👥 Partecipanti", self.styles['SectionHeader']))
        
        for speaker in speakers:
            name = speaker.get('inferred_name', speaker.get('id', 'Speaker'))
            role = speaker.get('role', '')
            percentage = speaker.get('speaking_percentage', 0)
            characteristics = speaker.get('characteristics', '')
            contributions = speaker.get('key_contributions', [])
            
            elements.append(Paragraph(f"<b>{name}</b>", self.styles['SubsectionHeader']))
            
            if role:
                elements.append(Paragraph(f"<i>Ruolo: {role}</i>", self.styles['Metadata']))
            
            if percentage:
                elements.append(Paragraph(f"Tempo di parola: {percentage}%", self.styles['Metadata']))
            
            if characteristics:
                elements.append(Paragraph(characteristics, self.styles['CustomBodyText']))
            
            if contributions:
                elements.append(Paragraph("<b>Contributi chiave:</b>", self.styles['CustomBodyText']))
                for contrib in contributions[:5]:
                    elements.append(Paragraph(f"• {contrib}", self.styles['ListItem']))
        
        elements.append(Spacer(1, 15))
        return elements
    
    def _build_topics_section(self, topics: List[Dict[str, Any]]) -> List:
        """Build topics timeline section for audio analysis."""
        elements = []
        
        elements.append(Paragraph("📌 Argomenti Discussi", self.styles['SectionHeader']))
        
        for topic in topics:
            name = topic.get('name', topic.get('topic', 'Argomento'))
            start = topic.get('start_time', 0)
            end = topic.get('end_time', 0)
            summary = topic.get('summary', '')
            key_points = topic.get('key_points', [])
            
            time_str = f"[{int(start//60)}:{int(start%60):02d} - {int(end//60)}:{int(end%60):02d}]"
            elements.append(Paragraph(f"<b>{name}</b> {time_str}", self.styles['SubsectionHeader']))
            
            if summary:
                elements.append(Paragraph(summary, self.styles['CustomBodyText']))
            
            if key_points:
                for point in key_points[:5]:
                    elements.append(Paragraph(f"• {point}", self.styles['ListItem']))
        
        elements.append(Spacer(1, 15))
        return elements
    
    def _build_action_items_section(self, action_items: List[Dict[str, Any]]) -> List:
        """Build action items section for audio analysis."""
        elements = []
        
        elements.append(Paragraph("✅ Action Items", self.styles['SectionHeader']))
        
        for idx, item in enumerate(action_items, 1):
            item_text = item.get('item', item.get('description', ''))
            assignee = item.get('assignee', '')
            deadline = item.get('deadline', '')
            priority = item.get('priority', 'medium')
            timestamp = item.get('timestamp', '')
            
            priority_label = f"[{priority.upper()}]" if priority else ""
            
            text = f"<b>{idx}. {priority_label}</b> {item_text}"
            if assignee:
                text += f" <i>(Assegnato a: {assignee})</i>"
            if deadline:
                text += f" <i>[Scadenza: {deadline}]</i>"
            if timestamp:
                text += f" <font size='8' color='#6b7280'>[{timestamp}]</font>"
            
            elements.append(Paragraph(text, self.styles['ListItem']))
        
        elements.append(Spacer(1, 15))
        return elements
    
    def _build_decisions_section(self, decisions: List[Dict[str, Any]]) -> List:
        """Build decisions section for audio analysis."""
        elements = []
        
        elements.append(Paragraph("🎯 Decisioni Chiave", self.styles['SectionHeader']))
        
        for idx, decision in enumerate(decisions, 1):
            decision_text = decision.get('decision', '')
            made_by = decision.get('made_by', '')
            timestamp = decision.get('timestamp', '')
            rationale = decision.get('rationale', '')
            
            text = f"<b>{idx}.</b> {decision_text}"
            if made_by:
                text += f" <i>(Deciso da: {made_by})</i>"
            if timestamp:
                text += f" <font size='8' color='#6b7280'>[{timestamp}]</font>"
            
            elements.append(Paragraph(text, self.styles['ListItem']))
            
            if rationale:
                elements.append(Paragraph(f"<i>Motivazione: {rationale}</i>", self.styles['Metadata']))
        
        elements.append(Spacer(1, 15))
        return elements
    
    def _build_ideas_section(self, ideas: List[Dict[str, Any]]) -> List:
        """Build ideas and proposals section for audio analysis."""
        elements = []
        
        elements.append(Paragraph("💡 Idee e Proposte", self.styles['SectionHeader']))
        
        for idea in ideas:
            idea_text = idea.get('idea', '')
            proposed_by = idea.get('proposed_by', '')
            reception = idea.get('reception', '')
            timestamp = idea.get('timestamp', '')
            
            text = f"• {idea_text}"
            if proposed_by:
                text += f" <i>(Proposto da: {proposed_by})</i>"
            if reception:
                text += f" <b>[{reception.upper()}]</b>"
            if timestamp:
                text += f" <font size='8' color='#6b7280'>[{timestamp}]</font>"
            
            elements.append(Paragraph(text, self.styles['ListItem']))
        
        elements.append(Spacer(1, 15))
        return elements
    
    def _build_quotes_section(self, quotes: List[Dict[str, Any]]) -> List:
        """Build key quotes section for audio analysis."""
        elements = []
        
        elements.append(Paragraph("💬 Citazioni Chiave", self.styles['SectionHeader']))
        
        for quote in quotes:
            quote_text = quote.get('quote', '')
            speaker = quote.get('speaker', '')
            timestamp = quote.get('timestamp', '')
            significance = quote.get('significance', '')
            
            elements.append(Paragraph(f'"{quote_text}"', self.styles['Transcript']))
            
            attribution = []
            if speaker:
                attribution.append(f"— {speaker}")
            if timestamp:
                attribution.append(f"[{timestamp}]")
            if attribution:
                elements.append(Paragraph(" ".join(attribution), self.styles['Metadata']))
            
            if significance:
                elements.append(Paragraph(f"<i>{significance}</i>", self.styles['CustomBodyText']))
            
            elements.append(Spacer(1, 8))
        
        elements.append(Spacer(1, 15))
        return elements
    
    def _build_open_issues_section(self, open_issues: List[Dict[str, Any]]) -> List:
        """Build open issues section for audio analysis."""
        elements = []
        
        elements.append(Paragraph("❓ Questioni Aperte", self.styles['SectionHeader']))
        
        for issue in open_issues:
            issue_text = issue.get('issue', '')
            discussed_at = issue.get('discussed_at', '')
            next_steps = issue.get('suggested_next_steps', '')
            
            text = f"• {issue_text}"
            if discussed_at:
                text += f" <font size='8' color='#6b7280'>[{discussed_at}]</font>"
            
            elements.append(Paragraph(text, self.styles['ListItem']))
            
            if next_steps:
                elements.append(Paragraph(f"<i>Prossimi passi: {next_steps}</i>", self.styles['Metadata']))
        
        elements.append(Spacer(1, 15))
        return elements
    
    def _build_next_steps_section(self, next_steps: List[str]) -> List:
        """Build next steps section for audio analysis."""
        elements = []
        
        elements.append(Paragraph("➡️ Prossimi Passi", self.styles['SectionHeader']))
        
        for idx, step in enumerate(next_steps, 1):
            elements.append(Paragraph(f"{idx}. {step}", self.styles['ListItem']))
        
        elements.append(Spacer(1, 15))
        return elements

    def _build_transcription_section(self, transcript_data: Dict[str, Any]) -> List:
        """Build transcription section with semantic summary - NO truncation."""
        elements = []
        
        elements.append(Paragraph("📝 Analisi Audio", self.styles['SectionHeader']))
        
        # Semantic summary (if enriched)
        semantic_summary = transcript_data.get('semantic_summary', '')
        if semantic_summary:
            elements.append(Paragraph("Riassunto Semantico", self.styles['SubsectionHeader']))
            elements.append(Paragraph(semantic_summary, self.styles['CustomBodyText']))
        
        # Topics
        topics = transcript_data.get('topics', [])
        if topics:
            elements.append(Paragraph("Argomenti Identificati", self.styles['SubsectionHeader']))
            
            for topic in topics[:10]:  # Limit to 10 topics
                topic_name = topic.get('topic', 'Argomento')
                start = topic.get('start_time', 0)
                end = topic.get('end_time', 0)
                desc = topic.get('description', '')
                
                time_str = f"[{int(start//60)}:{int(start%60):02d} - {int(end//60)}:{int(end%60):02d}]"
                elements.append(Paragraph(
                    f"• <b>{topic_name}</b> {time_str}<br/>{desc}",
                    self.styles['ListItem']
                ))
        
        # Tone and style
        tone = transcript_data.get('tone', '')
        style = transcript_data.get('speaking_style', '')
        if tone or style:
            elements.append(Spacer(1, 10))
            if tone:
                elements.append(Paragraph(f"<b>Tono:</b> {tone}", self.styles['Metadata']))
            if style:
                elements.append(Paragraph(f"<b>Stile:</b> {style}", self.styles['Metadata']))
        
        # Full transcript - NO TRUNCATION
        full_text = transcript_data.get('full_text', '')
        if full_text:
            elements.append(Paragraph("Trascrizione Completa", self.styles['SubsectionHeader']))
            # Split long text into paragraphs for better rendering
            paragraphs = full_text.split('\n\n')
            if len(paragraphs) == 1:
                # Single block of text, split by sentences for readability
                elements.append(Paragraph(full_text, self.styles['Transcript']))
            else:
                for para in paragraphs:
                    if para.strip():
                        elements.append(Paragraph(para.strip(), self.styles['Transcript']))
        
        elements.append(Spacer(1, 15))
        
        return elements

    def _build_flows_section(self, flows: List[Dict[str, Any]]) -> List:
        """Build user flows section."""
        elements = []
        
        elements.append(Paragraph("🔄 Flussi Utente", self.styles['SectionHeader']))
        
        for flow in flows:
            flow_name = flow.get('name', 'Flusso')
            actors = flow.get('actors', [])
            steps = flow.get('steps', [])
            
            actors_str = f" ({', '.join(actors)})" if actors else ""
            elements.append(Paragraph(f"{flow_name}{actors_str}", self.styles['SubsectionHeader']))
            
            for step in steps:
                step_num = step.get('step', '')
                action = step.get('action', '')
                timestamp = step.get('timestamp', '')
                outcome = step.get('outcome', '')
                
                step_text = f"<b>{step_num}.</b> {action}"
                if timestamp:
                    step_text += f" <i>[{timestamp}]</i>"
                if outcome:
                    step_text += f" → {outcome}"
                
                elements.append(Paragraph(step_text, self.styles['ListItem']))
        
        elements.append(Spacer(1, 15))
        
        return elements

    def _build_modules_section(self, modules: List[Dict[str, Any]]) -> List:
        """Build modules and features section."""
        elements = []
        
        elements.append(Paragraph("📦 Moduli e Funzionalità", self.styles['SectionHeader']))
        
        for module in modules:
            mod_name = module.get('name', 'Modulo')
            description = module.get('description', '')
            features = module.get('key_features', [])
            screens = module.get('screens', [])
            
            elements.append(Paragraph(mod_name, self.styles['SubsectionHeader']))
            
            if description:
                elements.append(Paragraph(description, self.styles['CustomBodyText']))
            
            if features:
                features_text = "<b>Features:</b> " + ", ".join(features)
                elements.append(Paragraph(features_text, self.styles['ListItem']))
            
            if screens:
                screens_text = "<b>Schermate:</b> " + ", ".join(screens)
                elements.append(Paragraph(screens_text, self.styles['ListItem']))
        
        elements.append(Spacer(1, 15))
        
        return elements

    def _build_issues_section(self, issues: List[Dict[str, Any]]) -> List:
        """Build issues and observations section."""
        elements = []
        
        elements.append(Paragraph("⚠️ Osservazioni e Issue", self.styles['SectionHeader']))
        
        for issue in issues:
            issue_type = issue.get('type', 'Osservazione')
            description = issue.get('description', '')
            timestamp = issue.get('timestamp', '')
            severity = issue.get('severity', 'medium').lower()
            
            severity_label = severity.upper()
            time_str = f" [{timestamp}]" if timestamp else ""
            
            elements.append(Paragraph(
                f"<b>[{severity_label}] {issue_type}</b>{time_str}",
                self.styles['ListItem']
            ))
            elements.append(Paragraph(description, self.styles['CustomBodyText']))
        
        elements.append(Spacer(1, 15))
        
        return elements

    def _build_recommendations_section(self, recommendations: List) -> List:
        """Build recommendations section - handles both strings and objects."""
        elements = []
        
        elements.append(Paragraph("💡 Raccomandazioni", self.styles['SectionHeader']))
        
        for i, rec in enumerate(recommendations, 1):
            if isinstance(rec, str):
                elements.append(Paragraph(f"{i}. {rec}", self.styles['ListItem']))
            elif isinstance(rec, dict):
                priority = rec.get('priority', 'medium')
                category = rec.get('category', '')
                desc = rec.get('description', str(rec))
                hint = rec.get('implementation_hint', '')
                
                priority_label = f"[{priority.upper()}]" if priority else ""
                category_label = f"[{category}]" if category else ""
                
                text = f"{i}. <b>{priority_label} {category_label}</b> {desc}"
                if hint:
                    text += f"<br/><i>💡 {hint}</i>"
                elements.append(Paragraph(text, self.styles['ListItem']))
            else:
                elements.append(Paragraph(f"{i}. {str(rec)}", self.styles['ListItem']))
        
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _build_data_model_section(self, data_model: Dict[str, Any]) -> List:
        """Build inferred data model section."""
        elements = []
        
        elements.append(Paragraph("🗃️ Modello Dati Inferito", self.styles['SectionHeader']))
        
        entities = data_model.get('entities', [])
        for entity in entities:
            entity_name = entity.get('name', 'Entity')
            entity_desc = entity.get('description', '')
            
            elements.append(Paragraph(f"<b>{entity_name}</b>", self.styles['SubsectionHeader']))
            if entity_desc:
                elements.append(Paragraph(entity_desc, self.styles['CustomBodyText']))
            
            fields = entity.get('fields', [])
            if fields:
                field_lines = []
                for field in fields[:10]:  # Limit fields
                    fname = field.get('name', '')
                    ftype = field.get('type', '')
                    fdesc = field.get('description', '')
                    field_lines.append(f"• <b>{fname}</b>: {ftype} - {fdesc}")
                elements.append(Paragraph("<br/>".join(field_lines), self.styles['ListItem']))
            
            relationships = entity.get('relationships', [])
            if relationships:
                rel_text = "Relazioni: " + ", ".join([
                    f"{r.get('type', '')} → {r.get('target', '')}" 
                    for r in relationships
                ])
                elements.append(Paragraph(rel_text, self.styles['Metadata']))
        
        elements.append(Spacer(1, 15))
        return elements
    
    def _build_api_section(self, api_spec: Dict[str, Any]) -> List:
        """Build inferred API specification section."""
        elements = []
        
        elements.append(Paragraph("🔌 API Inferite", self.styles['SectionHeader']))
        
        endpoints = api_spec.get('endpoints', [])
        for endpoint in endpoints[:15]:  # Limit endpoints
            method = endpoint.get('method', 'GET')
            path = endpoint.get('path', '/')
            desc = endpoint.get('description', '')
            
            elements.append(Paragraph(
                f"<b>{method}</b> <font face='Courier'>{path}</font>",
                self.styles['ListItem']
            ))
            if desc:
                elements.append(Paragraph(desc, self.styles['CustomBodyText']))
        
        elements.append(Spacer(1, 15))
        return elements
    
    def _build_technology_section(self, tech_stack: Dict[str, Any]) -> List:
        """Build technology stack section."""
        elements = []
        
        elements.append(Paragraph("🛠️ Stack Tecnologico", self.styles['SectionHeader']))
        
        tech_items = []
        if tech_stack.get('frontend_framework'):
            tech_items.append(f"<b>Frontend:</b> {tech_stack['frontend_framework']}")
        if tech_stack.get('ui_library'):
            tech_items.append(f"<b>UI Library:</b> {tech_stack['ui_library']}")
        if tech_stack.get('state_management'):
            tech_items.append(f"<b>State Management:</b> {tech_stack['state_management']}")
        if tech_stack.get('styling'):
            tech_items.append(f"<b>Styling:</b> {tech_stack['styling']}")
        if tech_stack.get('platform'):
            tech_items.append(f"<b>Platform:</b> {tech_stack['platform']}")
        
        for item in tech_items:
            elements.append(Paragraph(item, self.styles['ListItem']))
        
        elements.append(Spacer(1, 15))
        return elements
    
    def _build_reconstruction_guide_section(self, guide: Dict[str, Any]) -> List:
        """Build reconstruction guide section."""
        elements = []
        
        elements.append(Paragraph("📋 Guida alla Ricostruzione", self.styles['SectionHeader']))
        
        if guide.get('estimated_effort'):
            elements.append(Paragraph(
                f"<b>Effort stimato:</b> {guide['estimated_effort']}", 
                self.styles['CustomBodyText']
            ))
        
        if guide.get('key_challenges'):
            challenges = guide['key_challenges']
            elements.append(Paragraph("<b>Sfide principali:</b>", self.styles['CustomBodyText']))
            for challenge in challenges[:5]:
                elements.append(Paragraph(f"• {challenge}", self.styles['ListItem']))
        
        if guide.get('required_skills'):
            skills = ", ".join(guide['required_skills'][:10])
            elements.append(Paragraph(f"<b>Competenze richieste:</b> {skills}", self.styles['CustomBodyText']))
        
        if guide.get('mvp_features'):
            elements.append(Paragraph("<b>Features MVP:</b>", self.styles['CustomBodyText']))
            for feature in guide['mvp_features'][:5]:
                elements.append(Paragraph(f"• {feature}", self.styles['ListItem']))
        
        elements.append(Spacer(1, 15))
        return elements

    def _build_diagrams_section(self, diagrams_data: Dict[str, Any]) -> List:
        """Build diagrams section with rendered images."""
        elements = []
        
        elements.append(Paragraph("📊 Diagrammi", self.styles['SectionHeader']))
        
        # Sequence diagram
        if diagrams_data.get('sequence_diagram_image'):
            elements.append(Paragraph("Diagramma di Sequenza", self.styles['SubsectionHeader']))
            try:
                img_data = BytesIO(diagrams_data['sequence_diagram_image'])
                img_width, img_height = self._get_image_size_keeping_aspect_ratio(
                    img_data, max_width=16*cm, max_height=12*cm
                )
                elements.append(Image(img_data, width=img_width, height=img_height))
                elements.append(Spacer(1, 15))
            except Exception as e:
                logger.warning(f"Failed to add sequence diagram: {e}")
        
        # User flow diagram
        if diagrams_data.get('user_flow_diagram_image'):
            elements.append(Paragraph("Diagramma Flusso Utente", self.styles['SubsectionHeader']))
            try:
                img_data = BytesIO(diagrams_data['user_flow_diagram_image'])
                img_width, img_height = self._get_image_size_keeping_aspect_ratio(
                    img_data, max_width=16*cm, max_height=12*cm
                )
                elements.append(Image(img_data, width=img_width, height=img_height))
                elements.append(Spacer(1, 15))
            except Exception as e:
                logger.warning(f"Failed to add user flow diagram: {e}")
        
        return elements


    def _get_image_size_keeping_aspect_ratio(
        self, 
        img_data: BytesIO, 
        max_width: float, 
        max_height: float
    ) -> Tuple[float, float]:
        """Calculate image dimensions that fit within max bounds while preserving aspect ratio."""
        try:
            img_data.seek(0)
            pil_img = PILImage.open(img_data)
            orig_width, orig_height = pil_img.size
            img_data.seek(0)
            
            if orig_width == 0 or orig_height == 0:
                return max_width, max_height
            
            aspect_ratio = orig_width / orig_height
            new_width = max_width
            new_height = max_width / aspect_ratio
            
            if new_height > max_height:
                new_height = max_height
                new_width = max_height * aspect_ratio
            
            return new_width, new_height
            
        except Exception as e:
            logger.warning(f"Failed to get image dimensions: {e}")
            return max_width, max_height


    def _build_keyframes_section(self, keyframes: List[Dict[str, Any]], transcript_data: Optional[Dict[str, Any]] = None) -> List:
        """Build keyframes section with thumbnail images and detailed descriptions."""
        elements = []
        
        elements.append(Paragraph("🖼️ Keyframe Estratti con Analisi Visiva", self.styles['SectionHeader']))
        
        elements.append(Paragraph(
            f"Sono stati estratti e analizzati <b>{len(keyframes)}</b> keyframe dal video. "
            f"Ogni frame è stato analizzato con GPT-4 Vision per estrarre informazioni dettagliate. "
            f"Di seguito sono riportate le descrizioni, correllate con la trascrizione audio pertinente.",
            self.styles['CustomBodyText']
        ))
        
        elements.append(Spacer(1, 10))
        
        # Helper to find transcript for timestamp
        def get_transcript_for_time(ts, segments, window=5.0):
            if not segments:
                return ""
            
            relevant_texts = []
            for seg in segments:
                start = seg.get('start', 0)
                end = seg.get('end', 0)
                text = seg.get('text', '').strip()
                
                # Check intersection with a window around the timestamp
                # or if the timestamp falls within the segment
                if start <= ts <= end:
                    relevant_texts.append(text)
                elif abs(start - ts) < window or abs(end - ts) < window:
                    # If close enough (within window seconds), include it
                    # heuristic to catch context just before/after
                    if text not in relevant_texts:
                         relevant_texts.append(text)
            
            return " ".join(relevant_texts)
            
        transcript_segments = transcript_data.get('segments', []) if transcript_data else []

        # Process ALL keyframes - no limit
        for idx, kf in enumerate(keyframes, start=1):
            timestamp = kf.get('timestamp', 0)
            mins = int(timestamp // 60)
            secs = int(timestamp % 60)
            
            # Parse description
            desc_data = self._parse_description(kf.get('description', ''))
            
            # Handle case where desc_data might be a string instead of dict
            if not isinstance(desc_data, dict):
                desc_data = {"summary": str(desc_data) if desc_data else "Descrizione non disponibile"}
            
            # Extract key information - NO TRUNCATION
            summary = desc_data.get('summary', desc_data.get('visual_description', 'Descrizione non disponibile'))
            audio_corr = desc_data.get('audio_correlation', '')
            current_action = desc_data.get('current_action', {})
            if isinstance(current_action, dict):
                action_text = current_action.get('action', '')
            else:
                action_text = str(current_action) if current_action else ''
            
            # Get screen_type safely - handle nested layout dict
            screen_type = desc_data.get('screen_type', '')
            if not screen_type:
                layout = desc_data.get('layout')
                if isinstance(layout, dict):
                    screen_type = layout.get('type', '')
            
            module_name = desc_data.get('module_name', '')
            
            # Try to get OCR data
            ocr_data = desc_data.get('ocr_extracted_texts', {})
            if not isinstance(ocr_data, dict):
                ocr_data = {}
            visible_buttons = ocr_data.get('buttons', [])
            headers = ocr_data.get('headers', [])
            data_values = ocr_data.get('data_values', [])
            
            # Build description text - FULL content, no truncation
            desc_parts = [f"<b>Frame {idx} - [{mins}:{secs:02d}]</b>"]
            
            if screen_type:
                desc_parts.append(f"<i>Tipo: {screen_type}</i>")
            
            if module_name:
                desc_parts.append(f"<i>Modulo: {module_name}</i>")
            
            # Full summary - no truncation
            desc_parts.append(f"<br/>{summary}")

            # AUDIO TRANSCRIPT MATCHING (New!)
            actual_transcript = get_transcript_for_time(timestamp, transcript_segments)
            if actual_transcript:
                 desc_parts.append(f"<br/><b>Trascrizione originale:</b> <i>\"{actual_transcript}\"</i>")
            
            # Full audio correlation - no truncation
            if audio_corr:
                desc_parts.append(f"<br/><b>Audio Context:</b> {audio_corr}")
            
            # Full action text - no truncation
            if action_text:
                desc_parts.append(f"<br/><b>Azione Utente:</b> {action_text}")
            
            # Expanded OCR data
            if headers:
                desc_parts.append(f"<br/><b>Titoli rilevati:</b> {', '.join(headers[:3])}")
            
            if visible_buttons:
                desc_parts.append(f"<br/><b>Bottoni:</b> {', '.join(visible_buttons[:6])}")
                
            if data_values:
                 desc_parts.append(f"<br/><b>Dati:</b> {', '.join(data_values[:4])}")
            
            description_cell = Paragraph("<br/>".join(desc_parts), self.styles['CustomBodyText'])
            
            # Try to download and include image
            img_cell = None
            s3_url = kf.get('s3_url', '')
            if s3_url:
                img_data = self._download_image(s3_url)
                if img_data:
                    try:
                        # Increased image size (7cm width)
                        img_width, img_height = self._get_image_size_keeping_aspect_ratio(
                            img_data, max_width=7*cm, max_height=6*cm
                        )
                        img_cell = Image(img_data, width=img_width, height=img_height)
                    except Exception as e:
                        logger.warning(f"Failed to create image for frame {idx}: {e}")
            
            # Create table row with image and description
            if img_cell:
                # Adjusted column widths: 7cm + 9.5cm = 16.5cm
                table_data = [[img_cell, description_cell]]
                table = Table(table_data, colWidths=[7*cm, 9.5*cm])
                table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
                ]))
                elements.append(KeepTogether([table]))
            else:
                # No image - show full text description
                elements.append(Paragraph(
                    f"• <b>[{mins}:{secs:02d}]</b> {summary}",
                    self.styles['ListItem']
                ))
            
            elements.append(Spacer(1, 8))
        
        # All keyframes are now included - no "more" message needed
        
        return elements


def generate_video_report(
    video_data: Dict[str, Any],
    transcript_data: Optional[Dict[str, Any]],
    keyframes_data: List[Dict[str, Any]],
    analysis_data: Optional[Dict[str, Any]],
    output_path: Optional[str] = None,
    diagrams_data: Optional[Dict[str, Any]] = None,
    template_type: Optional[str] = None,
    analyzer = None
) -> bytes:
    """
    Convenience function to generate a PDF report.
    
    Args:
        video_data: Video metadata
        transcript_data: Transcription data
        keyframes_data: Keyframes data
        analysis_data: Analysis data
        output_path: Optional output file path
        diagrams_data: Optional rendered diagrams
        template_type: Optional template type for styling (reverse_engineering, meeting, etc.)
        analyzer: Optional AIAnalyzer instance for enhanced summary generation
        
    Returns:
        PDF content as bytes
    """
    generator = PDFReportGenerator(template_type=template_type, analyzer=analyzer)
    return generator.generate_report(
        video_data,
        transcript_data,
        keyframes_data,
        analysis_data,
        output_path,
        diagrams_data
    )


if __name__ == "__main__":
    # Test PDF generation
    print("PDF Generator module loaded successfully.")
    print("Use generate_video_report() to create PDF reports.")
