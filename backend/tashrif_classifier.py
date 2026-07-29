"""
tashrif_classifier.py — Rumus (Formula) Classifier for Tashrif Ishthilahi.

Determines which Rumus pattern (3A through 6) an Arabic word belongs to
based on its stem structure, root letters, and morphological features.

Reference: "At-Tashrif Al-Mujaz" by Andy Satiyo Ahmad (docs/tashrif.pdf)
Logic: docs/wazan.md — Al-Arabiyyah Al-Qaribah method

Rumus Overview:
  Rumus 3A-C:  Fi'il Tsulatsi Mujarrad  (basic 3-letter verbs)
  Rumus 4A-D:  augmented with 1 extra letter, or 4-letter base
  Rumus 5A-E:  augmented with 2 extra letters
  Rumus 6:     augmented with 3 extra letters (istaf'ala)

Known Limitations (Phase 1):
  - Madhi-only R3B/C → defaults to R3A (needs mudhari' form to disambiguate)
  - R4B (فاعل) ↔ Ism Fa'il of R3 (فَاعِل) — same structural pattern
  - 4C mudhari' (يُفْعِلُ) → R3 — hamzah prefix drops, stem = root only
  - Weak/defective/hamzated roots may produce unexpected patterns

Usage:
    from tashrif_classifier import classify_rumus
    result = classify_rumus("يَكتُبُ", root="كتب")
    print(result.rumus, result.form, result.confidence)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# ── Try to import pyarabic (soft dependency — improves stripping) ──────────

try:
    import pyarabic.araby as araby
    HAS_PYARABIC = True
except ImportError:
    HAS_PYARABIC = False


# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

# Arabic letters (Unicode)
HAMZA      = "\u0621"  # ء
ALIF       = "\u0627"  # ا
ALIF_HAMZA = "\u0623"  # أ
ALIF_MAKS  = "\u0649"  # ى
BA         = "\u0628"  # ب
TA         = "\u062A"  # ت
THA        = "\u062B"  # ث
LAM        = "\u0644"  # ل
NUN        = "\u0646"  # ن
SIN        = "\u0633"  # س
MEEM       = "\u0645"  # م
YA         = "\u064A"  # ي

# Diacritics
SHADDA = "\u0651"  # ّ
SUKUN  = "\u0652"  # ْ
FATHA  = "\u064E"  # َ
KASRA  = "\u0650"  # ِ
DAMMA  = "\u064F"  # ُ

# All Arabic letters for validation (includes hamza variants)
ARABIC_LETTERS = frozenset(
    "ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأؤإئىة"
)

# All diacritics to strip when analysing letter patterns
TASHKEEL_CHARS = frozenset({
    FATHA, KASRA, DAMMA,
    "\u064B", "\u064C", "\u064D",  # tanwin
    SHADDA, SUKUN, "\u0670",
})

# ── Prefix sets ──────────────────────────────────────────────────────────
# Mudhari' person prefixes (NOT including bare alif ا which can be stem)
# The actual prefixes are: أ (1st sg), ن (1st pl), ي (3rd masc), ت (2nd)
MUDHARI_PREFIXES = frozenset({ALIF_HAMZA, NUN, YA, TA})

# Amr prefix: bare alif (ا)
AMR_PREFIX = ALIF

# Future prefix: سـ or سَ
FUTURE_PREFIX = SIN

# Negation prefix: لا
NAHI = "\u0644\u0627"  # لا

# ── Common suffixes (ordered longest-first to avoid partial matches) ────
SUFFIXES = [
    "\u062A\u0645\u0627",    # تما
    "\u062A\u064F\u0645",    # تم
    "\u062A\u064F\u0646\u0651",  # تنّ
    "\u0648\u064F\u0627",    # وا
    "\u0648\u0646",          # ون (masculine plural)
    "\u064A\u0646",          # ين
    "\u0646\u0627",          # نا
    "\u0627\u062A",          # ات
    "\u062A\u0645",          # تم (without damma)
    "\u062A\u0646",          # تن
    "\u0643\u0645",          # كم
    "\u0647\u0645",          # هم
    "\u0647\u0627",          # ها
    "\u062A",                # ت
    "\u0627",                # ا (dual marker)
    "\u0646",                # ن
    "\u0648",                # و
    "\u0643",                # ك
    "\u0647",                # ه
]

# Hamza / alif variants for normalisation
ALIF_VARIANTS = frozenset({ALIF, ALIF_HAMZA, "\u0622", "\u0625", "\u0621"})


# ═══════════════════════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════════════════════

class FormNumber(Enum):
    """The 8 columns of Tashrif Ishthilahi."""
    FIIL_MADHI    = 1
    FIIL_MUDHARI  = 2
    FIIL_AMR      = 3
    FIIL_NAHI     = 4
    MASHDAR       = 5
    ISM_FAIL      = 6
    ISM_MAFUL     = 7
    ZAMAMI        = 8


FORM_LABELS: dict[FormNumber, str] = {
    FormNumber.FIIL_MADHI:   "الفعل الماضي",
    FormNumber.FIIL_MUDHARI: "الفعل المضارع",
    FormNumber.FIIL_AMR:     "فعل الأمر",
    FormNumber.FIIL_NAHI:    "فعل النهي",
    FormNumber.MASHDAR:      "المصدر",
    FormNumber.ISM_FAIL:     "اسم الفاعل",
    FormNumber.ISM_MAFUL:    "اسم المفعول",
    FormNumber.ZAMAMI:       "الزمني (ظرف زمان/مکان)",
}

FORM_LABELS_ID: dict[FormNumber, str] = {
    FormNumber.FIIL_MADHI:   "telah ...",
    FormNumber.FIIL_MUDHARI: "sedang/akan ...",
    FormNumber.FIIL_AMR:     "... lah",
    FormNumber.FIIL_NAHI:    "jangan ...",
    FormNumber.MASHDAR:      "pe ... an",
    FormNumber.ISM_FAIL:     "yang me ...",
    FormNumber.ISM_MAFUL:    "yang di ...",
    FormNumber.ZAMAMI:       "waktu/tempat ...",
}

# Rumus codes
R3A, R3B, R3C = "3A", "3B", "3C"
R4A, R4B, R4C, R4D = "4A", "4B", "4C", "4D"
R5A, R5B, R5C, R5D, R5E = "5A", "5B", "5C", "5D", "5E"
R6 = "6"

ALL_RUMUS = [R3A, R3B, R3C, R4A, R4B, R4C, R4D, R5A, R5B, R5C, R5D, R5E, R6]

RUMUS_CLASSIFICATION: dict[str, str] = {
    R3A: "Fi'il Tsulatsi Mujarrad — فتح يفتح (Bab 1)",
    R3B: "Fi'il Tsulatsi Mujarrad — ضرب يضرب (Bab 2)",
    R3C: "Fi'il Tsulatsi Mujarrad — نصر ينصر (Bab 3)",
    R4A: "Fi'il Mazid bi Harf — تفعيل (Fa''ala)",
    R4B: "Fi'il Mazid bi Harf — مفاعلة (Fa'ala)",
    R4C: "Fi'il Mazid bi Harf — إفعال (Af'ala)",
    R4D: "Fi'il Ruba'i Mujarrad — فعللة (Fa'lala)",
    R5A: "Fi'il Mazid bi Harfayn — تفعل (Tafa''ala)",
    R5B: "Fi'il Mazid bi Harfayn — تفاعل (Tafa'ala)",
    R5C: "Fi'il Mazid bi Harfayn — افتعال (Ifta'ala)",
    R5D: "Fi'il Mazid bi Harfayn — انفعال (Infa'ala)",
    R5E: "Fi'il Mazid bi Harfayn — افعلال (If'alla)",
    R6:  "Fi'il Mazid bi Tsalatsat Ahruf — استفعال (Istaf'ala)",
}

RUMUS_MEANING: dict[str, str] = {
    R3A: "Root meaning (fi'il tsulatsi mujarrad)",
    R3B: "Root meaning (fi'il tsulatsi mujarrad)",
    R3C: "Root meaning (fi'il tsulatsi mujarrad)",
    R4A: "Membuat jadi / mengulang (men...kan)",
    R4B: "Saling / berbalasan (ber...an)",
    R4C: "Menjadikan / transitif (me...kan)",
    R4D: "Root meaning (4-letter verb)",
    R5A: "Intransitif / refleksif (ber...)",
    R5B: "Saling melakukan (saling ber...)",
    R5C: "Melakukan pada diri sendiri (ber...)",
    R5D: "Pasif / intransitif (ter...)",
    R5E: "Menjadi warna/sifat (menjadi ...)",
    R6:  "Meminta / menganggap (meminta ...)",
}

@dataclass
class RumusResult:
    """Classification result for a single Arabic word."""
    word: str
    root: str
    rumus: str
    form: int
    form_label: str
    form_label_id: str
    classification: str
    meaning_pattern: str
    confidence: float
    stem: str = ""
    reasons: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# Arabic Text Utilities
# ═══════════════════════════════════════════════════════════════════════════

def strip_tashkeel(text: str) -> str:
    """Remove Arabic diacritics (harakat + shadda) from text."""
    if HAS_PYARABIC:
        return araby.strip_tashkeel(text)
    return "".join(ch for ch in text if ch not in TASHKEEL_CHARS)


def has_shadda(text: str) -> bool:
    """Return True if text contains shadda (tasydid)."""
    return SHADDA in text


def get_letters(text: str) -> str:
    """Extract only Arabic letters (no diacritics, no tatweel)."""
    return "".join(ch for ch in text if ch in ARABIC_LETTERS)


def _vowel_on_second_consonant(text: str) -> str:
    """Return the vowel (fatha/kasra/damma) on the second root consonant (C2).

    For madhi forms (no prefix): C2 is the 2nd letter (index 1 in letters).
    For mudhari' forms (with prefix ي, ت, أ, ن): C2 is the 3rd letter (index 2).
    Counts letters in the original diacritized text to correctly find C2
    even when C1 and C2 are the same letter.
    Returns '' if undetermined.
    """
    letters = get_letters(text)
    if len(letters) < 3:
        return ""

    # Determine C2 position: if first letter is a mudhari' prefix, skip it
    prefix_offset = 1 if letters[0] in MUDHARI_PREFIXES else 0
    c2_letter_index = 1 + prefix_offset  # 0-based index in letters array
    if c2_letter_index >= len(letters):
        return ""

    # Iterate through original text counting letters to find correct C2
    letter_count = 0
    for i, ch in enumerate(text):
        if ch in ARABIC_LETTERS:
            if letter_count == c2_letter_index:
                # This is C2 — the vowel (if any) is at i+1
                if i + 1 < len(text) and text[i + 1] in (FATHA, KASRA, DAMMA):
                    return text[i + 1]
                return ""
            letter_count += 1
    return ""


# ═══════════════════════════════════════════════════════════════════════════
# Affix Stripping  (works on the *plain* text, i.e. without diacritics)
# ═══════════════════════════════════════════════════════════════════════════

def _strip_prefixes(plain: str) -> dict:
    """Strip NON-morphological prefixes only: negation لا, future س, definite ال.

    Does NOT strip mudhari' person prefixes (أ, ن, ي, ت) because those
    CAN be part of the augmented stem (e.g., أ in 4C أفعل, ت in 5A تفعل).
    Mudhari' prefix detection is handled by the Rumus classifier itself
    using pattern matching on the full word letters.

    Returns a dict with:
        stem: remaining text after stripping
        prefixes: dict of prefix names -> stripped value
        stripped_count: how many chars were stripped from the left
    """
    prefixes: dict[str, str] = {}
    stem = plain

    # 1. Negation prefix لا
    if stem.startswith(NAHI):
        prefixes["la"] = stem[:2]
        stem = stem[2:]

    # 2. Future prefix س
    if stem.startswith(FUTURE_PREFIX) and len(stem) > 1:
        prefixes["sin"] = stem[:1]
        stem = stem[1:]

    # 3. Definite article ال
    if stem.startswith(ALIF + "\u0644") and len(stem) > 3:
        prefixes["al"] = stem[:2]
        stem = stem[2:]

    return {"stem": stem, "prefixes": prefixes, "stripped_count": sum(len(v) for v in prefixes.values())}


def _strip_suffixes(plain: str) -> dict:
    """Strip known suffixes from the end of a plain word.

    Returns dict with stem and list of stripped suffixes.
    """
    stem = plain
    found: list[str] = []
    for suf in SUFFIXES:
        if stem.endswith(suf) and len(stem) > len(suf) + 1:
            stem = stem[:-len(suf)]
            found.append(suf)
            break  # Only strip one layer
    return {"stem": stem, "suffixes": found}


# ═══════════════════════════════════════════════════════════════════════════
# Stem Analysis
# ═══════════════════════════════════════════════════════════════════════════

def analyze_word(word: str) -> dict:
    """Full morphological analysis of an Arabic word.

    Works in two layers:
      1. Strip tashkeel -> analyse plain text for prefixes/suffixes
      2. Preserve original diacritics for shadda detection

    Returns:
        dict with original, plain, letters, has_shadda, stem_plain,
        prefixes, suffixes, features
    """
    plain = strip_tashkeel(word)
    letters = get_letters(plain)

    # Step 1: Strip prefixes
    prefix_info = _strip_prefixes(plain)
    stem_plain = prefix_info["stem"]

    # Step 2: Strip suffixes
    suffix_info = _strip_suffixes(stem_plain)
    stem_plain = suffix_info["stem"]

    # Step 3: Detect shadda in the ORIGINAL word (before any stripping)
    # This is critical — must check the raw input, not the stripped version
    shd = has_shadda(word)

    # Shadda positions
    shadda_positions: list[int] = []
    for i, ch in enumerate(word):
        if ch == SHADDA:
            shadda_positions.append(i)

    stem_letters = get_letters(stem_plain)

    # Mudhari' prefix detection: used by the classifier
    # (NOT stripped from stem — we keep the full letters for pattern matching)
    has_mudhari_pref = bool(letters) and letters[0] in MUDHARI_PREFIXES

    return {
        "original": word,
        "plain": plain,
        "letters": letters,
        "len_letters": len(letters),
        "stem_plain": stem_plain,
        "stem_letters": stem_letters,
        "stem_letter_count": len(stem_letters),
        "has_shadda": shd,
        "shadda_positions": shadda_positions,
        "prefixes": prefix_info["prefixes"],
        "prefix_stripped": prefix_info["stripped_count"],
        "suffixes": suffix_info["suffixes"],
        "has_mudhari_prefix": has_mudhari_pref,
        "starts_with_alif": bool(letters) and letters[0] in ALIF_VARIANTS,
        "starts_with_ta": bool(letters) and letters[0] == TA,
        "starts_with_meem": bool(letters) and letters[0] == MEEM,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Rumus Classification
# ═══════════════════════════════════════════════════════════════════════════

def _classify_rumus_from_stem(analysis: dict, root_hint: str) -> tuple[str, float, list[str]]:
    """Determine the Rumus from the word's stem letter pattern.

    Uses stem_letters (after stripping suffixes and ال/لا/س prefixes,
    but NOT mudhari' prefixes) for main classification.

    Two passes:
      Pass 1 — Check stem letters against all known patterns.
      Pass 2 — If no match AND the word starts with a mudhari' prefix
                (أ/ن/ي/ت), strip the first letter and check the remaining
                against patterns. Handles mudhari' forms where alif-wasl
                (for 5C/5D/6) is replaced by the person prefix.
    """
    stem = analysis["stem_letters"]
    orig = analysis["letters"]
    has_shd = analysis["has_shadda"]
    stem_len = len(stem)
    orig_len = len(orig)
    has_pref = analysis["has_mudhari_prefix"]
    r = get_letters(root_hint) if root_hint else ""
    root_len = len(r)
    reasons: list[str] = []

    if not stem:
        return "", 0.0, ["Empty stem"]

    # ── Ruba'i (4-letter root) — Rumus 4D ──
    if root_len == 4:
        reasons.append(f"4-letter root '{r}' -> Rumus 4D (Fa'lala)")
        return R4D, 0.95, reasons

    # ═══════════════════════════════════════════════════════════════════
    # PASS 1: Check STEM letters against known patterns
    # ═══════════════════════════════════════════════════════════════════
    letters = stem
    letter_len = stem_len

    # 1a) Alif-wasl patterns: 5C, 5D, 5E, 6 (ا at start)
    if letters and letters[0] == ALIF and letter_len >= 4:
        # 6: استفعل (ا + س + ت)
        if letter_len >= 5 and letters[1] == SIN and letters[2] == TA:
            reasons.append("Pattern 'است' -> Rumus 6 (Istaf'ala)")
            return R6, 0.95, reasons
        # 5C: افتعل (ا + C1 + ت + C2 + C3) — needs 5+ letters to distinguish
        # from amr of R3 (ا + C1 + C2 + C3) where C2 happens to be ت
        if letter_len >= 5 and letters[2] == TA and letters[1] != SIN:
            reasons.append("Pattern 'افت' (5+ letters) -> Rumus 5C (Ifta'ala)")
            return R5C, 0.85, reasons
        # 5D: انفعل (ا + ن + C1 + C2 + C3) — needs 5+ letters
        if letter_len >= 5 and letters[1] == NUN and letters[2] != TA:
            reasons.append("Pattern 'ان' (5+ letters) -> Rumus 5D (Infa'ala)")
            return R5D, 0.85, reasons
        # 5E: افعلّ (ا + C1 + C2 + C3 with shadda on last)
        if has_shd and letter_len >= 4:
            reasons.append("Alif + shadda near end -> Rumus 5E (If'alla)")
            return R5E, 0.80, reasons

    # 1b) Ta-prefix: 5A (shadda) or 5B (alif at pos 2)
    if letters and letters[0] == TA and letter_len >= 4:
        if has_shd:
            reasons.append("Starts with ت + tasydid -> Rumus 5A (Tafa''ala)")
            return R5A, 0.90, reasons
        if letter_len >= 5 and letters[2] == ALIF:
            reasons.append("Starts with ت + alif at pos 2 -> Rumus 5B (Tafa'ala)")
            return R5B, 0.90, reasons

    # 1c) Hamzah prefix: 4C (أفعل)
    if letters and letters[0] == ALIF_HAMZA and (2 <= letter_len <= 5) and not has_shd:
        reasons.append(f"Starts with أ without augments -> Rumus 4C (Af'ala)")
        return R4C, 0.80, reasons

    # 1d) Meem prefix: derived nouns (مفاعيل patterns)
    meem_fell_through = False
    if letters and letters[0] == MEEM and letter_len >= 4:
        second = letters[1] if letter_len > 1 else ""
        third = letters[2] if letter_len > 2 else ""
        fourth = letters[3] if letter_len > 3 else ""

        # Exclude مفعول pattern (ism maf'ul of R3): م + C1 + C2 + و/ي + C3
        # The و/ي is at position 3 (0-indexed), e.g. مَفْتُوحٌ
        is_mfoool = letter_len >= 5 and fourth in ("\u0648", "\u064A")
        if is_mfoool:
            meem_fell_through = True  # Will be classified as R3 derived noun
        elif second == ALIF:
            reasons.append("مفاعل pattern -> Rumus 4B derived noun")
            return R4B, 0.80, reasons
        elif second == SIN and third == TA:
            reasons.append("مستفعل pattern -> Rumus 6 derived noun")
            return R6, 0.90, reasons
        elif third == TA and not has_shd:
            reasons.append("مفتعل pattern -> Rumus 5C derived noun")
            return R5C, 0.80, reasons
        elif third == NUN:
            reasons.append("منفعل pattern -> Rumus 5D derived noun")
            return R5D, 0.80, reasons
        elif has_shd:
            reasons.append("مفعل with shadda -> Rumus 4A derived noun")
            return R4A, 0.80, reasons
        elif second == TA and letter_len >= 5:
            if third == ALIF:
                reasons.append("متفاعل pattern -> Rumus 5B derived noun")
                return R5B, 0.80, reasons
            reasons.append("متفعل pattern -> Rumus 5A derived noun")
            return R5A, 0.80, reasons
        elif letter_len == 4:
            reasons.append("مفعل (4 letters) -> Rumus 4C derived noun")
            return R4C, 0.65, reasons
        else:
            reasons.append(f"م prefix + {letter_len} letters -> augmented verb derived noun")
            return R4C, 0.50, reasons

    # If a meem prefix word fell through (e.g. مفعول pattern), classify as R3 derived noun
    if meem_fell_through:
        reasons.append(f"م prefix word (مفعول pattern) -> Rumus 3 derived noun")
        return R3A, 0.60, reasons

    # 1e) 4-letter alif-start word (possible Amr of R3 like اِفتَحْ)
    if letters[0] == ALIF and letter_len == 4:
        reasons.append("4-letter word starting with ا -> possible Amr of Rumus 3")
        return R3A, 0.50, reasons

    # 1e) Alif after C1: 4B (فاعل) — also matches ism fa'il of R3
    if letter_len >= 4 and letters[1] == ALIF:
        reasons.append("Alif after C1 -> Rumus 4B or Ism Fa'il of R3 (same pattern)")
        return R4B, 0.70, reasons

    # 1f) Shadda on C2: 4A (فعّل)
    if has_shd and letter_len >= 3:
        for sp in analysis["shadda_positions"]:
            if sp > 0 and sp - 1 < len(analysis["original"]):
                orig_text = analysis["original"]
                letter_before = get_letters(orig_text[sp - 1:sp])
                if letter_before:
                    pos = letters.find(letter_before[0])
                    if pos == 1:  # Shadda on 2nd letter
                        reasons.append(f"Tasydid on C2 -> Rumus 4A (Fa''ala)")
                        return R4A, 0.90, reasons

    # 1g) 3-letter stem: Rumus 3
    if letter_len == 3:
        vowel_c2 = _vowel_on_second_consonant(analysis["original"])
        if vowel_c2 == KASRA:
            reasons.append(f"3-letter stem + C2 vowel kasra -> Rumus 3B")
            return R3B, 0.85, reasons
        elif vowel_c2 == DAMMA:
            reasons.append(f"3-letter stem + C2 vowel damma -> Rumus 3C")
            return R3C, 0.85, reasons
        if vowel_c2 == FATHA:
            reasons.append(f"3-letter stem + C2 vowel fatha -> Rumus 3A")
            return R3A, 0.85, reasons
        reasons.append("3-letter stem (madhi-only, default 3A)")
        return R3A, 0.60, reasons

    # ═══════════════════════════════════════════════════════════════════
    # PASS 2: Mudhari' prefix detected — check remaining letters
    # ═══════════════════════════════════════════════════════════════════
    if has_pref and stem_len >= 2:
        rest = stem[1:]
        rest_len = stem_len - 1

        # 2a) 6 mudhari': س + ت at rest[0:2] (e.g., يستغفر 👉 rest=ستغفر)
        if rest_len >= 5 and rest[0] == SIN and rest[1] == TA:
            reasons.append(f"Mudhari' prefix + 'ست' -> Rumus 6 (Istaf'ala)")
            return R6, 0.95, reasons

        # 2b) 5C mudhari': rest[1] == TA (e.g., يحترم 👉 rest=حترم)
        if rest_len >= 4 and rest[1] == TA:
            reasons.append(f"Mudhari' prefix + ت at C2 -> Rumus 5C (Ifta'ala)")
            return R5C, 0.85, reasons

        # 2c) 5D mudhari': rest[0] == NUN (e.g., ينكسر 👉 rest=نكسر)
        if rest_len >= 4 and rest[0] == NUN:
            reasons.append(f"Mudhari' prefix + ن at start -> Rumus 5D (Infa'ala)")
            return R5D, 0.85, reasons

        # 2d) 5A/5B mudhari': rest starts with ت (e.g., يتعلم 👉 rest=تعلم)
        if rest_len >= 4 and rest[0] == TA:
            if has_shd:
                reasons.append(f"Mudhari' prefix + ت + shadda -> Rumus 5A (Tafa''ala)")
                return R5A, 0.93, reasons
            if rest_len >= 5 and rest[2] == ALIF:
                reasons.append(f"Mudhari' prefix + ت + alif -> Rumus 5B (Tafa'ala)")
                return R5B, 0.93, reasons

        # 2e) 4A mudhari': shadda on C2 of rest
        if has_shd and rest_len >= 3:
            for sp in analysis["shadda_positions"]:
                if sp > 0 and sp - 1 < len(analysis["original"]):
                    orig_text = analysis["original"]
                    letter_before = get_letters(orig_text[sp - 1:sp])
                    if letter_before:
                        pos = rest.find(letter_before[0])
                        if pos == 1:
                            reasons.append(f"Mudhari' + tasydid on C2 -> Rumus 4A")
                            return R4A, 0.93, reasons

        # 2f) 4B mudhari': alif after C1 of rest
        if rest_len >= 4 and rest[1] == ALIF:
            reasons.append(f"Mudhari' + alif after C1 -> Rumus 4B")
            return R4B, 0.90, reasons

        # 2g) 4D mudhari': 4-letter rest (ruba'i)
        if root_len == 4 and rest_len >= 4:
            reasons.append(f"Mudhari' prefix + 4-letter root -> Rumus 4D")
            return R4D, 0.90, reasons

        # 2h) Rumus 3 with mudhari' prefix: 3-letter rest
        # NOTE: If rest == root (3 letters), this could ALSO be a 4C mudhari'
        # verb (e.g., يُسْلِمُ from أَسْلَمَ) — structurally identical to R3
        # mudhari'. Lower confidence to reflect this ambiguity.
        if rest_len == 3:
            is_mudhari_of_4c = (root_len == 3 and rest == r)
            conf_hi = 0.70 if is_mudhari_of_4c else 0.90
            conf_lo = 0.60 if is_mudhari_of_4c else 0.80
            vowel_c2 = _vowel_on_second_consonant(analysis["original"])
            if vowel_c2 == KASRA:
                if is_mudhari_of_4c:
                    reasons.append(f"Mudhari' + 3-letter root stem (could be R3B or 4C mudhari')")
                else:
                    reasons.append(f"Mudhari' + 3 let + C2 kasra -> Rumus 3B")
                return R3B, conf_hi, reasons
            elif vowel_c2 == DAMMA:
                if is_mudhari_of_4c:
                    reasons.append(f"Mudhari' + 3-letter root stem (could be R3C or 4C mudhari')")
                else:
                    reasons.append(f"Mudhari' + 3 let + C2 damma -> Rumus 3C")
                return R3C, conf_hi, reasons
            if vowel_c2 == FATHA:
                reasons.append(f"Mudhari' + 3 let + C2 fatha -> Rumus 3A")
                return R3A, conf_hi, reasons
            reasons.append("Mudhari' + 3 letters, default 3A")
            return R3A, conf_lo, reasons

    # ── Fallback ──
    reasons.append(f"Stem '{stem}' ({stem_len} letters) doesn't match known patterns")
    return "", 0.0, reasons

    def _check_shadda_4a(lets: str) -> str | None:
        """Check shadda on C2 -> 4A (Fa''ala)."""
        if not has_shd:
            return None
        for sp in analysis["shadda_positions"]:
            if sp > 0 and sp - 1 < len(analysis["original"]):
                orig = analysis["original"]
                letter_before = get_letters(orig[sp - 1:sp])
                if letter_before:
                    pos = lets.find(letter_before[0])
                    if pos == 1:  # Shadda on 2nd letter
                        return R4A
        return None

    def _check_alif_c2(lets: str, len_l: int) -> str | None:
        """Check alif after C1 -> 4B (Fa'ala)."""
        if len_l >= 4 and lets[1] == ALIF:
            return R4B
        return None

    # ═══════════════════════════════════════════════════════════════════
    # PASS 1: Check FULL word letters against all patterns
    # ═══════════════════════════════════════════════════════════════════

    # 1a) Alif-wasl prefix patterns: 5C, 5D, 5E, 6
    match = _check_alif_wasl(letters, letter_len)
    if match:
        reasons.append(f"Alif-wasl pattern -> Rumus {match}")
        return match, 0.85, reasons

    # 1b) Ta-prefix: 5A (shadda) or 5B (alif at pos 2)
    match = _check_ta_prefix(letters, letter_len)
    if match:
        reasons.append(f"Starts with ت -> Rumus {match}")
        return match, 0.90, reasons

    # 1c) Hamzah prefix: 4C (أفعل)
    if letters[0] == ALIF_HAMZA and (2 <= letter_len <= 5) and not has_shd:
        reasons.append(f"Starts with أ without augments -> Rumus 4C (Af'ala)")
        return R4C, 0.80, reasons

    # 1d) Meem prefix: derived nouns
    match = _check_meem_prefix(letters, letter_len)
    if match:
        reasons.append(f"م prefix pattern -> Rumus {match} derived noun")
        return match, 0.80, reasons

    # 1e) Alif after C1: 4B (فاعل)
    match = _check_alif_c2(letters, letter_len)
    if match:
        reasons.append(f"Alif after C1 -> Rumus 4B (Fa'ala)")
        return R4B, 0.75, reasons

    # 1f) Shadda on C2: 4A (فعّل)
    match = _check_shadda_4a(letters)
    if match:
        reasons.append(f"Tasydid on C2 -> Rumus {match} (Fa''ala)")
        return R4A, 0.90, reasons

    # 1g) 3-letter stem: Rumus 3
    if letter_len == 3:
        vowel_c2 = _vowel_on_second_consonant(analysis["original"])
        if vowel_c2 == KASRA:
            reasons.append(f"3-letter stem + C2 vowel kasra -> Rumus 3B")
            return R3B, 0.85, reasons
        elif vowel_c2 == DAMMA:
            reasons.append(f"3-letter stem + C2 vowel damma -> Rumus 3C")
            return R3C, 0.85, reasons
        # Default (fatha or unknown): 3A
        if vowel_c2 == FATHA:
            reasons.append(f"3-letter stem + C2 vowel fatha -> Rumus 3A")
            return R3A, 0.85, reasons
        else:
            reasons.append("3-letter stem (madhi-only, default 3A)")
            return R3A, 0.60, reasons

    # ═══════════════════════════════════════════════════════════════════
    # PASS 2: Check if word starts with mudhari' prefix
    # Then check the remaining letters against patterns
    # ═══════════════════════════════════════════════════════════════════

    if analysis.get("has_mudhari_prefix") and letter_len >= 2:
        # Strip the first letter (prefix) and check the rest
        rest = letters[1:]
        rest_len = letter_len - 1

        # 2a) Alif-wasl equivalent in mudhari' forms:
        #     The alif-wasl is replaced by the person prefix, so
        #     the infix markers are shifted left by 1.
        #     - 6 mudhari': س + ت at rest[0:2] (e.g., يستغفر -> rest=ستغفر)
        #     - 5C mudhari': ت at rest[1] (e.g., يحترم -> rest=حترم)
        #     - 5D mudhari': ن at rest[0] (e.g., ينكسر -> rest=نكسر)

        # 6 mudhari': rest starts with س + ت
        if rest_len >= 5 and rest[0] == SIN and rest[1] == TA:
            reasons.append(f"Mudhari' prefix + 'ست' pattern -> Rumus 6 (Istaf'ala)")
            return R6, 0.95, reasons

        # 5C mudhari': rest[1] == ت (infix after C1)
        if rest_len >= 4 and rest[1] == TA:
            reasons.append(f"Mudhari' prefix + ت at C2 -> Rumus 5C (Ifta'ala)")
            return R5C, 0.85, reasons

        # 5D mudhari': rest[0] == ن (nun replaces alif-wasl)
        if rest_len >= 4 and rest[0] == NUN:
            reasons.append(f"Mudhari' prefix + ن at start -> Rumus 5D (Infa'ala)")
            return R5D, 0.85, reasons

        # 2b) Ta-prefix patterns with mudhari' prefix
        #     يَتَعَلَّم: rest = تعلّم -> 5A (ت + shadda)
        #     يَتَعَارَف: rest = تعارف -> 5B (ت + alif at 2)
        if rest[0] == TA and rest_len >= 4:
            if has_shd:
                reasons.append(f"Mudhari' prefix + ت + shadda -> Rumus 5A (Tafa''ala)")
                return R5A, 0.93, reasons
            if rest_len >= 5 and rest[2] == ALIF:
                reasons.append(f"Mudhari' prefix + ت + alif at pos 2 -> Rumus 5B (Tafa'ala)")
                return R5B, 0.93, reasons

        # 2c) 4A mudhari': shadda on C2 of rest
        match = _check_shadda_4a(rest)
        if match:
            reasons.append(f"Mudhari' prefix + tasydid on C2 -> Rumus 4A (Fa''ala)")
            return R4A, 0.93, reasons

        # 2d) 4B mudhari': alif after C1 of rest
        if rest_len >= 4 and rest[1] == ALIF:
            reasons.append(f"Mudhari' prefix + alif after C1 -> Rumus 4B (Fa'ala)")
            return R4B, 0.90, reasons

        # 2e) 4C mudhari': rest starts with hamzah
        if rest[0] == ALIF_HAMZA and rest_len <= 4 and not has_shd:
            reasons.append(f"Mudhari' prefix + hamzah -> Rumus 4C (Af'ala)")
            return R4C, 0.85, reasons

        # 2f) 4D mudhari': 4-letter rest with 4-letter root
        if rest_len >= 4 and len(set(rest)) >= 4 and root_len == 4:
            reasons.append(f"Mudhari' prefix + 4-letter rest -> Rumus 4D (Fa'lala)")
            return R4D, 0.90, reasons

        # 2g) Rumus 3 with mudhari' prefix: 3-letter rest
        if rest_len == 3:
            vowel_c2 = _vowel_on_second_consonant(analysis["original"])
            if vowel_c2 == KASRA:
                reasons.append(f"Mudhari' prefix + 3 letters + C2 kasra -> Rumus 3B")
                return R3B, 0.90, reasons
            elif vowel_c2 == DAMMA:
                reasons.append(f"Mudhari' prefix + 3 letters + C2 damma -> Rumus 3C")
                return R3C, 0.90, reasons
            # Default: 3A (fatha or unknown)
            if vowel_c2 == FATHA:
                reasons.append(f"Mudhari' prefix + 3 letters + C2 fatha -> Rumus 3A")
                return R3A, 0.90, reasons
            reasons.append("Mudhari' prefix + 3 letters, default 3A")
            return R3A, 0.80, reasons

    # ── Fallback ──
    reasons.append(f"Letters '{letters}' ({letter_len}) doesn't match known patterns")
    return "", 0.0, reasons


# ═══════════════════════════════════════════════════════════════════════════
# Form Classification
# ═══════════════════════════════════════════════════════════════════════════

def _classify_form(word: str, rumus: str) -> tuple[FormNumber, float, list[str]]:
    """Determine which of the 8 Tashrif Ishthilahi forms this word is."""
    plain = strip_tashkeel(word)
    r: list[str] = []
    letters = get_letters(plain)
    # Also get analysis for feature detection
    analysis = analyze_word(word)
    pref = analysis["prefixes"]

    # 1. Laa negation -> Form 4 (Fi'il Nahi)
    if "la" in pref:
        r.append("Prefix 'لا' detected -> Fi'il Nahi (Form 4)")
        return FormNumber.FIIL_NAHI, 0.98, r

    # 2. Definite article ال -> it's a noun form
    if "al" in pref:
        stem_plain = analysis["stem_plain"]
        stem_lets_after_al = get_letters(stem_plain)
        if not stem_lets_after_al:
            return FormNumber.MASHDAR, 0.30, r
        first = stem_lets_after_al[0]
        # Check for فاعل pattern (active participle)
        if len(stem_lets_after_al) >= 4 and stem_lets_after_al[1] == ALIF:
            r.append("فاعل pattern after 'ال' -> Ism Fa'il (Form 6)")
            return FormNumber.ISM_FAIL, 0.85, r
        # م prefix -> ism maf'ul or ism zaman/makan
        if first == MEEM:
            r.append("م prefix after 'ال' -> Ism Maf'ul (Form 7) or Zamami (Form 8)")
            return FormNumber.ISM_MAFUL, 0.70, r
        # Default noun
        r.append("Definite article -> noun (general)")
        return FormNumber.MASHDAR, 0.50, r

    # 3. Mudhari' prefix -> Form 2 (Fi'il Mudhari')
    # Note: mudhari' info is stored in has_mudhari_prefix (boolean), not in pref dict.
    # Only apply to Rumus 3 (basic verbs) — augmented verbs (4-6) may start with
    # the same letters (e.g., تَفَعَّلَ starts with ت but is past tense, not mudhari').
    if analysis.get("has_mudhari_prefix") and rumus in (R3A, R3B, R3C):
        r.append("Mudhari' prefix -> Fi'il Mudhari' (Form 2)")
        return FormNumber.FIIL_MUDHARI, 0.95, r

    # 4. Past tense suffixes (ت/نا at end) -> Form 1 (Fi'il Madhi)
    if plain.endswith("\u062A") or plain.endswith("\u0646\u0627"):
        r.append("Past suffix -> Fi'il Madhi (Form 1)")
        return FormNumber.FIIL_MADHI, 0.80, r

    # 5. Amr prefix (ا) -> Form 3 (Fi'il Amr)
    # But only if it's not part of augmented stem (5C/5D/5E/6)
    if plain.startswith(ALIF) and len(plain) > 1:
        is_augmented = rumus in (R5C, R5D, R5E, R6)
        if not is_augmented:
            r.append("Alif prefix -> Fi'il Amr (Form 3)")
            return FormNumber.FIIL_AMR, 0.70, r

    # 6. Mu- prefix (م) -> derived noun forms
    if letters and letters[0] == MEEM and len(letters) >= 4:
        # Derived noun forms for augmented verbs (Rumus 4-6)
        if rumus in (R4A, R4B, R4C, R4D, R5A, R5B, R5C, R5D, R5E, R6):
            # Vowel pattern after mu- distinguishes:
            # مُفَعِّل (kasra before last) = ism fa'il
            # مُفَعَّل (fatha before last) = ism maf'ul / zamami
            # For simplicity, check the original diacritized word
            orig = analysis["original"]
            # Find the last vowel before the final letter
            # If kasra on second-to-last = ism fa'il, else ism maf'ul
            last_vowel = ""
            for i in range(len(orig) - 1, 0, -1):
                if orig[i] in (FATHA, KASRA, DAMMA):
                    last_vowel = orig[i]
                    break
            if last_vowel == KASRA:
                r.append("Mu- prefix + kasra before final -> Ism Fa'il (Form 6)")
                return FormNumber.ISM_FAIL, 0.75, r
            else:
                r.append("Mu- prefix + fatha/damma before final -> Ism Maf'ul/Zamami (Form 7/8)")
                return FormNumber.ISM_MAFUL, 0.65, r
        else:
            # Mu- prefix on Rumus 3 = ism maf'ul (مفعول) or zamami (مفعل)
            r.append("Mu- prefix on Rumus 3 -> Ism Maf'ul/Zamami (Form 7/8)")
            return FormNumber.ISM_MAFUL, 0.70, r

    # 7. Taa marbuta -> feminine noun
    if plain.endswith("\u0629"):
        r.append("Ends with ة -> noun (Mashdar or Ism)")
        return FormNumber.MASHDAR, 0.50, r

    # 8. 3 letters without affixes -> madhi (Form 1) or ism (Form 5)
    if len(letters) == 3:
        r.append("3-letter stem -> Fi'il Madhi (Form 1)")
        return FormNumber.FIIL_MADHI, 0.60, r

    # 9. 4+ letters -> augmented verb or derived noun
    if len(letters) >= 4:
        r.append("4+ letter stem -> augmented madhi or derived noun")
        # If starts with alif-hamza or ta, it's likely a verb
        if letters[0] in (ALIF_HAMZA, TA, ALIF):
            r.append("Likely augmented verb -> Fi'il Madhi (Form 1)")
            return FormNumber.FIIL_MADHI, 0.60, r
        return FormNumber.MASHDAR, 0.40, r

    r.append("Form not confidently determined")
    return FormNumber.FIIL_MADHI, 0.20, r


# ═══════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def classify_rumus(word: str, root: str = "", pos_type: str = "") -> RumusResult:
    """Classify an Arabic word into its Rumus pattern (3A-6) and Form (1-8).

    Args:
        word: The Arabic word (may have diacritics).
        root: The root letters (3 or 4). If empty, inferred.
        pos_type: POS hint ("verb", "noun", or "").

    Returns:
        RumusResult with rumus, form, classification, etc.
    """
    empty = RumusResult(
        word=word or "", root=root,
        rumus="", form=0,
        form_label="", form_label_id="",
        classification="", meaning_pattern="",
        confidence=0.0, reasons=["Empty input"],
    )
    if not word or not word.strip():
        return empty

    reasons: list[str] = []
    analysis = analyze_word(word)
    reasons.append(f"Stem letters: '{analysis['stem_letters']}' | Shadda: {analysis['has_shadda']}")

    # Determine root
    root_letters = get_letters(root) if root else ""
    if not root_letters:
        # Simple heuristic: if stem has 4+ letters, the root is likely 3
        # by removing extra letters
        base = analysis["stem_letters"]
        if analysis["has_shadda"]:
            # Remove shadda-doubled letter
            expanded = list(base)
            # Find doubled letter from original
            pos = analysis["shadda_positions"]
            if pos:
                orig_chars = list(analysis["original"])
                for p in pos:
                    if p > 0:
                        # The letter BEFORE shadda is the doubled one
                        doubled = get_letters(orig_chars[p-1:p])
                        if doubled:
                            # Remove one occurrence from expanded
                            d = doubled[0]
                            if d in expanded:
                                expanded.remove(d)
                base = "".join(expanded)
        root_letters = base[:3]  # Take first 3 letters as root

    reasons.append(f"Root: '{root_letters}'")

    # Classify Rumus
    rumus, rumus_conf, rumus_reasons = _classify_rumus_from_stem(analysis, root_letters)
    reasons.extend(rumus_reasons)

    if not rumus:
        return RumusResult(
            word=word, root=root_letters,
            rumus="", form=0,
            form_label="", form_label_id="",
            classification="Unknown", meaning_pattern="",
            confidence=0.0, stem=analysis["stem_plain"],
            reasons=reasons,
        )

    # Classify Form
    form_enum, form_conf, form_reasons = _classify_form(word, rumus)
    reasons.extend(form_reasons)

    overall_conf = round((rumus_conf + form_conf) / 2, 2)

    return RumusResult(
        word=word,
        root=root_letters,
        rumus=rumus,
        form=form_enum.value,
        form_label=FORM_LABELS.get(form_enum, ""),
        form_label_id=FORM_LABELS_ID.get(form_enum, ""),
        classification=RUMUS_CLASSIFICATION.get(rumus, f"Rumus {rumus}"),
        meaning_pattern=RUMUS_MEANING.get(rumus, ""),
        confidence=overall_conf,
        stem=analysis["stem_plain"],
        reasons=reasons,
    )


def classify_ishthilahi_table(word: str, root: str = "", pos_type: str = "") -> dict:
    """Convenience wrapper: returns a plain dict for JSON serialization."""
    result = classify_rumus(word, root, pos_type)
    return {
        "rumus": result.rumus,
        "classification": result.classification,
        "meaning_pattern": result.meaning_pattern,
        "current_form": {
            "number": result.form,
            "label": result.form_label,
            "label_id": result.form_label_id,
        },
        "confidence": result.confidence,
        "stem": result.stem,
        "root": result.root,
        "word": result.word,
        "reasons": result.reasons,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Demo / Test
# ═══════════════════════════════════════════════════════════════════════════

def _demo(output_path: str = ""):
    """Run test cases from the PDF and report accuracy."""
    from collections import defaultdict

    # (word, root, expected_rumus, note)
    test_words = [
        # --- Rumus 3 ---
        ("فَتَحَ",   "فتح", R3A, "Madhi"),
        ("يَفتَحُ",  "فتح", R3A, "Mudhari'"),
        ("اِفتَحْ",  "فتح", R3A, "Amr"),
        ("فَتْحًا",  "فتح", R3A, "Mashdar"),
        ("فَاتِحٌ",  "فتح", R3A, "Ism Fa'il"),
        ("مَفْتُوحٌ","فتح", R3A, "Ism Maf'ul"),
        # --- Rumus 3B ---
        ("ضَرَبَ",   "ضرب", R3B, "Madhi"),
        ("يَضرِبُ",  "ضرب", R3B, "Mudhari'"),
        # --- Rumus 3C ---
        ("نَصَرَ",   "نصر", R3C, "Madhi"),
        ("يَنصُرُ",  "نصر", R3C, "Mudhari'"),
        ("كَتَبَ",   "كتب", R3C, "Madhi"),
        ("يَكتُبُ",  "كتب", R3C, "Mudhari'"),
        # --- Rumus 4A ---
        ("عَلَّمَ",   "علم", R4A, "Madhi"),
        ("يُعَلِّمُ", "علم", R4A, "Mudhari'"),
        ("مُعَلِّمٌ", "علم", R4A, "Ism Fa'il"),
        ("مُعَلَّمٌ", "علم", R4A, "Ism Maf'ul"),
        # --- Rumus 4B ---
        ("شَاوَرَ",  "شور", R4B, "Madhi"),
        ("يُشَاوِرُ","شور", R4B, "Mudhari'"),
        # --- Rumus 4C ---
        ("أَسْلَمَ", "سلم", R4C, "Madhi"),
        ("يُسْلِمُ", "سلم", R4C, "Mudhari'"),
        ("مُسْلِمٌ", "سلم", R4C, "Ism Fa'il"),
        # --- Rumus 4D ---
        ("زَلْزَلَ",  "زلزل", R4D, "Madhi"),
        ("يُزَلْزِلُ","زلزل", R4D, "Mudhari'"),
        # --- Rumus 5A ---
        ("تَعَلَّمَ",  "علم", R5A, "Madhi"),
        ("يَتَعَلَّمُ","علم", R5A, "Mudhari'"),
        # --- Rumus 5B ---
        ("تَعَارَفَ",  "عرف", R5B, "Madhi"),
        ("يَتَعَارَفُ","عرف", R5B, "Mudhari'"),
        # --- Rumus 5C ---
        ("اِحتَرَمَ",  "حرم", R5C, "Madhi"),
        ("يَحتَرِمُ",  "حرم", R5C, "Mudhari'"),
        # --- Rumus 5D ---
        ("اِنْكَسَرَ", "كسر", R5D, "Madhi"),
        ("يَنكَسِرُ",  "كسر", R5D, "Mudhari'"),
        # --- Rumus 5E ---
        ("اِحمَرَّ",  "حمر", R5E, "Madhi"),
        # --- Rumus 6 ---
        ("اِستَغْفَرَ", "غفر", R6, "Madhi"),
        ("يَستَغْفِرُ", "غفر", R6, "Mudhari'"),
        ("مُستَغْفِرٌ", "غفر", R6, "Ism Fa'il"),
    ]

    lines = []
    lines.append("=" * 90)
    lines.append("  TASHRIF RUMUS CLASSIFIER - Phase 1 Demo")
    lines.append("=" * 90)
    lines.append(f"{'Word':<20} {'Note':<15} {'Exp':<6} {'Got':<6} {'Conf':<6} {'Form':<6} {'Status'}")
    lines.append("-" * 75)

    correct = 0
    by_rumus: dict[str, dict] = defaultdict(lambda: {"ok": 0, "total": 0})

    for word, root, expected, note in test_words:
        result = classify_rumus(word, root)
        ok = result.rumus == expected
        if ok:
            correct += 1
        by_rumus[expected]["total"] += 1
        if ok:
            by_rumus[expected]["ok"] += 1

        w_short = word[:12] + "..." if len(word) > 13 else word
        status = "OK" if ok else "FAIL"
        lines.append(f"{w_short:<20} {note:<15} {expected:<6} {result.rumus:<6} {result.confidence:<6.2f} {result.form:<6} {status}")

    total = len(test_words)
    lines.append("-" * 75)
    lines.append(f"  Overall Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    lines.append("")
    lines.append("  Per-Rumus Accuracy:")
    for rumus in sorted(by_rumus.keys()):
        d = by_rumus[rumus]
        pct = d["ok"] / d["total"] * 100 if d["total"] else 0
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        lines.append(f"    Rumus {rumus:<3}: {d['ok']:>2}/{d['total']:<2} ({pct:>5.1f}%) {bar}")
    lines.append("=" * 90)

    text = "\n".join(lines)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Results written to {output_path}")
    else:
        try:
            print(text)
        except UnicodeEncodeError:
            print("(Unicode output not supported in this console)")


if __name__ == "__main__":
    import sys
    out = ""
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        out = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
    _demo(output_path=out)
