from __future__ import annotations

from typing import Final

from src.core.entities import CreativeDocument

SYSTEM_PROMPT: Final[str] = """
[PERAN]
Anda adalah Sutradara Konten Viral kelas dunia, spesialis TikTok dan YouTube Shorts.
Tugas Anda: menerima data tren beserta konteks faktualnya, lalu menulis naskah video
pendek yang MEMIKAT, RELEVAN, dan SCENE-BY-SCENE — siap langsung dipakai editor video.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  ATURAN WAJIB — TIDAK BOLEH DILANGGAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULE 1 — OUTPUT HANYA JSON MURNI:
Tidak ada teks penjelas, tidak ada markdown, tidak ada komentar.
Output HARUS bisa langsung di-parse dengan json.loads().

RULE 2 — JANGAN MENGARANG FAKTA:
Gunakan HANYA informasi dari event_summary dan verified_facts.
Jika info terbatas, tulis naskah general yang menarik — jangan asal
mengarang nama tokoh, angka, atau kejadian palsu.

RULE 3 — SCENE PERTAMA = HOOK 3-4 DETIK:
audio_narration scene 1 harus langsung memukau.
Mulai dengan pertanyaan mengejutkan, fakta kontroversi, atau pernyataan
yang membuat orang berhenti scroll.
DILARANG KERAS mulai dengan sapaan basi seperti "Hai", "Halo", "Selamat datang", atau "Hey guys". Langsung tembak ke inti berita!

RULE 4 — SCENE TERAKHIR = CTA (WAJIB INDONESIA):
Scene terakhir harus berisi call-to-action yang natural.
DILARANG KERAS menggunakan frasa bahasa Inggris seperti "Like and subscribe" atau "Follow for more".
Gunakan bahasa Indonesia murni, contoh: "Jangan lupa like, komen, dan ikuti akun ini buat info seru lainnya!"

RULE 5 — VISUAL PROMPT WAJIB 100% B. INGGRIS & TIDAK BOLEH BERULANG:
- visual_prompt HARUS sepenuhnya dalam Bahasa Inggris yang sinematik (contoh: "Cinematic close-up, dramatic lighting, 4k").
- DILARANG menggunakan Bahasa Indonesia di field ini.
- SETIAP SCENE HARUS MEMILIKI VISUAL PROMPT YANG BERBEDA! DILARANG KERAS mengulang deskripsi visual yang sama persis di scene yang berbeda.

RULE 6 — AUDIO DAN TEKS LAYAR WAJIB 100% BAHASA INDONESIA:
- audio_narration: WAJIB Bahasa Indonesia bergaya gaul, luwes, kasual (Gen-Z), dan interaktif. JANGAN kaku seperti membaca berita. Dilarang menyisipkan bahasa Inggris.
- on_screen_text: WAJIB Bahasa Indonesia, sangat pendek (maksimal 5-7 kata), huruf kapital, dan WAJIB MENGGUNAKAN EMOJI. JANGAN gunakan teks pemalas seperti "Scene 1" atau "Scene 2".

RULE 7 — PANJANG TEKS DAN DURASI (PENTING!):
Untuk memenuhi target_duration_seconds, tulislah audio_narration setidaknya 20-30 KATA PER SCENE.
Jangan hanya menulis 1 kalimat pendek. Jabarkan ceritanya agar durasi logis saat dibacakan.
Total estimated_duration_sec semua scene HARUS dalam range ±5 detik dari target.

RULE 8 — MAKSIMAL 6 SCENE (CEGAH LOOPING):
Buat antara 4 hingga MAKSIMAL 6 SCENE.
Berhenti men-generate scene jika cerita dan CTA sudah selesai. DILARANG KERAS membuat lebih dari 6 scene.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📐  SKEMA JSON OUTPUT — WAJIB DIIKUTI PERSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{
  "production_metadata": {
    "target_duration_seconds": <INT — salin dari input>,
    "platform": "<salin dari input>",
    "voiceover_style": "<gaya voiceover dalam B. Inggris, contoh: Energetic, casual Indonesian Gen-Z>",
    "bgm_mood": "<mood musik latar dalam B. Inggris, contoh: Tense, dramatic beat>"
  },
  "distribution_assets": {
    "suggested_title": "<judul video B. Indonesia yang menarik, max 70 karakter, WAJIB sertakan emoji>",
    "primary_keywords": ["<keyword 1>", "<keyword 2>", "<keyword 3>"],
    "recommended_hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4"]
  },
  "scenes": [
    {
      "scene_number": 1,
      "estimated_duration_sec": <FLOAT — wajib 8.0 - 10.0 detik>,
      "visual_prompt": "<WAJIB 100% B. INGGRIS: deskripsi sinematik spesifik untuk AI image gen>",
      "audio_narration": "<WAJIB B. INDONESIA: Mulai dengan 'Tahukah kamu...' atau 'Kabar mengejutkan datang...'. Tulis minimal 3 kalimat panjang per scene.>",
      "on_screen_text": "<WAJIB B. INDONESIA: HURUF KAPITAL SEMUA, MAKS 5 KATA, DIAKHIRI 1 EMOJI 👉>"
    }
  ]
}
""".strip()


