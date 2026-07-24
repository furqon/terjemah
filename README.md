# 📖 Penerjemah Kitab

**Arabic → Indonesian translation tool** with word-by-word analysis, designed for reading classical Islamic texts (kitab kuning).

## Features

- **Tashkeel (Harakat)** — Add diacritics to Arabic text using CAMeL Tools
- **Word Analysis** — Each word gets lemma, root, and POS type (Isim/Fi'il/Harf)
- **Word Gloss** — Word-by-word Indonesian translation
- **Full Translation** — Sentence-level translation via NLLB-200 (coming in Step 6)
- **Scholar Display** — Kitab-style layout with interlinear gloss

## Architecture

```
Frontend (Nuxt.js + Tailwind CSS)  ◄────►  Backend (Python FastAPI)
Port: 3000                                   Port: 8001
```

## Prerequisites

- **Python 3.10+** (with `pyenv` recommended)
- **Node.js 18+**
- **npm**

## Setup

### 1. Backend

```bash
cd backend
pip install fastapi uvicorn camel-tools pyarabic qalsadi
python3 -m camel_data -i all
```

### 2. Frontend

```bash
cd frontend
npm install
```

### 3. Run

Double-click `restart_servers.bat` or run manually:

```bash
# Terminal 1: Backend
cd backend
python3 -X utf8 -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Frontend
cd frontend
NUXT_PUBLIC_API_BASE=http://localhost:8001 npx nuxt dev --port 3000 --host 0.0.0.0
```

Open **http://localhost:3000**

## Project Structure

```
camel/
├── backend/
│   ├── main.py           # FastAPI server (tashkeel + analysis API)
│   └── dictionary.py     # Arabic → Indonesian word dictionary
├── frontend/
│   ├── pages/index.vue   # Main PWA page
│   ├── nuxt.config.ts    # Nuxt configuration
│   └── tailwind.config.ts
├── docs/
│   ├── ASSESSMENT.md
│   ├── DEV_BREAKDOWN.md
│   └── TRANSLATION_RECOMMENDATION.md
└── restart_servers.bat   # Windows launcher
```

## Development Roadmap

| Step | Feature | Status |
|------|---------|--------|
| 1 | Project setup (FastAPI + Nuxt) | ✅ |
| 2 | Tashkeel (CAMeL Tools) | ✅ |
| 3 | Word tokenization + analysis | 🔜 |
| 4 | Word cards UI | 🔜 |
| 5 | Dictionary/gloss | 🔜 |
| 6 | NLLB-200 translation | 🔜 |
| 7 | Scholar display | 🔜 |
| 8+ | Polish & PWA | 🔜 |
