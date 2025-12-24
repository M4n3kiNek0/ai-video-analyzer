"""
AI Provider Abstraction Layer.
Unified interfaces for different AI providers (OpenAI, Groq, Ollama, etc.)
"""

import base64
import json
import logging
import os
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


# ============================================================================
# Abstract Interfaces
# ============================================================================

class TranscriptionProvider(ABC):
    """Abstract interface for transcription providers."""
    
    @abstractmethod
    def transcribe(self, audio_path: str, language: str = "it") -> Dict[str, Any]:
        """
        Transcribe audio file.
        
        Returns:
            Dict with full_text, segments, language, duration
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if provider is available and configured correctly."""
        pass


class VisionProvider(ABC):
    """Abstract interface for vision/image analysis providers."""
    
    @abstractmethod
    def describe_frame(self, image_path: str, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Analyze an image/frame.
        
        Args:
            image_path: Path to image file
            prompt: Text prompt for analysis
            context: Optional context (timestamp, transcript, etc.)
        
        Returns:
            JSON string with analysis
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if provider is available and configured correctly."""
        pass


class AnalysisProvider(ABC):
    """Abstract interface for text analysis providers."""
    
    @abstractmethod
    def analyze(self, prompt: str, system_message: str, max_tokens: int = 4000, response_format: Optional[str] = None) -> str:
        """
        Analyze text content.
        
        Args:
            prompt: User prompt
            system_message: System message/instructions
            max_tokens: Maximum tokens in response
            response_format: Optional format (e.g., "json_object")
        
        Returns:
            Response text
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if provider is available and configured correctly."""
        pass


# ============================================================================
# OpenAI Provider
# ============================================================================

class OpenAIProvider(TranscriptionProvider, VisionProvider, AnalysisProvider):
    """OpenAI provider supporting Whisper, GPT-4o Vision, and GPT-4o."""
    
    def __init__(self, api_key: str, model_transcription: str = "whisper-1", 
                 model_vision: str = "gpt-4o", model_analysis: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model_transcription = model_transcription
        self.model_vision = model_vision
        self.model_analysis = model_analysis
    
    def transcribe(self, audio_path: str, language: str = "it") -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper."""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        with open(audio_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model=self.model_transcription,
                file=audio_file,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
        
        segments = []
        if hasattr(transcript, 'segments') and transcript.segments:
            for seg in transcript.segments:
                segments.append({
                    "start": round(seg.start, 2),
                    "end": round(seg.end, 2),
                    "text": seg.text.strip()
                })
        
        return {
            "full_text": transcript.text,
            "segments": segments,
            "language": language,
            "duration": transcript.duration if hasattr(transcript, 'duration') else None
        }
    
    def describe_frame(self, image_path: str, prompt: str, context: Optional[Dict] = None) -> str:
        """Analyze frame using GPT-4o Vision."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        with open(image_path, "rb") as img_file:
            image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")
        
        ext = os.path.splitext(image_path)[1].lower()
        media_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}",
                            "detail": "high"
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        response = self.client.chat.completions.create(
            model=self.model_vision,
            max_completion_tokens=3000,
            messages=messages
        )
        
        return response.choices[0].message.content
    
    def analyze(self, prompt: str, system_message: str, max_tokens: int = 4000, response_format: Optional[str] = None) -> str:
        """Analyze text using GPT-4o."""
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        kwargs = {
            "model": self.model_analysis,
            "max_completion_tokens": max_tokens,
            "messages": messages
        }
        
        if response_format:
            kwargs["response_format"] = {"type": response_format}
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    def test_connection(self) -> bool:
        """Test OpenAI API connection."""
        try:
            self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False


# ============================================================================
# Groq Provider
# ============================================================================

class GroqProvider(AnalysisProvider):
    """Groq provider for text analysis (Llama models)."""
    
    def __init__(self, api_key: str, model: str = "llama-3.1-70b-versatile"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1"
        self.client = OpenAI(api_key=api_key, base_url=self.base_url)
    
    def analyze(self, prompt: str, system_message: str, max_tokens: int = 4000, response_format: Optional[str] = None) -> str:
        """Analyze text using Groq."""
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages
        }
        
        if response_format:
            kwargs["response_format"] = {"type": response_format}
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    def test_connection(self) -> bool:
        """Test Groq API connection."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error(f"Groq connection test failed: {e}")
            return False


# ============================================================================
# Ollama Provider (Local)
# ============================================================================

class OllamaProvider(VisionProvider, AnalysisProvider):
    """Ollama provider for local models (LLaVA, Llama)."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model_vision: str = "llava:13b", model_analysis: str = "llama3.1:8b"):
        self.base_url = base_url.rstrip('/')
        self.model_vision = model_vision
        self.model_analysis = model_analysis
    
    def describe_frame(self, image_path: str, prompt: str, context: Optional[Dict] = None) -> str:
        """Analyze frame using Ollama LLaVA."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        with open(image_path, "rb") as img_file:
            image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_vision,
                "prompt": prompt,
                "images": [image_data],
                "stream": False
            },
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.text}")
        
        return response.json().get("response", "")
    
    def analyze(self, prompt: str, system_message: str, max_tokens: int = 4000, response_format: Optional[str] = None) -> str:
        """Analyze text using Ollama."""
        full_prompt = f"{system_message}\n\n{prompt}"
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_analysis,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens
                }
            },
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.text}")
        
        return response.json().get("response", "")
    
    def test_connection(self) -> bool:
        """Test Ollama connection."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                available = [m.get("name", "") for m in models]
                return self.model_vision in available or self.model_analysis in available
            return False
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
            return False


# ============================================================================
# Local Whisper Provider
# ============================================================================

class LocalWhisperProvider(TranscriptionProvider):
    """Local Faster-Whisper provider for free transcription."""
    
    def __init__(self, model: str = "large-v3", device: str = "auto"):
        self.model_name = model
        self.device = device
        self._model = None
    
    def _load_model(self):
        """Lazy load Faster-Whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(self.model_name, device=self.device)
            except ImportError:
                raise ImportError(
                    "faster-whisper not installed. Install with: pip install faster-whisper"
                )
        return self._model
    
    def transcribe(self, audio_path: str, language: str = "it") -> Dict[str, Any]:
        """Transcribe using Faster-Whisper."""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        model = self._load_model()
        segments, info = model.transcribe(audio_path, language=language)
        
        full_text_parts = []
        segments_list = []
        
        for segment in segments:
            text = segment.text.strip()
            full_text_parts.append(text)
            segments_list.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text
            })
        
        return {
            "full_text": " ".join(full_text_parts),
            "segments": segments_list,
            "language": info.language,
            "duration": info.duration
        }
    
    def test_connection(self) -> bool:
        """Test if Faster-Whisper is available."""
        try:
            self._load_model()
            return True
        except Exception as e:
            logger.error(f"Local Whisper test failed: {e}")
            return False


