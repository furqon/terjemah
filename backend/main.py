# backend/main.py — Step 1: Tashkeel API
# Uses CAMeL Tools MLEDisambiguator for Arabic diacritization.
# Post-processing fixes: sun letter shadda, known phrase overrides, etc.
# Thread-safe: uses threading.local() for per-thread model instances.

import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from camel_tools.disambig.mle import MLEDisambiguator
from dictionary import lookup as dict_lookup


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
                # Use Indonesian dictionary + CAMeL English gloss
                gloss_id = dict_lookup(lemma) or '?'
                gloss_en = a.get('gloss', '') or ''
                pos_arabic = _map_pos(pos_tag)
            else:
                word_form = harakat_words[idx] if idx < len(harakat_words) else words[idx]
                lemma = words[idx]
                root = '—'
                pos_tag = 'unknown'
                pos_arabic = '—'
                gloss = ''
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


# ── NLLB-200 Translation ───────────────────────────────────────────
# Lazy-loaded: model downloads (~1.2GB) on first /api/translate request.

_nllb_lock = threading.Lock()
_nllb_tokenizer = None
_nllb_model = None


def _load_nllb():
    """Load NLLB-200 distilled 600M model (lazy, on first use).

    First call downloads ~1.2GB from HuggingFace Hub.
    Subsequent calls use cached model.
    """
    global _nllb_tokenizer, _nllb_model
    with _nllb_lock:
        if _nllb_model is not None:
            return
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            model_name = "facebook/nllb-200-distilled-600M"
            _nllb_tokenizer = AutoTokenizer.from_pretrained(model_name)
            _nllb_tokenizer.src_lang = "arb_Arab"  # Source: Arabic
            _nllb_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        except Exception as e:
            raise RuntimeError(f"Failed to load NLLB model: {e}")


class TranslateRequest(BaseModel):
    text: str


class TranslateResponse(BaseModel):
    source: str
    translation: str
    model: str = "nllb-200-distilled-600M"


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
    """Translate Arabic to Indonesian using NLLB-200.

    First call downloads model (~1.2GB); subsequent calls are fast.
    """
    if not request.text.strip():
        return TranslateResponse(source=request.text, translation="")
    try:
        _load_nllb()
        inputs = _nllb_tokenizer(request.text, return_tensors="pt", truncation=True, max_length=512)
        translated_tokens = _nllb_model.generate(
            **inputs,
            forced_bos_token_id=_nllb_tokenizer.convert_tokens_to_ids("ind_Latn"),
            max_length=512,
        )
        result = _nllb_tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
        return TranslateResponse(source=request.text, translation=result)
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
