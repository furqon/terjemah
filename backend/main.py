# backend/main.py — Penerjemah Kitab API
# Tashkeel + word analysis + translation + PDF OCR.

import os
import re
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
from sarf_client import SarfClient

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
    # Verb vs noun: CAMeL often prefers noun/masdar reading for common verbs
    # in simple VSO sentences like "ضرب زيد عمر".
    'ضَرْبِ': 'ضَرَبَ',   # ضرب as past tense "he hit" (not the masdar "hitting")
    'ضَرْبَ': 'ضَرَبَ',   # Accusative case variant
    'ضَرْبُ': 'ضَرَبَ',   # Nominative case variant
}


# Root corrections: CAMeL Tools uses '#' for weak radicals (و/ي) it cannot
# determine. Map problematic CAMeL roots → corrected roots here.
# Add entries as you encounter more words with '#' in the root.
ROOT_OVERRIDES: dict[str, str] = {
    # Common form III verbs (wazn فاعل) where the middle radical is weak
    'ش.#.ر': 'ش.و.ر',  # شاوَر / مشاورة / يتشاور (root: ش و ر — counsel/consult)
    # Prepositions / defective words where the final radical is weak
    'ع.ل.#': 'ع.ل.و',  # عَلَى / عليكم (root: ع ل و — on/above)
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

# Allow frontends on ports 3000 or 3001 to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Preload NLLB-200 model on startup (non-blocking background thread)
# so the first translation request doesn't time out while downloading ~1.2 GB.
@app.on_event("startup")
async def _preload_nllb():
    import threading as _th
    _th.Thread(target=_background_load_nllb, daemon=True).start()


def _background_load_nllb():
    """Download & cache the NLLB-200 model in the background."""
    import logging as _log
    _log.info("Background: pre-loading NLLB-200 model...")
    try:
        from nllb_translator import NLLBTranslator
        NLLBTranslator().is_available  # triggers download
        _log.info("Background: NLLB-200 model loaded.")
    except Exception as exc:
        _log.warning("Background: NLLB-200 preload failed: %s", exc)

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


class Morpheme(BaseModel):
    """A single morpheme within a word (e.g., prefix, stem, suffix/pronoun)."""
    text: str       # Arabic text of the morpheme
    tag: str        # POS tag (PREP, PRON_2MP, PV, etc.)
    gloss: str      # English gloss for this morpheme
    root: str       # Root letters (only for lexical morphemes; '—' for affixes)


class WordAnalysis(BaseModel):
    word: str          # Diacritized word form
    lemma: str         # Lexical form (lemma)
    root: str          # Root letters (e.g., كتب)
    pos_type: str      # POS type in English (noun, verb, prep, etc.)
    pos_arabic: str    # POS type in Arabic (إسم, فعل, حرف, etc.)
    gloss_id: str      # Indonesian translation
    gloss_en: str      # English gloss / meaning
    morphemes: list[Morpheme] = []  # Morpheme breakdown (prefixes, stems, suffixes/pronouns)


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


# Tags that carry a lexical root (verbs, nouns, adjectives)
_LEXICAL_ROOT_TAGS = frozenset({
    'PV', 'IV', 'NOUN', 'NOUN_PROP', 'NOUN_QUANT', 'NOUN_NUM',
    'ADJ',
})


def _is_lexical_morpheme(tag: str) -> bool:
    """Check if a CAMeL morpheme tag represents a lexical stem (verb/noun)."""
    if not tag:
        return False
    # Extract the base tag (before ':' or '_' suffix)
    base = tag.split(':')[0].split('_')[0]
    return base in _LEXICAL_ROOT_TAGS


def _parse_morphemes_from_bw(bw: str, gloss: str, word_root: str = '') -> list[dict]:
    """Parse CAMeL Tools bw and gloss fields into morpheme objects.

    The bw field uses '+' to separate morphemes. Each morpheme has
    Arabic text + '/' + POS tag (e.g., عَلَي/PREP+كُم/PRON_2MP).
    The gloss field also uses '+' to separate per-morpheme glosses.

    Args:
        bw: Buckwalter-encoded morpheme sequence.
        gloss: Per-morpheme English glosses.
        word_root: Root letters for the whole word; assigned only to
                   lexical morphemes (verbs, nouns). Affixes get '—'.

    Returns a list of dicts with keys: text, tag, gloss, root.
    Returns empty list if the word is a single morpheme (no + in bw).
    """
    if not bw or '+' not in bw:
        return []

    parts = bw.split('+')
    gloss_parts = gloss.split('+') if gloss else []

    morphemes: list[dict] = []
    for i, part in enumerate(parts):
        # Split by the LAST '/' to separate Arabic text from tag
        seg = part.rsplit('/', 1)
        text = seg[0]
        tag = seg[1] if len(seg) > 1 else ''

        # Get corresponding gloss, cleaning up Buckwalter placeholders
        m_gloss = ''
        if i < len(gloss_parts):
            m_gloss = gloss_parts[i].strip('_')

        # Root: only for lexical morphemes
        m_root = word_root if _is_lexical_morpheme(tag) else '—'

        morphemes.append({'text': text, 'tag': tag, 'gloss': m_gloss, 'root': m_root})

    return morphemes


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
                word_form = harakat_words[idx] if idx < len(harakat_words) else words[idx]
                lemma = a.get('lex', words[idx])
                root = a.get('root', '—')
                # Apply root overrides to fix '#' placeholders from CAMeL
                root = ROOT_OVERRIDES.get(root, root)
                pos_tag = a.get('pos', 'unknown')
                gloss_id = dict_lookup(lemma) or '?'
                gloss_en = dict_lookup_en(lemma) or '?'
                pos_arabic = _map_pos(pos_tag)
                morpheme_data = _parse_morphemes_from_bw(
                    a.get('bw', ''),
                    a.get('gloss', ''),
                    word_root=root
                )
            else:
                word_form = harakat_words[idx] if idx < len(harakat_words) else words[idx]
                lemma = words[idx]
                root = '—'
                pos_tag = 'unknown'
                pos_arabic = '—'
                gloss_id = ''
                gloss_en = ''
                morpheme_data = []
        else:
            word_form = harakat_words[idx] if idx < len(harakat_words) else words[idx]
            lemma = words[idx]
            root = '—'
            pos_tag = 'unknown'
            pos_arabic = '—'
            gloss_id = ''
            gloss_en = ''
            morpheme_data = []

        word_list.append(WordAnalysis(
            word=word_form,
            lemma=lemma,
            root=root,
            pos_type=pos_tag,
            pos_arabic=pos_arabic,
            gloss_id=gloss_id,
            gloss_en=gloss_en,
            morphemes=[Morpheme(**m) for m in morpheme_data],
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


def _translate_safe(google_translator, text: str) -> str | None:
    """Try Google Translate for a single text, returning None on failure."""
    try:
        result = google_translator.translate(text) or ""
        return result if result else None
    except Exception:
        return None


def _translate_id_fallback(text: str) -> tuple[str, str]:
    """Translate Arabic → Indonesian. Google first, then NLLB-200.

    Returns:
        (translated_text, engine_name)
    """
    if not text.strip():
        return "", "none"

    # Try Google first
    trans_id, _ = _get_translators()
    result = _translate_safe(trans_id, text)
    if result is not None:
        return result, "google-translate"

    # Fallback to NLLB-200 offline
    try:
        from nllb_translator import NLLBTranslator
        nllb = NLLBTranslator()
        return nllb.translate(text, target="id"), "nllb-200"
    except Exception as e:
        return f"[Translation unavailable: {e}]", "error"


def _translate_en_fallback(text: str) -> tuple[str, str]:
    """Translate Arabic → English. Google first, then NLLB-200.

    Returns:
        (translated_text, engine_name)
    """
    if not text.strip():
        return "", "none"

    # Try Google first
    _, trans_en = _get_translators()
    result = _translate_safe(trans_en, text)
    if result is not None:
        return result, "google-translate"

    # Fallback to NLLB-200 offline
    try:
        from nllb_translator import NLLBTranslator
        nllb = NLLBTranslator()
        return nllb.translate(text, target="en"), "nllb-200"
    except Exception as e:
        return f"[Translation unavailable: {e}]", "error"


class TranslateRequest(BaseModel):
    text: str


class TranslateResponse(BaseModel):
    source: str
    translation_id: str   # Indonesian translation
    translation_en: str   # English translation
    engine: str = "google-translate"


# ── Sarf morphology client ───────────────────────────────────────────
sarf_client = SarfClient()


# ── Pydantic models for Sarf ─────────────────────────────────────────

class SarfAnalyzeRequest(BaseModel):
    root: str  # 3 Arabic letters
    bab: int = 1  # Conjugation class 1-6


class SarfConjugationRow(BaseModel):
    pronoun: str
    text: str


class SarfAnalyzeResponse(BaseModel):
    root: str
    bab: int
    classification: str
    past_tense: list[SarfConjugationRow]
    present_tense: list[SarfConjugationRow]
    present_subjunctive: list[SarfConjugationRow]
    present_jussive: list[SarfConjugationRow]
    masdars: list[str]


# ── Tashrif endpoint models ───────────────────────────────────────────

class TashrifAnalyzeRequest(BaseModel):
    root: str  # Arabic root letters (3 or 4)
    word: str = ""  # Optional: the inflected word form for Rumus classification
    bab: int | None = None  # Optional bab override


class TashrifRow(BaseModel):
    form_number: int
    form_name: str
    form_label_ar: str = ""
    form_label_id: str = ""
    value: str = ""
    source: str = ""
    translation_id: str = ""
    translation_en: str = ""


class TashrifLughowiRow(BaseModel):
    pronoun: str
    text: str = ""
    description: str = ""


class TashrifAnalyzeResponse(BaseModel):
    root: str
    rumus: str
    bab: int
    classification: str = ""
    meaning_pattern: str = ""
    confidence: float = 0.0
    root_meaning: dict[str, str] = {}
    rumus_semantic: dict[str, str] = {}
    verb_base: dict[str, str] = {}
    ishthilahi_table: list[TashrifRow] = []
    lughowi: dict[str, list[TashrifLughowiRow]] = {}
    current_form: dict = {}


# ── OCR engine & database singletons ────────────────────────────────
ocr_engine = OCREngine(dpi=300)
ocr_db = OCRDatabase()


# ── Pydantic models for OCR ─────────────────────────────────────────

class OCRHealthResponse(BaseModel):
    tesseract_installed: bool
    tesseract_version: str
    nllb_available: bool = False


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


class OCRSavePageRequest(BaseModel):
    page_id: int
    text: str  # The edited Arabic text to save


class OCRTashkeelPageRequest(BaseModel):
    text: str  # Arabic text to diacritize


class OCRTashkeelPageResponse(BaseModel):
    original: str
    harakat: str


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


# ── Paragraph models ───────────────────────────────────────────────────

class OCRParagraphItem(BaseModel):
    index: int
    arabic: str
    translation_id: str = ""
    translation_en: str = ""


class OCRTranslateParagraphsRequest(BaseModel):
    page_id: int
    text: str  # Full page text to split into paragraphs


class OCRTranslateParagraphsResponse(BaseModel):
    page_id: int
    page_number: int
    paragraphs: list[OCRParagraphItem]
    total: int


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

    Falls back to NLLB-200 offline model when Google is unavailable.
    """
    if not request.text.strip():
        return TranslateResponse(source=request.text, translation_id="", translation_en="")

    result_id, engine_id = _translate_id_fallback(request.text)
    # Small delay to avoid rate limiting before English call
    time.sleep(0.3)
    result_en, engine_en = _translate_en_fallback(request.text)

    engine = f"{engine_id}+{engine_en}" if engine_id != engine_en else engine_id
    return TranslateResponse(
        source=request.text,
        translation_id=result_id,
        translation_en=result_en,
        engine=engine,
    )


# ── Sarf (Arabic morphology) endpoint ───────────────────────────────────

@app.post("/api/sarf/analyze", response_model=SarfAnalyzeResponse)
def sarf_analyze(request: SarfAnalyzeRequest):
    """Analyze a triliteral Arabic root using the Sarf morphology engine.

    Returns full conjugation tables (past, present, imperative), derived
    nouns, and gerunds for the given root.
    """
    if not sarf_client.is_available():
        raise HTTPException(
            status_code=503,
            detail="Sarf morphology engine not available. Ensure Java 17+ is installed and sarf-source is compiled."
        )

    # Clean root: strip dots and non-Arabic markers (CAMeL Tools returns "س.ل.م" format)
    clean_root = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', '', request.root)
    if len(clean_root) < 3 or len(clean_root) > 4:
        raise HTTPException(status_code=400, detail=f"Root must be 3 or 4 Arabic letters, got '{clean_root}' ({len(clean_root)} chars)")

    try:
        raw = sarf_client.analyze(clean_root, request.bab)

        def _dict_to_rows(data: dict) -> list[SarfConjugationRow]:
            return [SarfConjugationRow(pronoun=k, text=v) for k, v in data.items()]

        return SarfAnalyzeResponse(
            root=raw.get("root", clean_root),
            bab=raw.get("bab", request.bab),
            classification=raw.get("classification", ""),
            past_tense=_dict_to_rows(raw.get("pastTense", {})),
            present_tense=_dict_to_rows(raw.get("presentTense", {})),
            present_subjunctive=_dict_to_rows(raw.get("presentSubjunctive", {})),
            present_jussive=_dict_to_rows(raw.get("presentJussive", {})),
            masdars=raw.get("masdars", []),
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Tashrif Ishthilahi (morphology) endpoint ────────────────────────────

@app.post("/api/tashrif/analyze", response_model=TashrifAnalyzeResponse)
def tashrif_analyze(request: TashrifAnalyzeRequest):
    """Analyze an Arabic root using the Tashrif Ishthilahi system.

    Returns the 8-column Ishthilahi table with Indonesian & English
    translations, plus full Lughowi (pronoun) conjugation tables.

    Uses the Python-based tashrif engine (Phases 1-4).
    """
    # Clean root
    clean_root = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', '', request.root)
    if len(clean_root) < 3 or len(clean_root) > 4:
        raise HTTPException(
            status_code=400,
            detail=f"Root must be 3 or 4 Arabic letters, got '{clean_root}' ({len(clean_root)} chars)"
        )

    try:
        from tashrif_pipeline import tashrif_analyze as pipeline_analyze
        from tashrif_translate import translate_ishthilahi
        from tashrif_lughowi import conjugate_lughowi
        from tashrif_classifier import RUMUS_CLASSIFICATION

        # Determine root length for default classification
        root_len = len(clean_root) if clean_root else 0

        # Step 1: Classify + generate the Ishthilahi table
        pip_result = pipeline_analyze(
            request.word or "",
            root=clean_root,
            bab=request.bab,
        )

        rumus = pip_result.get("rumus", "")
        bab = pip_result.get("bab", 1) if request.bab is None else request.bab

        if not rumus:
            # No word form provided or classification failed.
            # Fallback: infer Rumus from root length
            if root_len == 4:
                rumus = "4D"
                bab = request.bab or 1
            elif root_len == 3:
                # Use provided bab, or default to 3A (فتح يفتح — most common)
                bab = request.bab or 1
                if bab == 1:
                    rumus = "3A"
                elif bab == 2:
                    rumus = "3B"
                elif bab == 3:
                    rumus = "3C"
                elif bab == 4:
                    rumus = "3A"
                elif bab == 5:
                    rumus = "3B"
                elif bab == 6:
                    rumus = "3C"
                else:
                    rumus = "3A"
            # Regenerate with explicit rumus + bab
            from tashrif_generator import generate_ishthilahi
            gen_result = generate_ishthilahi(clean_root, rumus, bab)
            pip_result = {
                "root": clean_root,
                "rumus": rumus,
                "bab": bab,
                "classification": RUMUS_CLASSIFICATION.get(rumus, ""),
                "ishthilahi_table": gen_result.get("table", []),
                "ishthilahi_dict": gen_result.get("table_dict", {}),
                "meaning_pattern": "",
                "confidence": 0.7,
                "current_form": {},
                "stem": "",
                "reasons": [f"Root-only classification: {root_len}-letter root → Rumus {rumus}"],
            }

        root_found = pip_result.get("root", clean_root) or clean_root

        # Step 2: Add translations
        table_dict = pip_result.get("ishthilahi_dict", {})
        trans_result = translate_ishthilahi(
            root_found, rumus, bab, table_dict,
        ) if rumus else {}

        # Step 3: Generate Lughowi conjugation
        lughowi_result = {}
        if rumus:
            try:
                lughowi_result = conjugate_lughowi(root_found, rumus, bab)
            except Exception:
                lughowi_result = {}

        # Step 4: Build response — use the generated Ishthilahi table as-is
        # (always shows the standard base 3rd person masculine singular forms)
        table_rows = []
        for row in pip_result.get("ishthilahi_table", []):
            fn = row.get("form_name", "")
            trans_id = ""
            trans_en = ""
            if trans_result:
                td = trans_result.get("translations_dict", {})
                trans_id = td.get("id", {}).get(fn, "")
                trans_en = td.get("en", {}).get(fn, "")

            table_rows.append(TashrifRow(
                form_number=row.get("form_number", 0),
                form_name=fn,
                form_label_ar=row.get("form_label_ar", ""),
                form_label_id=row.get("form_label_id", ""),
                value=row.get("value", ""),
                source=row.get("source", ""),
                translation_id=trans_id,
                translation_en=trans_en,
            ))

        # Build lughowi tables
        lughowi_out: dict[str, list[TashrifLughowiRow]] = {}
        for tense_key in ["past_tense", "present_tense", "present_subjunctive",
                          "present_jussive", "imperative", "nahi"]:
            rows = lughowi_result.get(tense_key, [])
            lughowi_out[tense_key] = [
                TashrifLughowiRow(
                    pronoun=r.get("pronoun", ""),
                    text=r.get("text", ""),
                    description=r.get("description", ""),
                ) for r in rows
            ]

        classification = pip_result.get("classification", "")
        if not classification and rumus:
            classification = RUMUS_CLASSIFICATION.get(rumus, f"Rumus {rumus}")

        root_meaning = trans_result.get("root_meaning", {"id": "", "en": ""}) if trans_result else {"id": "", "en": ""}
        rumus_semantic = trans_result.get("rumus_semantic", {"id": "", "en": ""}) if trans_result else {"id": "", "en": ""}
        verb_base = trans_result.get("verb_base", {"id": "", "en": ""}) if trans_result else {"id": "", "en": ""}

        return TashrifAnalyzeResponse(
            root=root_found,
            rumus=rumus,
            bab=bab,
            classification=classification,
            meaning_pattern=pip_result.get("meaning_pattern", ""),
            confidence=pip_result.get("confidence", 0.0),
            root_meaning=root_meaning,
            rumus_semantic=rumus_semantic,
            verb_base=verb_base,
            ishthilahi_table=table_rows,
            lughowi=lughowi_out,
            current_form=pip_result.get("current_form", {}),
        )

    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Tashrif engine not available: {e}. Ensure all backend modules are installed."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# OCR ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/ocr/health", response_model=OCRHealthResponse)
def ocr_health():
    """Check Tesseract OCR availability."""
    from nllb_translator import NLLBTranslator
    return OCRHealthResponse(
        tesseract_installed=is_tesseract_available(),
        tesseract_version=tesseract_version(),
        nllb_available=NLLBTranslator().is_available,
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

    results: list[OCRTranslatePage] = []

    for page in pages:
        text = page.get("cleaned_text") or page.get("raw_text") or ""
        if not text.strip():
            continue

        tid, _engine_id = _translate_id_fallback(text)
        time.sleep(0.3)
        ten, _engine_en = _translate_en_fallback(text)

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

    tid, _engine_id = _translate_id_fallback(request.text)
    ten, _engine_en = _translate_en_fallback(request.text)

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


@app.post("/api/ocr/save-page")
def ocr_save_page(request: OCRSavePageRequest):
    """Save edited Arabic text for a page without translating.

    The user can fix OCR mistakes and save the corrected text
    to the database before running tashkeel or translate.
    """
    page_row = ocr_db.get_page_by_id(request.page_id)
    if not page_row:
        raise HTTPException(status_code=404, detail="Page not found")

    ocr_db.save_page(
        page_row["pdf_id"],
        page_row["page_number"],
        page_row.get("raw_text", ""),
        request.text,
        page_row.get("confidence", 0.0),
    )
    return {"status": "saved", "page_id": request.page_id}


@app.post("/api/ocr/tashkeel-page", response_model=OCRTashkeelPageResponse)
def ocr_tashkeel_page(request: OCRTashkeelPageRequest):
    """Add harakat (diacritics) to OCR text using CAMeL Tools.

    Tesseract OCR output often lacks diacritics. This endpoint
    runs the existing CAMeL Tools diacritization pipeline on the
    text so users see proper harakat before translating.
    """
    if not request.text.strip():
        return OCRTashkeelPageResponse(original=request.text, harakat=request.text)
    result = diacritize(request.text)
    return OCRTashkeelPageResponse(original=request.text, harakat=result)


@app.post("/api/ocr/delete/{pdf_id}")
def ocr_delete(pdf_id: int):
    """Soft-delete a PDF and its pages."""
    pdf = ocr_db.get_pdf(pdf_id)
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")
    ocr_db.delete_pdf(pdf_id)
    return {"status": "deleted", "pdf_id": pdf_id}


# ── Paragraph-level translation ─────────────────────────────────────


def _split_paragraphs(text: str) -> list[str]:
    """Split Arabic text into paragraphs.

    Splits on double newlines first (true paragraph breaks),
    then further splits on single newlines for OCR text where
    each line is typically a separate paragraph/verse.

    Returns a list of non-empty stripped paragraphs.
    """
    if not text.strip():
        return []

    # Try double newlines first (true paragraph breaks)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # If that yields only one block, try single newlines
    if len(paragraphs) <= 1 and "\n" in text:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    # Filter out very short lines (likely noise)
    paragraphs = [p for p in paragraphs if len(p) > 2]

    return paragraphs if paragraphs else [text.strip()]


@app.post("/api/ocr/translate-paragraphs", response_model=OCRTranslateParagraphsResponse)
def ocr_translate_paragraphs(request: OCRTranslateParagraphsRequest):
    """Split page text into paragraphs, translate each individually.

    Takes a page_id and page text, splits by newlines into paragraphs,
    translates each paragraph to Indonesian and English, saves to the
    paragraphs table, and returns the results.
    """
    page_row = ocr_db.get_page_by_id(request.page_id)
    if not page_row:
        raise HTTPException(status_code=404, detail="Page not found")

    if not request.text.strip():
        return OCRTranslateParagraphsResponse(
            page_id=request.page_id,
            page_number=page_row["page_number"],
            paragraphs=[],
            total=0,
        )

    # Split into paragraphs
    paragraphs = _split_paragraphs(request.text)

    # Remove old paragraphs for this page before inserting new ones
    ocr_db.delete_paragraphs_for_page(request.page_id)

    # Persist the (possibly user-edited) text back to the pages table
    ocr_db.save_page(
        page_row["pdf_id"],
        page_row["page_number"],
        page_row.get("raw_text", ""),
        request.text,
        page_row.get("confidence", 0.0),
    )

    results: list[OCRParagraphItem] = []
    for idx, para_text in enumerate(paragraphs):
        tid, _engine_id = _translate_id_fallback(para_text)
        time.sleep(0.3)
        ten, _engine_en = _translate_en_fallback(para_text)

        ocr_db.save_paragraph(
            request.page_id, idx, para_text, tid, ten,
        )

        results.append(OCRParagraphItem(
            index=idx,
            arabic=para_text,
            translation_id=tid,
            translation_en=ten,
        ))

        # Small delay between translations to avoid rate limiting
        time.sleep(0.3)

    # Also save the overall page-level translation (concatenated)
    full_id = " ".join([p.translation_id for p in results])
    full_en = " ".join([p.translation_en for p in results])
    ocr_db.save_translation(request.page_id, full_id, full_en)

    return OCRTranslateParagraphsResponse(
        page_id=request.page_id,
        page_number=page_row["page_number"],
        paragraphs=results,
        total=len(results),
    )


@app.get("/api/ocr/paragraphs/{page_id}", response_model=OCRTranslateParagraphsResponse)
def ocr_get_paragraphs(page_id: int):
    """Get saved paragraph translations for a page."""
    page_row = ocr_db.get_page_by_id(page_id)
    if not page_row:
        raise HTTPException(status_code=404, detail="Page not found")

    rows = ocr_db.get_paragraphs_for_page(page_id)
    paragraphs = [
        OCRParagraphItem(
            index=r["paragraph_index"],
            arabic=r["arabic_text"],
            translation_id=r.get("translation_id", "") or "",
            translation_en=r.get("translation_en", "") or "",
        )
        for r in rows
    ]

    return OCRTranslateParagraphsResponse(
        page_id=page_id,
        page_number=page_row["page_number"],
        paragraphs=paragraphs,
        total=len(paragraphs),
    )



@app.get("/api/ocr/stats")
def ocr_stats():
    """Get summary statistics about OCR processing."""
    stats = ocr_db.get_stats()
    stats["tesseract_installed"] = is_tesseract_available()
    stats["tesseract_version"] = tesseract_version()
    return stats
