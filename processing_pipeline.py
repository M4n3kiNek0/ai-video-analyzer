"""
Media Processing Pipelines.
Background tasks for video and audio analysis using Celery.
"""

import os
import shutil
import logging
import json
from datetime import datetime
from typing import Optional

from celery_app import celery_app
from models import Video, Media, Transcript, Keyframe, Analysis, SessionLocal, ProcessingLog
from video_processor import VideoProcessor
from audio_processor import AudioProcessor
from ai_analyzer import AIAnalyzer
from storage import MinIOStorage
from diagram_generator import DiagramGenerator

# Configure logging
logger = logging.getLogger(__name__)

# Global instances (set by worker.py on initialization, or lazy loaded)
analyzer: Optional[AIAnalyzer] = None
storage: Optional[MinIOStorage] = None

def log_progress(video_id: int, message: str, level: str = "INFO"):
    """
    Log progress to database for user feedback.
    """
    try:
        db = SessionLocal()
        try:
            log = ProcessingLog(
                video_id=video_id,
                message=message,
                level=level
            )
            db.add(log)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to write log to DB: {e}")


def set_analyzer(ai_analyzer: Optional[AIAnalyzer]):
    """Set the global AI analyzer instance."""
    global analyzer
    analyzer = ai_analyzer


def set_storage(minio_storage: Optional[MinIOStorage]):
    """Set the global MinIO storage instance."""
    global storage
    storage = minio_storage


def _get_analyzer():
    """Lazy load analyzer if not set (fallback for direct execution outside worker)."""
    global analyzer
    if analyzer is None:
        try:
            logger.info("Lazy loading AIAnalyzer...")
            analyzer = AIAnalyzer()
        except Exception as e:
            logger.error(f"Failed to lazy load analyzer: {e}")
    return analyzer


def _get_storage():
    """Lazy load storage if not set."""
    global storage
    if storage is None:
        try:
            logger.info("Lazy loading MinIOStorage...")
            storage = MinIOStorage()
        except Exception as e:
            logger.error(f"Failed to lazy load storage: {e}")
    return storage


