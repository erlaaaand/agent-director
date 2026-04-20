from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.core.entities import Scene, ScriptDocument

logger = logging.getLogger(__name__)

# ── Konstanta threshold ────────────────────────────────────────────────────────
_DURATION_TOLERANCE_SEC: float = 10.0   # toleransi ±10 detik dari target
_MAX_ON_SCREEN_WORDS: int = 8           # batas kata di on_screen_text
_MIN_SCENE_DURATION: float = 4.0        # scene terlalu pendek jika di bawah ini


@dataclass
class ValidationIssue:
    level: str      # "ERROR" | "WARN" | "INFO"
    field: str      # path ke field yang bermasalah
    message: str


@dataclass
class ValidationResult:
    document_id: str
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.level == "ERROR" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.level in ("ERROR", "WARN") for i in self.issues)

    def log_summary(self) -> None:
        if not self.issues:
            logger.info("Validasi OK  doc='%s'", self.document_id)
            return
        for issue in self.issues:
            fn = logger.warning if issue.level in ("ERROR", "WARN") else logger.debug
            fn("Validasi [%s] doc='%s'  field='%s'  %s",
               issue.level, self.document_id, issue.field, issue.message)


def validate_script(script: ScriptDocument) -> ValidationResult:
    """
    Jalankan semua pemeriksaan QA pada satu ScriptDocument.
    Kembalikan ValidationResult berisi daftar isu yang ditemukan.
    """
    result = ValidationResult(document_id=script.document_id)
    _check_duration(script, result)
    _check_on_screen_text(script, result)
    _check_scene_durations(script, result)
    _check_audio_narration(script, result)
    _check_title(script, result)
    result.log_summary()
    return result


# ── Pemeriksa individual ───────────────────────────────────────────────────────

def _check_duration(script: ScriptDocument, result: ValidationResult) -> None:
    """Total durasi scene harus mendekati target_duration_seconds."""
    target = script.production_metadata.target_duration_seconds
    total = sum(s.estimated_duration_sec for s in script.scenes)
    diff = abs(total - target)

    if diff > _DURATION_TOLERANCE_SEC:
        result.issues.append(ValidationIssue(
            level="WARN",
            field="scenes[*].estimated_duration_sec",
            message=(
                f"Total durasi {total:.1f}s jauh dari target {target}s "
                f"(selisih {diff:.1f}s, toleransi ±{_DURATION_TOLERANCE_SEC}s). "
                "Naikkan durasi scene atau tambah scene agar proporsional."
            ),
        ))


def _check_scene_durations(script: ScriptDocument, result: ValidationResult) -> None:
    """Deteksi scene yang terlalu pendek (audio tidak cukup terbaca)."""
    for scene in script.scenes:
        if scene.estimated_duration_sec < _MIN_SCENE_DURATION:
            result.issues.append(ValidationIssue(
                level="WARN",
                field=f"scenes[{scene.scene_number - 1}].estimated_duration_sec",
                message=(
                    f"Scene {scene.scene_number} terlalu pendek "
                    f"({scene.estimated_duration_sec}s < min {_MIN_SCENE_DURATION}s). "
                    "Audio narasi tidak cukup untuk durasi ini."
                ),
            ))


def _check_on_screen_text(script: ScriptDocument, result: ValidationResult) -> None:
    """Cek duplikat dan panjang on_screen_text."""
    seen: dict[str, int] = {}   # teks → scene_number pertama kali muncul

    for scene in script.scenes:
        raw = scene.on_screen_text.strip()

        # ── Duplikat ──────────────────────────────────────────────────────────
        # Normalisasi: lowercase + strip emoji untuk perbandingan
        key = _normalize_for_dedup(raw)
        if key in seen:
            result.issues.append(ValidationIssue(
                level="WARN",
                field=f"scenes[{scene.scene_number - 1}].on_screen_text",
                message=(
                    f"Scene {scene.scene_number} memiliki on_screen_text yang identik "
                    f"dengan Scene {seen[key]}. "
                    "Setiap scene harus punya teks layar yang unik."
                ),
            ))
        else:
            seen[key] = scene.scene_number

        # ── Terlalu panjang ───────────────────────────────────────────────────
        # Hitung kata (abaikan emoji sebagai "kata")
        word_count = _count_words_no_emoji(raw)
        if word_count > _MAX_ON_SCREEN_WORDS:
            result.issues.append(ValidationIssue(
                level="WARN",
                field=f"scenes[{scene.scene_number - 1}].on_screen_text",
                message=(
                    f"Scene {scene.scene_number}: on_screen_text terlalu panjang "
                    f"({word_count} kata, maks {_MAX_ON_SCREEN_WORDS}). "
                    f"Teks: {repr(raw[:60])}"
                ),
            ))


def _check_audio_narration(script: ScriptDocument, result: ValidationResult) -> None:
    """Deteksi narasi yang terlalu pendek per scene."""
    _MIN_WORDS = 15  # minimal kata agar durasi masuk akal
    for scene in script.scenes:
        words = len(scene.audio_narration.split())
        if words < _MIN_WORDS:
            result.issues.append(ValidationIssue(
                level="WARN",
                field=f"scenes[{scene.scene_number - 1}].audio_narration",
                message=(
                    f"Scene {scene.scene_number}: audio_narration hanya {words} kata "
                    f"(disarankan ≥{_MIN_WORDS}). "
                    "Narasi terlalu singkat untuk diisi TTS secara natural."
                ),
            ))


def _check_title(script: ScriptDocument, result: ValidationResult) -> None:
    """Pastikan suggested_title berisi emoji dan tidak terlalu panjang."""
    title = script.distribution_assets.suggested_title
    if len(title) > 75:
        result.issues.append(ValidationIssue(
            level="WARN",
            field="distribution_assets.suggested_title",
            message=f"Judul terlalu panjang ({len(title)} karakter, maks 75). Teks: {repr(title[:75])}",
        ))

    has_emoji = any(ord(c) > 0x2500 for c in title)
    if not has_emoji:
        result.issues.append(ValidationIssue(
            level="INFO",
            field="distribution_assets.suggested_title",
            message=f"Judul tidak mengandung emoji. Disarankan tambahkan emoji untuk CTR. Teks: {repr(title)}",
        ))


# ── Helper ─────────────────────────────────────────────────────────────────────

def _normalize_for_dedup(text: str) -> str:
    """Lowercase + hapus karakter non-alfanumerik untuk perbandingan duplikat."""
    import re
    return re.sub(r"[^\w]", "", text.lower())


def _count_words_no_emoji(text: str) -> int:
    """Hitung kata, abaikan token yang seluruhnya emoji/simbol Unicode."""
    import re
    tokens = text.split()
    word_tokens = [t for t in tokens if re.search(r"[a-zA-Z\u00C0-\u024F\u0400-\u04FF\u4e00-\u9fff]", t)]
    return len(word_tokens)