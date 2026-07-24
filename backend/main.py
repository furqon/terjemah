# backend/main.py — Penerjemah Kitab API
# Tashkeel + word analysis + translation + PDF OCR.

import os
import threading
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from camel_tools.disambig.mle import MLEDisambiguator
from dictionary import lookup as dict_lookup
from dictionary_en import lookup as dict_lookup_en
from ocr_engine import OCREngine, is_tesseract_available, tesseract_version
from ocr_database import OCRDatabase

# ── Upload directory for PDFs ──
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# ── Post-processing helpers ──────────────────────────────────────────

# Arabic sun letters (الحروف الشمسية) — the ل of ال is assimilated and
# the sun letter gets a shadda. CAMeL Tools often misses this.
SUN_LETTERS = set("ت ث د ذ ر ز س ش ص ض ط ظ ل ن")

# Override dictionary: CAMeL Tools diacritization can be imperfect for
# common greetings / fixed expressions. Map input phrase → correct output.
# Add entries here as you find more problematic phrases.
PHRASE_OVERRIDES: dict[str, str] = {
    # Islamic greetings
    "السلام عليكم": "السَّلَامُ عَلَيْكُمْ",
    "السلام عليكم ورحمة الله": "السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ اللَّهِ",
    "السلام عليكم ورحمة الله وبركاته": "السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ اللَّهِ وَبَرَكَاتُهُ",
    "وعليكم السلام": "وَعَلَيْكُمُ السَّلَامُ",
    "بسم الله الرحمن الرحيم": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ",
    "الحمد لله": "الْحَمْدُ لِلَّهِ",
    "الحمدلله": "الْحَمْدُ لِلَّهِ",
    "سبحان الله": "سُبْحَانَ اللَّهِ",
    "ما شاء الله": "مَا شَاءَ اللَّهُ",
    "إن شاء الله": "إِنْ شَاءَ اللَّهُ",
    "بإذن الله": "بِإِذْنِ اللَّهِ",
    "لا إله إلا الله": "لَا إِلَهَ إِلَّا اللَّهُ",
    "محمد": "مُحَمَّدٌ",
    "الله": "اللَّهُ",
}


# Word-level corrections for words CAMeL Tools commonly gets wrong.
# Keys should match the EXACT diacritized form CAMeL outputs (including case endings).
WORD_OVERRIDES: dict[str, str] = {
    # Add entries as you find problematic words: "camel_output": "corrected",
}


def _fix_sun_letter_shadda(word: str) -> str:
    """If word starts with ال + sun letter without shadda, add shadda+fatha."""
    if len(word) >= 4 and word[:2] == "ال" and word[2] in SUN_LETTERS:
        sun_letter = word[2]
        # Check if sun letter already has shadda
        if len(word) > 3 and word[3] != chr(0x0651):
            # Insert shadda + fatha after the sun letter
            # Remove any existing vowel on the sun letter first
            rest = word[3:]
            # If there's a fatha/kasra/damma on the sun letter, remove it
            if rest and rest[0] in (chr(0x064E), chr(0x064F), chr(0x0650)):
                rest = rest[1:]
            word = f"ال{sun_letter}{chr(0x0651)}{chr(0x064E)}{rest}"
    return word


def _postprocess_diacritized(original: str, diacritized: str) -> str:
    """Apply post-processing to fix known CAMeL Tools issues.

    Args:
        original: The original undiacritized input text.
        diacritized: The CAMeL Tools diacritized output.
    """
    # Step 1: Exact phrase overrides — match against ORIGINAL text
    stripped_orig = original.strip()
    if stripped_orig in PHRASE_OVERRIDES:
        return PHRASE_OVERRIDES[stripped_orig]

    # Step 2: Word-by-word post-processing on the diacritized output
    words = diacritized.strip().split()
    fixed_words = []
    for w in words:
        # Check word-level overrides (match against exact CAMeL output form)
        if w in WORD_OVERRIDES:
            w = WORD_OVERRIDES[w]
        # Fix sun letter shadda (applies regardless)
        w = _fix_sun_letter_shadda(w)
        fixed_words.append(w)

    return " ".join(fixed_words)