# ============================================================================
# Together AI Provider
# ============================================================================

class TogetherAIProvider(VisionProvider, AnalysisProvider):
    """Together AI provider for vision and text analysis."""
    
    def __init__(self, api_key: str, model_vision: str = "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo", 
                 model_analysis: str = "meta-llama/Llama-3.1-70B-Instruct-Turbo"):
        self.api_key = api_key
        self.model_vision = model_vision
        self.model_analysis = model_analysis
        self.base_url = "https://api.together.xyz/v1"
        self.client = OpenAI(api_key=api_key, base_url=self.base_url)
    
    def describe_frame(self, image_path: str, prompt: str, context: Optional[Dict] = None) -> str:
        """Analyze frame using Together AI vision model."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        with open(image_path, "rb") as img_file:
            image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")
        
        ext = os.path.splitext(image_path)[1].lower()
        media_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
        
        response = self.client.chat.completions.create(
            model=self.model_vision,
            max_completion_tokens=3000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}",
                                "detail": "high"
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        )
        
        return response.choices[0].message.content
    
    def analyze(self, prompt: str, system_message: str, max_tokens: int = 4000, response_format: Optional[str] = None) -> str:
        """Analyze text using Together AI."""
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        kwargs = {
            "model": self.model_analysis,
            "max_tokens": max_tokens,
            "messages": messages
        }
        
        if response_format:
            kwargs["response_format"] = {"type": response_format}
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    def test_connection(self) -> bool:
        """Test Together AI connection."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_analysis,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error(f"Together AI connection test failed: {e}")
            return False


# ============================================================================
# Google AI Studio Provider
# ============================================================================

