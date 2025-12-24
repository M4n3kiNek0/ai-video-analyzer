"""
Base Report Generator.
Common functionality shared between PDF and HTML report generators.
"""

import json
import logging
from io import BytesIO
from typing import Dict, List, Any, Optional

import requests

from description_parser import DescriptionParser

# Configure logging
logger = logging.getLogger(__name__)


class BaseReportGenerator:
    """
    Base class for report generators with common utility methods.
    """
    
    def __init__(self):
        """Initialize base generator."""
        self.image_cache = {}
    
    def _escape_text(self, text: str) -> str:
        """
        Escape special characters for safe rendering.
        
        Args:
            text: Raw text to escape
            
        Returns:
            Escaped text safe for rendering
        """
        if not text:
            return ""
        return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds as MM:SS or HH:MM:SS.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        if not seconds:
            return "0:00"
        seconds = float(seconds)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
    
    def _download_image(self, url: str, timeout: int = 10) -> Optional[BytesIO]:
        """
        Download image from URL and return as BytesIO.
        
        Args:
            url: Image URL
            timeout: Request timeout in seconds
            
        Returns:
            BytesIO with image data or None on failure
        """
        if not url:
            return None
        
        # Check cache
        if url in self.image_cache:
            # Return a new BytesIO with cached data
            cached = self.image_cache[url]
            cached.seek(0)
            return BytesIO(cached.read())
        
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                img_data = BytesIO(response.content)
                # Cache the data
                self.image_cache[url] = BytesIO(response.content)
                return img_data
        except Exception as e:
            logger.warning(f"Failed to download image from {url}: {e}")
        return None

    def _parse_description(self, description: str) -> Dict[str, Any]:
        """
        Parse JSON description or return structured fallback.
        Delegates to the shared DescriptionParser for robust handling.
        """
        return DescriptionParser.parse_description(description)
    
    def _get_summary_from_analysis(self, analysis_data: Optional[Dict[str, Any]]) -> str:
        """
        Extract summary text from analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            
        Returns:
            Summary string
        """
        if not analysis_data:
            return "Nessun riepilogo disponibile."
        return analysis_data.get('summary', 'Nessun riepilogo disponibile.')
    
    def _get_app_type(self, analysis_data: Optional[Dict[str, Any]], is_audio: bool = False) -> str:
        """
        Get application/audio type from analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            is_audio: Whether this is audio content
            
        Returns:
            Type string (uppercase)
        """
        if not analysis_data:
            return 'N/A'
        
        if is_audio:
            audio_type = analysis_data.get('audio_type', 'N/A')
            return audio_type.upper() if audio_type else 'N/A'
        else:
            app_type = analysis_data.get('app_type', 'N/A')
            return app_type.upper() if app_type else 'N/A'
    
    def _get_technology_hints(self, analysis_data: Optional[Dict[str, Any]]) -> List[str]:
        """
        Get technology hints from analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            
        Returns:
            List of technology strings
        """
        if not analysis_data:
            return []
        return analysis_data.get('technology_hints', [])
    
    def _get_modules(self, analysis_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get modules from analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            
        Returns:
            List of module dictionaries
        """
        if not analysis_data:
            return []
        return analysis_data.get('modules', [])
    
    def _get_user_flows(self, analysis_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get user flows from analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            
        Returns:
            List of user flow dictionaries
        """
        if not analysis_data:
            return []
        return analysis_data.get('user_flows', [])
    
    def _get_issues(self, analysis_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get issues and observations from analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            
        Returns:
            List of issue dictionaries
        """
        if not analysis_data:
            return []
        return analysis_data.get('issues_and_observations', [])
    
    def _get_recommendations(self, analysis_data: Optional[Dict[str, Any]]) -> List:
        """
        Get recommendations from analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            
        Returns:
            List of recommendations (strings or dicts)
        """
        if not analysis_data:
            return []
        return analysis_data.get('recommendations', [])
    
    def _get_speakers(self, analysis_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get speakers from audio analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            
        Returns:
            List of speaker dictionaries
        """
        if not analysis_data:
            return []
        return analysis_data.get('speakers', [])
    
    def _get_topics(self, analysis_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get topics from analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            
        Returns:
            List of topic dictionaries
        """
        if not analysis_data:
            return []
        return analysis_data.get('topics', [])
    
    def _get_action_items(self, analysis_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get action items from audio analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            
        Returns:
            List of action item dictionaries
        """
        if not analysis_data:
            return []
        return analysis_data.get('action_items', [])
    
    def _get_decisions(self, analysis_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get decisions from audio analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            
        Returns:
            List of decision dictionaries
        """
        if not analysis_data:
            return []
        return analysis_data.get('decisions', [])
    
    def _get_ideas(self, analysis_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get ideas and proposals from audio analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            
        Returns:
            List of idea dictionaries
        """
        if not analysis_data:
            return []
        return analysis_data.get('ideas_and_proposals', [])
    
    def _get_key_quotes(self, analysis_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get key quotes from audio analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            
        Returns:
            List of quote dictionaries
        """
        if not analysis_data:
            return []
        return analysis_data.get('key_quotes', [])
    
    def _get_open_issues(self, analysis_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get open issues from audio analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            
        Returns:
            List of open issue dictionaries
        """
        if not analysis_data:
            return []
        return analysis_data.get('open_issues', [])
    
    def _get_next_steps(self, analysis_data: Optional[Dict[str, Any]]) -> List[str]:
        """
        Get next steps from audio analysis data.
        
        Args:
            analysis_data: Full analysis dictionary
            
        Returns:
            List of next step strings
        """
        if not analysis_data:
            return []
        return analysis_data.get('next_steps', [])
    
    def _extract_keyframe_summary(self, description: str, max_length: int = 200) -> str:
        """
        Extract a brief summary from keyframe description.
        
        Args:
            description: Full keyframe description (may be JSON)
            max_length: Maximum summary length
            
        Returns:
            Brief summary string
        """
        desc_data = self._parse_description(description)
        
        summary = desc_data.get('summary', 
                  desc_data.get('visual_description', 
                  'Descrizione non disponibile'))
        
        if len(summary) > max_length:
            return summary[:max_length] + "..."
        return summary