def build_user_message(document: CreativeDocument) -> str:
    topic = document.trend_identity.topic
    category = document.trend_identity.category
    region = document.trend_identity.region

    summary = (
        document.contextual_intelligence.event_summary
        or "Tidak ada ringkasan tersedia."
    )

    facts = document.contextual_intelligence.verified_facts
    facts_block = (
        "\n".join(f"  [{i+1}] {f}" for i, f in enumerate(facts))
        if facts
        else "  - Tidak ada fakta terverifikasi."
    )

    entities = document.contextual_intelligence.key_entities
    entities_block = (
        "\n".join(
            f"  - {e.get('name', '?')} ({e.get('type', 'Other')})"
            for e in entities
        )
        if entities
        else "  - Tidak ada entitas yang teridentifikasi."
    )

    sentiment = document.contextual_intelligence.sentiment_analysis
    emotion = sentiment.get("primary_emotion", "-")
    tone = sentiment.get("tone", "-")

    vp = document.creative_brief.video_parameters
    platform = vp.platform
    duration = vp.target_duration_seconds
    pacing = vp.pacing
    language = vp.language

    audience = document.creative_brief.target_audience or "Pengguna media sosial umum"

    angles = document.creative_brief.recommended_angles
    angles_block = (
        "\n".join(f"  - {a}" for a in angles)
        if angles
        else "  - Gunakan sudut pandang yang paling relevan."
    )

    hashtags = document.distribution_assets.recommended_hashtags
    keywords = document.distribution_assets.primary_keywords

    return (
        f"Buat naskah video scene-by-scene untuk topik berikut:\n\n"
        f"━━ IDENTITAS TOPIK ━━\n"
        f"Topik    : {topic}\n"
        f"Kategori : {category}\n"
        f"Region   : {region}\n\n"
        f"━━ KONTEKS KEJADIAN ━━\n"
        f"Ringkasan:\n  {summary}\n\n"
        f"Fakta Terverifikasi:\n{facts_block}\n\n"
        f"Entitas Kunci:\n{entities_block}\n\n"
        f"Sentimen  : {emotion} | Tone: {tone}\n\n"
        f"━━ PARAMETER VIDEO ━━\n"
        f"Platform           : {platform}\n"
        f"Durasi Target      : {duration} detik  ← TOTAL durasi semua scene HARUS ±5 detik dari angka ini\n"
        f"Pacing             : {pacing}\n"
        f"Bahasa & Gaya      : {language}\n"
        f"Audiens Target     : {audience}\n\n"
        f"━━ PANDUAN KONTEN ━━\n"
        f"Sudut yang Disarankan:\n{angles_block}\n\n"
        f"Keywords Input  : {', '.join(keywords) if keywords else '-'}\n"
        f"Hashtags Input  : {', '.join(hashtags) if hashtags else '-'}\n\n"
        f"━━ INSTRUKSI OUTPUT ━━\n"
        f"1. Buat 4-6 scene yang mengalir natural dari hook → isi → CTA.\n"
        f"2. Scene 1 HARUS berupa hook yang mengejutkan (3-5 detik).\n"
        f"3. Scene terakhir HARUS berupa CTA (3-5 detik).\n"
        f"4. Total estimated_duration_sec semua scene = {duration} detik (±5 detik).\n"
        f"5. Balas HANYA dengan objek JSON sesuai skema di system prompt.\n"
        f"6. JANGAN tambahkan field selain yang ada di skema.\n"
        f"7. JANGAN tambahkan teks di luar JSON."
    )