class GoogleAIProvider(VisionProvider, AnalysisProvider):
    """Google AI Studio provider (Gemini models)."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
    
    def describe_frame(self, image_path: str, prompt: str, context: Optional[Dict] = None) -> str:
        """Analyze frame using Google Gemini."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        with open(image_path, "rb") as img_file:
            image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")
        
        response = requests.post(
            f"{self.base_url}:generateContent?key={self.api_key}",
            json={
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg" if image_path.lower().endswith((".jpg", ".jpeg")) else "image/png",
                                "data": image_data
                            }
                        }
                    ]
                }]
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception(f"Google AI API error: {response.text}")
        
        result = response.json()
        return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    
    def analyze(self, prompt: str, system_message: str, max_tokens: int = 4000, response_format: Optional[str] = None) -> str:
        """Analyze text using Google Gemini."""
        full_prompt = f"{system_message}\n\n{prompt}"
        
        response = requests.post(
            f"{self.base_url}:generateContent?key={self.api_key}",
            json={
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }],
                "generationConfig": {
                    "maxOutputTokens": max_tokens
                }
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception(f"Google AI API error: {response.text}")
        
        result = response.json()
        return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    
    def test_connection(self) -> bool:
        """Test Google AI connection."""
        try:
            response = requests.post(
                f"{self.base_url}:generateContent?key={self.api_key}",
                json={
                    "contents": [{"parts": [{"text": "test"}]}]
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Google AI connection test failed: {e}")
            return False


# ============================================================================
# Anthropic Provider
# ============================================================================

class AnthropicProvider(AnalysisProvider):
    """Anthropic provider (Claude models)."""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"
    
    def analyze(self, prompt: str, system_message: str, max_tokens: int = 4000, response_format: Optional[str] = None) -> str:
        """Analyze text using Anthropic Claude."""
        response = requests.post(
            f"{self.base_url}/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "system": system_message,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception(f"Anthropic API error: {response.text}")
        
        return response.json().get("content", [{}])[0].get("text", "")
    
    def test_connection(self) -> bool:
        """Test Anthropic connection."""
        try:
            response = requests.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": self.model,
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "test"}]
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Anthropic connection test failed: {e}")
            return False


# ============================================================================
# Provider Factory
# ============================================================================

def create_transcription_provider(provider: str, model: str, api_key: Optional[str] = None, 
                                   base_url: Optional[str] = None) -> TranscriptionProvider:
    """Factory function to create transcription provider."""
    if provider == "openai":
        if not api_key:
            raise ValueError("OpenAI API key required")
        return OpenAIProvider(api_key=api_key, model_transcription=model)
    elif provider == "local_whisper":
        return LocalWhisperProvider(model=model)
    else:
        raise ValueError(f"Unsupported transcription provider: {provider}")


def create_vision_provider(provider: str, model: str, api_key: Optional[str] = None,
                           base_url: Optional[str] = None) -> VisionProvider:
    """Factory function to create vision provider."""
    if provider == "openai":
        if not api_key:
            raise ValueError("OpenAI API key required")
        return OpenAIProvider(api_key=api_key, model_vision=model)
    elif provider == "ollama":
        return OllamaProvider(base_url=base_url or "http://localhost:11434", model_vision=model)
    elif provider == "together":
        if not api_key:
            raise ValueError("Together AI API key required")
        return TogetherAIProvider(api_key=api_key, model_vision=model)
    elif provider == "google":
        if not api_key:
            raise ValueError("Google AI API key required")
        return GoogleAIProvider(api_key=api_key, model=model)
    else:
        raise ValueError(f"Unsupported vision provider: {provider}. Supported: openai, ollama, together, google")


def create_analysis_provider(provider: str, model: str, api_key: Optional[str] = None,
                             base_url: Optional[str] = None) -> AnalysisProvider:
    """Factory function to create analysis provider."""
    if provider == "openai":
        if not api_key:
            raise ValueError("OpenAI API key required")
        return OpenAIProvider(api_key=api_key, model_analysis=model)
    elif provider == "groq":
        if not api_key:
            raise ValueError("Groq API key required")
        return GroqProvider(api_key=api_key, model=model)
    elif provider == "ollama":
        return OllamaProvider(base_url=base_url or "http://localhost:11434", model_analysis=model)
    elif provider == "together":
        if not api_key:
            raise ValueError("Together AI API key required")
        return TogetherAIProvider(api_key=api_key, model_analysis=model)
    elif provider == "google":
        if not api_key:
            raise ValueError("Google AI API key required")
        return GoogleAIProvider(api_key=api_key, model=model)
    elif provider == "anthropic":
        if not api_key:
            raise ValueError("Anthropic API key required")
        return AnthropicProvider(api_key=api_key, model=model)
    else:
        raise ValueError(f"Unsupported analysis provider: {provider}")
