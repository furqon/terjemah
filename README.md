# ﷽ Penerjemah Kitab

**Arabic → Indonesian translation tool** with **word-by-word analysis**, **Tashkeel (diacritization)**, and **PDF OCR** — designed for reading classical Islamic texts (kitab kuning) like a scholar.

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
│  │                                              │   │
│  │  Terjemahan: "Siswa menulis pelajaran di..."  │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Your Machine (localhost)             │
│                                                      │
│  ┌────────────────────┐    ┌──────────────────────┐ │
│  │   Frontend (PWA)   │    │   Backend API         │ │
│  │                    │    │                        │ │
│  │   Nuxt 3 + Vue 3  │◄──►│   Python FastAPI       │ │
│  │   + Tailwind CSS  │    │   Port: 8000            │ │
│  │   Port: 3000      │    │                        │ │
│  │                    │    │   - CAMeL Tools        │ │
│  │   - PWA ready     │    │   - Google Translate    │ │
│  │   - Installable   │    │   - NLLB-200 (fallback) │ │
│  │   - Responsive    │    │   - Tesseract OCR       │ │
│  └────────────────────┘    │   - SQLite database    │ │
│                             └──────────────────────┘ │
└─────────────────────────────────────────────────────┘
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

### Frontend (TypeScript)
- **Nuxt 3** + **Vue 3** — Modern web framework
- **Tailwind CSS** — Utility-first styling
- **@vite-pwa/nuxt** — Progressive Web App support
- **Amiri** (Google Font) — Traditional Arabic typeface

## 🔧 Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **Tesseract OCR 5.x** (for PDF Scan feature only — [download](https://github.com/UB-Mannheim/tesseract/wiki))
  - Ensure **Arabic language data** is installed during setup

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
├── docs/
│   ├── ASSESSMENT.md         # Original tech assessment
│   ├── DEV_BREAKDOWN.md      # Development plan
│   ├── HOW_TERJEMAH_WORKS.md # Translation engine docs
│   ├── PDF_OCR_ASSESSMENT.md # OCR feature assessment
│   ├── OPUS_ASSESSMENT.md    # OPUS-MT translation assessment
│   └── TRANSLATION_RECOMMENDATION.md  # Translation strategy
├── start.bat                # Windows launcher script
├── restart_servers.bat       # Windows restart script
└── README.md                # This file
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Server health check |
| `/api/tashkeel` | POST | Add diacritics to Arabic text |
| `/api/analyze` | POST | Word-by-word analysis (lemma, root, POS, gloss) |
| `/api/translate` | POST | Full sentence translation (ID + EN) |
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

## ⚙️ Configuration

### Backend
The backend runs on port **8000** by default. Change in `start.bat` / `restart_servers.bat`.

### Frontend
The API base URL is configured via `NUXT_PUBLIC_API_BASE` environment variable:

```bash
NUXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

See `.env.example` for configuration template.

## 📚 How It Works

See detailed documentation in the `docs/` folder:
- **[HOW_TERJEMAH_WORKS.md](docs/HOW_TERJEMAH_WORKS.md)** — Translation engine internals
- **[PDF_OCR_ASSESSMENT.md](docs/PDF_OCR_ASSESSMENT.md)** — OCR pipeline architecture
- **[TRANSLATION_RECOMMENDATION.md](docs/TRANSLATION_RECOMMENDATION.md)** — Translation strategy

## 🎓 Use Cases

1. **Students** reading kitab kuning — see every word's meaning and grammar
2. **Teachers** preparing lesson materials — get harakat + translation quickly
3. **Researchers** working with Arabic manuscripts — OCR + translate scanned pages
4. **Self-learners** studying Arabic — understand sentence structure word by word

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

## 🤝 Contributing

Add vocabulary to the dictionaries:
- **[`backend/dictionary.py`](backend/dictionary.py)** — Add Arabic→Indonesian word entries
- **[`backend/dictionary_en.py`](backend/dictionary_en.py)** — Add Arabic→English word entries

Add phrase overrides for better diacritization in `backend/main.py` (`PHRASE_OVERRIDES` dict).

## 📜 License

This project uses the following open-source libraries:
- **CAMeL Tools** — Arabic NLP toolkit (MIT License)
- **PyArabic** — Arabic text utilities (MIT License)
- **NLLB-200** — Translation model (CC-BY-NC 4.0)
- **Tesseract OCR** — Optical character recognition (Apache 2.0)

---

*"Barangsiapa menempuh jalan untuk mencari ilmu, maka Allah akan memudahkan baginya jalan ke surga." — HR. Muslim*

**Built with ❤️ for students of knowledge.**