app = FastAPI(title="Penerjemah Kitab API")

# Allow frontend (localhost:3000) to call backend (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread-safe singleton: each thread gets its own MLEDisambiguator instance
# because it loads large model data that may not be thread-safe.
_thread_local = threading.local()


def get_disambiguator():
    if not hasattr(_thread_local, "disambig"):
        _thread_local.disambig = MLEDisambiguator.pretrained()
    return _thread_local.disambig


def diacritize(text: str, analyses=None) -> str:
    """Add harakat (diacritics) to Arabic text using CAMeL Tools.

    Args:
        text: The undiacritized Arabic text.
        analyses: Optional pre-computed CAMeL analyses to avoid redundant calls.
    """
    if not text.strip():
        return text

    words = text.strip().split()
    if analyses is None:
        disambig = get_disambiguator()
        analyses = disambig.disambiguate(words)

    diacritized_words: list[str] = []
    for idx, word_analyses in enumerate(analyses):
        if word_analyses.analyses:
            best = word_analyses.analyses[0]
            if isinstance(best.analysis, dict):
                diac = best.analysis.get("diac", words[idx])
            else:
                # Fallback: keep original word
                diac = getattr(best.analysis, "diac", words[idx])
            diacritized_words.append(diac)
        else:
            # CAMeL couldn't analyze this word — keep as-is
            diacritized_words.append(words[idx])

    result = " ".join(diacritized_words)
    return _postprocess_diacritized(text, result)


# ── Pydantic models ────────────────────────────────────────────────

class TashkeelRequest(BaseModel):
    text: str


class TashkeelResponse(BaseModel):
    original: str
    harakat: str


class AnalyzeRequest(BaseModel):
    text: str


class WordAnalysis(BaseModel):
    word: str          # Diacritized word form
    lemma: str         # Lexical form (lemma)
    root: str          # Root letters (e.g., كتب)
    pos_type: str      # POS type in English (noun, verb, prep, etc.)
    pos_arabic: str    # POS type in Arabic (إسم, فعل, حرف, etc.)
    gloss_id: str      # Indonesian translation
    gloss_en: str      # English gloss / meaning


class AnalyzeResponse(BaseModel):
    original: str
    harakat: str
    words: list[WordAnalysis]
    word_count: int


# ── POS mapping: CAMeL Tools tags → Arabic labels ─────────────────

POS_MAP: dict[str, str] = {
    'noun': 'إسم',
    'verb': 'فعل',
    'adj': 'صفة',
    'adv': 'ظرف',
    'pron': 'ضمير',
    'dem': 'إشارة',
    'rel': 'موصول',
    'prep': 'حرف جر',
    'conj': 'حرف عطف',
    'part': 'حرف',
    'neg': 'حرف نفي',
    'interr': 'حرف استفهام',
    'det': 'أداة تعريف',
    'num': 'عدد',
    'noun_prop': 'علم',
    'noun_quant': 'كمية',
    'noun_num': 'عدد',
    'abbrev': 'اختصار',
}


# ── Analysis helper ─────────────────────────────────────────────────

def _map_pos(pos_tag: str) -> str:
    """Map a CAMeL Tools POS tag to its Arabic label."""
    if not pos_tag:
        return '—'
    pos_lower = pos_tag.lower().strip()
    if pos_lower in POS_MAP:
        return POS_MAP[pos_lower]
    return pos_tag  # Return raw tag if no mapping


