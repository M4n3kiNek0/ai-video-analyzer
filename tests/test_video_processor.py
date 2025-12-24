import os
import shutil
import tempfile
import cv2
import numpy as np
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from video_processor import VideoProcessor

class TestVideoProcessor:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup a temporary directory and a dummy video file path."""
        self.temp_dir = tempfile.mkdtemp()
        self.video_path = os.path.join(self.temp_dir, "test_video.mp4")
        
        # We don't verify video content in these tests anymore, just existence
        with open(self.video_path, 'wb') as f:
            f.write(b"dummy content")
            
        yield
        
        # Cleanup
        shutil.rmtree(self.temp_dir)

    @patch('video_processor.cv2.VideoCapture')
    def test_initialization(self, mock_capture_cls):
        """Test that VideoProcessor initializes correctly with mocked VideoCapture."""
        mock_cap = MagicMock()
        mock_capture_cls.return_value = mock_cap
        
        # Setup mock return values for properties
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 10.0,
            cv2.CAP_PROP_FRAME_COUNT: 50.0,
            cv2.CAP_PROP_FRAME_WIDTH: 100.0,
            cv2.CAP_PROP_FRAME_HEIGHT: 100.0
        }.get(prop, 0.0)

        processor = VideoProcessor(self.video_path)
        
        assert processor.video_path == self.video_path
        assert processor.fps == 10.0
        assert processor.total_frames == 50
        assert abs(processor.duration - 5.0) < 0.1
        processor.close()

    @patch('video_processor.cv2.VideoCapture')
    def test_get_duration(self, mock_capture_cls):
        """Test get_duration method."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 10.0,
            cv2.CAP_PROP_FRAME_COUNT: 50.0
        }.get(prop, 0.0)
        mock_capture_cls.return_value = mock_cap

        processor = VideoProcessor(self.video_path)
        duration = processor.get_duration()
        assert abs(duration - 5.0) < 0.1
        processor.close()

    @patch('video_processor.cv2.VideoCapture')
    @patch('subprocess.run')
    def test_extract_audio(self, mock_run, mock_capture_cls):
        """Test extract_audio method (mocking ffmpeg)."""
        # Mock VideoCapture to avoid initialization error
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 10.0,
            cv2.CAP_PROP_FRAME_COUNT: 50.0,
            cv2.CAP_PROP_FRAME_WIDTH: 100.0,
            cv2.CAP_PROP_FRAME_HEIGHT: 100.0
        }.get(prop, 0.0)
        mock_capture_cls.return_value = mock_cap
        
        processor = VideoProcessor(self.video_path)
        output_path = os.path.join(self.temp_dir, "output_audio.mp3")
        
        # Mock successful ffmpeg execution
        mock_run.return_value = MagicMock(returncode=0)
        
        processor.extract_audio(output_path)
        
        # Verify subprocess was called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "ffmpeg" in args
        assert "-i" in args
        assert self.video_path in args
        assert output_path in args
        processor.close()

    @patch('video_processor.cv2.VideoCapture')
    @patch('video_processor.cv2.imwrite')
    def test_extract_keyframes_adaptive(self, mock_imwrite, mock_capture_cls):
        """Test adaptive keyframe extraction with mocks."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 10.0,
            cv2.CAP_PROP_FRAME_COUNT: 50.0,
            cv2.CAP_PROP_FRAME_WIDTH: 100.0,
            cv2.CAP_PROP_FRAME_HEIGHT: 100.0
        }.get(prop, 0.0)
        
        # Mock reading frames (return True, dummy_frame 50 times, then False)
        dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        # Create a side effect that returns (True, frame) 60 times, then (False, None)
        mock_cap.read.side_effect = [(True, dummy_frame)] * 60 + [(False, None)]
        
        mock_capture_cls.return_value = mock_cap

        processor = VideoProcessor(self.video_path)
        output_dir = os.path.join(self.temp_dir, "keyframes")
        
        # Extract frames
        keyframes = processor.extract_keyframes_adaptive(
            output_dir,
            interval_seconds=1.0, 
            min_frames=3,
            max_frames=10
        )
        
        assert len(keyframes) >= 3
        # Should verify keyframe structure
        kf = keyframes[0]
        assert "timestamp" in kf
        assert "path" in kf
        assert "frame_number" in kf
        processor.close()

    @patch('video_processor.cv2.VideoCapture')
    @patch('video_processor.cv2.imread')
    @patch('video_processor.compute_perceptual_hash')
    def test_deduplicate_keyframes(self, mock_phash, mock_imread, mock_capture_cls):
        """Test keyframe deduplication."""
        # Setup basic processor mock
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 10.0,
            cv2.CAP_PROP_FRAME_COUNT: 50.0
        }.get(prop, 0.0)
        mock_capture_cls.return_value = mock_cap
        
        processor = VideoProcessor(self.video_path)
        
        # Create mocked keyframes input
        kf1 = {"path": "path1", "timestamp": 1.0, "frame_number": 10}
        kf2 = {"path": "path2", "timestamp": 2.0, "frame_number": 20}
        
        # Mock reading images
        mock_imread.return_value = np.zeros((10, 10), dtype=np.uint8)
        
        # Mock hash computation - Return SAME hash to force duplication detection
        # Return a simple numpy array as hash
        dummy_hash = np.ones(10)
        mock_phash.return_value = dummy_hash
        
        result, removed = processor.deduplicate_keyframes([kf1, kf2], similarity_threshold=10)
        
        # Should return 1 frame, removed 1
        assert len(result) == 1
        assert removed == 1
        
        processor.close()
