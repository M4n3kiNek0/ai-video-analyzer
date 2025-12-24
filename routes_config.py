"""
API Configuration Routes.
Endpoints for managing AI provider configurations.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models import APIConfig, get_db
from config_presets import PRESETS, PROVIDER_INFO, get_preset, get_provider_info
from ai_providers import (
    create_transcription_provider, create_vision_provider, create_analysis_provider
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class ProviderConfig(BaseModel):
    """Provider configuration schema."""
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class ConfigCreate(BaseModel):
    """Schema for creating a new configuration."""
    config_name: str = Field(..., min_length=1, max_length=100)
    transcription: ProviderConfig
    vision: ProviderConfig
    analysis: ProviderConfig
    enrichment: ProviderConfig
    quality_rating: str = Field(default="medium", pattern="^(high|medium|low)$")
    estimated_cost_per_video: str = Field(default="Unknown")
    notes: Optional[str] = None


class ConfigUpdate(BaseModel):
    """Schema for updating a configuration."""
    config_name: Optional[str] = Field(None, min_length=1, max_length=100)
    transcription: Optional[ProviderConfig] = None
    vision: Optional[ProviderConfig] = None
    analysis: Optional[ProviderConfig] = None
    enrichment: Optional[ProviderConfig] = None
    quality_rating: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    estimated_cost_per_video: Optional[str] = None
    notes: Optional[str] = None


class ConfigTest(BaseModel):
    """Schema for testing a configuration."""
    transcription: ProviderConfig
    vision: ProviderConfig
    analysis: ProviderConfig
    enrichment: ProviderConfig


# ============================================================================
# Helper Functions
# ============================================================================

def _config_to_dict(config: APIConfig) -> dict:
    """Convert APIConfig model to dictionary."""
    return {
        "id": config.id,
        "config_name": config.config_name,
        "is_active": config.is_active,
        "transcription": {
            "provider": config.transcription_provider,
            "model": config.transcription_model,
            "api_key": "***" if config.transcription_api_key else None,
            "base_url": config.transcription_base_url
        },
        "vision": {
            "provider": config.vision_provider,
            "model": config.vision_model,
            "api_key": "***" if config.vision_api_key else None,
            "base_url": config.vision_base_url
        },
        "analysis": {
            "provider": config.analysis_provider,
            "model": config.analysis_model,
            "api_key": "***" if config.analysis_api_key else None,
            "base_url": config.analysis_base_url
        },
        "enrichment": {
            "provider": config.enrichment_provider,
            "model": config.enrichment_model,
            "api_key": "***" if config.enrichment_api_key else None,
            "base_url": config.enrichment_base_url
        },
        "quality_rating": config.quality_rating,
        "estimated_cost_per_video": config.estimated_cost_per_video,
        "notes": config.notes,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None
    }


def _save_provider_config(config: APIConfig, provider_type: str, provider_config: ProviderConfig):
    """Save provider configuration to APIConfig model."""
    if provider_type == "transcription":
        config.transcription_provider = provider_config.provider
        config.transcription_model = provider_config.model
        config.transcription_api_key = provider_config.api_key
        config.transcription_base_url = provider_config.base_url
    elif provider_type == "vision":
        config.vision_provider = provider_config.provider
        config.vision_model = provider_config.model
        config.vision_api_key = provider_config.api_key
        config.vision_base_url = provider_config.base_url
    elif provider_type == "analysis":
        config.analysis_provider = provider_config.provider
        config.analysis_model = provider_config.model
        config.analysis_api_key = provider_config.api_key
        config.analysis_base_url = provider_config.base_url
    elif provider_type == "enrichment":
        config.enrichment_provider = provider_config.provider
        config.enrichment_model = provider_config.model
        config.enrichment_api_key = provider_config.api_key
        config.enrichment_base_url = provider_config.base_url


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("")
async def get_configs(db: Session = Depends(get_db)):
    """List all configurations."""
    configs = db.query(APIConfig).order_by(APIConfig.created_at.desc()).all()
    return {
        "configs": [_config_to_dict(c) for c in configs]
    }


@router.get("/active")
async def get_active_config(db: Session = Depends(get_db)):
    """Get currently active configuration."""
    active_config = db.query(APIConfig).filter(APIConfig.is_active == True).first()
    if not active_config:
        raise HTTPException(status_code=404, detail="No active configuration found")
    return _config_to_dict(active_config)


@router.get("/presets")
async def get_presets():
    """Get all available preset configurations with metadata."""
    presets_list = []
    for preset_id, preset_data in PRESETS.items():
        presets_list.append({
            "id": preset_id,
            "name": preset_data["name"],
            "description": preset_data["description"],
            "quality": preset_data["quality"],
            "quality_stars": preset_data.get("quality_stars", 3),
            "cost_per_video_5min": preset_data["cost_per_video_5min"],
            "cost_breakdown": preset_data.get("cost_breakdown", {}),
            "setup_requirements": preset_data.get("setup_requirements", []),
            "rate_limits": preset_data.get("rate_limits", ""),
            "config": {
                "transcription": preset_data["transcription"],
                "vision": preset_data["vision"],
                "analysis": preset_data["analysis"],
                "enrichment": preset_data["enrichment"]
            }
        })
    return {"presets": presets_list}


@router.get("/providers")
async def get_providers():
    """Get information about all available providers."""
    return {"providers": PROVIDER_INFO}


@router.get("/{config_id}")
async def get_config(config_id: int, db: Session = Depends(get_db)):
    """Get a specific configuration by ID."""
    config = db.query(APIConfig).filter(APIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return _config_to_dict(config)


@router.post("")
async def create_config(config_data: ConfigCreate, db: Session = Depends(get_db)):
    """Create a new configuration."""
    # Check if name already exists
    existing = db.query(APIConfig).filter(APIConfig.config_name == config_data.config_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Configuration name already exists")
    
    # Create new config
    new_config = APIConfig(
        config_name=config_data.config_name,
        is_active=False,
        quality_rating=config_data.quality_rating,
        estimated_cost_per_video=config_data.estimated_cost_per_video,
        notes=config_data.notes
    )
    
    # Save provider configs
    _save_provider_config(new_config, "transcription", config_data.transcription)
    _save_provider_config(new_config, "vision", config_data.vision)
    _save_provider_config(new_config, "analysis", config_data.analysis)
    _save_provider_config(new_config, "enrichment", config_data.enrichment)
    
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    
    logger.info(f"Created new configuration: {new_config.config_name} (ID: {new_config.id})")
    return _config_to_dict(new_config)


@router.put("/{config_id}")
async def update_config(config_id: int, config_data: ConfigUpdate, db: Session = Depends(get_db)):
    """Update an existing configuration."""
    config = db.query(APIConfig).filter(APIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    # Update fields if provided
    if config_data.config_name is not None:
        # Check if new name conflicts
        existing = db.query(APIConfig).filter(
            APIConfig.config_name == config_data.config_name,
            APIConfig.id != config_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Configuration name already exists")
        config.config_name = config_data.config_name
    
    if config_data.quality_rating is not None:
        config.quality_rating = config_data.quality_rating
    if config_data.estimated_cost_per_video is not None:
        config.estimated_cost_per_video = config_data.estimated_cost_per_video
    if config_data.notes is not None:
        config.notes = config_data.notes
    
    # Update provider configs if provided
    if config_data.transcription:
        _save_provider_config(config, "transcription", config_data.transcription)
    if config_data.vision:
        _save_provider_config(config, "vision", config_data.vision)
    if config_data.analysis:
        _save_provider_config(config, "analysis", config_data.analysis)
    if config_data.enrichment:
        _save_provider_config(config, "enrichment", config_data.enrichment)
    
    db.commit()
    db.refresh(config)
    
    logger.info(f"Updated configuration: {config.config_name} (ID: {config.id})")
    return _config_to_dict(config)


@router.post("/{config_id}/activate")
async def activate_config(config_id: int, db: Session = Depends(get_db)):
    """Activate a configuration (deactivates all others)."""
    config = db.query(APIConfig).filter(APIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    # Deactivate all configs
    db.query(APIConfig).update({"is_active": False})
    
    # Activate this one
    config.is_active = True
    db.commit()
    db.refresh(config)
    
    logger.info(f"Activated configuration: {config.config_name} (ID: {config.id})")
    return {
        "message": "Configuration activated successfully",
        "config": _config_to_dict(config)
    }


@router.post("/test")
async def test_config(config_data: ConfigTest):
    """Test a configuration without saving it."""
    results = {
        "transcription": {"success": False, "error": None},
        "vision": {"success": False, "error": None},
        "analysis": {"success": False, "error": None},
        "enrichment": {"success": False, "error": None}
    }
    
    # Test transcription
    try:
        provider = create_transcription_provider(
            provider=config_data.transcription.provider,
            model=config_data.transcription.model,
            api_key=config_data.transcription.api_key,
            base_url=config_data.transcription.base_url
        )
        results["transcription"]["success"] = provider.test_connection()
    except Exception as e:
        results["transcription"]["error"] = str(e)
    
    # Test vision
    try:
        provider = create_vision_provider(
            provider=config_data.vision.provider,
            model=config_data.vision.model,
            api_key=config_data.vision.api_key,
            base_url=config_data.vision.base_url
        )
        results["vision"]["success"] = provider.test_connection()
    except Exception as e:
        results["vision"]["error"] = str(e)
    
    # Test analysis
    try:
        provider = create_analysis_provider(
            provider=config_data.analysis.provider,
            model=config_data.analysis.model,
            api_key=config_data.analysis.api_key,
            base_url=config_data.analysis.base_url
        )
        results["analysis"]["success"] = provider.test_connection()
    except Exception as e:
        results["analysis"]["error"] = str(e)
    
    # Test enrichment
    try:
        provider = create_analysis_provider(
            provider=config_data.enrichment.provider,
            model=config_data.enrichment.model,
            api_key=config_data.enrichment.api_key,
            base_url=config_data.enrichment.base_url
        )
        results["enrichment"]["success"] = provider.test_connection()
    except Exception as e:
        results["enrichment"]["error"] = str(e)
    
    all_success = all(r["success"] for r in results.values())
    
    return {
        "success": all_success,
        "results": results
    }


@router.post("/presets/{preset_id}/apply")
async def apply_preset(preset_id: str, config_name: Optional[str] = None, db: Session = Depends(get_db)):
    """Apply a preset configuration (creates and activates it)."""
    preset = get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    
    # Use preset name or provided name
    name = config_name or preset["name"]
    
    # Check if name exists
    existing = db.query(APIConfig).filter(APIConfig.config_name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Configuration name already exists")
    
    # Create config from preset
    new_config = APIConfig(
        config_name=name,
        is_active=False,
        quality_rating=preset["quality"],
        estimated_cost_per_video=preset["cost_per_video_5min"],
        notes=preset["description"]
    )
    
    # Map preset to provider configs
    _save_provider_config(new_config, "transcription", ProviderConfig(**preset["transcription"]))
    _save_provider_config(new_config, "vision", ProviderConfig(**preset["vision"]))
    _save_provider_config(new_config, "analysis", ProviderConfig(**preset["analysis"]))
    _save_provider_config(new_config, "enrichment", ProviderConfig(**preset["enrichment"]))
    
    db.add(new_config)
    
    # Deactivate all others and activate this one
    db.query(APIConfig).update({"is_active": False})
    new_config.is_active = True
    
    db.commit()
    db.refresh(new_config)
    
    logger.info(f"Applied preset '{preset_id}' as configuration: {new_config.config_name} (ID: {new_config.id})")
    return {
        "message": f"Preset '{preset_id}' applied and activated",
        "config": _config_to_dict(new_config)
    }


@router.delete("/{config_id}")
async def delete_config(config_id: int, db: Session = Depends(get_db)):
    """Delete a configuration."""
    config = db.query(APIConfig).filter(APIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    if config.is_active:
        raise HTTPException(status_code=400, detail="Cannot delete active configuration. Deactivate it first.")
    
    db.delete(config)
    db.commit()
    
    logger.info(f"Deleted configuration: {config.config_name} (ID: {config_id})")
    return {"message": "Configuration deleted successfully"}