def analyze_words(text: str) -> AnalyzeResponse:
    """Get harakat + word-by-word analysis for Arabic text."""
    if not text.strip():
        return AnalyzeResponse(
            original=text, harakat=text,
            words=[], word_count=0
        )

    # Step 1: Get CAMeL Tools word-level analyses (once, reused for diacritize)
    words = text.strip().split()
    disambig = get_disambiguator()
    analyses = disambig.disambiguate(words)

    # Step 2: Get diacritized text using the SAME analyses (avoids redundant CAMeL call)
    harakat_text = diacritize(text, analyses=analyses)

    # Step 3: Build word list
    word_list: list[WordAnalysis] = []
    harakat_words = harakat_text.split()

    for idx, word_analyses in enumerate(analyses):
        if word_analyses.analyses:
            best = word_analyses.analyses[0]
            if isinstance(best.analysis, dict):
                a = best.analysis
                # Get the diacritized word form (from the harakat output to keep post-processing)
                word_form = harakat_words[idx] if idx < len(harakat_words) else words[idx]
                lemma = a.get('lex', words[idx])
                root = a.get('root', '—')
                pos_tag = a.get('pos', 'unknown')
                # Use Indonesian + English dictionaries for word translations
                gloss_id = dict_lookup(lemma) or '?'
                gloss_en = dict_lookup_en(lemma) or '?'
                pos_arabic = _map_pos(pos_tag)
            else:
                word_form = harakat_words[idx] if idx < len(harakat_words) else words[idx]
                lemma = words[idx]
                root = '—'
                pos_tag = 'unknown'
                pos_arabic = '—'
                gloss_id = ''
                gloss_en = ''
        else:
            word_form = harakat_words[idx] if idx < len(harakat_words) else words[idx]
            lemma = words[idx]
            root = '—'
            pos_tag = 'unknown'
            pos_arabic = '—'
            gloss_id = ''
            gloss_en = ''

        word_list.append(WordAnalysis(
            word=word_form,
            lemma=lemma,
            root=root,
            pos_type=pos_tag,
            pos_arabic=pos_arabic,
            gloss_id=gloss_id,
            gloss_en=gloss_en,
        ))

    return AnalyzeResponse(
        original=text,
        harakat=harakat_text,
        words=word_list,
        word_count=len(word_list),
    )


# ── Translation ────────────────────────────────────────────────────
# Uses deep-translator (free Google Translate API) — instant, no model download.

_translator_lock = threading.Lock()
_translator = None


_translator_en = None


def _get_translators():
    """Get or create both Google Translate translators (thread-safe)."""
    global _translator, _translator_en
    if _translator is not None and _translator_en is not None:
        return _translator, _translator_en
    with _translator_lock:
        if _translator is not None and _translator_en is not None:
            return _translator, _translator_en
        from deep_translator import GoogleTranslator
        _translator = GoogleTranslator(source='ar', target='id')
        _translator_en = GoogleTranslator(source='ar', target='en')
        return _translator, _translator_en


class TranslateRequest(BaseModel):
    text: str


class TranslateResponse(BaseModel):
    source: str
    translation_id: str   # Indonesian translation
    translation_en: str   # English translation
    engine: str = "google-translate"


# ── OCR engine & database singletons ────────────────────────────────
ocr_engine = OCREngine(dpi=300)
ocr_db = OCRDatabase()


# ── Pydantic models for OCR ─────────────────────────────────────────

class OCRHealthResponse(BaseModel):
    tesseract_installed: bool
    tesseract_version: str


class OCRUploadResponse(BaseModel):
    pdf_id: int
    filename: str
    total_pages: int


class OCRProcessRequest(BaseModel):
    pdf_id: int
    page_start: int
    page_end: int


class OCRProcessPage(BaseModel):
    page_number: int
    text: str
    confidence: float


class OCRProcessResponse(BaseModel):
    pdf_id: int
    pages_processed: int
    pages: list[OCRProcessPage]


class OCRTranslateRequest(BaseModel):
    pdf_id: int
    target: str = "id"  # "id", "en", or "both"


class OCRTranslatePageRequest(BaseModel):
    page_id: int
    text: str  # The user-edited Arabic text


class OCRTranslatePage(BaseModel):
    page_number: int
    translation_id: str = ""
    translation_en: str = ""


