# Assessment: PDF Upload + OCR + Translation Feature
## Adding a \"Scan PDF\" Tab to Penerjemah Kitab

**Date:** July 24, 2026
**Context:** Add a new tab to the app where users can upload a PDF (kitab/manuscript), extract Arabic text via OCR page-by-page, save to a database, and translate paragraph-by-paragraph with original Arabic + Indonesian translation displayed side-by-side.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [PDF Processing Pipeline](#3-pdf-processing-pipeline)
4. [OCR Engine Selection](#4-ocr-engine-selection)
5. [Database Storage](#5-database-storage)
6. [Translation Integration](#6-translation-integration)
7. [Frontend UI](#7-frontend-ui)
8. [Step-by-Step Implementation Plan](#8-step-by-step-implementation-plan)
9. [Dependencies & Installation](#9-dependencies--installation)
10. [Risks & Challenges](#10-risks--challenges)
11. [Final Verdict](#11-final-verdict)

---

## 1. Overview

### What the user wants

> "Add one more tab: upload PDF → Tesseract OCR convert to text, not in one time but per range page. Saved converted txt to database or then with translation engine will do translation per paragraph (original Arabic, translation Bahasa Indonesia below)."

### Key requirements

| Requirement | Details |
|---|---|
| **New tab** | Separate from the existing text analysis tab |
| **PDF upload** | User uploads a PDF file (e.g., scanned kitab/manuscript) |
| **Page range** | Process specific pages, not the whole PDF at once |
| **OCR** | Extract Arabic text from scanned pages |
| **Database** | Save extracted text permanently |
| **Translation** | Use existing translation engine per paragraph |
| **Display** | Original Arabic text with Bahasa Indonesia translation below |

### Current app architecture

```
┌──────────────────────────────────────────────┐
│            Penerjemah Kitab (Nuxt + FastAPI)  │
│                                              │
│  [Tab 1: Analisis Teks] ← existing           │
│  [Tab 2: Scan PDF]      ← NEW               │
│                                              │
│  Backend API endpoints:                      │
│  - /api/analyze     (existing)               │
│  - /api/tashkeel    (existing)               │
│  - /api/translate   (existing)               │
│  - /api/ocr/upload  (new)                    │
│  - /api/ocr/process (new)                    │
│  - /api/ocr/pages   (new)                    │
│  - /api/ocr/translate-paragraph (new)        │
└──────────────────────────────────────────────┘
```

---

## 2. Architecture

### Data Flow

```
┌──────────┐    PDF upload     ┌──────────────────────┐
│  Browser │ ────────────────► │   FastAPI Backend     │
│  (Nuxt)  │                   │                      │
│          │ ◄──── JSON ────── │  /api/ocr/upload      │
│  Tab 2:  │                   │  /api/ocr/pages       │
│  Scan    │                   │  /api/ocr/translate   │
│  PDF     │                   │                      │
└──────────┘                   │  ┌──────────────────┐ │
                               │  │  SQLite Database │ │
                               │  │  (ocr_texts.db)  │ │
                               │  └──────────────────┘ │
                               │                      │
                               │  ┌──────────────────┐ │
                               │  │  PyMuPDF (fitz)  │ │
                               │  │  → PDF→image     │ │
                               │  └──────────────────┘ │
                               │                      │
                               │  ┌──────────────────┐ │
                               │  │  Tesseract OCR   │ │
                               │  │  → image→text    │ │
                               │  └──────────────────┘ │
                               │                      │
                               │  ┌──────────────────┐ │
                               │  │  Google Translate │ │
                               │  │  (existing)       │ │
                               │  └──────────────────┘ │
                               └──────────────────────┘
```

### Tab structure in frontend

```
┌─────────────────────────────────────────────────────┐
│  Penerjemah Kitab                                    │
│                                                      │
│  [Analisis Teks]  [Scan PDF]  ← tab navigation       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─ Upload ──────────────────────────────────────┐  │
│  │  [📁 Choose PDF]  [Page: ██ to ██]  [Process] │  │
│  └───────────────────────────────────────────────┘  │
│                                                      │
│  ┌─ Saved Pages ─────────────────────────────────┐  │
│  │  Halaman 1  ■■■■■■■■■■■■■■■□  95%             │  │
│  │  ┌──────────────────────────────────────────┐ │  │
│  │  │ Arabic text from page 1...               │ │  │
│  │  │ ──────────────────────────────────────  │ │  │
│  │  │ Indonesian translation of paragraph...   │ │  │
│  │  └──────────────────────────────────────────┘ │  │
│  │                                                │  │
│  │  Halaman 2  ■■■■■■■□□□□□□□□□□□  50%           │  │
│  │  ┌──────────────────────────────────────────┐ │  │
│  │  │ Arabic text from page 2...               │ │  │
│  │  │ ──────────────────────────────────────  │ │  │
│  │  │ Indonesian translation of paragraph...   │ │  │
│  │  └──────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 3. PDF Processing Pipeline

### Recommended: PyMuPDF (fitz)

**PyMuPDF** is the best choice for PDF-to-image conversion:

| Feature | PyMuPDF (fitz) | pdf2image |
|---|---|---|
| **Speed** | Very fast (native C) | Moderate (wrapper around pdftoppm) |
| **External deps** | None (self-contained) | Requires poppler installed separately |
| **Windows setup** | `pip install pymupdf` | Needs poppler download + PATH config |
| **Page range** | Built-in: `doc.load_page(n)` | Built-in: `pdf2image.convert_from_path(pdf, first_page=n, last_page=m)` |
| **DPI control** | `page.get_pixmap(dpi=300)` | `dpi=300` parameter |
| **Memory** | Efficient (page-by-page) | Can load all pages at once |

```python
import fitz  # PyMuPDF

def pdf_page_to_image(pdf_path: str, page_num: int, dpi: int = 300):
    """Convert a single PDF page to a PIL Image for OCR."""
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)  # 0-indexed
    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return img

def get_page_count(pdf_path: str) -> int:
    """Get total number of pages in PDF."""
    doc = fitz.open(pdf_path)
    count = doc.page_count
    doc.close()
    return count
```

### Image Preprocessing (Critical for Arabic OCR)

Raw PDF page images often need preprocessing for good OCR results:

```python
import cv2
import numpy as np

def preprocess_for_ocr(image):
    """Preprocess image for better Arabic OCR accuracy."""
    # Convert to grayscale
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

    # Increase contrast (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(enhanced, h=30)

    # Threshold (Otsu's binarization)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Deskew (correct slight rotation)
    coords = np.column_stack(np.where(binary > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    if abs(angle) > 0.5:  # Only rotate if significant
        h, w = binary.shape
        matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        binary = cv2.warpAffine(binary, matrix, (w, h),
                                flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return binary
```

---

## 4. OCR Engine Selection

### Comparison

| Engine | Arabic Accuracy | Speed | Tashkeel Support | Ease of Setup | Resource Usage |
|---|---|---|---|---|---|
| **Tesseract 5** | ★★★☆☆ Good | ★★★★★ Fast | ★★☆☆☆ Poor | ★★★★☆ Easy | ★★★★★ Light |
| **EasyOCR** | ★★★★☆ Very Good | ★★☆☆☆ Slow (CPU) | ★★★☆☆ Fair | ★★★★☆ Easy | ★★☆☆☆ Heavy |
| **PaddleOCR** | ★★★★★ Excellent | ★★★★☆ Fast | ★★★★☆ Good | ★★★☆☆ Medium | ★★★☆☆ Moderate |
| **Surya OCR** | ★★★★★ Excellent | ★★★☆☆ Moderate | ★★★★★ Good | ★★☆☆☆ Complex | ★★★☆☆ Moderate |
| **Cloud API** | ★★★★★ Excellent | ★★★★★ Fast | ★★★★★ Excellent | ★★★★★ Easy | ★★★★★ None |

### Recommendation: Start with Tesseract, upgrade if needed

**Why start with Tesseract:**
- ✅ Already requested by the user
- ✅ Lightest resource usage
- ✅ Free and open-source
- ✅ Good enough for clear, printed Arabic text
- ✅ Easy Windows setup

**When to upgrade to EasyOCR/PaddleOCR:**
- If the PDFs are old/manuscripts with irregular fonts
- If tashkeel (harakat) preservation is critical
- If Tesseract accuracy is below 85% on test pages

### Tesseract Setup

```python
import pytesseract
from PIL import Image

# Windows: Set path to tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def ocr_arabic(image, config="--psm 6 --oem 3"):
    """
    Extract Arabic text from an image using Tesseract.

    Args:
        image: PIL Image or numpy array
        config: Tesseract config string
            --psm 6: Assume uniform block of text
            --oem 3: Default (LSTM + Legacy)

    Returns:
        Extracted Arabic text string
    """
    # Use 'ara' language pack
    # For better results with diacritics, use 'ara+ar' combined
    text = pytesseract.image_to_string(
        image,
        lang='ara',  # or 'ara+ar' for combined language data
        config=config
    )
    return text.strip()


def ocr_page_with_confidence(image):
    """Get OCR text with per-character confidence data."""
    data = pytesseract.image_to_data(
        image, lang='ara',
        config='--psm 6 --oem 3',
        output_type=pytesseract.Output.DICT
    )

    # Filter low-confidence words
    words = []
    for i, conf in enumerate(data['conf']):
        if conf != '-1' and int(conf) > 40:  # Only keep >40% confidence
            words.append(data['text'][i])

    return ' '.join(words)
```

### Tesseract Language Packs

| Pack | File | Best For |
|---|---|---|
| `ara` (standard) | `ara.traineddata` | Modern printed Arabic |
| `ara` + `ar` (combined) | Both | Better coverage |
| `tessdata_best/ara` | Highest quality | Maximum accuracy (slower) |
| `tessdata_fast/ara` | Fast inference | Speed-critical apps |

**Tesseract post-processing** is essential for Arabic:

```python
import re

def clean_ocr_output(text: str) -> str:
    """Clean common Tesseract Arabic OCR errors."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)

    # Fix common substitution errors (extend as needed)
    replacements = {
        'للها': 'لله',
        'اللّه': 'الله',
        'الرّحمن': 'الرحمن',
        'الرّحيم': 'الرحيم',
        # Add more replacements based on your specific corpus
    }
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    # Remove lines that are too short (likely noise)
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 3]

    return '\n'.join(lines)
```

---

## 5. Database Storage

### Recommendation: SQLite

SQLite is the ideal choice for a desktop app:

- **Zero configuration** — no server, no setup
- **Single file** — easy to backup, move, or share
- **Built into Python** — `import sqlite3`, no extra deps
- **Good performance** — fast enough for thousands of pages
- **ACID compliant** — data integrity guaranteed

### Schema Design

```sql
-- Main database: ocr_texts.db

CREATE TABLE IF NOT EXISTS pdfs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,           -- Original PDF filename
    filepath TEXT NOT NULL,           -- Path to stored PDF (or blob)
    total_pages INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active'       -- active, deleted
);

CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_id INTEGER NOT NULL,           -- FK to pdfs.id
    page_number INTEGER NOT NULL,      -- 1-based page number
    raw_text TEXT,                      -- Raw OCR output
    cleaned_text TEXT,                  -- Post-processed OCR text
    confidence REAL DEFAULT 0.0,        -- Average OCR confidence
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    translated_id TEXT,                 -- Indonesian translation (paragraph)
    translated_en TEXT,                 -- English translation (optional)
    translated_at TIMESTAMP,
    UNIQUE(pdf_id, page_number),        -- One entry per page per PDF
    FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS paragraphs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id INTEGER NOT NULL,           -- FK to pages.id
    paragraph_index INTEGER NOT NULL,   -- Order within the page
    arabic_text TEXT NOT NULL,
    translation_id TEXT,                 -- Indonesian translation
    translation_en TEXT,                 -- English translation
    UNIQUE(page_id, paragraph_index),
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
);
```

### Python Database Layer

```python
import sqlite3
from datetime import datetime
from contextlib import contextmanager

class OCRDatabase:
    def __init__(self, db_path="ocr_texts.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS pdfs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    total_pages INTEGER NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                );
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pdf_id INTEGER NOT NULL,
                    page_number INTEGER NOT NULL,
                    raw_text TEXT,
                    cleaned_text TEXT,
                    confidence REAL DEFAULT 0.0,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    translated_id TEXT,
                    translated_en TEXT,
                    UNIQUE(pdf_id, page_number),
                    FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE
                );
            """)

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def save_pdf(self, filename, total_pages):
        with self._get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO pdfs (filename, total_pages) VALUES (?, ?)",
                (filename, total_pages)
            )
            return cur.lastrowid

    def save_page(self, pdf_id, page_number, raw_text, cleaned_text, confidence):
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO pages
                (pdf_id, page_number, raw_text, cleaned_text, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (pdf_id, page_number, raw_text, cleaned_text, confidence))

    def get_untranslated_pages(self, pdf_id=None):
        """Get pages that haven't been translated yet."""
        with self._get_conn() as conn:
            if pdf_id:
                rows = conn.execute("""
                    SELECT * FROM pages
                    WHERE pdf_id = ? AND (translated_id IS NULL OR translated_id = '')
                    ORDER BY page_number
                """, (pdf_id,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM pages
                    WHERE translated_id IS NULL OR translated_id = ''
                    ORDER BY pdf_id, page_number
                """).fetchall()
            return rows

    def get_all_pdfs(self):
        with self._get_conn() as conn:
            return conn.execute(
                "SELECT * FROM pdfs WHERE status = 'active' ORDER BY uploaded_at DESC"
            ).fetchall()

    def get_pages_for_pdf(self, pdf_id):
        with self._get_conn() as conn:
            return conn.execute(
                "SELECT * FROM pages WHERE pdf_id = ? ORDER BY page_number",
                (pdf_id,)
            ).fetchall()
```

---

## 6. Translation Integration

### Reuse existing translation engine

The app already has Google Translate integration via `deep-translator`. The OCR tab should reuse this:

```python
from deep_translator import GoogleTranslator

class OCRTranslator:
    def __init__(self):
        self.translator_id = GoogleTranslator(source='ar', target='id')
        self.translator_en = GoogleTranslator(source='ar', target='en')

    def translate_paragraph(self, arabic_text: str) -> dict:
        """Translate an Arabic paragraph to ID and EN."""
        if not arabic_text.strip():
            return {"id": "", "en": ""}

        # Split into sentences for better translation
        # (Google Translate handles paragraphs fine, but splitting
        #  can improve accuracy for long texts)
        try:
            id_result = self.translator_id.translate(arabic_text) or ""
            en_result = self.translator_en.translate(arabic_text) or ""
            return {"id": id_result, "en": en_result}
        except Exception as e:
            return {"id": f"[Translation error: {e}]", "en": ""}

    def translate_page(self, page_text: str) -> list:
        """Split page into paragraphs and translate each."""
        paragraphs = [p.strip() for p in page_text.split('\n') if p.strip()]
        results = []
        for para in paragraphs:
            trans = self.translate_paragraph(para)
            results.append({
                "arabic": para,
                "id": trans["id"],
                "en": trans["en"]
            })
        return results
```

### Paragraph splitting logic

For kitab texts, paragraphs are typically separated by:
- New lines
- Verse markers (﴿﴾)
- Numbered verses/paragraphs
- Topic headings

```python
import re

def split_into_paragraphs(text: str) -> list[str]:
    """Split OCR'd Arabic text into meaningful paragraphs."""
    # Split on multiple newlines
    paragraphs = re.split(r'\n\s*\n+', text)

    # Further split long paragraphs at sentence boundaries
    result = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # If paragraph is very long, split at punctuation
        if len(p) > 500:
            # Split at period, question mark, or Arabic verse marker
            sentences = re.split(r'(？|！|۔|\.|\?|!|﴿|﴾)', p)
            current = ""
            for s in sentences:
                current += s
                if len(current) > 100 and s in ('؟', '.', '!', '﴿', '﴾'):
                    result.append(current.strip())
                    current = ""
            if current.strip():
                result.append(current.strip())
        else:
            result.append(p)

    return result
```

---

## 7. Frontend UI

### Tab Navigation

Add a tab system to the existing frontend:

```vue
<template>
  <div class="min-h-screen" style="background: #f5f0e8">
    <!-- Header (same as existing) -->
    <header>...</header>

    <!-- Tab navigation -->
    <div class="max-w-4xl mx-auto px-4 py-3">
      <div class="flex gap-1 border-b" style="border-color: #d4c5a9;">
        <button
          @click="activeTab = 'analyze'"
          class="px-4 py-2 text-sm font-medium rounded-t-lg transition-colors"
          :style="activeTab === 'analyze'
            ? { background: '#fffdf5', color: '#2d5a3d', border: '1px solid #d4c5a9', borderBottom: '1px solid #fffdf5' }
            : { color: '#a0896a', border: '1px solid transparent' }"
        >
          Analisis Teks
        </button>
        <button
          @click="activeTab = 'scan'"
          class="px-4 py-2 text-sm font-medium rounded-t-lg transition-colors"
          :style="activeTab === 'scan'
            ? { background: '#fffdf5', color: '#2d5a3d', border: '1px solid #d4c5a9', borderBottom: '1px solid #fffdf5' }
            : { color: '#a0896a', border: '1px solid transparent' }"
        >
          Scan PDF
        </button>
      </div>

      <!-- Tab content -->
      <div v-if="activeTab === 'analyze'" class="mt-3">
        <!-- Existing analyze UI -->
      </div>

      <div v-if="activeTab === 'scan'" class="mt-3">
        <!-- New Scan PDF UI -->
      </div>
    </div>
  </div>
</template>
```

### Scan PDF Tab Layout

```vue
<!-- Scan PDF Tab -->
<div class="space-y-3">
  <!-- Upload section -->
  <div class="bg-white rounded-lg shadow-sm border p-4"
       style="background: #fffdf5; border-color: #d4c5a9;">
    <h2 class="text-base font-bold mb-3" style="color: #3a2a1a;">
      Upload PDF
    </h2>

    <input
      type="file"
      accept=".pdf"
      @change="handlePdfUpload"
      class="mb-3"
    >

    <div class="flex gap-2 items-end">
      <div>
        <label class="text-xs block mb-1" style="color: #8b7355;">
          Halaman dari
        </label>
        <input
          v-model.number="pageStart"
          type="number"
          min="1"
          class="w-20 p-2 border rounded text-sm"
          style="border-color: #e0d5c0; background: #faf8f0;"
        >
      </div>
      <div>
        <label class="text-xs block mb-1" style="color: #8b7355;">
          sampai
        </label>
        <input
          v-model.number="pageEnd"
          type="number"
          min="1"
          class="w-20 p-2 border rounded text-sm"
          style="border-color: #e0d5c0; background: #faf8f0;"
        >
      </div>
      <button
        @click="processPages"
        :disabled="!selectedFile || processing"
        class="px-4 py-2 rounded text-sm font-medium"
        style="background: #2d5a3d; color: white;"
      >
        {{ processing ? 'Memproses...' : 'Proses' }}
      </button>
    </div>

    <!-- Progress bar -->
    <div v-if="processing" class="mt-3">
      <div class="flex justify-between text-xs mb-1" style="color: #8b7355;">
        <span>Halaman {{ currentPage }} / {{ totalPagesToProcess }}</span>
        <span>{{ Math.round(progress * 100) }}%</span>
      </div>
      <div class="h-2 rounded-full" style="background: #e0d5c0;">
        <div
          class="h-full rounded-full transition-all duration-300"
          style="background: #2d5a3d; width: {{ progress * 100 }}%"
        ></div>
      </div>
    </div>
  </div>

  <!-- Saved PDFs list -->
  <div
    v-for="pdf in pdfList"
    :key="pdf.id"
    class="bg-white rounded-lg shadow-sm border p-4"
    style="background: #fffdf5; border-color: #d4c5a9;"
  >
    <div class="flex justify-between items-start mb-2">
      <div>
        <h3 class="text-sm font-semibold" style="color: #3a2a1a;">
          {{ pdf.filename }}
        </h3>
        <p class="text-xs" style="color: #a0896a;">
          {{ pdf.total_pages }} halaman • {{ pdf.processed_pages }} diproses
        </p>
      </div>
      <button
        @click="translatePdf(pdf.id)"
        class="text-xs px-3 py-1 rounded"
        style="background: #c9a84c; color: white;"
      >
        Terjemahkan Semua
      </button>
    </div>

    <!-- Page list for this PDF -->
    <div
      v-for="page in getPages(pdf.id)"
      :key="page.id"
      class="mt-2 p-3 rounded"
      style="background: #faf8f0; border: 1px solid #e0d5c0;"
    >
      <p class="text-xs font-medium mb-1" style="color: #8b7355;">
        Halaman {{ page.page_number }}
      </p>
      <div class="grid md:grid-cols-2 gap-2 text-xs">
        <div>
          <p class="font-arabic" dir="rtl" style="color: #3a2a1a;">
            {{ page.cleaned_text }}
          </p>
        </div>
        <div v-if="page.translated_id">
          <p style="color: #3a7a4d;">
            {{ page.translated_id }}
          </p>
        </div>
      </div>
    </div>
  </div>
</div>
```

---

## 8. Step-by-Step Implementation Plan

### Phase 1: Backend Foundation (2-3 hours)

| Step | Task | Files |
|:----:|---|---|
| 1 | Install Tesseract OCR on Windows + Python deps | System + `requirements.txt` |
| 2 | Create `backend/ocr_engine.py` — PDF→image + OCR | `backend/ocr_engine.py` |
| 3 | Create `backend/ocr_database.py` — SQLite layer | `backend/ocr_database.py` |
| 4 | Add OCR API endpoints to `main.py` | `backend/main.py` |

### Phase 2: Frontend Tab (2-3 hours)

| Step | Task | Files |
|:----:|---|---|
| 5 | Add tab navigation to `index.vue` | `frontend/pages/index.vue` |
| 6 | Build PDF upload + page range UI | Same file |
| 7 | Add progress display + saved PDFs list | Same file |
| 8 | Add per-paragraph translation display | Same file |

### Phase 3: Polish (1-2 hours)

| Step | Task |
|:----:|---|
| 9 | Test with real scanned kitab PDFs |
| 10 | Add Tesseract post-processing for common errors |
| 11 | Add "Translate All" batch functionality |
| 12 | Add confidence indicator per page |

### Detailed Implementation

#### Step 1: Install dependencies

```bash
# 1. Install Tesseract OCR from:
#    https://github.com/UB-Mannheim/tesseract/wiki
#    Choose 64-bit installer, check "Arabic language data"

# 2. Install Python packages
pip install pytesseract pymupdf opencv-python pillow
```

#### Step 2: OCR Engine (`backend/ocr_engine.py`)

```python
"""OCR engine: PDF → images → Arabic text using Tesseract."""
import fitz  # PyMuPDF
import pytesseract
import cv2
import numpy as np
from PIL import Image
import re
import os

# Windows: point to tesseract install
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.name == 'nt' and os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


class OCREngine:
    """Convert PDF pages to Arabic text."""

    def __init__(self, dpi=300):
        self.dpi = dpi

    def get_page_count(self, pdf_path: str) -> int:
        doc = fitz.open(pdf_path)
        count = doc.page_count
        doc.close()
        return count

    def page_to_image(self, pdf_path: str, page_num: int):
        """Convert a PDF page to a PIL Image."""
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=self.dpi)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img

    def preprocess(self, image):
        """Enhance image for Arabic OCR."""
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    def ocr_page(self, image) -> tuple[str, float]:
        """Extract Arabic text from an image. Returns (text, confidence)."""
        processed = self.preprocess(image)
        data = pytesseract.image_to_data(
            processed, lang='ara',
            config='--psm 6 --oem 3',
            output_type=pytesseract.Output.DICT
        )
        # Filter by confidence
        words = []
        confs = []
        for i, conf in enumerate(data['conf']):
            if conf != '-1' and int(conf) > 0:
                words.append(data['text'][i])
                confs.append(int(conf))
        text = ' '.join(words)
        avg_conf = sum(confs) / len(confs) if confs else 0.0
        return self._clean_text(text), avg_conf / 100.0

    def process_page_range(self, pdf_path: str, start: int, end: int):
        """Process a range of pages, yielding results one by one."""
        for page_num in range(start - 1, end):  # Convert to 0-indexed
            img = self.page_to_image(pdf_path, page_num)
            text, conf = self.ocr_page(img)
            yield page_num + 1, text, conf

    def _clean_text(self, text: str) -> str:
        """Post-process Tesseract output."""
        text = re.sub(r'\s+', ' ', text)
        # Common Tesseract Arabic fixes
        fixes = {
            'للها': 'لله',
            'اللّه': 'الله',
            'بسم': 'بسم',
        }
        for wrong, correct in fixes.items():
            text = text.replace(wrong, correct)
        return text.strip()
```

#### Step 3: Database layer (`backend/ocr_database.py`)

See Section 5 above for the complete database layer implementation.

#### Step 4: API endpoints (add to `backend/main.py`)

```python
import os
import uuid
from fastapi import UploadFile, File, Form
from ocr_engine import OCREngine
from ocr_database import OCRDatabase

ocr_engine = OCREngine(dpi=300)
ocr_db = OCRDatabase("ocr_texts.db")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Pydantic models ──
class OCRUploadResponse(BaseModel):
    pdf_id: int
    filename: str
    total_pages: int

class OCRProcessRequest(BaseModel):
    pdf_id: int
    page_start: int
    page_end: int

class OCRProcessResponse(BaseModel):
    pages_processed: int
    pages: list[dict]

class OCRTranslateRequest(BaseModel):
    pdf_id: int
    page_id: int = None  # None = translate all untranslated

# ── API endpoints ──

@app.post("/api/ocr/upload", response_model=OCRUploadResponse)
async def ocr_upload(file: UploadFile = File(...)):
    """Upload a PDF file for OCR processing."""
    ext = os.path.splitext(file.filename)[1] or ".pdf"
    unique_name = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, unique_name)

    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    total_pages = ocr_engine.get_page_count(filepath)
    pdf_id = ocr_db.save_pdf(file.filename, filepath, total_pages)

    return OCRUploadResponse(pdf_id=pdf_id, filename=file.filename, total_pages=total_pages)

@app.post("/api/ocr/process", response_model=OCRProcessResponse)
def ocr_process(request: OCRProcessRequest):
    """Process a range of pages with OCR."""
    pdf_info = ocr_db.get_pdf(request.pdf_id)
    pages_processed = []
    for page_num, text, conf in ocr_engine.process_page_range(
        pdf_info['filepath'], request.page_start, request.page_end
    ):
        cleaned = ocr_engine._clean_text(text)
        ocr_db.save_page(request.pdf_id, page_num, text, cleaned, conf)
        pages_processed.append({
            "page_number": page_num,
            "text": cleaned,
            "confidence": conf
        })
    return OCRProcessResponse(pages_processed=len(pages_processed), pages=pages_processed)

@app.post("/api/ocr/translate")
def ocr_translate(request: OCRTranslateRequest):
    """Translate untranslated pages for a PDF."""
    # Reuse existing translation logic
    pages = ocr_db.get_untranslated_pages(request.pdf_id)
    from deep_translator import GoogleTranslator
    t_id = GoogleTranslator(source='ar', target='id')
    t_en = GoogleTranslator(source='ar', target='en')
    results = []
    for page in pages:
        try:
            trans_id = t_id.translate(page['cleaned_text']) or ""
            trans_en = t_en.translate(page['cleaned_text']) or ""
            ocr_db.save_translation(page['id'], trans_id, trans_en)
            results.append({
                "page_number": page['page_number'],
                "translation_id": trans_id,
                "translation_en": trans_en
            })
        except Exception as e:
            results.append({
                "page_number": page['page_number'],
                "error": str(e)
            })
    return {"translated": len(results), "results": results}
```

---

## 9. Dependencies & Installation

### System Requirements

| Component | Requirement |
|---|---|
| **Tesseract OCR** | [UB-Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki) (Windows) |
| **Python** | 3.10+ |
| **RAM** | 4GB+ (8GB recommended for large PDFs) |
| **Disk** | 500MB for Tesseract + models + Python packages |

### Python Packages

```txt
# backend/requirements.txt additions
pytesseract>=0.3.10
pymupdf>=1.23.0
opencv-python>=4.8.0
pillow>=10.0.0
numpy>=1.24.0
```

### Tesseract Installation (Windows)

1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Choose: `tesseract-ocr-w64-setup-5.x.x.exe`
3. During install, check **"Arabic"** under language data
4. Or download `ara.traineddata` separately to `C:\Program Files\Tesseract-OCR\tessdata\`

---

## 10. Risks & Challenges

### Risk Matrix

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| **Tesseract accuracy low on old kitab PDFs** | High | Likely | Preprocess images aggressively; switch to EasyOCR/Surya as fallback |
| **Arabic tashkeel (harakat) lost in OCR** | Medium | Very Likely | Tesseract doesn't output harakat well; add tashkeel via existing CAMeL Tools pipeline after OCR |
| **Mixed RTL/LTR text issues** | Medium | Moderate | Handle Unicode bidi markers; display Arabic with `dir="rtl"` |
| **Large PDF (500+ pages) performance** | Low | Moderate | Process page-by-page, not bulk; show progress |
| **OCR on image-based PDFs (scanned)** | Low | Certain | PyMuPDF renders pages to images; Tesseract handles them |
| **OCR on text-based PDFs (born-digital)** | Low | Moderate | Try PyMuPDF text extraction first (faster), fallback to OCR if empty |
| **Database corruption** | Low | Low | SQLite WAL mode; regular backups |

### Key Challenge: Tashkeel Preservation

Tesseract is **poor at preserving Arabic diacritics (harakat/tashkeel)**. For kitab texts where harakat are important:

**Solution:** Run OCR text through the existing CAMeL Tools diacritization pipeline (`/api/tashkeel`) after OCR:

```python
def add_tashkeel_to_ocr(text: str) -> str:
    """Add harakat to OCR'd text using existing CAMeL pipeline."""
    import requests
    resp = requests.post("http://localhost:8001/api/tashkeel",
                         json={"text": text})
    return resp.json().get("harakat", text)
```

---

## 11. Final Verdict

### Feasibility

| Question | Answer |
|---|---|
| **Can Tesseract handle Arabic kitab PDFs?** | ⚠️ Yes, with good preprocessing. Expect 80-95% accuracy on clean prints, lower on old manuscripts. |
| **Is SQLite sufficient for storage?** | ✅ Yes, ideal for a desktop app. No server needed. |
| **Can we reuse existing translation engine?** | ✅ Yes, the existing `deep-translator` Google Translate integration works perfectly. |
| **Page-range processing doable?** | ✅ Yes, PyMuPDF makes this trivial. |
| **How long to implement?** | ~2-3 days for v1 (backend + frontend + testing) |
| **Is this a good addition to the app?** | ✅ Yes — turns the app from a text-paste tool into a full kitab reading/translation platform. |

### Recommended Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Penerjemah Kitab                              │
│                                                                     │
│  ┌─────────────────────┐      ┌──────────────────────────────────┐  │
│  │   Tab 1: Analisis   │      │   Tab 2: Scan PDF                │  │
│  │   (existing)        │      │                                  │  │
│  │                     │      │   Upload PDF → PyMuPDF render    │  │
│  │   - Paste text      │      │   → OpenCV preprocess           │  │
│  │   - Tashkeel        │      │   → Tesseract OCR (ara)          │  │
│  │   - Word analysis   │      │   → Post-process text            │  │
│  │   - Dictionary      │      │   → Save to SQLite               │  │
│  │   - Translation     │      │   → Translate via Google API     │  │
│  └─────────────────────┘      │   → Display Arabic + ID side-by- │  │
│                                │     side                          │  │
│                                └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase Priority

| Phase | What | Est. Time | Value |
|:-----:|------|:---------:|:-----:|
| **1** | Backend: PyMuPDF + Tesseract + SQLite endpoints | 2-3 hrs | ⭐⭐⭐ |
| **2** | Frontend: Tab UI + upload + page range + display | 2-3 hrs | ⭐⭐⭐ |
| **3** | Polish: Batch translate, progress bars, confidence | 1-2 hrs | ⭐⭐ |

### Files to Create/Modify

| File | Action | Purpose |
|---|---|---|
| `backend/ocr_engine.py` | **Create** | PDF→image conversion, image preprocessing, Tesseract OCR |
| `backend/ocr_database.py` | **Create** | SQLite database layer for storing OCR results |
| `backend/main.py` | **Modify** | Add `/api/ocr/upload`, `/api/ocr/process`, `/api/ocr/translate` endpoints |
| `frontend/pages/index.vue` | **Modify** | Add tab navigation + Scan PDF tab UI |
| `backend/requirements.txt` | **Modify** | Add pytesseract, pymupdf, opencv-python |

---

*Assessment prepared by researching PyMuPDF, Tesseract OCR 5, EasyOCR, PaddleOCR, SQLite, and the existing Penerjemah Kitab codebase.*
