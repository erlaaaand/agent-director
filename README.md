# agent_director

Bagian kedua dari pipeline otomatisasi konten. Membaca output JSON dari `agent_market_intelligence`, lalu menggunakan LLM lokal (Ollama) untuk menulis naskah video pendek (TikTok / YouTube Shorts) lengkap dengan arahan visual.

---

## Alur Pipeline Lengkap

```
agent_market_intelligence
        │
        │  data/01_briefs/creative_docs_*.json
        ▼
  agent_director
        │
        │  data/output/scripts_ID_2026-xx-xx_*.json
        ▼
  agent_creative  (tahap berikutnya)
```

---

## Struktur Folder

```
agent_director/
├── .env.example
├── .env                   ← dibuat dari .env.example (jangan di-commit)
├── config.py
├── main.py
├── requirements.txt
├── data/
│   ├── input/             ← taruh file JSON dari agent_market_intelligence di sini
│   │   └── _processed/    ← file yang sudah diproses dipindah ke sini otomatis
│   └── output/            ← hasil skrip JSON tersimpan di sini
└── src/
    ├── core/
    │   ├── entities.py
    │   ├── exceptions.py
    │   └── ports.py
    ├── application/
    │   └── director_use_case.py
    ├── infrastructure/
    │   ├── local_storage.py
    │   └── llm/
    │       ├── ollama_adapter.py
    │       ├── parser.py
    │       └── prompts.py
    └── interfaces/
        ├── cli.py
        └── cli_components/
            ├── display.py
            └── theme.py
```

---

## Instalasi

```bash
# 1. Buat virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Salin dan isi file environment
cp .env.example .env
```

---

## Konfigurasi `.env`

| Key | Default | Keterangan |
|---|---|---|
| `INPUT_DATA_PATH` | `data/input` | Folder tempat file JSON input dibaca |
| `OUTPUT_DATA_PATH` | `data/output` | Folder tempat hasil skrip disimpan |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL server Ollama |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Model Ollama yang digunakan |
| `OLLAMA_TIMEOUT` | `180.0` | Timeout HTTP ke Ollama (detik) |
| `OLLAMA_RETRIES` | `2` | Jumlah retry jika Ollama gagal |
| `LOG_LEVEL` | `INFO` | Level logging Python |

---

## Cara Menjalankan

```bash
# Pastikan Ollama berjalan
ollama serve

# Pastikan model sudah di-pull
ollama pull qwen2.5:7b

# Taruh file input (dari agent_market_intelligence) ke data/input/
# lalu jalankan:
python main.py
```

---

## Format Input (dari agent_market_intelligence)

File JSON di `data/input/` harus mengikuti skema `CreativeDocumentBatch`:

```json
{
  "region": "ID",
  "date": "2026-04-20",
  "documents": [
    {
      "document_id": "trend_abc123_20260420",
      "trend_identity": {
        "topic": "Nama Topik",
        "category": "Sports / Football",
        "region": "ID"
      },
      "contextual_intelligence": {
        "event_summary": "Ringkasan kejadian nyata...",
        "verified_facts": ["Fakta 1", "Fakta 2"]
      },
      "creative_brief": {
        "target_audience": "Pengguna media sosial Indonesia 18-35 tahun",
        "video_parameters": {
          "platform": "YouTube Shorts / TikTok",
          "target_duration_seconds": 60,
          "pacing": "Fast-paced",
          "language": "Indonesian (Gaya bahasa santai/gaul)"
        },
        "recommended_angles": ["Sudut konten 1", "Sudut konten 2"]
      },
      "distribution_assets": {
        "primary_keywords": ["keyword 1"],
        "recommended_hashtags": ["#hashtag1"]
      }
    }
  ]
}
```

---

## Format Output

File JSON hasil tersimpan di `data/output/scripts_<REGION>_<DATE>_<TS>.json`:

```json
{
  "region": "ID",
  "date": "2026-04-20",
  "generated_at": "2026-04-20T10:00:00+00:00",
  "scripts": [
    {
      "document_id": "trend_abc123_20260420",
      "topic": "Nama Topik",
      "script_content": {
        "hook_audio": "Kalimat pembuka 1-2 kalimat yang langsung memukau...",
        "body_audio": "Narasi utama 3-5 kalimat yang menjelaskan fakta inti...",
        "cta_audio": "Call to action yang natural...",
        "visual_prompts": [
          "Deskripsi scene sinematik 1",
          "Deskripsi scene sinematik 2",
          "Deskripsi scene sinematik 3"
        ]
      }
    }
  ]
}
```

---

## Troubleshooting

**Ollama tidak bisa dikonek**
```
Pastikan `ollama serve` berjalan dan port 11434 tidak diblokir firewall.
```

**Model tidak ditemukan**
```bash
ollama pull qwen2.5:7b
```

**Output JSON LLM tidak valid / ngawur**
- Coba model yang lebih besar: `OLLAMA_MODEL=qwen2.5:14b` atau `llama3.1:8b`
- Naikkan timeout: `OLLAMA_TIMEOUT=300.0`
- Kurangi jumlah topik yang diproses sekaligus di `agent_market_intelligence` (`LLM_TOP_N=5`)

**File input tidak terdeteksi**
- Pastikan file berekstensi `.json` dan tidak diawali `_`
- File yang sudah diproses pindah otomatis ke `data/input/_processed/`
