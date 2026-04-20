from __future__ import annotations

import re
import unicodedata

from src.core.entities import ScriptDocument, Scene, ProductionMetadata, ScriptDistributionAssets

_HASHTAG_PATTERN = re.compile(r"#\S+", flags=re.UNICODE)
_MULTI_SPACE_PATTERN = re.compile(r" {2,}")


def _is_emoji(char: str) -> bool:
    cp = ord(char)
    if (
        0x1F600 <= cp <= 0x1F64F
        or 0x1F300 <= cp <= 0x1F5FF
        or 0x1F680 <= cp <= 0x1F6FF
        or 0x1F1E0 <= cp <= 0x1F1FF
        or 0x1F900 <= cp <= 0x1F9FF
        or 0x1FA00 <= cp <= 0x1FA6F
        or 0x1FA70 <= cp <= 0x1FAFF
        or 0x2600 <= cp <= 0x26FF
        or 0x2700 <= cp <= 0x27BF
        or 0x2300 <= cp <= 0x23FF
        or 0x2B50 <= cp <= 0x2B55
        or 0x25A0 <= cp <= 0x25FF
        or 0x2400 <= cp <= 0x243F
        or 0x1F004 <= cp <= 0x1F0CF
        or 0x1F170 <= cp <= 0x1F171
        or 0x1F17E <= cp <= 0x1F17F
        or 0x1F18E <= cp <= 0x1F18E
        or 0x1F191 <= cp <= 0x1F19A
        or 0x1F1E6 <= cp <= 0x1F1FF
        or 0x1F201 <= cp <= 0x1F202
        or 0x1F21A <= cp <= 0x1F21A
        or 0x1F22F <= cp <= 0x1F22F
        or 0x1F232 <= cp <= 0x1F23A
        or 0x1F250 <= cp <= 0x1F251
        or cp == 0x200D
        or cp == 0xFE0F
        or cp == 0xFE0E
        or cp == 0x20E3
        or 0xE0020 <= cp <= 0xE007F
        or 0x1F3FB <= cp <= 0x1F3FF
    ):
        return True
    try:
        name = unicodedata.name(char, "")
        cat = unicodedata.category(char)
        if "EMOJI" in name or "SYMBOL" in name:
            return True
        if cat in ("So", "Mn") and cp > 0x2000:
            return True
    except (TypeError, ValueError):
        pass
    return False


def _strip_emoji(text: str) -> str:
    result: list[str] = []
    i = 0
    chars = list(text)
    while i < len(chars):
        ch = chars[i]
        cp = ord(ch)
        if cp in (0x200D, 0xFE0F, 0xFE0E, 0x20E3):
            i += 1
            continue
        if _is_emoji(ch):
            i += 1
            while i < len(chars) and ord(chars[i]) in (0x200D, 0xFE0F, 0xFE0E, 0x20E3):
                i += 1
            if i < len(chars) and _is_emoji(chars[i]):
                i += 1
            continue
        result.append(ch)
        i += 1
    return "".join(result)


_ENGLISH_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bLike\s*&\s*Follow\b", re.IGNORECASE), "Sukai & Ikuti"),
    (re.compile(r"\bLike\s+and\s+Follow\b", re.IGNORECASE), "Sukai dan Ikuti"),
    (re.compile(r"\bFollow\b", re.IGNORECASE), "Ikuti"),
    (re.compile(r"\bSubscribe\b", re.IGNORECASE), "Ikuti"),
    (re.compile(r"\bShare\b", re.IGNORECASE), "Bagikan"),
    (re.compile(r"\bComment\b", re.IGNORECASE), "Komen"),
    (re.compile(r"\bGuys\b", re.IGNORECASE), "Teman-teman"),
]


def _clean(text: str) -> str:
    result = _MULTI_SPACE_PATTERN.sub(" ", text)
    return result.strip()


def translate_leaked_english(text: str) -> str:
    result = text
    for pattern, replacement in _ENGLISH_REPLACEMENTS:
        result = pattern.sub(replacement, result)
    return result


def sanitize_audio_narration(text: str) -> str:
    result = translate_leaked_english(text)
    result = _strip_emoji(result)
    result = _HASHTAG_PATTERN.sub("", result)
    return _clean(result)


def sanitize_on_screen_text(text: str) -> str:
    result = translate_leaked_english(text)
    result = _HASHTAG_PATTERN.sub("", result)
    return _clean(result)


def sanitize_visual_prompt(text: str) -> str:
    result = _strip_emoji(text)
    return _clean(result)


def sanitize_plain_text(text: str) -> str:
    result = _strip_emoji(text)
    result = _HASHTAG_PATTERN.sub("", result)
    return _clean(result)


def sanitize_script_document(script: ScriptDocument) -> ScriptDocument:
    clean_title = sanitize_plain_text(script.distribution_assets.suggested_title)
    clean_keywords = [sanitize_plain_text(k) for k in script.distribution_assets.primary_keywords]
    clean_hashtags = [tag for tag in script.distribution_assets.recommended_hashtags if tag.strip()]

    clean_dist = ScriptDistributionAssets(
        suggested_title=clean_title or script.distribution_assets.suggested_title,
        primary_keywords=clean_keywords,
        recommended_hashtags=clean_hashtags,
    )

    clean_voiceover = sanitize_plain_text(script.production_metadata.voiceover_style)
    clean_bgm = sanitize_plain_text(script.production_metadata.bgm_mood)
    clean_platform = sanitize_plain_text(script.production_metadata.platform)

    clean_meta = ProductionMetadata(
        target_duration_seconds=script.production_metadata.target_duration_seconds,
        platform=clean_platform or script.production_metadata.platform,
        voiceover_style=clean_voiceover or script.production_metadata.voiceover_style,
        bgm_mood=clean_bgm or script.production_metadata.bgm_mood,
    )

    clean_scenes: list[Scene] = []
    for scene in script.scenes:
        clean_narration = sanitize_audio_narration(scene.audio_narration)
        clean_on_screen = sanitize_on_screen_text(scene.on_screen_text)
        clean_visual = sanitize_visual_prompt(scene.visual_prompt)

        clean_scenes.append(
            Scene(
                scene_number=scene.scene_number,
                estimated_duration_sec=scene.estimated_duration_sec,
                visual_prompt=clean_visual or scene.visual_prompt,
                audio_narration=clean_narration or scene.audio_narration,
                on_screen_text=clean_on_screen or scene.on_screen_text,
            )
        )

    return ScriptDocument(
        document_id=script.document_id,
        topic=script.topic,
        production_metadata=clean_meta,
        distribution_assets=clean_dist,
        scenes=clean_scenes,
    )