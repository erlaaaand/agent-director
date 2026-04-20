from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator


class VideoParameters(BaseModel):
    platform: str = "YouTube Shorts / TikTok"
    target_duration_seconds: Annotated[int, Field(ge=5, le=600)] = 60
    pacing: str = "Medium-paced"
    language: str = "Indonesian"
    model_config = {"frozen": True}


class CreativeBrief(BaseModel):
    target_audience: str = ""
    video_parameters: VideoParameters = Field(default_factory=VideoParameters)
    recommended_angles: list[str] = Field(default_factory=list)
    model_config = {"frozen": True}


class ContextualIntelligence(BaseModel):
    event_summary: str = ""
    key_entities: list[dict[str, Any]] = Field(default_factory=list)
    sentiment_analysis: dict[str, str] = Field(default_factory=dict)
    verified_facts: list[str] = Field(default_factory=list)
    model_config = {"frozen": True}


class TrendIdentity(BaseModel):
    topic: str
    category: str = "General"
    region: str = "ID"
    metrics: dict[str, Any] = Field(default_factory=dict)
    model_config = {"frozen": True}


class InputDistributionAssets(BaseModel):
    primary_keywords: list[str] = Field(default_factory=list)
    recommended_hashtags: list[str] = Field(default_factory=list)
    model_config = {"frozen": True}


class CreativeDocument(BaseModel):
    document_id: str
    pipeline_routing: dict[str, Any] = Field(default_factory=dict)
    trend_identity: TrendIdentity
    contextual_intelligence: ContextualIntelligence = Field(
        default_factory=ContextualIntelligence
    )
    creative_brief: CreativeBrief = Field(default_factory=CreativeBrief)
    distribution_assets: InputDistributionAssets = Field(
        default_factory=InputDistributionAssets
    )
    model_config = {"frozen": True}


class CreativeDocumentBatch(BaseModel):
    region: str
    date: str
    documents: list[CreativeDocument] = Field(default_factory=list)

    @field_validator("region", mode="before")
    @classmethod
    def _upper(cls, v: str) -> str:
        return str(v).strip().upper()

    model_config = {"frozen": True}


class ProductionMetadata(BaseModel):
    target_duration_seconds: Annotated[int, Field(ge=5, le=600)] = 60
    platform: str = "YouTube Shorts / TikTok"
    voiceover_style: Annotated[str, Field(min_length=1)]
    bgm_mood: Annotated[str, Field(min_length=1)]
    model_config = {"frozen": True}


class ScriptDistributionAssets(BaseModel):
    suggested_title: Annotated[str, Field(min_length=1)]
    primary_keywords: list[str] = Field(default_factory=list)
    recommended_hashtags: list[str] = Field(default_factory=list)
    model_config = {"frozen": True}


class Scene(BaseModel):
    scene_number: Annotated[int, Field(ge=1)]
    estimated_duration_sec: Annotated[float, Field(ge=0.5, le=120.0)]
    visual_prompt: Annotated[str, Field(min_length=1)]
    audio_narration: Annotated[str, Field(min_length=1)]
    on_screen_text: Annotated[str, Field(min_length=1)]
    model_config = {"frozen": True}


class ScriptDocument(BaseModel):
    document_id: str
    topic: str
    production_metadata: ProductionMetadata
    distribution_assets: ScriptDistributionAssets
    scenes: Annotated[list[Scene], Field(min_length=1)]
    model_config = {"frozen": True}


class ScriptDocumentBatch(BaseModel):
    region: str
    date: str
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    scripts: list[ScriptDocument] = Field(default_factory=list)

    @field_validator("region", mode="before")
    @classmethod
    def _upper(cls, v: str) -> str:
        return str(v).strip().upper()

    model_config = {"frozen": True}
