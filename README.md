# ﷽ Penerjemah Kitab

**Arabic → Indonesian translation tool** with **word-by-word analysis**, **Tashkeel (diacritization)**, **PDF OCR**, and **Sarf morphology (full verb conjugation)** — designed for reading classical Islamic texts (kitab kuning) like a scholar.

> "Penerjemah Kitab" means "Kitab Translator" — an app that helps students read Arabic texts the way a traditional *kyai* (scholar) explains a kitab to their students: word by word, with grammatical analysis and translation.

---

## ✨ Features

### 📖 Analisis Teks (Text Analysis)
| Feature | Description |
|---|---|
| **Tashkeel (Harakat)** | Add Arabic diacritics using **CAMeL Tools** with custom post-processing (phrase overrides + sun letter fix) |
| **Word Analysis** | Each word analyzed for: **lemma**, **root**, **POS type** (20+ categories: Isim, Fi'il, Harf, Dhomir, etc.) |
| **Word Gloss** | Word-by-word translation in **Indonesian** and **English** via built-in dictionaries (300+ entries each) |
| **Full Translation** | Sentence-level translation to **Indonesian + English** via Google Translate (free), with **NLLB-200 fallback** |
| **🔬 Sarf Morphology** | Click the 🔬 button on any word root to see **full verb conjugation tables** — past tense, present tense, subjunctive, jussive, and masdars (gerunds) — powered by the **[alsaydi/sarf](https://github.com/alsaydi/sarf)** library |
| **📖 Tashrif Ishthilahi** | Click the 📖 button on any word root to see the **8-column Tashrif grid** (fi'il madhi, mudhari', amr, nahi, mashdar, ism fa'il, ism maf'ul, zamami) with **Indonesian + English translations** and **Lughowi pronoun conjugation tables** |
| **Scholar Display** | Kitab-style layout with interlinear gloss, POS badges, and expandable detail table |

### 📄 Scan PDF (OCR)
| Feature | Description |
|---|---|
| **PDF Upload** | Upload scanned or born-digital PDFs via drag-and-drop or file picker |
| **Page Range Processing** | Process specific pages, not the whole PDF at once |
| **Arabic OCR** | **Tesseract OCR** with custom image preprocessing (CLAHE, Otsu, deskew) via **PyMuPDF + OpenCV** |
| **Per-Page Editing** | Edit OCR text directly in the browser, save corrections |
| **Per-Page Tashkeel** | Add diacritics to OCR'd text via CAMeL Tools |
| **Per-Page Translation** | Translate individual pages to Indonesian + English |
| **Bulk Translation** | "Terjemah Semua" — translate all untranslated pages at once |
| **SQLite Database** | All OCR results saved permanently in `ocr_texts.db` |
| **Confidence Indicators** | Color-coded per-page OCR confidence badges |
| **Accordion UI** | Expandable/collapsible pages per PDF |

### 🛡️ Translation Engine
| Priority | Engine | Quality | Offline | Size |
|---|---|---|---|---|
| **🥇 Primary** | **Google Translate** (via `deep-translator`) | ★★★★★ Excellent | ❌ Needs internet | 0 MB |
| **🥈 Fallback** | **NLLB-200** (Meta AI) | ★★★★ Very Good | ✅ Fully offline | ~1.2 GB |
| **🥉 Dict Lookup** | Custom Arabic→ID/EN dictionary | ★★★ Good (per word) | ✅ Fully offline | Instant |

---

## 🖥️ Screenshots

```
┌─────────────────────────────────────────────────────┐
│  Penerjemah Kitab                                    │
│  ✦ Analisis + OCR + Terjemahan ✦                    │
├─────────────────────────────────────────────────────┤
│  [📖 Analisis Teks]  [📄 Scan PDF]                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  يَكْتُبُ   الطَّالِبُ   الدَّرْسَ     فِي   │   │
│  │ ───────   ─────────   ───────   ─────        │   │
│  │  menulis   siswa       pelajaran  di          │   │
│  │   فعل       إسم         إسم       حرف جر      │   │
│  │  (كتب)    (طالب)      (درس)     (في)         │   │
│  │   🔬───► Full conjugation table               │   │
│  │                                              │   │
│  │  Terjemahan: "Siswa menulis pelajaran di..."  │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────────┐
│                    Your Machine (localhost)                  │
│                                                             │
│  ┌────────────────────┐    ┌────────────────────────────┐  │
│  │   Frontend (PWA)   │    │   Backend API               │  │
│  │                    │    │                              │  │
│  │   Nuxt 3 + Vue 3  │◄──►│   Python FastAPI             │  │
│  │   + Tailwind CSS  │    │   Port: 8000                  │  │
│  │   Port: 3000      │    │                              │  │
│  │                    │    │   - CAMeL Tools              │  │
│  │   - PWA ready     │    │   - Google Translate          │  │
│  │   - Installable   │    │   - NLLB-200 (fallback)       │  │
│  │   - Responsive    │    │   - Tesseract OCR             │  │
│  └────────────────────┘    │   - SQLite database          │  │
│                             │   - Sarf (Java via JAR) ◄───┼──┐
│                             └────────────────────────────┘  │
│                                                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Sarf Morphology Engine (Java 17+)                  │     │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────────┐ │     │
│  │  │ XML Root │  │ Conjugation  │  │ CLI Wrapper  │ │     │
│  │  │ Database │─►│ Engine       │─►│ (SarfCLI.java)│─►───┘
│  │  │ 24K+ roots│  │ 30 bab types│  │ stdin → JSON │ │     │
│  │  └──────────┘  └──────────────┘  └──────────────┘ │     │
│  └────────────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────────┘
```

## 📦 Tech Stack

### Backend (Python)
- **FastAPI** — REST API framework
- **CAMeL Tools** — Arabic morphological analysis & diacritization
- **PyArabic** — Arabic text utilities
- **deep-translator** — Free Google Translate API wrapper
- **NLLB-200** (Hugging Face Transformers) — Offline translation fallback
- **Tesseract OCR** + **PyMuPDF** + **OpenCV** — PDF→Arabic text pipeline
- **SQLite** — Persistent storage for OCR results

### Sarf Morphology (Java)
- **[alsaydi/sarf](https://github.com/alsaydi/sarf)** — Arabic verb conjugation & noun derivation engine
- **24,000+ triliteral roots** with conjugation class (bab) classification
- **30 verb types** (صحيح سالم, مهموز, أجوف, ناقص, لفيف, etc.)
- **Full paradigm generation**: past, present, subjunctive, jussive, imperative + masdars
- **Packaged as a CLI JAR** (`backend/sarf-cli.jar`) called from Python via subprocess

### Tashrif Ishthilahi (Python)
- **8-Column Tashrif grid**: fi'il madhi, fi'il mudhari', fi'il amr, fi'il nahi, mashdar, ism fa'il, ism maf'ul, zamami
- **13 Rumus patterns** (3A–6): covers all augmented verb forms (fa''ala, fa'ala, af'ala, tafa''ala, tafa'ala, ifta'ala, infa'ala, if'alla, istaf'ala, etc.)
- **Lughowi pronoun conjugation**: past, present, subjunctive, jussive, imperative, and prohibition (nahi) for all 14 Arabic pronouns
- **Indonesian + English translation overlay**: per-column translations with Rumus-specific semantics (e.g., 4A = "membuat jadi", 5D = "ter-", 6 = "meminta")
- **Root-only or full word classification**: provide a word form for precise Rumus detection, or just the root for a quick 8-column table
- **Pure Python implementation**: no external dependencies, based on wazan pattern matching

### Frontend (TypeScript)
- **Nuxt 3** + **Vue 3** — Modern web framework
- **Tailwind CSS** — Utility-first styling
- **@vite-pwa/nuxt** — Progressive Web App support
- **Amiri** (Google Font) — Traditional Arabic typeface

## 🔧 Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **Java 17+** (JRE) — required for the **Sarf morphology** feature ([download Eclipse Temurin](https://adoptium.net/temurin/releases/?version=17))
- **Tesseract OCR 5.x** (for PDF Scan feature only — [download](https://github.com/UB-Mannheim/tesseract/wiki))
  - Ensure **Arabic language data** is installed during setup

### Optional: Build Sarf from Source
The pre-built `backend/sarf-cli.jar` is included, but if you want to rebuild it:

```bash
cd sarf-source
# Requires: Java 17+ JDK and Maven
mvn compile -pl sarf-library
```

## 🚀 Quick Start

### 1. Clone & Install Backend

```bash
cd backend
pip install fastapi uvicorn camel-tools pyarabic deep-translator transformers torch sentencepiece pytesseract pymupdf opencv-python pillow numpy
python3 -m camel_data -i all   # Download CAMeL Tools model data (~500MB)
```

### 2. Install Frontend

```bash
cd frontend
npm install
```

### 3. Run Both Servers

**Option A: Double-click `restart_servers.bat` (Windows)**

**Option B: Manual (two terminals)**

```bash
# Terminal 1 — Backend (port 8000)
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend (port 3000)
cd frontend
npm run dev
```

### 4. Open http://localhost:3000

Paste Arabic text → click **☾ Analisis Teks** → see word-by-word analysis with translation!

Click **🔬** on any word root in the "Detail Lengkap" table to see full **Sarf conjugation tables**.

Click **📖** on any word root to see the **Tashrif Ishthilahi 8-column grid** with Indonesian/English translations and Lughowi pronoun tables.

For OCR: Switch to **📄 Scan PDF** tab → upload PDF → select page range → click **☾ Proses OCR**

## 📂 Project Structure

```
camel/
├── backend/
│   ├── main.py              # FastAPI server (all API endpoints)
│   ├── dictionary.py         # Arabic → Indonesian word dictionary (300+ entries)
│   ├── dictionary_en.py      # Arabic → English word dictionary (300+ entries)
│   ├── nllb_translator.py    # NLLB-200 offline translator (fallback)
│   ├── ocr_engine.py         # PDF→image→OCR pipeline
│   ├── ocr_database.py       # SQLite database layer
│   ├── sarf_client.py        # Python wrapper for Sarf Java CLI
│   ├── sarf-cli.jar           # Pre-built Sarf morphology engine (Java 17+)
│   └── uploads/              # Uploaded PDF storage
├── frontend/
│   ├── pages/index.vue       # Main application page
│   ├── app.vue               # Nuxt app entry
│   ├── nuxt.config.ts        # Nuxt configuration (incl. PWA)
│   ├── tailwind.config.ts    # Tailwind CSS configuration
│   ├── package.json
│   ├── public/
│   │   └── icons/            # PWA icons
│   └── assets/css/main.css   # Tailwind entry CSS
├── sarf-source/
│   └── sarf-library/         # Sarf Java source (alsaydi/sarf)
│       ├── pom.xml
│       ├── src/main/java/sarf/
│       │   ├── SarfCLI.java          # CLI wrapper (stdin → JSON)
│       │   ├── util/FileUtil.java    # Fixed classloader for JAR loading
│       │   └── ... (50+ morphology classes)
│       └── src/main/resources/db/    # XML root databases (24K+ roots)
├── docs/
│   ├── ASSESSMENT.md         # Original tech assessment
│   ├── DEV_BREAKDOWN.md      # Development plan
│   ├── HOW_TERJEMAH_WORKS.md # Translation engine docs
│   ├── PDF_OCR_ASSESSMENT.md # OCR feature assessment
│   ├── OPUS_ASSESSMENT.md    # OPUS-MT translation assessment
│   ├── SARF_ASSESSMENT.md    # Sarf integration assessment
│   └── TRANSLATION_RECOMMENDATION.md  # Translation strategy
├── start.bat                # Windows launcher script
├── restart_servers.bat       # Windows restart script
└── README.md                # This file
```

## 🔌 API Endpoints

### Core Analysis
| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Server health check |
| `/api/tashkeel` | POST | Add diacritics to Arabic text |
| `/api/analyze` | POST | Word-by-word analysis (lemma, root, POS, gloss) |
| `/api/translate` | POST | Full sentence translation (ID + EN) |

### Sarf Morphology
| Endpoint | Method | Description |
|---|---|---|
| `/api/sarf/analyze` | POST | Analyze triliteral root: full conjugation tables (past, present, subjunctive, jussive) + masdars |

### PDF OCR
| Endpoint | Method | Description |
|---|---|---|
| `/api/ocr/health` | GET | Tesseract & NLLB availability check |
| `/api/ocr/upload` | POST | Upload PDF file |
| `/api/ocr/process` | POST | Run OCR on page range |
| `/api/ocr/pdfs` | GET | List all PDFs with status |
| `/api/ocr/pages/{pdf_id}` | GET | Get all pages for a PDF |
| `/api/ocr/translate` | POST | Bulk translate untranslated pages |
| `/api/ocr/translate-page` | POST | Translate single page with edited text |
| `/api/ocr/tashkeel-page` | POST | Add diacritics to OCR text |
| `/api/ocr/save-page` | POST | Save edited OCR text |
| `/api/ocr/delete/{pdf_id}` | POST | Soft-delete a PDF |
| `/api/ocr/stats` | GET | OCR processing statistics |

### Tashrif Ishthilahi Endpoint
| Endpoint | Method | Description |
|---|---|---|
| `/api/tashrif/analyze` | POST | Analyze Arabic word/root: 8-column Tashrif Ishthilahi grid + Lughowi pronoun tables + ID/EN translations |

### Sarf Analyze Example

```bash
curl -X POST http://localhost:8000/api/sarf/analyze \
  -H "Content-Type: application/json" \
  -d '{"root": "كتب", "bab": 1}'
```

Returns:
```json
{
  "root": "كتب",
  "bab": 1,
  "classification": "فعل ثلاثي مجرد — فَعَلَ يَفْعَلُ (Bab 1: فتح يفتح)",
  "past_tense": [
    {"pronoun": "أنا", "text": "كَتَبْتُ"},
    {"pronoun": "نحن", "text": "كَتَبْنَا"},
    {"pronoun": "هو", "text": "كَتَبَ"},
    {"pronoun": "هي", "text": "كَتَبَت"},
    ...
  ],
  "present_tense": [
    {"pronoun": "أنا", "text": "أَكْتُبُ"},
    {"pronoun": "نحن", "text": "نَكْتُبُ"},
    {"pronoun": "هو", "text": "يَكْتُبُ"},
    ...
  ],
  "present_subjunctive": [...],
  "present_jussive": [...],
  "masdars": ["كِتَابًا", "كُتُبًا", ...]
}
```

## ⚙️ Configuration

### Backend
The backend runs on port **8000** by default. Change in `start.bat` / `restart_servers.bat`.

### Frontend
The API base URL is configured via `NUXT_PUBLIC_API_BASE` environment variable:

```bash
NUXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

See `.env.example` for configuration template.

### Sarf (Java)
The Sarf engine auto-detects Java 17+:
1. Checks project-local JDK at `tools/jdk17_extracted/` (if you've extracted one)
2. Falls back to `java` on `PATH`
3. Falls back to common Windows JDK paths

To verify it's working, check the Sarf button in the UI or call `/api/sarf/analyze` directly.

## 📚 How It Works

See detailed documentation in the `docs/` folder:
- **[HOW_TERJEMAH_WORKS.md](docs/HOW_TERJEMAH_WORKS.md)** — Translation engine internals
- **[PDF_OCR_ASSESSMENT.md](docs/PDF_OCR_ASSESSMENT.md)** — OCR pipeline architecture
- **[TRANSLATION_RECOMMENDATION.md](docs/TRANSLATION_RECOMMENDATION.md)** — Translation strategy
- **[SARF_ASSESSMENT.md](docs/SARF_ASSESSMENT.md)** — Sarf morphology integration assessment

### ### How Sarf Analysis Works

1. User types Arabic text (e.g., "يكتب الطالب الدرس")
2. CAMeL Tools analyzes each word — extracts **root** for verbs (e.g., "كتب" from "يكتب")
3. User clicks **🔬** next to a root in the "Detail Lengkap" table
4. Frontend calls `POST /api/sarf/analyze` with the root
5. Backend's `sarf_client.py` spawns a Java subprocess running `sarf-cli.jar`
6. The Sarf engine loads the XML root database, applies conjugation rules, and returns full JSON
7. Frontend displays the conjugation tables in a modal dialog

### How Tashrif Ishthilahi Works

1. User clicks **📖** next to a root in the "Detail Lengkap" table
2. Frontend calls `POST /api/tashrif/analyze` with the root
3. Backend's **tashrif_pipeline.py** classifies the word/root into a **Rumus pattern** (e.g., 3C for simple triliteral verbs)
4. **tashrif_generator.py** generates the 8-column Ishthilahi table (Arabic forms for fi'il madhi through zamami)
5. **tashrif_translate.py** adds Indonesian and English translations using:
   - Dictionary lookups for root meaning
   - Rumus-specific semantic overlays (e.g., 4C = "men...kan")
   - Form-level templates (e.g., madhi = "telah {base}")
6. **tashrif_lughowi.py** generates the Lughowi pronoun conjugation tables (past, present, subjunctive, jussive, imperative, nahi)
7. Frontend displays everything in a modal with the 8-column grid, pronoun tables, and translations

### Architecture Difference: Sarf vs Tashrif

| Aspect | 🔬 Sarf | 📖 Tashrif |
|---|---|---|
| **Engine** | Java (alsaydi/sarf JAR) | Pure Python |
| **Output** | Verb conjugation by pronoun | 8-column Ishthilahi grid |
| **Translations** | None | Indonesian + English per column |
| **Lughowi tables** | Past, present, subjunctive, jussive | Past, present, subjunctive, jussive, imperative, nahi |
| **Root coverage** | 24,000+ roots with bab classification | All 3-4 letter roots (pattern-based) |
| **Dependencies** | Java 17+ required | Python only (no external deps) |

## 🎓 Use Cases

1. **Students** reading kitab kuning — see every word's meaning and grammar, plus full verb conjugation & tashrif patterns
2. **Teachers** preparing lesson materials — get harakat + translation + root analysis + tashrif tables for teaching
3. **Researchers** working with Arabic manuscripts — OCR + translate scanned pages + analyze verb morphology
4. **Self-learners** studying Arabic — understand sentence structure word by word, explore verb patterns with the Tashrif Ishthilahi grid

## 🧪 Development Roadmap

| Step | Feature | Status |
|---|---|---|
| 1 | Project setup (FastAPI + Nuxt) | ✅ Complete |
| 2 | Tashkeel (CAMeL Tools diacritization) | ✅ Complete |
| 3 | Word-by-word analysis (POS, lemma, root) | ✅ Complete |
| 4 | Word cards UI with POS badges | ✅ Complete |
| 5 | Dictionary/gloss (ID + EN) | ✅ Complete |
| 6 | Sentence translation (Google + NLLB fallback) | ✅ Complete |
| 7 | Scholar kitab display | ✅ Complete |
| 8 | PDF OCR (Tesseract + PyMuPDF + SQLite) | ✅ Complete |
| 9 | PWA (installable, offline manifest) | ✅ Complete |
| 10 | Polish, error handling, batch operations | ✅ Complete |
| **11** | **🔬 Sarf Morphology (verb conjugation)** | **✅ Complete** |
| **12** | **📖 Tashrif Ishthilahi (8-column grid + translations)** | **✅ Complete** |

## 🤝 Contributing

Add vocabulary to the dictionaries:
- **[`backend/dictionary.py`](backend/dictionary.py)** — Add Arabic→Indonesian word entries
- **[`backend/dictionary_en.py`](backend/dictionary_en.py)** — Add Arabic→English word entries

Add phrase overrides for better diacritization in `backend/main.py` (`PHRASE_OVERRIDES` dict).

Improve Sarf integration:
- Modify [`backend/sarf_client.py`](backend/sarf_client.py) to tweak Java invocation or add new conjugation types
- Modify [`sarf-source/sarf-library/src/main/java/sarf/SarfCLI.java`](sarf-source/sarf-library/src/main/java/sarf/SarfCLI.java) to add new output fields

## 📜 License

This project uses the following open-source libraries:
- **CAMeL Tools** — Arabic NLP toolkit (MIT License)
- **PyArabic** — Arabic text utilities (MIT License)
- **NLLB-200** — Translation model (CC-BY-NC 4.0)
- **Tesseract OCR** — Optical character recognition (Apache 2.0)
- **[alsaydi/sarf](https://github.com/alsaydi/sarf)** — Arabic morphology engine (Apache 2.0)

---

*"Barangsiapa menempuh jalan untuk mencari ilmu, maka Allah akan memudahkan baginya jalan ke surga." — HR. Muslim*

**Built with ❤️ for students of knowledge.**
