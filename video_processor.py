"""
Video Processing Service.
Handles audio extraction with FFmpeg and keyframe detection with OpenCV.
Includes perceptual hashing for frame deduplication.
"""

import subprocess
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import cv2
import numpy as np
import logging
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compute_perceptual_hash(image: np.ndarray, hash_size: int = 16) -> np.ndarray:
    """
    Compute perceptual hash (pHash) of an image.
    Returns a binary hash that can be compared with Hamming distance.
    
    Args:
        image: BGR image (OpenCV format)
        hash_size: Size of the hash (default 16x16 = 256 bits)
        
    Returns:
        Binary hash as numpy array
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Resize to hash_size + 1 (for DCT-like difference)
    resized = cv2.resize(gray, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
    
    # Compute difference hash (simpler and faster than DCT)
    diff = resized[:, 1:] > resized[:, :-1]
    
    return diff.flatten()


def hamming_distance(hash1: np.ndarray, hash2: np.ndarray) -> int:
    """Calculate Hamming distance between two hashes."""
    return np.count_nonzero(hash1 != hash2)


def compute_image_hash_from_file(image_path: str) -> Optional[np.ndarray]:
    """Load image and compute its perceptual hash."""
    img = cv2.imread(image_path)
    if img is None:
        return None
    return compute_perceptual_hash(img)


class VideoProcessor:
    """
    Video processing class for audio extraction and keyframe detection.
    """

    def __init__(self, video_path: str):
        """
        Initialize video processor with video file path.
        
        Args:
            video_path: Path to the video file
        """
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0
        
        logger.info(f"Video loaded: {video_path}")
        logger.info(f"  Duration: {self.duration:.2f}s, FPS: {self.fps}, Frames: {self.total_frames}")
        logger.info(f"  Resolution: {self.width}x{self.height}")

    def extract_audio(self, output_audio_path: str, audio_format: str = "mp3") -> str:
        """
        Extract audio from video using FFmpeg.
        
        Args:
            output_audio_path: Path for output audio file
            audio_format: Output format (mp3, wav, etc.)
            
        Returns:
            Path to extracted audio file
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_audio_path) or ".", exist_ok=True)
        
        # Build FFmpeg command optimized for Whisper
        cmd = [
            "ffmpeg",
            "-i", self.video_path,
            "-vn",  # No video
            "-ac", "1",  # Mono is enough for transcription and reduces size
            "-ar", "16000",  # 16kHz is the native sample rate for Whisper
            "-acodec", "libmp3lame" if audio_format == "mp3" else "pcm_s16le",
            "-b:a", "64k",  # 64kbps is plenty for speech and stays under 25MB for ~50min
            "-y",  # Overwrite output
            output_audio_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Audio extracted to: {output_audio_path}")
            return output_audio_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            raise RuntimeError(f"Failed to extract audio: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg:\n"
                "  Windows: winget install FFmpeg\n"
                "  macOS: brew install ffmpeg\n"
                "  Linux: sudo apt install ffmpeg"
            )

    def extract_keyframes_scene_detection(
        self,
        output_dir: str,
        threshold: float = 25.0,
        max_frames: int = 10,
        min_interval_seconds: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Extract keyframes based on scene change detection using histogram correlation.
        
        Args:
            output_dir: Directory to save keyframe images
            threshold: Scene change threshold (0-100, higher = more sensitive)
            max_frames: Maximum number of keyframes to extract
            min_interval_seconds: Minimum time between keyframes
            
        Returns:
            List of keyframe dictionaries with metadata
        """
        os.makedirs(output_dir, exist_ok=True)
        
        keyframes: List[Dict[str, Any]] = []
        prev_frame_gray: Optional[np.ndarray] = None
        frame_count = 0
        keyframe_count = 0
        last_keyframe_time = -min_interval_seconds  # Allow first frame
        
        # Reset video to beginning
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # Always capture first frame
        ret, first_frame = self.cap.read()
        if ret:
            frame_path = os.path.join(output_dir, f"keyframe_{keyframe_count:03d}.jpg")
            cv2.imwrite(frame_path, first_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            keyframes.append({
                "frame_number": 0,
                "timestamp": 0.0,
                "path": frame_path,
                "scene_change_score": 100.0  # First frame is always 100%
            })
            prev_frame_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
            keyframe_count += 1
            last_keyframe_time = 0.0
            logger.info(f"Keyframe {keyframe_count} at 0.00s (first frame)")
        
        frame_count = 1
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 1)
        
        while keyframe_count < max_frames:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            current_time = frame_count / self.fps
            
            # Convert to grayscale for histogram comparison
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame_gray is not None:
                # Calculate histogram difference
                hist_curr = cv2.calcHist([gray], [0], None, [256], [0, 256])
                hist_prev = cv2.calcHist([prev_frame_gray], [0], None, [256], [0, 256])
                
                # Normalize histograms
                hist_curr = cv2.normalize(hist_curr, hist_curr).flatten()
                hist_prev = cv2.normalize(hist_prev, hist_prev).flatten()
                
                # Calculate correlation (1 = identical, 0 = completely different)
                correlation = cv2.compareHist(hist_curr, hist_prev, cv2.HISTCMP_CORREL)
                scene_change = (1 - correlation) * 100
                
                # Check if this is a significant scene change
                time_since_last = current_time - last_keyframe_time
                
                if scene_change > threshold and time_since_last >= min_interval_seconds:
                    frame_path = os.path.join(output_dir, f"keyframe_{keyframe_count:03d}.jpg")
                    cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    
                    keyframes.append({
                        "frame_number": frame_count,
                        "timestamp": round(current_time, 2),
                        "path": frame_path,
                        "scene_change_score": round(scene_change, 2)
                    })
                    
                    keyframe_count += 1
                    last_keyframe_time = current_time
                    
                    logger.info(
                        f"Keyframe {keyframe_count} at {current_time:.2f}s "
                        f"(scene_change={scene_change:.2f}%)"
                    )
            
            prev_frame_gray = gray
            frame_count += 1
        
        # If we didn't get enough keyframes, sample evenly
        if len(keyframes) < 3 and self.duration > 10:
            logger.info("Not enough scene changes detected, sampling evenly...")
            keyframes = self._extract_keyframes_uniform(output_dir, max_frames)
        
        logger.info(f"Total keyframes extracted: {len(keyframes)}")
        return keyframes

    def _extract_keyframes_uniform(
        self,
        output_dir: str,
        num_frames: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Extract keyframes at uniform intervals (fallback method).
        
        Args:
            output_dir: Directory to save keyframe images
            num_frames: Number of frames to extract
            
        Returns:
            List of keyframe dictionaries
        """
        os.makedirs(output_dir, exist_ok=True)
        
        keyframes: List[Dict[str, Any]] = []
        interval = self.total_frames // (num_frames + 1)
        
        for i in range(num_frames):
            frame_pos = interval * (i + 1)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            timestamp = frame_pos / self.fps
            frame_path = os.path.join(output_dir, f"keyframe_{i:03d}.jpg")
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            keyframes.append({
                "frame_number": frame_pos,
                "timestamp": round(timestamp, 2),
                "path": frame_path,
                "scene_change_score": 0  # Uniform sampling, no score
            })
            
            logger.info(f"Uniform keyframe {i + 1} at {timestamp:.2f}s")
        
        return keyframes

    def extract_keyframes_adaptive(
        self,
        output_dir: str,
        interval_seconds: float = 4.0,
        min_frames: int = 10,
        max_frames: int = 60,
        scene_detection_threshold: float = 20.0
    ) -> List[Dict[str, Any]]:
        """
        Extract keyframes adaptively based on video duration.
        Combines uniform sampling with scene detection for comprehensive coverage.
        
        Strategy:
        1. Calculate target frames based on duration (1 frame every interval_seconds)
        2. First pass: uniform sampling to ensure coverage
        3. Second pass: add scene changes between uniform samples
        4. Sort by timestamp and remove duplicates
        
        Args:
            output_dir: Directory to save keyframe images
            interval_seconds: Target interval between frames (default 4 seconds)
            min_frames: Minimum number of frames to extract
            max_frames: Maximum number of frames to extract
            scene_detection_threshold: Threshold for scene change detection
            
        Returns:
            List of keyframe dictionaries with metadata including timestamp for audio correlation
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Calculate target number of frames based on duration
        target_frames = int(self.duration / interval_seconds)
        target_frames = max(min_frames, min(target_frames, max_frames))
        
        logger.info(f"Adaptive extraction: duration={self.duration:.1f}s, target_frames={target_frames}")
        
        keyframes: List[Dict[str, Any]] = []
        keyframe_timestamps = set()  # Track timestamps to avoid duplicates
        
        # Phase 1: Uniform sampling for guaranteed coverage
        uniform_interval = self.duration / (target_frames + 1)
        
        for i in range(target_frames):
            target_time = uniform_interval * (i + 1)
            frame_pos = int(target_time * self.fps)
            
            # Ensure we don't exceed video bounds
            frame_pos = min(frame_pos, self.total_frames - 1)
            
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = self.cap.read()
            
            if not ret:
                continue
            
            timestamp = round(frame_pos / self.fps, 2)
            
            # Skip if we already have a frame very close to this timestamp
            if any(abs(t - timestamp) < 1.0 for t in keyframe_timestamps):
                continue
            
            frame_path = os.path.join(output_dir, f"keyframe_{len(keyframes):03d}.jpg")
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            keyframes.append({
                "frame_number": frame_pos,
                "timestamp": timestamp,
                "timestamp_formatted": self._format_timestamp(timestamp),
                "path": frame_path,
                "scene_change_score": 0,
                "extraction_method": "uniform"
            })
            keyframe_timestamps.add(timestamp)
            
            logger.info(f"Uniform frame {len(keyframes)} at {timestamp:.2f}s")
        
        # Phase 2: Scene detection to capture important transitions
        # Only if we haven't reached max_frames
        if len(keyframes) < max_frames:
            scene_frames = self._detect_scene_changes(
                output_dir,
                threshold=scene_detection_threshold,
                max_additional=max_frames - len(keyframes),
                existing_timestamps=keyframe_timestamps,
                start_index=len(keyframes)
            )
            keyframes.extend(scene_frames)
        
        # Sort by timestamp
        keyframes.sort(key=lambda x: x["timestamp"])
        
        # Re-index after sorting using two-pass rename to avoid Windows FileExistsError
        # Pass 1: Rename all files to temporary names
        temp_paths = []
        for i, kf in enumerate(keyframes):
            old_path = kf["path"]
            temp_path = os.path.join(output_dir, f"_temp_{i:03d}.jpg")
            if os.path.exists(old_path):
                os.rename(old_path, temp_path)
                temp_paths.append((i, temp_path, kf))
            else:
                temp_paths.append((i, old_path, kf))
        
        # Pass 2: Rename from temporary to final names
        for i, temp_path, kf in temp_paths:
            new_path = os.path.join(output_dir, f"keyframe_{i:03d}.jpg")
            if os.path.exists(temp_path):
                os.rename(temp_path, new_path)
            kf["path"] = new_path
        
        logger.info(f"Adaptive extraction complete: {len(keyframes)} keyframes")
        return keyframes

    def _detect_scene_changes(
        self,
        output_dir: str,
        threshold: float,
        max_additional: int,
        existing_timestamps: set,
        start_index: int
    ) -> List[Dict[str, Any]]:
        """
        Detect scene changes and extract frames at transition points.
        
        Args:
            output_dir: Directory to save frames
            threshold: Scene change threshold
            max_additional: Maximum additional frames to extract
            existing_timestamps: Set of already extracted timestamps
            start_index: Starting index for frame naming
            
        Returns:
            List of scene change keyframes
        """
        scene_frames: List[Dict[str, Any]] = []
        prev_frame_gray = None
        
        # Sample every Nth frame for efficiency
        sample_rate = max(1, int(self.fps / 2))  # Sample at ~2fps for detection
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame_idx = 0
        
        while len(scene_frames) < max_additional:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            if frame_idx % sample_rate != 0:
                frame_idx += 1
                continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame_gray is not None:
                # Calculate scene change score
                hist_curr = cv2.calcHist([gray], [0], None, [256], [0, 256])
                hist_prev = cv2.calcHist([prev_frame_gray], [0], None, [256], [0, 256])
                
                hist_curr = cv2.normalize(hist_curr, hist_curr).flatten()
                hist_prev = cv2.normalize(hist_prev, hist_prev).flatten()
                
                correlation = cv2.compareHist(hist_curr, hist_prev, cv2.HISTCMP_CORREL)
                scene_change = (1 - correlation) * 100
                
                timestamp = round(frame_idx / self.fps, 2)
                
                # Check if significant scene change and not too close to existing frames
                if scene_change > threshold:
                    if not any(abs(t - timestamp) < 2.0 for t in existing_timestamps):
                        frame_path = os.path.join(
                            output_dir, 
                            f"keyframe_{start_index + len(scene_frames):03d}.jpg"
                        )
                        cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                        
                        scene_frames.append({
                            "frame_number": frame_idx,
                            "timestamp": timestamp,
                            "timestamp_formatted": self._format_timestamp(timestamp),
                            "path": frame_path,
                            "scene_change_score": round(scene_change, 2),
                            "extraction_method": "scene_detection"
                        })
                        existing_timestamps.add(timestamp)
                        
                        logger.info(
                            f"Scene change frame at {timestamp:.2f}s "
                            f"(score={scene_change:.1f}%)"
                        )
            
            prev_frame_gray = gray
            frame_idx += 1
        
        return scene_frames

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as MM:SS or HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def deduplicate_keyframes(
        self,
        keyframes: List[Dict[str, Any]],
        similarity_threshold: int = 20,
        keep_first: bool = True
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Remove duplicate or very similar keyframes using perceptual hashing.
        
        Args:
            keyframes: List of keyframe dictionaries with 'path' key
            similarity_threshold: Max Hamming distance to consider frames as duplicates
                                 (lower = stricter, 0 = identical only)
                                 Default 20 out of 256 bits (~8% difference)
            keep_first: If True, keep first occurrence of duplicates
            
        Returns:
            Tuple of (deduplicated keyframes list, number of duplicates removed)
        """
        if not keyframes:
            return keyframes, 0
        
        logger.info(f"Deduplicating {len(keyframes)} keyframes (threshold={similarity_threshold})...")
        
        # Compute hashes for all frames
        frame_hashes = []
        for kf in keyframes:
            img = cv2.imread(kf["path"])
            if img is not None:
                hash_val = compute_perceptual_hash(img)
                frame_hashes.append(hash_val)
            else:
                frame_hashes.append(None)
        
        # Find duplicates
        unique_indices = []
        duplicate_indices = []
        
        for i, hash_i in enumerate(frame_hashes):
            if hash_i is None:
                unique_indices.append(i)
                continue
            
            is_duplicate = False
            for j in unique_indices:
                hash_j = frame_hashes[j]
                if hash_j is not None:
                    distance = hamming_distance(hash_i, hash_j)
                    if distance <= similarity_threshold:
                        is_duplicate = True
                        duplicate_indices.append(i)
                        logger.debug(
                            f"Frame {i} ({keyframes[i]['timestamp']:.1f}s) is duplicate of "
                            f"frame {j} ({keyframes[j]['timestamp']:.1f}s) - distance={distance}"
                        )
                        break
            
            if not is_duplicate:
                unique_indices.append(i)
        
        # Build deduplicated list
        deduplicated = [keyframes[i] for i in unique_indices]
        removed_count = len(keyframes) - len(deduplicated)
        
        logger.info(
            f"Deduplication complete: {len(deduplicated)} unique frames, "
            f"{removed_count} duplicates removed"
        )
        
        return deduplicated, removed_count

    def get_transcript_segment_for_timestamp(
        self,
        timestamp: float,
        segments: List[Dict],
        window_seconds: float = 5.0
    ) -> str:
        """
        Get transcript text around a specific timestamp.
        
        Args:
            timestamp: Target timestamp in seconds
            segments: List of transcript segments with start/end times
            window_seconds: Time window to include before/after
            
        Returns:
            Relevant transcript text for the timestamp
        """
        if not segments:
            return ""
        
        relevant_text = []
        start_window = max(0, timestamp - window_seconds)
        end_window = timestamp + window_seconds
        
        for seg in segments:
            seg_start = seg.get("start", 0)
            seg_end = seg.get("end", seg_start)
            
            # Check if segment overlaps with our window
            if seg_start <= end_window and seg_end >= start_window:
                text = seg.get("text", "").strip()
                if text:
                    relevant_text.append(text)
        
        return " ".join(relevant_text)

    def get_duration(self) -> float:
        """
        Get video duration in seconds.
        
        Returns:
            Duration in seconds
        """
        return self.duration

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get video metadata.
        
        Returns:
            Dictionary with video metadata
        """
        return {
            "duration_seconds": round(self.duration, 2),
            "fps": round(self.fps, 2),
            "total_frames": self.total_frames,
            "width": self.width,
            "height": self.height,
            "resolution": f"{self.width}x{self.height}"
        }

    def close(self):
        """Release video capture resources."""
        if hasattr(self, 'cap') and self.cap is not None:
            self.cap.release()
            self.cap = None

    def __del__(self):
        """Release video capture on deletion."""
        self.close()


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
    # Test with a sample video
    import sys
    
    if not check_ffmpeg_installed():
        print("ERROR: FFmpeg is not installed!")
        print("Install with: winget install FFmpeg")
        sys.exit(1)
    
    print("FFmpeg is installed and ready.")
    print("VideoProcessor module loaded successfully.")

