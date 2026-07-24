# backend/main.py — Step 1: Tashkeel API
# Uses CAMeL Tools MLEDisambiguator for Arabic diacritization.
# Post-processing fixes: sun letter shadda, known phrase overrides, etc.
# Thread-safe: uses threading.local() for per-thread model instances.

import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from camel_tools.disambig.mle import MLEDisambiguator


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


def diacritize(text: str) -> str:
    """Add harakat (diacritics) to Arabic text using CAMeL Tools."""
    if not text.strip():
        return text

    words = text.strip().split()
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


class TashkeelRequest(BaseModel):
    text: str


class TashkeelResponse(BaseModel):
    original: str
    harakat: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/tashkeel", response_model=TashkeelResponse)
def tashkeel(request: TashkeelRequest):
    """Add harakat (diacritics) to Arabic text using CAMeL Tools."""
    result = diacritize(request.text)
    return TashkeelResponse(original=request.text, harakat=result)
