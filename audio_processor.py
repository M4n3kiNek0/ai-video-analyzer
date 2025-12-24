"""
Audio Processing Service.
Handles audio file validation, metadata extraction, and format conversion.
Supports pure audio files for transcription-only analysis.
"""

import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import logging
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = {
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.m4a': 'audio/mp4',
    '.ogg': 'audio/ogg',
    '.flac': 'audio/flac',
    '.webm': 'audio/webm',
    '.aac': 'audio/aac',
    '.wma': 'audio/x-ms-wma',
    '.opus': 'audio/opus',
}

# Maximum file size for Whisper API (25 MB)
MAX_WHISPER_FILE_SIZE = 25 * 1024 * 1024


class AudioProcessor:
    """
    Audio processing class for file validation, metadata extraction, and conversion.
    """

    def __init__(self, audio_path: str):
        """
        Initialize audio processor with audio file path.
        
        Args:
            audio_path: Path to the audio file
        """
        self.audio_path = audio_path
        self.file_ext = os.path.splitext(audio_path)[1].lower()
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        if self.file_ext not in SUPPORTED_AUDIO_FORMATS:
            raise ValueError(
                f"Unsupported audio format: {self.file_ext}. "
                f"Supported formats: {', '.join(SUPPORTED_AUDIO_FORMATS.keys())}"
            )
        
        self.file_size = os.path.getsize(audio_path)
        self._metadata: Optional[Dict[str, Any]] = None
        
        logger.info(f"Audio file loaded: {audio_path}")
        logger.info(f"  Format: {self.file_ext}, Size: {self.file_size / 1024 / 1024:.2f} MB")

    def get_metadata(self) -> Dict[str, Any]:
        """
        Extract audio metadata using FFprobe.
        
        Returns:
            Dictionary with audio metadata
        """
        if self._metadata is not None:
            return self._metadata
        
        try:
            # Use FFprobe to get audio metadata
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                self.audio_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            import json
            probe_data = json.loads(result.stdout)
            
            # Extract relevant metadata
            format_info = probe_data.get("format", {})
            streams = probe_data.get("streams", [])
            
            # Find audio stream
            audio_stream = None
            for stream in streams:
                if stream.get("codec_type") == "audio":
                    audio_stream = stream
                    break
            
            duration = float(format_info.get("duration", 0))
            
            self._metadata = {
                "duration_seconds": round(duration, 2),
                "duration_formatted": self._format_duration(duration),
                "file_size_bytes": self.file_size,
                "file_size_mb": round(self.file_size / 1024 / 1024, 2),
                "format": self.file_ext[1:].upper(),
                "format_long": format_info.get("format_long_name", "Unknown"),
                "bitrate": int(format_info.get("bit_rate", 0)) // 1000 if format_info.get("bit_rate") else None,
                "codec": audio_stream.get("codec_name", "unknown") if audio_stream else "unknown",
                "sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else None,
                "channels": audio_stream.get("channels", 1) if audio_stream else 1,
                "channel_layout": audio_stream.get("channel_layout", "mono") if audio_stream else "mono",
            }
            
            logger.info(f"  Duration: {self._metadata['duration_formatted']}")
            logger.info(f"  Codec: {self._metadata['codec']}, Bitrate: {self._metadata['bitrate']} kbps")
            
            return self._metadata
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe error: {e.stderr}")
            # Return basic metadata without FFprobe
            self._metadata = {
                "duration_seconds": None,
                "duration_formatted": "Unknown",
                "file_size_bytes": self.file_size,
                "file_size_mb": round(self.file_size / 1024 / 1024, 2),
                "format": self.file_ext[1:].upper(),
                "format_long": "Unknown",
                "bitrate": None,
                "codec": "unknown",
                "sample_rate": None,
                "channels": None,
                "channel_layout": None,
            }
            return self._metadata
        except FileNotFoundError:
            logger.warning("FFprobe not found. Install FFmpeg for full metadata extraction.")
            self._metadata = {
                "duration_seconds": None,
                "duration_formatted": "Unknown",
                "file_size_bytes": self.file_size,
                "file_size_mb": round(self.file_size / 1024 / 1024, 2),
                "format": self.file_ext[1:].upper(),
                "format_long": "Unknown",
                "bitrate": None,
                "codec": "unknown",
                "sample_rate": None,
                "channels": None,
                "channel_layout": None,
            }
            return self._metadata

    def get_duration(self) -> float:
        """
        Get audio duration in seconds.
        
        Returns:
            Duration in seconds, or 0 if unknown
        """
        metadata = self.get_metadata()
        return metadata.get("duration_seconds", 0) or 0

    def needs_conversion(self) -> bool:
        """
        Check if audio needs to be converted for Whisper API compatibility.
        
        Whisper works best with MP3 or WAV files under 25MB.
        
        Returns:
            True if conversion is recommended
        """
        # Check file size
        if self.file_size > MAX_WHISPER_FILE_SIZE:
            return True
        
        # These formats work well with Whisper
        good_formats = {'.mp3', '.wav', '.m4a', '.webm'}
        if self.file_ext not in good_formats:
            return True
        
        return False

    def convert_for_whisper(self, output_path: Optional[str] = None) -> str:
        """
        Convert audio to Whisper-compatible format (MP3, 16kHz mono).
        
        Args:
            output_path: Optional output path. If None, creates temp file.
            
        Returns:
            Path to converted audio file
        """
        if output_path is None:
            output_dir = os.path.dirname(self.audio_path) or "."
            output_path = os.path.join(output_dir, "converted_audio.mp3")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        
        # Build FFmpeg command for optimal Whisper input
        # - Convert to mono (ac 1)
        # - Sample rate 16kHz (optimal for Whisper)
        # - MP3 format with controlled bitrate to stay under 25MB
        cmd = [
            "ffmpeg",
            "-i", self.audio_path,
            "-vn",  # No video
            "-ac", "1",  # Mono
            "-ar", "16000",  # 16kHz sample rate
            "-acodec", "libmp3lame",
            "-b:a", "64k",  # 64kbps CBR ensures < 25MB for up to ~50 minutes
            "-y",  # Overwrite output
            output_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            new_size = os.path.getsize(output_path)
            logger.info(f"Audio converted: {self.file_size / 1024 / 1024:.2f} MB → {new_size / 1024 / 1024:.2f} MB")
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion error: {e.stderr}")
            raise RuntimeError(f"Failed to convert audio: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg:\n"
                "  Windows: winget install FFmpeg\n"
                "  macOS: brew install ffmpeg\n"
                "  Linux: sudo apt install ffmpeg"
            )

    def split_for_whisper(self, output_dir: str, segment_duration: int = 600) -> List[str]:
        """
        Split long audio files into segments for Whisper API.
        
        Whisper has a 25MB limit. This splits audio into segments.
        
        Args:
            output_dir: Directory to save segments
            segment_duration: Duration of each segment in seconds (default 10 minutes)
            
        Returns:
            List of paths to audio segments
        """
        os.makedirs(output_dir, exist_ok=True)
        
        duration = self.get_duration()
        if duration <= segment_duration and self.file_size <= MAX_WHISPER_FILE_SIZE:
            # No splitting needed
            return [self.audio_path]
        
        segments = []
        num_segments = int(duration // segment_duration) + 1
        
        for i in range(num_segments):
            start_time = i * segment_duration
            output_path = os.path.join(output_dir, f"segment_{i:03d}.mp3")
            
            cmd = [
                "ffmpeg",
                "-i", self.audio_path,
                "-ss", str(start_time),
                "-t", str(segment_duration),
                "-vn",
                "-ac", "1",
                "-ar", "16000",
                "-acodec", "libmp3lame",
                "-b:a", "64k",
                "-y",
                output_path
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    segments.append(output_path)
                    logger.info(f"Created segment {i + 1}/{num_segments}: {output_path}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to create segment {i}: {e.stderr}")
        
        return segments

    def _format_duration(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS or MM:SS."""
        if seconds <= 0:
            return "0:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"


def is_audio_file(filename: str) -> bool:
    """
    Check if a file is a supported audio format.
    
    Args:
        filename: Filename to check
        
    Returns:
        True if file is a supported audio format
    """
    ext = os.path.splitext(filename)[1].lower()
    return ext in SUPPORTED_AUDIO_FORMATS


def get_supported_audio_extensions() -> List[str]:
    """
    Get list of supported audio file extensions.
    
    Returns:
        List of extensions (e.g., ['.mp3', '.wav', ...])
    """
    return list(SUPPORTED_AUDIO_FORMATS.keys())


def check_ffmpeg_installed() -> bool:
    """
    Check if FFmpeg is installed and accessible.
    
    Returns:
        True if FFmpeg is available
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


if __name__ == "__main__":
    # Test
    print("Audio Processor Module")
    print("=" * 40)
    print(f"Supported formats: {', '.join(SUPPORTED_AUDIO_FORMATS.keys())}")
    print(f"FFmpeg installed: {check_ffmpeg_installed()}")

