"""
AI Analysis Service.
Integrates multiple AI providers for transcription, visual analysis, and structured flow analysis.
Supports OpenAI, Groq, Ollama, Together AI, Google AI, Anthropic, and local providers.
"""

import base64
import json
import logging
import os
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from models import APIConfig, SessionLocal
from ai_providers import (
    TranscriptionProvider, VisionProvider, AnalysisProvider,
    create_transcription_provider, create_vision_provider, create_analysis_provider
)

# Import prompt templates
from ai_prompts import (
    SYSTEM_ENRICH_TRANSCRIPTION, PROMPT_ENRICH_TRANSCRIPTION,
    SYSTEM_CONTEXTUAL_FRAME, PROMPT_CONTEXTUAL_FRAME,
    SYSTEM_FULL_FLOW_ANALYSIS, PROMPT_FULL_FLOW_ANALYSIS,
    SYSTEM_AUDIO_CONTENT_ANALYSIS, PROMPT_AUDIO_CONTENT_ANALYSIS,
    SYSTEM_OPTIMIZE_CONTEXT, PROMPT_OPTIMIZE_CONTEXT,
    SYSTEM_ENHANCED_EXECUTIVE_SUMMARY, PROMPT_ENHANCED_EXECUTIVE_SUMMARY,
    # Template-specific prompts
    SYSTEM_INFER_CONTENT_TYPE, PROMPT_INFER_CONTENT_TYPE,
    SYSTEM_MEETING_ANALYSIS, PROMPT_MEETING_ANALYSIS,
    SYSTEM_DEBRIEF_ANALYSIS, PROMPT_DEBRIEF_ANALYSIS,
    SYSTEM_BRAINSTORMING_ANALYSIS, PROMPT_BRAINSTORMING_ANALYSIS,
    SYSTEM_NOTES_ANALYSIS, PROMPT_NOTES_ANALYSIS
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIAnalyzer:
    """
    AI-powered analyzer supporting multiple providers for video content analysis.
    Can load configuration from database or use environment variables as fallback.
    """

    def __init__(self, config_id: Optional[int] = None):
        """
        Initialize AIAnalyzer with configuration from database or environment.
        
        Args:
            config_id: Optional ID of APIConfig to use. If None, loads active config or uses env vars.
        """
        self.config = self._load_config(config_id)
        self._init_providers()
        
        logger.info(f"AIAnalyzer initialized with config: {self.config.config_name if self.config else 'default (env vars)'}")
    
    def _load_config(self, config_id: Optional[int] = None) -> Optional[APIConfig]:
        """Load configuration from database or return None to use env vars."""
        try:
            db = SessionLocal()
            try:
                if config_id:
                    config = db.query(APIConfig).filter(APIConfig.id == config_id).first()
                else:
                    config = db.query(APIConfig).filter(APIConfig.is_active == True).first()
                
                if config:
                    logger.info(f"Loaded configuration from database: {config.config_name}")
                    return config
                else:
                    logger.info("No active configuration found, using environment variables")
                    return None
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to load config from database: {e}. Using environment variables.")
            return None
    
    def _init_providers(self):
        """Initialize provider instances based on configuration."""
        if self.config:
            # Use database configuration
            self.transcriber = create_transcription_provider(
                provider=self.config.transcription_provider,
                model=self.config.transcription_model,
                api_key=self.config.transcription_api_key,
                base_url=self.config.transcription_base_url
            )
            
            self.vision_provider = create_vision_provider(
                provider=self.config.vision_provider,
                model=self.config.vision_model,
                api_key=self.config.vision_api_key,
                base_url=self.config.vision_base_url
            )
            
            self.analysis_provider = create_analysis_provider(
                provider=self.config.analysis_provider,
                model=self.config.analysis_model,
                api_key=self.config.analysis_api_key,
                base_url=self.config.analysis_base_url
            )
            
            self.enrichment_provider = create_analysis_provider(
                provider=self.config.enrichment_provider,
                model=self.config.enrichment_model,
                api_key=self.config.enrichment_api_key,
                base_url=self.config.enrichment_base_url
            )
        else:
            # Fallback to environment variables (backward compatibility)
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("No API configuration found. Set OPENAI_API_KEY or configure via Settings.")
            
            self.client = OpenAI(api_key=api_key)
            self.model_transcription = "whisper-1"
            self.model_vision = "gpt-4o"
            self.model_analysis = "gpt-4o"
            self.model_enrichment = "gpt-4o-mini"
            
            # Create OpenAI providers for backward compatibility
            from ai_providers import OpenAIProvider
            self.transcriber = OpenAIProvider(api_key=api_key, model_transcription=self.model_transcription)
            self.vision_provider = OpenAIProvider(api_key=api_key, model_vision=self.model_vision)
            self.analysis_provider = OpenAIProvider(api_key=api_key, model_analysis=self.model_analysis)
            self.enrichment_provider = OpenAIProvider(api_key=api_key, model_analysis=self.model_enrichment)

    def infer_content_type(
        self,
        transcript_text: str,
        user_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Infer the content type from transcript and context.
        
        Uses AI to determine the best template type for the content:
        - reverse_engineering: App demos, technical tutorials
        - meeting: Structured meetings with action items
        - debrief: Post-event analysis, retrospectives
        - brainstorming: Creative sessions
        - notes: General notes, memos
        
        Args:
            transcript_text: The transcript text to analyze
            user_context: Optional user-provided context
            
        Returns:
            Dict with content_type, confidence, reasoning
        """
        logger.info("Inferring content type from transcript...")
        
        # Limit transcript for inference
        MAX_CHARS = 4000
        truncated_transcript = transcript_text[:MAX_CHARS] if transcript_text else ""
        if len(transcript_text or "") > MAX_CHARS:
            truncated_transcript += "\n... [troncato]"
        
        prompt = PROMPT_INFER_CONTENT_TYPE.format(
            transcript=truncated_transcript,
            user_context=user_context or "(nessun contesto fornito)"
        )
        
        try:
            response_text = self.enrichment_provider.analyze(
                prompt=prompt,
                system_message=SYSTEM_INFER_CONTENT_TYPE,
                max_tokens=500,
                response_format="json_object"
            )
            
            result = self._extract_json(response_text)
            
            # Validate and normalize
            valid_types = ["reverse_engineering", "meeting", "debrief", "brainstorming", "notes"]
            content_type = result.get("content_type", "notes")
            if content_type not in valid_types:
                content_type = "notes"
            
            result["content_type"] = content_type
            
            logger.info(f"Inferred content type: {content_type} (confidence: {result.get('confidence', 'unknown')})")
            return result
            
        except Exception as e:
            logger.error(f"Content type inference failed: {e}")
            return {
                "content_type": "notes",
                "confidence": 0.5,
                "reasoning": f"Default to notes due to inference error: {str(e)}",
                "detected_indicators": []
            }

    def get_analysis_prompt_for_type(self, analysis_type: str) -> tuple:
        """
        Get the appropriate system message and prompt template for an analysis type.
        
        Args:
            analysis_type: One of meeting, debrief, brainstorming, notes, reverse_engineering
            
        Returns:
            Tuple of (system_message, prompt_template)
        """
        prompts = {
            "meeting": (SYSTEM_MEETING_ANALYSIS, PROMPT_MEETING_ANALYSIS),
            "debrief": (SYSTEM_DEBRIEF_ANALYSIS, PROMPT_DEBRIEF_ANALYSIS),
            "brainstorming": (SYSTEM_BRAINSTORMING_ANALYSIS, PROMPT_BRAINSTORMING_ANALYSIS),
            "notes": (SYSTEM_NOTES_ANALYSIS, PROMPT_NOTES_ANALYSIS),
            # Default/fallback uses generic audio analysis
            "reverse_engineering": (SYSTEM_AUDIO_CONTENT_ANALYSIS, PROMPT_AUDIO_CONTENT_ANALYSIS),
        }
        
        return prompts.get(analysis_type, (SYSTEM_NOTES_ANALYSIS, PROMPT_NOTES_ANALYSIS))

    def transcribe_audio(
        self,
        audio_path: str,
        language: str = "it"
    ) -> Dict[str, Any]:
        """
        Transcribe audio using configured transcription provider.
        
        Args:
            audio_path: Path to audio file (mp3, wav, etc.)
            language: Language code (default: Italian)
            
        Returns:
            Dictionary with full_text and segments with timestamps
        """
        logger.info(f"Starting transcription: {audio_path}")
        return self.transcriber.transcribe(audio_path, language)

    def enrich_transcription(
        self,
        transcript_result: Dict[str, Any],
        video_duration: float,
        video_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enrich the raw transcription with semantic analysis using GPT-4o.
        
        Produces:
        - Detailed semantic summary
        - Topics/arguments identified with timestamps
        - Tone and style analysis
        - Speaker detection (if multiple)
        - Keywords for visual context correlation
        
        Args:
            transcript_result: Raw transcription from Whisper
            video_duration: Video duration in seconds
            video_filename: Optional filename for context
            
        Returns:
            Enriched transcription dictionary
        """
        logger.info("Enriching transcription with GPT-4o...")
        
        full_text = transcript_result.get("full_text", "")
        segments = transcript_result.get("segments", [])
        
        if not full_text:
            logger.warning("No transcription text to enrich")
            return {
                **transcript_result,
                "enriched": False,
                "semantic_summary": "",
                "topics": [],
                "tone": "unknown",
                "keywords": []
            }
        
        # Format segments with timestamps for context
        segments_formatted = "\n".join([
            f"[{seg['start']:.1f}s - {seg['end']:.1f}s]: {seg['text']}"
            for seg in segments
        ])
        
        prompt = PROMPT_ENRICH_TRANSCRIPTION.format(
            video_filename=video_filename or 'video demo',
            video_duration=video_duration,
            full_text=full_text,
            segments_formatted=segments_formatted
        )

        try:
            response_text = self.enrichment_provider.analyze(
                prompt=prompt,
                system_message=SYSTEM_ENRICH_TRANSCRIPTION,
                max_tokens=2000
            )
            enrichment = self._extract_json(response_text)
            
            # Merge with original transcript
            result = {
                **transcript_result,
                "enriched": True,
                "semantic_summary": enrichment.get("semantic_summary", ""),
                "topics": enrichment.get("topics", []),
                "tone": enrichment.get("tone", "unknown"),
                "speaking_style": enrichment.get("speaking_style", ""),
                "speakers_detected": enrichment.get("speakers_detected", 1),
                "keywords": enrichment.get("keywords", []),
                "visual_context_hints": enrichment.get("visual_context_hints", []),
                "action_phrases": enrichment.get("action_phrases", [])
            }
            
            logger.info(f"Transcription enriched: {len(result['topics'])} topics, {len(result['keywords'])} keywords")
            return result
            
        except Exception as e:
            logger.error(f"Transcription enrichment failed: {e}")
            return {
                **transcript_result,
                "enriched": False,
                "enrichment_error": str(e)
            }

    def describe_frame(
        self,
        image_path: str,
        context: Optional[str] = None
    ) -> str:
        """
        Analyze a keyframe image using GPT-4 Vision (basic mode).
        
        Args:
            image_path: Path to image file
            context: Optional context about the video/application
            
        Returns:
            JSON string with structured visual description
        """
        return self.describe_frame_contextual(image_path, context=context)

    def describe_frame_contextual(
        self,
        image_path: str,
        timestamp: Optional[float] = None,
        transcript_segment: Optional[str] = None,
        topics: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        previous_frame_description: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Analyze a keyframe with full contextual information from audio transcription.
        
        This method correlates visual content with audio narration for richer analysis.
        
        Args:
            image_path: Path to image file
            timestamp: Frame timestamp in seconds
            transcript_segment: Relevant transcript text around this timestamp
            topics: Current topics being discussed
            keywords: Relevant keywords from transcription
            previous_frame_description: Description of previous frame for continuity
            context: Additional context (app name, etc.)
            
        Returns:
            JSON string with contextual visual description
        """
        logger.info(f"Contextual frame analysis: {image_path} at {timestamp}s")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Read and encode image
        with open(image_path, "rb") as img_file:
            image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")
        
        # Determine image type
        ext = os.path.splitext(image_path)[1].lower()
        media_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
        
        # Build contextual prompt with enriched context
        context_parts = []
        
        if context:
            # Extract key functionality mentions from context
            context_parts.append(f"**Applicazione**: {context}")
            
            # Try to extract key features/functionality from context
            context_lower = context.lower()
            key_features = []
            feature_keywords = {
                'gestione ordini': ['ordini', 'comande', 'ordinazioni'],
                'pagamenti': ['pagamenti', 'pago', 'pagamento', 'cassa'],
                'inventario': ['inventario', 'magazzino', 'stock'],
                'clienti': ['clienti', 'cliente', 'anagrafica'],
                'fatturazione': ['fatture', 'fatturazione', 'fattura'],
                'report': ['report', 'reportistica', 'statistiche']
            }
            
            for feature, keywords in feature_keywords.items():
                if any(kw in context_lower for kw in keywords):
                    key_features.append(feature)
            
            if key_features:
                context_parts.append(f"**Funzionalità chiave menzionate nel contesto**: {', '.join(key_features)}")
        
        if timestamp is not None:
            mins = int(timestamp // 60)
            secs = int(timestamp % 60)
            context_parts.append(f"**Timestamp**: {mins}:{secs:02d} ({timestamp:.1f}s)")
        
        if transcript_segment:
            context_parts.append(f"**Narrazione audio in questo momento**:\n\"{transcript_segment}\"")
        
        if topics:
            context_parts.append(f"**Argomenti discussi**: {', '.join(topics)}")
        
        if keywords:
            context_parts.append(f"**Parole chiave**: {', '.join(keywords[:10])}")
        
        if previous_frame_description:
            # Extract summary from previous description for context
            try:
                prev_data = json.loads(previous_frame_description)
                prev_summary = prev_data.get('summary', '')[:200]
                prev_module = prev_data.get('module_name', '')
                if prev_summary:
                    context_parts.append(f"**Frame precedente - Summary**: {prev_summary}")
                if prev_module:
                    context_parts.append(f"**Frame precedente - Modulo**: {prev_module}")
            except:
                # Fallback if previous description is not JSON
                prev_summary = previous_frame_description[:300] + "..." if len(previous_frame_description) > 300 else previous_frame_description
                context_parts.append(f"**Frame precedente**: {prev_summary}")
        
        context_block = "\n".join(context_parts) if context_parts else "Nessun contesto disponibile"
        
        prompt = PROMPT_CONTEXTUAL_FRAME.format(context_block=context_block)

        try:
            context_dict = {
                "timestamp": timestamp,
                "transcript_segment": transcript_segment,
                "topics": topics,
                "keywords": keywords,
                "previous_frame_description": previous_frame_description,
                "context": context
            }
            
            # First attempt
            result = self.vision_provider.describe_frame(
                image_path=image_path,
                prompt=prompt,
                context=context_dict
            )
            
            # Check if result is an error response
            if result and isinstance(result, str):
                error_indicators = [
                    "i'm sorry",
                    "i can't assist",
                    "i'm unable",
                    "cannot assist",
                    "content policy",
                    "i cannot",
                    "i'm not able"
                ]
                result_lower = result.lower()
                
                if any(indicator in result_lower for indicator in error_indicators):
                    logger.warning(f"Vision API returned error response, attempting retry...")
                    
                    # Retry with simplified prompt
                    try:
                        # Create a more direct prompt for retry
                        retry_prompt = f"""Analizza questa schermata di un'applicazione software. 

{context_block}

Fornisci una descrizione dettagliata della schermata in formato JSON. Concentrati sugli elementi visibili: testo, bottoni, layout, componenti UI. Rispondi SEMPRE con JSON valido."""
                        
                        result = self.vision_provider.describe_frame(
                            image_path=image_path,
                            prompt=retry_prompt,
                            context=context_dict
                        )
                        
                        # Check if retry also failed
                        if result and isinstance(result, str):
                            result_lower_retry = result.lower()
                            if any(indicator in result_lower_retry for indicator in error_indicators):
                                logger.warning(f"Retry also failed, using fallback description")
                                return self._create_fallback_description(
                                    image_path, timestamp, context, transcript_segment, topics
                                )
                    except Exception as retry_error:
                        logger.warning(f"Retry failed: {retry_error}, using fallback")
                        return self._create_fallback_description(
                            image_path, timestamp, context, transcript_segment, topics
                        )
            
            logger.info(f"Contextual frame analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"Vision API error: {e}")
            return self._create_fallback_description(
                image_path, timestamp, context, transcript_segment, topics
            )
    
    def _create_fallback_description(
        self,
        image_path: str,
        timestamp: Optional[float] = None,
        context: Optional[str] = None,
        transcript_segment: Optional[str] = None,
        topics: Optional[List[str]] = None
    ) -> str:
        """
        Create a fallback description when API fails or returns error responses.
        
        Args:
            image_path: Path to image file
            timestamp: Frame timestamp
            context: Application context
            transcript_segment: Audio transcript segment
            topics: Current topics
            
        Returns:
            JSON string with fallback description
        """
        # Build basic summary from available context
        summary_parts = []
        if context:
            summary_parts.append(f"Schermata dell'applicazione {context}")
        if timestamp is not None:
            summary_parts.append(f"al timestamp {int(timestamp // 60)}:{int(timestamp % 60):02d}")
        if transcript_segment:
            summary_parts.append(f"durante la descrizione: \"{transcript_segment[:100]}...\"")
        
        summary = ". ".join(summary_parts) + "." if summary_parts else "Schermata dell'applicazione analizzata."
        
        # Determine screen type from context if possible
        screen_type = "unknown"
        if context:
            context_lower = context.lower()
            if any(kw in context_lower for kw in ['ordini', 'comande']):
                screen_type = "order_management"
            elif any(kw in context_lower for kw in ['pagamenti', 'cassa', 'pago']):
                screen_type = "payment"
            elif any(kw in context_lower for kw in ['dashboard', 'dashboard']):
                screen_type = "dashboard"
        
        fallback_data = {
            "fallback": True,
            "error": "Analisi dettagliata non disponibile - descrizione fallback generata",
            "summary": summary,
            "screen_type": screen_type,
            "module_name": "",
            "audio_correlation": transcript_segment[:200] if transcript_segment else "Non disponibile",
            "ocr_extracted_texts": {
                "headers": [],
                "buttons": [],
                "labels": [],
                "menu_items": [],
                "data_values": [],
                "messages": []
            },
            "layout_architecture": {
                "grid_system": "unknown",
                "header_height": "",
                "navigation_type": "",
                "main_area": "",
                "color_scheme": "",
                "spacing_pattern": ""
            },
            "components": [],
            "inferred_data_model": {
                "entities": []
            },
            "inferred_api": {
                "get_endpoints": [],
                "post_endpoints": [],
                "put_endpoints": [],
                "delete_endpoints": []
            },
            "current_state": {
                "mode": "unknown",
                "loaded_data": "",
                "active_selection": "",
                "active_filters": "",
                "modal_open": ""
            },
            "current_action": {
                "action": "unknown",
                "target_element": "",
                "user_intent": "",
                "next_step": ""
            },
            "technology_hints": {
                "ui_framework": "unknown",
                "frontend_framework": "unknown",
                "css_approach": "unknown",
                "platform": "unknown",
                "design_patterns": []
            },
            "transition_from_previous": {
                "changed_elements": [],
                "new_elements": [],
                "removed_elements": [],
                "animation_detected": ""
            },
            "reconstruction_notes": {
                "key_components": [],
                "complex_interactions": [],
                "state_management": "",
                "styling_notes": []
            },
            "detected_features": [],
            "confidence": "low",
            "analysis_notes": "Fallback description generated due to API error or content policy restriction"
        }
        
        return json.dumps(fallback_data)

    def _extract_summary_from_description(self, description: str) -> str:
        """
        Estrae solo il sommario da una descrizione JSON per ridurre i token.
        
        Args:
            description: Descrizione JSON completa del keyframe
            
        Returns:
            Stringa riassuntiva di max 500 caratteri
        """
        if not description:
            return "Descrizione non disponibile"
        
        # Prova a parsare come JSON
        try:
            # Rimuovi wrapper markdown se presente
            text = description.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            # Trova l'inizio e fine del JSON
            json_start = text.find('{')
            json_end = text.rfind('}')
            
            if json_start != -1 and json_end != -1:
                text = text[json_start:json_end + 1]
            
            data = json.loads(text)
            
            # Estrai solo i campi essenziali
            summary = data.get('summary', '')
            screen_type = data.get('screen_type', '')
            module_name = data.get('module_name', '')
            audio_corr = data.get('audio_correlation', '')
            
            # Costruisci risultato compatto
            parts = []
            if screen_type:
                parts.append(f"[{screen_type}]")
            if module_name:
                parts.append(f"Modulo: {module_name}")
            if summary:
                parts.append(summary[:250])
            if audio_corr:
                parts.append(f"Audio: {audio_corr[:100]}")
            
            result = " | ".join(parts) if parts else summary[:400]
            return result[:500]  # Max 500 caratteri per frame
            
        except (json.JSONDecodeError, KeyError, TypeError):
            # Se non è JSON, restituisci i primi 400 caratteri puliti
            clean = description.replace('\n', ' ').replace('  ', ' ')
            return clean[:400]

    def analyze_full_flow(
        self,
        transcript_text: str,
        keyframes_descriptions: List[Dict[str, Any]],
        video_duration: float,
        video_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze the complete video flow: transcription + keyframe descriptions.
        Generates structured output with modules, flows, issues, and recommendations.
        
        Args:
            transcript_text: Full transcription text
            keyframes_descriptions: List of {timestamp, description} dicts
            video_duration: Video duration in seconds
            video_filename: Optional filename for context
            
        Returns:
            Structured analysis dictionary
        """
        logger.info("Starting full flow analysis...")
        
        # ============================================
        # RATE LIMIT PROTECTION: Troncare input lunghi
        # ============================================
        
        # Limite trascrizione a ~8000 caratteri (~2000 token)
        MAX_TRANSCRIPT_CHARS = 8000
        truncated_transcript = transcript_text
        if transcript_text and len(transcript_text) > MAX_TRANSCRIPT_CHARS:
            truncated_transcript = transcript_text[:MAX_TRANSCRIPT_CHARS] + "\n... [trascrizione troncata per limiti API]"
            logger.warning(f"Transcript truncated from {len(transcript_text)} to {MAX_TRANSCRIPT_CHARS} chars")
        
        # Limite keyframe a 15 e usa solo sommari
        MAX_KEYFRAMES = 15
        keyframes_to_use = keyframes_descriptions[:MAX_KEYFRAMES]
        
        # Estrai solo i sommari dalle descrizioni (non il JSON completo)
        keyframes_str = "\n".join([
            f"[{kf['timestamp']}s] {self._extract_summary_from_description(kf.get('description', ''))}"
            for kf in keyframes_to_use
        ])
        
        if len(keyframes_descriptions) > MAX_KEYFRAMES:
            keyframes_str += f"\n... [+ altri {len(keyframes_descriptions) - MAX_KEYFRAMES} keyframe non mostrati per limiti API]"
            logger.warning(f"Keyframes limited from {len(keyframes_descriptions)} to {MAX_KEYFRAMES}")
        
        logger.info(f"Final prompt size: transcript={len(truncated_transcript)} chars, keyframes={len(keyframes_to_use)}")
        
        context = f"File: {video_filename}\n" if video_filename else ""
        
        prompt = PROMPT_FULL_FLOW_ANALYSIS.format(
            context=context,
            video_duration=video_duration,
            truncated_transcript=truncated_transcript if truncated_transcript else "(Nessuna trascrizione disponibile)",
            keyframes_str=keyframes_str if keyframes_str else "(Nessuna schermata disponibile)"
        )

        try:
            response_text = self.analysis_provider.analyze(
                prompt=prompt,
                system_message=SYSTEM_FULL_FLOW_ANALYSIS,
                max_tokens=4000
            )
            
            # Parse JSON from response
            analysis_json = self._extract_json(response_text)
            
            logger.info("Full flow analysis completed successfully")
            return analysis_json
            
        except Exception as e:
            logger.error(f"Analysis API error: {e}")
            return {
                "error": str(e),
                "summary": "Analysis failed",
                "app_type": "unknown",
                "modules": [],
                "user_flows": [],
                "issues_and_observations": [],
                "technology_hints": [],
                "recommendations": []
            }

    def analyze_audio_content(
        self,
        transcript_text: str,
        enriched_transcript: Dict[str, Any],
        audio_duration: float,
        audio_filename: Optional[str] = None,
        user_context: Optional[str] = None,
        analysis_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Analyze audio-only content without visual elements.
        Generates structured output optimized for audio content like meetings,
        podcasts, brainstorming sessions, and voice notes.
        
        Uses template-specific prompts based on analysis_type:
        - auto: Infer the best type from content
        - meeting: Focus on action items, decisions, participants
        - debrief: Focus on lessons learned, improvements
        - brainstorming: Focus on ideas, categorization
        - notes: General structured notes
        - reverse_engineering: Technical analysis (uses generic prompt)
        
        Args:
            transcript_text: Full transcription text
            enriched_transcript: Enriched transcription with topics, keywords, etc.
            audio_duration: Audio duration in seconds
            audio_filename: Optional filename for context
            user_context: User-provided context about the audio
            analysis_type: Type of analysis template to use
            
        Returns:
            Structured analysis dictionary with audio-specific fields
        """
        # Handle auto-detection
        if analysis_type == "auto" or analysis_type == "descriptive":
            inferred = self.infer_content_type(transcript_text, user_context)
            analysis_type = inferred.get("content_type", "notes")
            logger.info(f"Auto-detected content type: {analysis_type}")
        
        logger.info(f"Starting audio content analysis (type: {analysis_type})...")
        
        # Get template-specific prompts
        system_message, prompt_template = self.get_analysis_prompt_for_type(analysis_type)
        
        # ============================================
        # RATE LIMIT PROTECTION: Troncare input lunghi
        # ============================================
        MAX_TRANSCRIPT_CHARS = 10000  # Audio può avere trascrizioni più lunghe
        truncated_transcript = transcript_text
        if transcript_text and len(transcript_text) > MAX_TRANSCRIPT_CHARS:
            truncated_transcript = transcript_text[:MAX_TRANSCRIPT_CHARS] + "\n... [trascrizione troncata per limiti API]"
            logger.warning(f"Audio transcript truncated from {len(transcript_text)} to {MAX_TRANSCRIPT_CHARS} chars")
        
        # Get enriched data
        topics = enriched_transcript.get("topics", [])
        keywords = enriched_transcript.get("keywords", [])
        speakers_detected = enriched_transcript.get("speakers_detected", 1)
        tone = enriched_transcript.get("tone", "unknown")
        semantic_summary = enriched_transcript.get("semantic_summary", "")
        
        # Limita semantic summary
        if semantic_summary and len(semantic_summary) > 1500:
            semantic_summary = semantic_summary[:1500] + "..."
        
        # Format topics for prompt (limita a 10)
        MAX_TOPICS = 10
        topics_to_use = topics[:MAX_TOPICS]
        topics_str = "\n".join([
            f"- [{t.get('start_time', 0):.0f}s - {t.get('end_time', 0):.0f}s] {t.get('topic', '')}: {t.get('description', '')[:150]}"
            for t in topics_to_use
        ]) if topics_to_use else "(Nessun argomento identificato)"
        
        if len(topics) > MAX_TOPICS:
            topics_str += f"\n... [+ altri {len(topics) - MAX_TOPICS} argomenti]"
        
        context_block = f"CONTESTO UTENTE: {user_context}" if user_context else ""
        
        logger.info(f"Audio analysis prompt size: transcript={len(truncated_transcript)} chars, topics={len(topics_to_use)}")
        
        duration_minutes = int(audio_duration // 60)
        duration_formatted = f"{int(audio_duration // 60)}:{int(audio_duration % 60):02d}"
        keywords_str = ', '.join(keywords[:20]) if keywords else '(Nessuna parola chiave)'
        
        prompt = prompt_template.format(
            audio_filename=audio_filename or 'audio recording',
            audio_duration=audio_duration,
            duration_minutes=duration_minutes,
            speakers_detected=speakers_detected,
            tone=tone,
            context_block=context_block,
            semantic_summary=semantic_summary,
            topics_str=topics_str,
            keywords_str=keywords_str,
            truncated_transcript=truncated_transcript if truncated_transcript else "(Nessuna trascrizione disponibile)",
            duration_formatted=duration_formatted
        )

        try:
            response_text = self.analysis_provider.analyze(
                prompt=prompt,
                system_message=system_message,
                max_tokens=4000
            )
            
            # Parse JSON from response
            analysis_json = self._extract_json(response_text)
            
            # Add the analysis type used
            analysis_json["_analysis_type"] = analysis_type
            
            logger.info(f"Audio content analysis completed successfully (template: {analysis_type})")
            return analysis_json
            
        except Exception as e:
            logger.error(f"Audio analysis API error: {e}")
            return {
                "error": str(e),
                "summary": "Audio analysis failed",
                "audio_type": "unknown",
                "_analysis_type": analysis_type,
                "speakers": [],
                "topics": [],
                "action_items": [],
                "decisions": [],
                "ideas_and_proposals": [],
                "recommendations": [],
                "confidence": "low"
            }

    def generate_enhanced_executive_summary(
        self,
        existing_summary: str,
        transcript_data: Optional[Dict[str, Any]] = None,
        keyframes_data: Optional[List[Dict[str, Any]]] = None,
        analysis_data: Optional[Dict[str, Any]] = None,
        user_context: Optional[str] = None
    ) -> str:
        """
        Generate an enhanced executive summary that integrates information from multiple sources.
        
        Args:
            existing_summary: Summary from analysis_data
            transcript_data: Enriched transcript data with semantic_summary
            keyframes_data: List of keyframe descriptions
            analysis_data: Full analysis data with modules, flows, etc.
            user_context: User-provided context about the video
            
        Returns:
            Enhanced executive summary string
        """
        logger.info("Generating enhanced executive summary...")
        
        # Extract semantic summary from transcript
        semantic_summary = ""
        if transcript_data and transcript_data.get('semantic_summary'):
            semantic_summary = transcript_data['semantic_summary']
        
        # Extract key observations from keyframes
        keyframes_observations = []
        if keyframes_data:
            for kf in keyframes_data[:15]:  # Analyze first 15 frames
                try:
                    desc_str = kf.get('description', '')
                    if desc_str:
                        desc_data = self._extract_summary_from_description(desc_str)
                        if desc_data and len(desc_data) > 50:  # Only meaningful descriptions
                            timestamp = kf.get('timestamp', 0)
                            mins = int(timestamp // 60)
                            secs = int(timestamp % 60)
                            keyframes_observations.append(f"[{mins}:{secs:02d}] {desc_data[:200]}")
                except Exception:
                    pass
        
        keyframes_str = "\n".join(keyframes_observations[:10]) if keyframes_observations else "(Nessuna osservazione significativa dai keyframe)"
        
        # Extract modules summary
        modules_summary = ""
        if analysis_data and analysis_data.get('modules'):
            modules = analysis_data['modules']
            module_names = [m.get('name', 'Modulo') for m in modules[:5]]
            modules_summary = f"Moduli identificati: {', '.join(module_names)}"
            if len(modules) > 5:
                modules_summary += f" e altri {len(modules) - 5} moduli."
        else:
            modules_summary = "(Nessun modulo identificato)"
        
        # Extract user flows summary
        user_flows_summary = ""
        if analysis_data and analysis_data.get('user_flows'):
            flows = analysis_data['user_flows']
            flow_names = [f.get('name', 'Flusso') for f in flows[:3]]
            user_flows_summary = f"Flussi principali: {', '.join(flow_names)}"
            if len(flows) > 3:
                user_flows_summary += f" e altri {len(flows) - 3} flussi."
        else:
            user_flows_summary = "(Nessun flusso utente identificato)"
        
        prompt = PROMPT_ENHANCED_EXECUTIVE_SUMMARY.format(
            user_context=user_context or "(Nessun contesto utente fornito)",
            existing_summary=existing_summary or "(Nessun summary esistente)",
            semantic_summary=semantic_summary or "(Nessun riassunto semantico disponibile)",
            keyframes_observations=keyframes_str,
            modules_summary=modules_summary,
            user_flows_summary=user_flows_summary
        )
        
        try:
            response_text = self.enrichment_provider.analyze(
                prompt=prompt,
                system_message=SYSTEM_ENHANCED_EXECUTIVE_SUMMARY,
                max_tokens=2000,
                response_format="json_object"
            )
            
            result = self._extract_json(response_text)
            enhanced_summary = result.get('executive_summary', existing_summary or 'Nessun riepilogo disponibile.')
            
            logger.info("Enhanced executive summary generated successfully")
            return enhanced_summary
            
        except Exception as e:
            logger.error(f"Enhanced summary generation failed: {e}")
            # Fallback to existing summary
            return existing_summary or 'Nessun riepilogo disponibile.'

    def optimize_context_prompt(self, user_context: str) -> Dict[str, Any]:
        """
        Ottimizza la descrizione fornita dall'utente per migliorare l'analisi video/audio.
        
        Usa AI per suggerire una versione migliorata del prompt che produrrà
        risultati di analisi più accurati e dettagliati.
        
        Args:
            user_context: Descrizione originale dell'utente
            
        Returns:
            Dict con testo ottimizzato e lista dei miglioramenti applicati
        """
        logger.info("Optimizing user context prompt...")
        
        prompt = PROMPT_OPTIMIZE_CONTEXT.format(user_context=user_context)

        try:
            # Use enrichment_provider instead of self.client
            response_text = self.enrichment_provider.analyze(
                prompt=prompt,
                system_message=SYSTEM_OPTIMIZE_CONTEXT,
                max_tokens=1500,
                response_format="json_object"
            )
            
            result = self._extract_json(response_text)
            
            # Validate result
            if not result.get("optimized_text"):
                result["optimized_text"] = user_context
            if not result.get("improvements"):
                result["improvements"] = ["Formattazione migliorata"]
            
            logger.info(f"Context optimized: {len(result.get('improvements', []))} improvements applied")
            return result
            
        except Exception as e:
            logger.error(f"Context optimization failed: {e}")
            # Fallback: return original with error note
            return {
                "optimized_text": user_context,
                "improvements": ["Ottimizzazione automatica non disponibile - usa la descrizione originale"]
            }

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract and parse JSON from response text.
        Handles markdown code fences and raw JSON.
        
        Args:
            text: Response text that may contain JSON
            
        Returns:
            Parsed JSON dictionary
        """
        # Try to extract JSON from markdown code block
        if "```json" in text:
            json_part = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            json_part = text.split("```")[1].split("```")[0]
        else:
            json_part = text
        
        # Clean up and parse
        json_part = json_part.strip()
        
        try:
            return json.loads(json_part)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            # Return raw response if parsing fails
            return {"raw_response": text, "parse_error": str(e)}


def test_api_connection() -> bool:
    """
    Test API connection with current configuration.
    
    Returns:
        True if connection successful
    """
    try:
        analyzer = AIAnalyzer()
        # Test transcription provider
        if hasattr(analyzer, 'transcriber'):
            success = analyzer.transcriber.test_connection()
            if success:
                logger.info("API connection successful")
                return True
        logger.warning("Could not test API connection")
        return False
    except Exception as e:
        logger.error(f"API connection test failed: {e}")
        return False


if __name__ == "__main__":
    # Test API connection
    print("Testing API connection...")
    if test_api_connection():
        print("✓ API connection successful")
    else:
        print("✗ API connection failed - check configuration")

