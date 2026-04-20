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


# ─────────────────────────────────────────────────────────────────────────────
# Kamus terjemahan — urutan PENTING: frasa panjang dulu, kata tunggal belakangan
# ─────────────────────────────────────────────────────────────────────────────
_ENGLISH_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    # ── Frasa CTA multi-kata ─────────────────────────────────────────────────
    (re.compile(r"\bLike\s*[,&]\s*[Cc]omment\s*[,&and\s]+[Ff]ollow\b", re.IGNORECASE), "Sukai, komentari, dan ikuti"),
    (re.compile(r"\bLike\s*[,&]\s*[Ss]ubscribe\b", re.IGNORECASE), "Sukai dan berlangganan"),
    (re.compile(r"\bLike\s*&\s*[Ff]ollow\b", re.IGNORECASE), "Sukai & Ikuti"),
    (re.compile(r"\bLike\s+and\s+[Ff]ollow\b", re.IGNORECASE), "Sukai dan Ikuti"),
    (re.compile(r"\bLike\s+and\s+[Ss]ubscribe\b", re.IGNORECASE), "Sukai dan Berlangganan"),
    (re.compile(r"\bStay\s+tuned\b", re.IGNORECASE), "Pantau terus"),
    (re.compile(r"\bDon[\'']?t\s+miss\b", re.IGNORECASE), "Jangan sampai ketinggalan"),
    (re.compile(r"\bDon[\'']?t\s+forget\b", re.IGNORECASE), "Jangan lupa"),
    (re.compile(r"\bfor\s+more\b", re.IGNORECASE), "untuk info lebih lanjut"),
    (re.compile(r"\band\s+more\b", re.IGNORECASE), "dan lainnya"),
    (re.compile(r"\bFind\s+out\s+more\b", re.IGNORECASE), "Pelajari lebih lanjut"),
    (re.compile(r"\bFind\s+out\b", re.IGNORECASE), "Cari tahu"),
    (re.compile(r"\bWhat[\'']?s\s+next\b", re.IGNORECASE), "Apa Selanjutnya"),
    (re.compile(r"\bWhat[\'']?s\s+happening\b", re.IGNORECASE), "Apa yang terjadi"),
    (re.compile(r"\bHow\s+will\b", re.IGNORECASE), "Bagaimana"),
    (re.compile(r"\bCome\s+on\b", re.IGNORECASE), "Ayo"),
    (re.compile(r"\bCheck\s+it\s+out\b", re.IGNORECASE), "Cek sekarang"),
    (re.compile(r"\bCheck\s+out\b", re.IGNORECASE), "Lihat"),
    (re.compile(r"\bWatch\s+now\b", re.IGNORECASE), "Tonton sekarang"),
    (re.compile(r"\bWatch\s+more\b", re.IGNORECASE), "Tonton selengkapnya"),
    (re.compile(r"\bLearn\s+more\b", re.IGNORECASE), "Pelajari lebih lanjut"),
    (re.compile(r"\bClick\s+here\b", re.IGNORECASE), "Klik di sini"),
    (re.compile(r"\bTap\s+below\b", re.IGNORECASE), "Tekan tombol di bawah"),
    (re.compile(r"\bKeep\s+watching\b", re.IGNORECASE), "Terus nonton"),
    (re.compile(r"\bThink\s+about\s+it\b", re.IGNORECASE), "Pikirkan"),
    (re.compile(r"\bNo\s+doubt\b", re.IGNORECASE), "Tidak diragukan lagi"),
    (re.compile(r"\bOf\s+course\b", re.IGNORECASE), "Tentu saja"),
    (re.compile(r"\bRight\s+now\b", re.IGNORECASE), "Sekarang juga"),
    (re.compile(r"\bSo\s+far\b", re.IGNORECASE), "Sejauh ini"),
    (re.compile(r"\bAs\s+well\b", re.IGNORECASE), "juga"),
    (re.compile(r"\bIn\s+fact\b", re.IGNORECASE), "Faktanya"),
    (re.compile(r"\bIn\s+the\s+end\b", re.IGNORECASE), "Pada akhirnya"),
    (re.compile(r"\bAt\s+the\s+same\s+time\b", re.IGNORECASE), "Pada saat yang sama"),
    (re.compile(r"\bOne\s+more\s+time\b", re.IGNORECASE), "Sekali lagi"),
    (re.compile(r"\bAll\s+of\s+a\s+sudden\b", re.IGNORECASE), "Tiba-tiba"),
    (re.compile(r"\bTime\s+will\s+tell\b", re.IGNORECASE), "Waktu yang akan membuktikan"),
    (re.compile(r"\bGame\s+over\b", re.IGNORECASE), "Permainan berakhir"),
    (re.compile(r"\bGame\s+changer\b", re.IGNORECASE), "Pengubah permainan"),
    (re.compile(r"\bLevel\s+up\b", re.IGNORECASE), "Naik level"),
    (re.compile(r"\bBig\s+deal\b", re.IGNORECASE), "Hal besar"),
    (re.compile(r"\bTop\s+notch\b", re.IGNORECASE), "Kelas atas"),
    (re.compile(r"\bWorld\s+class\b", re.IGNORECASE), "Kelas dunia"),
    (re.compile(r"\bBreaking\s+news\b", re.IGNORECASE), "Berita terkini"),
    (re.compile(r"\bBreaking\s+point\b", re.IGNORECASE), "Titik kritis"),
    (re.compile(r"\bFull\s+time\b", re.IGNORECASE), "Penuh waktu"),
    (re.compile(r"\bHalf\s+time\b", re.IGNORECASE), "Babak pertama"),
    (re.compile(r"\bExtra\s+time\b", re.IGNORECASE), "Perpanjangan waktu"),
    (re.compile(r"\bPenalty\s+shoot[-\s]?out\b", re.IGNORECASE), "Adu penalti"),
    (re.compile(r"\bClean\s+sheet\b", re.IGNORECASE), "Tanpa kebobolan"),
    (re.compile(r"\bHat\s+trick\b", re.IGNORECASE), "Hat-trick"),
    (re.compile(r"\bOff\s+side\b", re.IGNORECASE), "Offside"),
    (re.compile(r"\bQuarter[-\s]?[Ff]inal\b", re.IGNORECASE), "Perempat Final"),
    (re.compile(r"\bSemi[-\s]?[Ff]inal\b", re.IGNORECASE), "Semifinal"),
    (re.compile(r"\bKnock\s*out\b", re.IGNORECASE), "Gugur"),
    (re.compile(r"\bGroup\s+[Ss]tage\b", re.IGNORECASE), "Babak Grup"),
    (re.compile(r"\bRound\s+of\s+\d+\b", re.IGNORECASE), "Babak 16 besar"),
    (re.compile(r"\bHome\s+team\b", re.IGNORECASE), "Tim tuan rumah"),
    (re.compile(r"\bAway\s+team\b", re.IGNORECASE), "Tim tamu"),
    (re.compile(r"\bTop\s+scorer\b", re.IGNORECASE), "Top scorer"),
    (re.compile(r"\bHighlight\s+reel\b", re.IGNORECASE), "Cuplikan terbaik"),

    # ── Kata tunggal — urutan paling akhir ───────────────────────────────────
    (re.compile(r"\bfollow\b", re.IGNORECASE), "ikuti"),
    (re.compile(r"\bFollow\b"), "Ikuti"),
    (re.compile(r"\bsubscribe\b", re.IGNORECASE), "ikuti"),
    (re.compile(r"\bSubscribe\b"), "Berlangganan"),
    (re.compile(r"\bshare\b", re.IGNORECASE), "bagikan"),
    (re.compile(r"\bShare\b"), "Bagikan"),
    (re.compile(r"\bcomment\b", re.IGNORECASE), "komen"),
    (re.compile(r"\bComment\b"), "Komen"),
    (re.compile(r"\blike\b(?!\s+dan\b)(?!\s+ini\b)(?!\s+itu\b)(?!\s+yang\b)", re.IGNORECASE), "sukai"),
    (re.compile(r"\bguys\b", re.IGNORECASE), "teman-teman"),
    (re.compile(r"\bGuy\b", re.IGNORECASE), "orang"),
    (re.compile(r"\bwatch\b", re.IGNORECASE), "tonton"),
    (re.compile(r"\bWin\b(?!\w)"), "Menang"),
    (re.compile(r"\bLose\b(?!\w)"), "Kalah"),
    (re.compile(r"\bScore\b(?!\w)"), "Skor"),
    (re.compile(r"\bGoal\b(?!\w)"), "Gol"),
    (re.compile(r"\bMatch\b(?!\w)"), "Pertandingan"),
    (re.compile(r"\bTeam\b(?!\w)"), "Tim"),
    (re.compile(r"\bPlayer\b(?!\w)"), "Pemain"),
    (re.compile(r"\bCoach\b(?!\w)"), "Pelatih"),
    (re.compile(r"\bManager\b(?!\w)"), "Manajer"),
    (re.compile(r"\bClub\b(?!\w)"), "Klub"),
    (re.compile(r"\bLeague\b(?!\w)"), "Liga"),
    (re.compile(r"\bChampion\b(?!\w)"), "Juara"),
    (re.compile(r"\bChampions\b(?!\w)"), "Juara"),
    (re.compile(r"\bDefeat\b(?!\w)"), "Kekalahan"),
    (re.compile(r"\bVictory\b(?!\w)"), "Kemenangan"),
    (re.compile(r"\bStadium\b(?!\w)"), "Stadion"),
    (re.compile(r"\bFan\b(?!\w)"), "Penggemar"),
    (re.compile(r"\bFans\b(?!\w)"), "Para penggemar"),
    (re.compile(r"\bBound\b(?!\w)"), "Melaju"),
    (re.compile(r"\bNext\b(?!\w)"), "Berikutnya"),
    (re.compile(r"\bNow\b(?!\w)"), "Sekarang"),
    (re.compile(r"\bMore\b(?!\w)"), "Lebih banyak"),
    (re.compile(r"\bUpdate\b(?!\w)"), "Pembaruan"),
    (re.compile(r"\bUpdates\b(?!\w)"), "Informasi terbaru"),
    (re.compile(r"\bNews\b(?!\w)"), "Berita"),
    (re.compile(r"\bInfo\b(?!\w)"), "Info"),
    (re.compile(r"\bContent\b(?!\w)"), "Konten"),
    (re.compile(r"\bTrend\b(?!\w)"), "Tren"),
    (re.compile(r"\bViral\b(?!\w)"), "Viral"),
    (re.compile(r"\bStar\b(?!\w)"), "Bintang"),
    (re.compile(r"\bPerformance\b(?!\w)"), "Performa"),
    (re.compile(r"\bMoment\b(?!\w)"), "Momen"),
    (re.compile(r"\bMoments\b(?!\w)"), "Momen"),
    (re.compile(r"\bFinal\b(?!\w)"), "Final"),
    (re.compile(r"\bAdvice\b", re.IGNORECASE), "Saran"),
    (re.compile(r"\bDominant\s+Win\b", re.IGNORECASE), "Kemenangan Telak"),
    (re.compile(r"\bDominant\s+Performance\b", re.IGNORECASE), "Performa Dominan"),
    (re.compile(r"\bDominant\b", re.IGNORECASE), "Dominan"),
    (re.compile(r"\bWins?\b", re.IGNORECASE), "Menang"),
    (re.compile(r"\bWinning\b", re.IGNORECASE), "Kemenangan"),
    (re.compile(r"\bWinner\b", re.IGNORECASE), "Pemenang"),
    (re.compile(r"\bWon\b(?!\w)"), "Menang"),
    (re.compile(r"\bLosing\b", re.IGNORECASE), "Kekalahan"),
    (re.compile(r"\bLost\b(?!\w)"), "Kalah"),
    (re.compile(r"\bCrushing\b", re.IGNORECASE), "Telak"),
    (re.compile(r"\bCrush\b(?!\w)"), "Hancurkan"),
    (re.compile(r"\bCome\s+back\b", re.IGNORECASE), "Kembali"),
    (re.compile(r"\bComeback\b", re.IGNORECASE), "Kebangkitan"),
    (re.compile(r"\bShocking\b", re.IGNORECASE), "Mengejutkan"),
    (re.compile(r"\bSurprising\b", re.IGNORECASE), "Mengejutkan"),
    (re.compile(r"\bAmazing\b", re.IGNORECASE), "Luar biasa"),
    (re.compile(r"\bIncredible\b", re.IGNORECASE), "Luar biasa"),
    (re.compile(r"\bUnbelievable\b", re.IGNORECASE), "Tidak percaya"),
    (re.compile(r"\bEpic\b", re.IGNORECASE), "Epik"),
    (re.compile(r"\bLegend\b(?!\w)"), "Legenda"),
    (re.compile(r"\bLegendary\b", re.IGNORECASE), "Legendaris"),
    (re.compile(r"\bReturn\b(?!\w)"), "Kembali"),
    (re.compile(r"\bReturns\b(?!\w)"), "Kembali"),
    (re.compile(r"\bTransfer\b(?!\w)"), "Transfer"),
    (re.compile(r"\bReaction\b(?!\w)"), "Reaksi"),
    (re.compile(r"\bDefeated\b", re.IGNORECASE), "Dikalahkan"),
    (re.compile(r"\bDefeats\b(?!\w)"), "Mengalahkan"),
    (re.compile(r"\bCrashed\b", re.IGNORECASE), "Hancur"),
    (re.compile(r"\bStruggle\b", re.IGNORECASE), "Berjuang"),
    (re.compile(r"\bStruggling\b", re.IGNORECASE), "Kesulitan"),
    (re.compile(r"\bQualified\b", re.IGNORECASE), "Lolos"),
    (re.compile(r"\bQualifies\b", re.IGNORECASE), "Lolos"),
    (re.compile(r"\bAdvances\b(?!\w)"), "Melaju"),
    (re.compile(r"\bAdvanced\b(?!\w)"), "Melaju"),
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
    # Hapus newline dan whitespace berlebih dulu agar regex bisa match
    result = text.replace("\n", " ").replace("\r", "")
    result = translate_leaked_english(result)
    result = _HASHTAG_PATTERN.sub("", result)
    return _clean(result)


def sanitize_visual_prompt(text: str) -> str:
    result = _strip_emoji(text)
    return _clean(result)


def sanitize_plain_text(text: str) -> str:
    result = _strip_emoji(text)
    result = _HASHTAG_PATTERN.sub("", result)
    return _clean(result)


def sanitize_title(text: str) -> str:
    """Untuk suggested_title: terjemahkan kata Inggris + hapus hashtag, pertahankan emoji."""
    result = text.replace("\n", " ").replace("\r", "")
    result = translate_leaked_english(result)
    result = _HASHTAG_PATTERN.sub("", result)
    return _clean(result)


def sanitize_script_document(script: ScriptDocument) -> ScriptDocument:
    # Gunakan sanitize_title agar judul juga diterjemahkan, bukan hanya strip emoji
    clean_title = sanitize_title(script.distribution_assets.suggested_title)
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