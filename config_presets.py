"""
Preset API Configurations.
Predefined combinations of AI providers optimized for different use cases.
"""

PRESETS = {
    "accurate": {
        "name": "Massima Qualità",
        "description": "Migliore qualità, costi più alti. Ideale per analisi critiche e produzione.",
        "transcription": {
            "provider": "openai",
            "model": "whisper-1",
            "api_key_required": True,
            "base_url": None
        },
        "vision": {
            "provider": "openai",
            "model": "gpt-4o",
            "api_key_required": True,
            "base_url": None
        },
        "analysis": {
            "provider": "openai",
            "model": "gpt-4o",
            "api_key_required": True,
            "base_url": None
        },
        "enrichment": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key_required": True,
            "base_url": None
        },
        "quality": "high",
        "quality_stars": 5,
        "cost_per_video_5min": "$2.50 - $5.00",
        "cost_breakdown": {
            "transcription": "$0.03",
            "vision": "$2.00 - $4.50",
            "analysis": "$0.30 - $0.50",
            "enrichment": "$0.02"
        },
        "setup_requirements": [
            "OpenAI API Key richiesta",
            "Account OpenAI con credito disponibile"
        ],
        "rate_limits": "Alti limiti, adatto per produzione"
    },
    "economical": {
        "name": "Economico",
        "description": "Buon compromesso qualità/prezzo. Ideale per uso frequente con budget limitato.",
        "transcription": {
            "provider": "openai",
            "model": "whisper-1",
            "api_key_required": True,
            "base_url": None
        },
        "vision": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key_required": True,
            "base_url": None
        },
        "analysis": {
            "provider": "groq",
            "model": "llama-3.1-70b-versatile",
            "api_key_required": True,
            "base_url": None
        },
        "enrichment": {
            "provider": "groq",
            "model": "llama-3.1-8b-instant",
            "api_key_required": True,
            "base_url": None
        },
        "quality": "medium-high",
        "quality_stars": 4,
        "cost_per_video_5min": "$0.30 - $0.50",
        "cost_breakdown": {
            "transcription": "$0.03",
            "vision": "$0.20 - $0.30",
            "analysis": "$0.05 (Groq gratis)",
            "enrichment": "$0.00 (Groq gratis)"
        },
        "setup_requirements": [
            "OpenAI API Key per trascrizione e vision",
            "Groq API Key (gratis) per analisi"
        ],
        "rate_limits": "Groq: 30 req/min, OpenAI: alti limiti"
    },
    "free": {
        "name": "Gratuito (Rate Limited)",
        "description": "Gratuito ma con limiti di rate. Ideale per test e sviluppo.",
        "transcription": {
            "provider": "local_whisper",
            "model": "large-v3",
            "api_key_required": False,
            "base_url": None
        },
        "vision": {
            "provider": "groq",
            "model": "llama-3.1-70b-versatile",
            "api_key_required": True,
            "base_url": None
        },
        "analysis": {
            "provider": "groq",
            "model": "llama-3.1-70b-versatile",
            "api_key_required": True,
            "base_url": None
        },
        "enrichment": {
            "provider": "groq",
            "model": "llama-3.1-8b-instant",
            "api_key_required": True,
            "base_url": None
        },
        "quality": "medium",
        "quality_stars": 3,
        "cost_per_video_5min": "Free (rate limits apply)",
        "cost_breakdown": {
            "transcription": "Free (locale)",
            "vision": "Free (Groq)",
            "analysis": "Free (Groq)",
            "enrichment": "Free (Groq)"
        },
        "setup_requirements": [
            "Faster-Whisper installato (pip install faster-whisper)",
            "Groq API Key (gratis, registrazione richiesta)",
            "GPU consigliata per Faster-Whisper (opzionale)"
        ],
        "rate_limits": "Groq: 30 req/min, Faster-Whisper: limitato da CPU/GPU"
    },
    "local": {
        "name": "100% Locale",
        "description": "Completamente locale, nessun costo. Richiede Ollama installato e modelli scaricati.",
        "transcription": {
            "provider": "local_whisper",
            "model": "large-v3",
            "api_key_required": False,
            "base_url": None
        },
        "vision": {
            "provider": "ollama",
            "model": "llava:13b",
            "api_key_required": False,
            "base_url": "http://localhost:11434"
        },
        "analysis": {
            "provider": "ollama",
            "model": "llama3.1:8b",
            "api_key_required": False,
            "base_url": "http://localhost:11434"
        },
        "enrichment": {
            "provider": "ollama",
            "model": "llama3.1:8b",
            "api_key_required": False,
            "base_url": "http://localhost:11434"
        },
        "quality": "medium",
        "quality_stars": 3,
        "cost_per_video_5min": "Free (requires local setup)",
        "cost_breakdown": {
            "transcription": "Free (locale)",
            "vision": "Free (locale)",
            "analysis": "Free (locale)",
            "enrichment": "Free (locale)"
        },
        "setup_requirements": [
            "Ollama installato (https://ollama.ai)",
            "Modelli scaricati: ollama pull llava:13b",
            "Modelli scaricati: ollama pull llama3.1:8b",
            "Faster-Whisper installato (pip install faster-whisper)",
            "GPU consigliata per performance migliori"
        ],
        "rate_limits": "Limitato solo da hardware locale"
    }
}

# Provider metadata for UI display
PROVIDER_INFO = {
    "openai": {
        "name": "OpenAI",
        "website": "https://openai.com",
        "api_key_url": "https://platform.openai.com/api-keys",
        "quality_rating": "high",
        "cost_rating": "high",
        "rate_limits": "Alti limiti basati su tier account"
    },
    "groq": {
        "name": "Groq",
        "website": "https://groq.com",
        "api_key_url": "https://console.groq.com/keys",
        "quality_rating": "medium-high",
        "cost_rating": "free",
        "rate_limits": "30 req/min (gratis)"
    },
    "ollama": {
        "name": "Ollama",
        "website": "https://ollama.ai",
        "api_key_url": None,
        "quality_rating": "medium",
        "cost_rating": "free",
        "rate_limits": "Limitato da hardware locale"
    },
    "together": {
        "name": "Together AI",
        "website": "https://together.ai",
        "api_key_url": "https://api.together.xyz/settings/api-keys",
        "quality_rating": "medium-high",
        "cost_rating": "low",
        "rate_limits": "Basati su tier"
    },
    "google": {
        "name": "Google AI Studio",
        "website": "https://aistudio.google.com",
        "api_key_url": "https://aistudio.google.com/app/apikey",
        "quality_rating": "high",
        "cost_rating": "free",
        "rate_limits": "15 req/min (gratis)"
    },
    "anthropic": {
        "name": "Anthropic",
        "website": "https://anthropic.com",
        "api_key_url": "https://console.anthropic.com/settings/keys",
        "quality_rating": "high",
        "cost_rating": "medium",
        "rate_limits": "Basati su tier"
    },
    "local_whisper": {
        "name": "Faster-Whisper (Locale)",
        "website": "https://github.com/guillaumekln/faster-whisper",
        "api_key_url": None,
        "quality_rating": "high",
        "cost_rating": "free",
        "rate_limits": "Limitato da CPU/GPU"
    }
}

def get_preset(preset_id: str):
    """Get preset configuration by ID."""
    return PRESETS.get(preset_id)

def list_presets():
    """List all available presets."""
    return PRESETS

def get_provider_info(provider: str):
    """Get provider metadata."""
    return PROVIDER_INFO.get(provider, {})