@celery_app.task(bind=True, max_retries=2)
def process_audio_task(
    self,
    audio_id: int, 
    audio_path: str, 
    temp_dir: str, 
    user_context: Optional[str] = None,
    analysis_type: str = "auto"
):
    """
    Celery task for complete audio processing pipeline.
    """
    import traceback
    
    logger.info(f"Task process_audio_task[{self.request.id}] started for audio_id={audio_id}")
    
    # Ensure resources are available
    local_analyzer = _get_analyzer()
    # storage not strictly needed for audio-only but good to have
    
    if not os.path.exists(audio_path):
        logger.error(f"[{audio_id}] FILE NOT FOUND: {audio_path}")
        # Update DB status
        db = SessionLocal()
        try:
            audio_record = db.query(Media).filter(Media.id == audio_id).first()
            if audio_record:
                audio_record.status = "failed"
                db.commit()
        finally:
            db.close()
        return
    
    db = SessionLocal()
    
    try:
        # Initialize processor
        logger.info(f"[{audio_id}] Initializing AudioProcessor...")
        processor = AudioProcessor(audio_path)
        metadata = processor.get_metadata()
        audio_duration = processor.get_duration()
        
        # Update duration in DB
        audio_record = db.query(Media).filter(Media.id == audio_id).first()
        audio_record.duration_seconds = int(audio_duration) if audio_duration else None
        db.commit()
        
        # Use provided context or filename as fallback
        context = user_context or audio_record.context or audio_record.filename
        
        # Step 1: ALWAYS convert audio to MP3 for Whisper compatibility
        converted_path = os.path.join(temp_dir, "audio_for_whisper.mp3")
        try:
            transcription_path = processor.convert_for_whisper(converted_path)
        except Exception as conv_err:
            logger.warning(f"[{audio_id}] Conversion failed, using original: {conv_err}")
            transcription_path = audio_path
        
        # Step 2: Transcribe audio
        transcript_result = {"full_text": "", "segments": []}
        enriched_transcript = {}
        
        if local_analyzer:
            logger.info(f"[{audio_id}] Transcribing audio (Whisper)...")
            transcript_result = local_analyzer.transcribe_audio(transcription_path)
            
            # Step 3: Enrich transcription
            logger.info(f"[{audio_id}] Enriching transcription...")
            enriched_transcript = local_analyzer.enrich_transcription(
                transcript_result,
                audio_duration,
                audio_record.filename
            )
        
        # Save transcript to DB
        transcript = Transcript(
            video_id=audio_id,  # Using video_id column for compatibility
            full_text=enriched_transcript.get("full_text", transcript_result.get("full_text", "")),
            segments=enriched_transcript.get("segments", transcript_result.get("segments", [])),
            language=enriched_transcript.get("language", "it")
        )
        db.add(transcript)
        db.commit()
        
        # Step 4: Full audio analysis
        logger.info(f"[{audio_id}] performing full audio analysis...")
        analysis_result = {}
        if local_analyzer:
            analysis_result = local_analyzer.analyze_audio_content(
                transcript_result.get("full_text", ""),
                enriched_transcript,
                audio_duration,
                audio_record.filename,
                context,
                analysis_type
            )
        
        # Save analysis to DB
        analysis_record = Analysis(
            video_id=audio_id,
            summary=analysis_result.get("summary"),
            app_type=analysis_result.get("audio_type"),
            modules=None,
            user_flows=None,
            issues=analysis_result.get("open_issues"),
            technology_hints=analysis_result.get("tags"),
            recommendations=analysis_result.get("recommendations"),
            output_format=analysis_result,
            speakers=analysis_result.get("speakers"),
            action_items=analysis_result.get("action_items"),
            decisions=analysis_result.get("decisions"),
            topics=analysis_result.get("topics")
        )
        db.add(analysis_record)
        
        # Update audio status
        audio_record = db.query(Media).filter(Media.id == audio_id).first()
        audio_record.status = "completed"
        audio_record.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"[{audio_id}] Audio processing COMPLETED successfully.")
        
    except Exception as e:
        logger.error(f"[{audio_id}] Processing failed: {e}")
        logger.error(traceback.format_exc())
        
        # Update status to failed
        try:
            audio_record = db.query(Media).filter(Media.id == audio_id).first()
            if audio_record:
                audio_record.status = "failed"
                db.commit()
        except:
            pass
        
        # Retry logic could be added here
        raise self.retry(exc=e)
    
    finally:
        db.close()
        # Cleanup temp files
        shutil.rmtree(temp_dir, ignore_errors=True)


