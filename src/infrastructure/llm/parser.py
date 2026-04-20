from __future__ import annotations

import json
import logging
import re
from typing import Any

from pydantic import ValidationError

from src.core.entities import (
    ProductionMetadata,
    Scene,
    ScriptDistributionAssets,
    ScriptDocument,
)
from src.core.exceptions import LLMGenerationError
from src.infrastructure.llm.sanitizer import (
    sanitize_audio_narration,
    sanitize_on_screen_text,
    translate_leaked_english,
)

logger = logging.getLogger(__name__)


def strip_thinking_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def strip_markdown_fences(text: str) -> str:
    text = re.sub(r"```(?:json)?\s*", "", text)
    return re.sub(r"```", "", text).strip()


def extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return text
    return text[start: end + 1]


def _safe_str(val: Any, default: str = "") -> str:
    return val if (isinstance(val, str) and val.strip()) else default


def _safe_int(val: Any, default: int = 60, lo: int = 5, hi: int = 600) -> int:
    try:
        return max(lo, min(hi, int(val)))
    except (TypeError, ValueError):
        return default


def _safe_float(val: Any, default: float = 5.0, lo: float = 0.5, hi: float = 120.0) -> float:
    try:
        return max(lo, min(hi, float(val)))
    except (TypeError, ValueError):
        return default


def _coerce_production_metadata(raw: Any, fallback_duration: int = 60) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}
    return {
        "target_duration_seconds": _safe_int(
            raw.get("target_duration_seconds"), fallback_duration
        ),
        "platform": _safe_str(raw.get("platform"), "YouTube Shorts / TikTok"),
        "voiceover_style": _safe_str(
            raw.get("voiceover_style"), "Energetic, casual Indonesian"
        ),
        "bgm_mood": _safe_str(raw.get("bgm_mood"), "Upbeat, dynamic"),
    }


def _coerce_distribution_assets(raw: Any, topic: str = "") -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}
    title = _safe_str(
        raw.get("suggested_title"),
        f"Fakta Mengejutkan tentang {topic}! 😱",
    )
    keywords = raw.get("primary_keywords")
    hashtags = raw.get("recommended_hashtags")
    return {
        "suggested_title": title,
        "primary_keywords": keywords if isinstance(keywords, list) else [],
        "recommended_hashtags": hashtags if isinstance(hashtags, list) else [],
    }


def _coerce_scene(raw: Any, idx: int) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    narration = _safe_str(raw.get("audio_narration"), "")
    visual = _safe_str(raw.get("visual_prompt"), "")
    text = _safe_str(raw.get("on_screen_text"), "")
    if not narration and not visual:
        return None
    return {
        "scene_number": _safe_int(raw.get("scene_number"), idx + 1, lo=1, hi=999),
        "estimated_duration_sec": _safe_float(raw.get("estimated_duration_sec"), 5.0),
        "visual_prompt": visual or f"Sinematic shot relevan dengan scene {idx + 1}",
        "audio_narration": narration or "...",
        "on_screen_text": text or f"Scene {idx + 1}",
    }


def _coerce_scenes(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    result = []
    for i, item in enumerate(raw):
        coerced = _coerce_scene(item, i)
        if coerced:
            result.append(coerced)
    return result


def _apply_scene_sanitization(scenes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sanitized = []
    for scene in scenes:
        narration = scene.get("audio_narration", "")
        narration = translate_leaked_english(narration)
        narration = sanitize_audio_narration(narration)

        on_screen = scene.get("on_screen_text", "")
        on_screen = translate_leaked_english(on_screen)
        on_screen = sanitize_on_screen_text(on_screen)

        sanitized.append({**scene, "audio_narration": narration, "on_screen_text": on_screen})
    return sanitized


def parse_script_document(
    content: str,
    model: str,
    document_id: str,
    topic: str,
    fallback_duration: int = 60,
) -> ScriptDocument:
    cleaned = strip_thinking_tags(content)
    cleaned = strip_markdown_fences(cleaned)
    json_str = extract_json_object(cleaned)

    try:
        raw: dict[str, Any] = json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning(
            "JSON parse gagal untuk document_id='%s'. Raw (300 char): %s",
            document_id,
            json_str[:300],
        )
        raise LLMGenerationError(
            model=model,
            reason=f"Output bukan JSON valid (doc={document_id}). Cuplikan: {json_str[:200]}",
        ) from None

    prod_meta = _coerce_production_metadata(
        raw.get("production_metadata"), fallback_duration
    )
    dist_assets = _coerce_distribution_assets(raw.get("distribution_assets"), topic)
    scenes = _coerce_scenes(raw.get("scenes"))
    scenes = _apply_scene_sanitization(scenes)

    if not scenes:
        raise LLMGenerationError(
            model=model,
            reason=(
                f"LLM tidak menghasilkan scene apapun untuk document_id='{document_id}'. "
                "Cek prompt atau coba model yang lebih besar."
            ),
        )

    payload = {
        "document_id": document_id,
        "topic": topic,
        "production_metadata": prod_meta,
        "distribution_assets": dist_assets,
        "scenes": scenes,
    }

    try:
        return ScriptDocument.model_validate(payload)
    except ValidationError as exc:
        raise LLMGenerationError(
            model=model,
            reason=f"Validasi ScriptDocument gagal (doc={document_id}): {exc}",
        ) from exc