class OCRTranslateResponse(BaseModel):
    pdf_id: int
    translated: int
    results: list[OCRTranslatePage]


class OCRPDFInfo(BaseModel):
    id: int
    filename: str
    total_pages: int
    uploaded_at: str
    pages_processed: int
    pages_translated: int


# ── API endpoints ───────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/tashkeel", response_model=TashkeelResponse)
def tashkeel(request: TashkeelRequest):
    """Add harakat (diacritics) to Arabic text using CAMeL Tools."""
    result = diacritize(request.text)
    return TashkeelResponse(original=request.text, harakat=result)


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    """Get harakat + word-by-word analysis (lemma, root, POS, gloss)."""
    return analyze_words(request.text)


@app.post("/api/translate", response_model=TranslateResponse)
def translate(request: TranslateRequest):
    """Translate Arabic to Indonesian using Google Translate (free).

    Uses deep-translator library — no model download needed.
    Requires internet connection. Free with reasonable rate limits.
    """
    if not request.text.strip():
        return TranslateResponse(source=request.text, translation_id="", translation_en="")
    try:
        trans_id, trans_en = _get_translators()
        result_id = trans_id.translate(request.text) or ''
        # Small delay to avoid rate limiting on rapid sequential calls
        time.sleep(0.3)
        try:
            result_en = trans_en.translate(request.text) or ''
        except Exception:
            result_en = ''
        return TranslateResponse(source=request.text, translation_id=result_id, translation_en=result_en)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# OCR ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/ocr/health", response_model=OCRHealthResponse)
def ocr_health():
    """Check Tesseract OCR availability."""
    return OCRHealthResponse(
        tesseract_installed=is_tesseract_available(),
        tesseract_version=tesseract_version(),
    )