@celery_app.task(bind=True, max_retries=2)
def process_video_task(
    self, 
    video_id: int, 
    video_path: str, 
    temp_dir: str, 
    user_context: Optional[str] = None, 
    analysis_type: str = "auto"
):
    """
    Celery task for complete video processing pipeline.
    """
    import traceback
    
    logger.info(f"Task process_video_task[{self.request.id}] started for video_id={video_id}")
    log_progress(video_id, "Avvio elaborazione video...", "INFO")
    
    local_analyzer = _get_analyzer()
    local_storage = _get_storage()
    
    if not os.path.exists(video_path):
        logger.error(f"[{video_id}] FILE NOT FOUND: {video_path}")
        log_progress(video_id, "ERRORE: File video non trovato sul server!", "ERROR")
        db = SessionLocal()
        try:
            video_record = db.query(Video).filter(Video.id == video_id).first()
            if video_record:
                video_record.status = "failed"
                db.commit()
        finally:
            db.close()
        return
    
    db = SessionLocal()
    
    try:
        # Initialize processor
        log_progress(video_id, "Inizializzazione processore video...", "INFO")
        processor = VideoProcessor(video_path)
        video_duration = processor.get_duration()
        
        # Update duration in DB
        video = db.query(Video).filter(Video.id == video_id).first()
        video.duration_seconds = int(video_duration)
        db.commit()
        
        context = user_context or video.context or video.filename
        log_progress(video_id, f"Durata video rilevata: {int(video_duration)} secondi. Analisi in corso...", "INFO")
        
        # Step 1: Extract and transcribe audio
        logger.info(f"[{video_id}] Extracting audio...")
        log_progress(video_id, "Estrazione traccia audio...", "INFO")
        audio_path = os.path.join(temp_dir, "audio.mp3")
        processor.extract_audio(audio_path)
        
        transcript_result = {"full_text": "", "segments": []}
        enriched_transcript = {}
        
        if local_analyzer and os.path.exists(audio_path):
            logger.info(f"[{video_id}] Transcribing audio...")
            log_progress(video_id, "Trascrizione audio con Whisper (potrebbe richiedere tempo)...", "INFO")
            transcript_result = local_analyzer.transcribe_audio(audio_path)
            
            logger.info(f"[{video_id}] Enriching transcription...")
            log_progress(video_id, "Analisi semantica del testo...", "INFO")
            enriched_transcript = local_analyzer.enrich_transcription(
                transcript_result,
                video_duration,
                video.filename
            )
        
        # Save transcript
        transcript = Transcript(
            video_id=video_id,
            full_text=enriched_transcript.get("full_text", transcript_result.get("full_text", "")),
            segments=enriched_transcript.get("segments", transcript_result.get("segments", [])),
            language=enriched_transcript.get("language", "it")
        )
        db.add(transcript)
        db.commit()
        
        topics = enriched_transcript.get("topics", [])
        keywords = enriched_transcript.get("keywords", [])
        
        # Step 3: Extract keyframes
        logger.info(f"[{video_id}] Extracting keyframes...")
        log_progress(video_id, "Estrazione frame significativi...", "INFO")
        keyframes_dir = os.path.join(temp_dir, "keyframes")
        keyframes_list = processor.extract_keyframes_adaptive(
            keyframes_dir,
            interval_seconds=4.0,
            min_frames=10,
            max_frames=50,
            scene_detection_threshold=20.0
        )
        
        # Deduplicate
        keyframes_list, _ = processor.deduplicate_keyframes(
            keyframes_list,
            similarity_threshold=20,
            keep_first=True
        )
        log_progress(video_id, f"Selezionati {len(keyframes_list)} frame unici per l'analisi.", "INFO")
        
        # Step 4: Analyze keyframes
        logger.info(f"[{video_id}] Analyzing {len(keyframes_list)} keyframes...")
        log_progress(video_id, "Analisi visiva dei frame con GPT-4 Vision...", "INFO")
        keyframes_with_descriptions = []
        segments = enriched_transcript.get("segments", [])
        previous_description = None
        
        for idx, kf in enumerate(keyframes_list):
            # Log progress every few frames
            if idx % 3 == 0:
                log_progress(video_id, f"Analisi frame {idx+1}/{len(keyframes_list)}...", "INFO")
            try:
                # Correlate with audio
                transcript_segment = processor.get_transcript_segment_for_timestamp(
                    kf["timestamp"], segments, window_seconds=5.0
                )
                
                current_topics = [
                    t["topic"] for t in topics 
                    if t.get("start_time", 0) <= kf["timestamp"] <= t.get("end_time", 9999)
                ]
                
                # Vision analysis
                description = ""
                if local_analyzer:
                    description = local_analyzer.describe_frame_contextual(
                        image_path=kf["path"],
                        timestamp=kf["timestamp"],
                        transcript_segment=transcript_segment,
                        topics=current_topics,
                        keywords=keywords[:15],
                        previous_frame_description=previous_description,
                        context=context
                    )
                
                previous_description = description
                
                # Upload to MinIO
                s3_url = ""
                if local_storage:
                    s3_url = local_storage.upload_keyframe(kf["path"], video_id, idx)
                
                # Save to DB
                keyframe_db = Keyframe(
                    video_id=video_id,
                    timestamp=int(kf["timestamp"]),
                    frame_number=kf["frame_number"],
                    s3_url=s3_url,
                    visual_description=description,
                    scene_change_score=int(kf.get("scene_change_score", 0))
                )
                db.add(keyframe_db)
                db.commit()
                
                keyframes_with_descriptions.append({
                    "timestamp": kf["timestamp"],
                    "description": description
                })
                
            except Exception as kf_err:
                logger.error(f"[{video_id}] Error analyzing frame {idx}: {kf_err}")
                log_progress(video_id, f"Errore analisi frame {idx}: {kf_err}", "WARNING")
        
        # Step 5: Full flow analysis
        logger.info(f"[{video_id}] Generating final report...")
        log_progress(video_id, "Generazione report finale e sintesi...", "INFO")
        analysis_result = {}
        if local_analyzer:
            analysis_result = local_analyzer.analyze_full_flow(
                transcript_result.get("full_text", ""),
                keyframes_with_descriptions,
                video_duration,
                video.filename
            )
            
        # Generate diagrams
        logger.info(f"[{video_id}] Generating diagrams...")
        log_progress(video_id, "Generazione diagrammi UML e flussi utente...", "INFO")
        sequence_diagram = ""
        user_flow_diagram = ""
        wireframes_list = []
        
        try:
            diagram_gen = DiagramGenerator()
            app_name = analysis_result.get("app_name_short", "App")
            
            user_flows = analysis_result.get("user_flows", [])
            if user_flows:
                sequence_diagram = diagram_gen.generate_sequence_diagram(user_flows, app_name=app_name)
            
            user_flow_diagram = diagram_gen.generate_combined_flow_diagram(analysis_result)
            
            # Wireframes for first frames (up to 5)
            for kf_data in keyframes_with_descriptions[:5]:
                desc_raw = kf_data.get("description")
                if not desc_raw:
                    continue
                try:
                    desc_parsed = json.loads(desc_raw) if isinstance(desc_raw, str) else desc_raw
                    wireframe_ascii = diagram_gen.generate_ascii_wireframe(desc_parsed)
                    wireframes_list.append({
                        "timestamp": kf_data.get("timestamp", 0),
                        "wireframe": wireframe_ascii
                    })
                except Exception as wf_err:
                    logger.warning(f"Wireframe generation failed for frame at {kf_data.get('timestamp')}: {wf_err}")
        except Exception as diag_err:
            logger.error(f"Failed diagram generation: {diag_err}")
            log_progress(video_id, "Errore generazione diagrammi, procedo con il salvataggio.", "WARNING")

        # Save analysis
        analysis_record = Analysis(
            video_id=video_id,
            summary=analysis_result.get("summary"),
            app_type=analysis_result.get("app_type"),
            modules=analysis_result.get("modules"),
            user_flows=analysis_result.get("user_flows"),
            issues=analysis_result.get("issues_and_observations"),
            technology_hints=analysis_result.get("technology_hints"),
            recommendations=analysis_result.get("recommendations"),
            output_format=analysis_result,
            sequence_diagram=sequence_diagram,
            user_flow_diagram=user_flow_diagram,
            wireframes=wireframes_list
        )
        db.add(analysis_record)
        
        # Complete
        video = db.query(Video).filter(Video.id == video_id).first()
        video.status = "completed"
        video.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"[{video_id}] Video processing COMPLETED successfully.")
        log_progress(video_id, "Analisi completata con successo!", "SUCCESS")
        
    except Exception as e:
        logger.error(f"[{video_id}] Video processing FAILED: {e}")
        logger.error(traceback.format_exc())
        log_progress(video_id, f"ERRORE CRITICO: {str(e)}", "ERROR")
        
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = "failed"
                db.commit()
        except:
            pass
            
        raise self.retry(exc=e)
    
    finally:
        db.close()
        # Do NOT delete temp files immediately if we want to debug, but in prod we should.
        # However, video file is now in static/videos so we can safely delete temp_dir
        # which contains extracted audio and keyframes.
        shutil.rmtree(temp_dir, ignore_errors=True)