@app.post("/api/ocr/upload", response_model=OCRUploadResponse)
async def ocr_upload(file: UploadFile = File(...)):
    """Upload a PDF file for OCR processing.

    Accepts .pdf files. Saves to uploads/ and returns pdf_id + page count.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Save with unique filename to avoid collisions
    ext = os.path.splitext(file.filename)[1] or ".pdf"
    unique_name = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / unique_name

    content = await file.read()
    filepath.write_bytes(content)

    total_pages = ocr_engine.get_page_count(str(filepath))
    pdf_id = ocr_db.save_pdf(file.filename, str(filepath), total_pages)

    return OCRUploadResponse(pdf_id=pdf_id, filename=file.filename, total_pages=total_pages)


@app.post("/api/ocr/process", response_model=OCRProcessResponse)
def ocr_process(request: OCRProcessRequest):
    """Run OCR on a range of pages for an uploaded PDF.

    Processes pages page_start through page_end (1-based, inclusive),
    stores results in the database, and returns extracted text.
    """
    pdf = ocr_db.get_pdf(request.pdf_id)
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")
    if not is_tesseract_available():
        raise HTTPException(status_code=503, detail="Tesseract OCR is not installed")

    pages_processed: list[OCRProcessPage] = []
    for page_num, text, confidence in ocr_engine.process_page_range(
        pdf["filepath"], request.page_start, request.page_end
    ):
        ocr_db.save_page(request.pdf_id, page_num, text, text, confidence)
        pages_processed.append(OCRProcessPage(
            page_number=page_num, text=text, confidence=confidence
        ))

    return OCRProcessResponse(
        pdf_id=request.pdf_id,
        pages_processed=len(pages_processed),
        pages=pages_processed,
    )


@app.get("/api/ocr/pdfs", response_model=list[OCRPDFInfo])
def ocr_list_pdfs():
    """List all uploaded PDFs with processing status."""
    pdfs = ocr_db.get_all_pdfs()
    result: list[OCRPDFInfo] = []
    for p in pdfs:
        pages = ocr_db.get_pages_for_pdf(p["id"])
        translated = sum(1 for pg in pages if pg.get("translated_id"))
        result.append(OCRPDFInfo(
            id=p["id"],
            filename=p["filename"],
            total_pages=p["total_pages"],
            uploaded_at=p["uploaded_at"],
            pages_processed=len(pages),
            pages_translated=translated,
        ))
    return result


@app.get("/api/ocr/pages/{pdf_id}")
def ocr_get_pages(pdf_id: int):
    """Get all processed pages for a PDF."""
    pdf = ocr_db.get_pdf(pdf_id)
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")
    pages = ocr_db.get_pages_for_pdf(pdf_id)
    return {
        "pdf_id": pdf_id,
        "filename": pdf["filename"],
        "total_pages": pdf["total_pages"],
        "pages": pages,
    }


@app.post("/api/ocr/translate", response_model=OCRTranslateResponse)
def ocr_translate(request: OCRTranslateRequest):
    """Translate untranslated pages of a PDF."""
    pdf = ocr_db.get_pdf(request.pdf_id)
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    pages = ocr_db.get_untranslated_pages(request.pdf_id)
    if not pages:
        return OCRTranslateResponse(pdf_id=request.pdf_id, translated=0, results=[])

    trans_id, trans_en = _get_translators()
    results: list[OCRTranslatePage] = []

    for page in pages:
        text = page.get("cleaned_text") or page.get("raw_text") or ""
        if not text.strip():
            continue

        try:
            tid = trans_id.translate(text) or ""
        except Exception as e:
            tid = f"[Translation error: {e}]"

        try:
            ten = trans_en.translate(text) or ""
        except Exception:
            ten = ""

        ocr_db.save_translation(page["id"], tid, ten)
        results.append(OCRTranslatePage(
            page_number=page["page_number"],
            translation_id=tid,
            translation_en=ten,
        ))

        # Small delay between translations to avoid rate limiting
        time.sleep(0.3)

    return OCRTranslateResponse(
        pdf_id=request.pdf_id,
        translated=len(results),
        results=results,
    )


@app.post("/api/ocr/translate-page")
def ocr_translate_page(request: OCRTranslatePageRequest):
    """Translate a single page with user-edited Arabic text.

    The user can edit the OCR result in the frontend before sending
    the corrected text here for translation.  Saves the corrected
    text and translation to the database.
    """
    # Efficient direct lookup by page_id
    page_row = ocr_db.get_page_by_id(request.page_id)
    if not page_row:
        raise HTTPException(status_code=404, detail="Page not found")

    if not request.text.strip():
        return OCRTranslatePage(
            page_number=page_row["page_number"],
            translation_id="",
            translation_en="",
        )

    trans_id, trans_en = _get_translators()

    try:
        tid = trans_id.translate(request.text) or ""
    except Exception as e:
        tid = f"[Translation error: {e}]"

    try:
        ten = trans_en.translate(request.text) or ""
    except Exception:
        ten = ""

    # Save both the corrected text and the translation
    ocr_db.save_page(
        page_row["pdf_id"],
        page_row["page_number"],
        page_row.get("raw_text", ""),
        request.text,  # Save the edited text as cleaned_text
        page_row.get("confidence", 0.0),
    )
    ocr_db.save_translation(request.page_id, tid, ten)

    return OCRTranslatePage(
        page_number=page_row["page_number"],
        translation_id=tid,
        translation_en=ten,
    )


@app.post("/api/ocr/delete/{pdf_id}")
def ocr_delete(pdf_id: int):
    """Soft-delete a PDF and its pages."""
    pdf = ocr_db.get_pdf(pdf_id)
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")
    ocr_db.delete_pdf(pdf_id)
    return {"status": "deleted", "pdf_id": pdf_id}


@app.get("/api/ocr/stats")
def ocr_stats():
    """Get summary statistics about OCR processing."""
    stats = ocr_db.get_stats()
    stats["tesseract_installed"] = is_tesseract_available()
    stats["tesseract_version"] = tesseract_version()
    return stats
