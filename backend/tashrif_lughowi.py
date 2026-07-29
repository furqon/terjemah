"""
tashrif_lughowi.py — Tashrif Lughowi (Full Pronoun Conjugation) Generator.

Generates the full 14-pronoun conjugation tables for Arabic verbs:

  - For Rumus 3 (R3A/B/C): Uses Sarf CLI directly for accurate diacritized forms
  - For Rumus 4-6: Uses wazan pattern substitution + standard affix patterns
  - For all: Derives amr (imperative) and nahi (prohibitive) from jussive forms

Tenses generated:
  - past_tense:      13 pronouns (fi'il madhi)
  - present_tense:   13 pronouns (fi'il mudhari' marfu'/indicative)
  - present_subjunctive: 13 pronouns (fi'il mudhari' manṣub/subjunctive)
  - present_jussive: 13 pronouns (fi'il mudhari' majzum/jussive)
  - imperative:       6 pronouns (fi'il amr — 2nd person only)
  - nahi:             6 pronouns (fi'il nahi — 2nd person only)

Usage:
    from tashrif_lughowi import conjugate_lughowi
    result = conjugate_lughowi("كتب", "3C", bab=3)
    print(result["past_tense"][0]["text"])  # كَتَبْتُ
"""

from __future__ import annotations

from typing import Any

from tashrif_classifier import R3A, R3B, R3C
from tashrif_generator import apply_wazan, WAZAN, _get_root_letters, HAS_SARF, _SARF

try:
    import pyarabic.araby as araby
    HAS_PYARABIC = True
except ImportError:
    HAS_PYARABIC = False

# Diacritics (same as other modules)
FATHA = "\u064E"
KASRA = "\u0650"
DAMMA = "\u064F"
SUKUN = "\u0652"
SHADDA = "\u0651"
ALIF = "\u0627"
ALIF_HAMZA = "\u0623"


# ═══════════════════════════════════════════════════════════════════════════
# Standard Pronoun Tables
# ═══════════════════════════════════════════════════════════════════════════

# 13 pronouns for past/present tenses
# RTL order: 3rd person (male sg → dual → pl, female sg → dual → pl),
# 2nd person (male sg → dual → pl, female sg → dual → pl),
# 1st person (sg → pl).
# Note: dual pronouns (هما, أنتما) appear twice in the list —
# once in the male section and once in the female section —
# because the same Arabic form covers both genders.
PRONOUNS_13 = [
    ("هو", "3rd m sg"),
    ("هما (m)", "3rd dual m"),
    ("هم", "3rd m pl"),
    ("هي", "3rd f sg"),
    ("هما (f)", "3rd dual f"),
    ("هن", "3rd f pl"),
    ("أنت", "2nd m sg"),
    ("أنتما", "2nd dual"),
    ("أنتم", "2nd m pl"),
    ("أنتِ", "2nd f sg"),
    ("أنتن", "2nd f pl"),
    ("أنا", "1st sg"),
    ("نحن", "1st pl"),
]

# 6 pronouns for imperative and prohibitive (2nd person only)
# RTL order: male (sg → dual → pl) then female (sg → dual → pl).
PRONOUNS_6 = [
    ("أنت", "2nd m sg"),
    ("أنتما", "2nd dual"),
    ("أنتم", "2nd m pl"),
    ("أنتِ", "2nd f sg"),
    ("أنتن", "2nd f pl"),
]


# ═══════════════════════════════════════════════════════════════════════════
# Sarf CLI Integration — Full Conjugation Tables
# ═══════════════════════════════════════════════════════════════════════════

def _get_sarf_full(root: str, bab: int) -> dict[str, Any] | None:
    """Get full Sarf conjugation data for a triliteral root (Rumus 3)."""
    if not HAS_SARF:
        return None
    try:
        return _SARF.analyze(root, bab)
    except Exception:
        return None


def _format_sarf_table(
    data: dict[str, str] | None,
    pronouns: list[tuple[str, str]],
) -> list[dict[str, str]]:
    """Format a Sarf pronoun table into a list of {pronoun, text} dicts."""
    if not data:
        return [{"pronoun": p[0], "text": ""} for p in pronouns]
    rows = []
    for pronoun, desc in pronouns:
        text = data.get(pronoun, "")
        rows.append({"pronoun": pronoun, "text": text, "description": desc})
    return rows


# ═══════════════════════════════════════════════════════════════════════════
# Amr (Imperative) Derivation from Jussive
# ═══════════════════════════════════════════════════════════════════════════

# Amr prefix vowel by bab (for prosthetic alif only)
_AMR_VOWEL = {1: KASRA, 2: KASRA, 3: DAMMA, 4: KASRA, 5: KASRA, 6: DAMMA}

# Suffixes for imperative, by 2nd-person pronoun
# These replace the final sukun of the base amr form
_AMR_SUFFIXES: dict[str, str] = {
    "أنت": "",           # m sg: base ends with sukun, keep as-is
    "أنتِ": "ِي",        # f sg: replace sukun with ◌ِي (ئ with kasra + ي)
    "أنتما": "َا",       # dual: replace sukun with ◌َا (ل with fatha + ا)
    "أنتم": "ُوا",       # m pl: replace sukun with ◌ُوا (ل with damma + وا)
    "أنتن": "ْنَ",       # f pl: replace sukun with ◌ْنَ (ل with sukun + ن + fatha)
}


def _derive_amr_from_jussive(
    jussive_data: dict[str, str] | None,
    bab: int,
    rumus_root_base: str,
    c1: str, c2: str, c3: str,
) -> list[dict[str, str]]:
    """Derive imperative (amr) forms from the jussive conjugation.

    For each 2nd-person pronoun:
    1. Take the jussive form
    2. Strip the person prefix (ت/ي/أ/ن)
    3. Add prosthetic alif ONLY if stem starts with consonant + sukun
    """
    rows = []
    for pronoun, desc in PRONOUNS_6:
        if jussive_data and pronoun in jussive_data:
            jussive_form = jussive_data[pronoun]
            if jussive_form and len(jussive_form) > 1:
                # Strip the person prefix (ت/ن/أ/ي) AND its following vowel
                # The jussive prefix is always a single consonant with a short vowel
                # E.g., تَفْتُحْ → strip ت + ◌َ → stem = فْتُحْ
                if jussive_form[0] in ("ت", "ي", "أ", "ن"):
                    strip_count = 2 if len(jussive_form) > 1 and jussive_form[1] in (FATHA, KASRA, DAMMA) else 1
                    stem = jussive_form[strip_count:]
                else:
                    stem = jussive_form
                # Add prosthetic alif only if stem starts with consonant+sukun
                if len(stem) >= 2 and stem[1] == SUKUN and stem[0] not in (FATHA, KASRA, DAMMA, SUKUN):
                    vowel = _AMR_VOWEL.get(bab, KASRA)
                    amr = ALIF + vowel + stem
                else:
                    amr = stem
                rows.append({"pronoun": pronoun, "text": amr, "description": desc})
            else:
                rows.append({"pronoun": pronoun, "text": "", "description": desc})
        else:
            rows.append({"pronoun": pronoun, "text": "", "description": desc})
    return rows


def _derive_nahi_from_jussive(
    jussive_data: dict[str, str] | None,
) -> list[dict[str, str]]:
    """Derive prohibitive (nahi) forms from the jussive conjugation.

    Simply prefix the jussive with لا.
    """
    rows = []
    for pronoun, desc in PRONOUNS_6:
        if jussive_data and pronoun in jussive_data:
            jussive_form = jussive_data[pronoun]
            if jussive_form:
                nahi = "لا " + jussive_form
                rows.append({"pronoun": pronoun, "text": nahi, "description": desc})
            else:
                rows.append({"pronoun": pronoun, "text": "", "description": desc})
        else:
            rows.append({"pronoun": pronoun, "text": "", "description": desc})
    return rows


# ═══════════════════════════════════════════════════════════════════════════
# Diacritic Cleanup Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _clean_diacritics(text: str) -> str:
    """Remove invalid diacritic combinations.

    Handles:
    - Shadda + sukun → just sukun (shadda implies a vowel)
    - Shadda + consecutive vowels → keep only the vowel after shadda
    - Consecutive same vowels → keep one
    """
    if not text:
        return text

    # Fix shadda + sukun: impossible in Arabic
    text = text.replace(SHADDA + SUKUN, SUKUN)
    text = text.replace(SUKUN + SHADDA, SUKUN)

    # Remove consecutive vowels (keep the last one)
    # A vowel should never be immediately followed by another vowel
    cleaned = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in (FATHA, KASRA, DAMMA) and cleaned and cleaned[-1] in (FATHA, KASRA, DAMMA):
            # Skip this vowel, keep previous one
            i += 1
            continue
        cleaned.append(ch)
        i += 1

    return "".join(cleaned)


def _unfold_geminated_stem(stem: str) -> str:
    """Unfold a geminated (shadda) stem for consonant-initial suffixes.

    E.g., stem اِحْمَرّ (from اِحْمَرَّ) → اِحْمَرْر
    This is needed for 5E (اِفْعَلَّ) pattern madhi conjugation.
    """
    if SHADDA not in stem:
        return stem
    idx = stem.find(SHADDA)
    if idx > 0:
        geminated_letter = stem[idx - 1]
        # Replace shadda with the letter (keep sukun on preceding consonant)
        # The vowel between the geminated letters is inferred from context
        unfolded = stem[:idx] + geminated_letter + stem[idx + 1:]
        return unfolded
    return stem


# ═══════════════════════════════════════════════════════════════════════════
# Pattern-Based Conjugation for Augmented Verbs (Rumus 4-6)
# ═══════════════════════════════════════════════════════════════════════════

# Standard madhi suffixes for each pronoun (applied to the huwa form stem)
_MADHI_SUFFIXES: dict[str, str] = {
    "أنا": "ْتُ",        # فَعَلْتُ
    "نحن": "ْنَا",       # فَعَلْنَا
    "أنت": "ْتَ",        # فَعَلْتَ
    "أنتِ": "ْتِ",       # فَعَلْتِ
    "أنتما": "ْتُمَا",   # فَعَلْتُمَا
    "أنتم": "ْتُمْ",     # فَعَلْتُمْ
    "أنتن": "ْتُنَّ",     # فَعَلْتُنَّ
    "هو": "َ",           # فَعَلَ (base with fatha)
    "هي": "َتْ",         # فَعَلَتْ
    "هما (m)": "َا",     # فَعَلَا
    "هما (f)": "َتَا",   # فَعَلَتَا
    "هم": "ُوا",         # فَعَلُوا
    "هن": "ْنَ",         # فَعَلْنَ
}


def _conjugate_madhi(madhi_huwa: str) -> dict[str, str]:
    """Conjugate a verb in past tense (madhi) for all 13 pronouns.

    Takes the 3rd m sg form (هو) and applies standard suffixes.
    The madhi stem = huwa_form without the final fatha on C3.
    Handles geminated (5E) verbs by unfolding shadda before consonant suffixes.
    """
    if not madhi_huwa:
        return {p[0]: "" for p in PRONOUNS_13}

    # Check for gemination (shadda on last letter — e.g., 5E pattern)
    has_gemination = SHADDA in madhi_huwa

    # Extract stem: remove the last vowel
    stem = madhi_huwa
    if stem.endswith(FATHA):
        stem = stem[:-1]  # Remove final fatha
    elif stem.endswith(DAMMA):
        stem = stem[:-1]
    # Remove any remaining trailing vowels/sukun
    while stem and stem[-1] in (FATHA, KASRA, DAMMA, SUKUN):
        stem = stem[:-1]

    # For geminated verbs (5E), unfold for consonant-initial suffixes
    # Extract the inter-consonant vowel from the ORIGINAL huwa form
    inter_vowel = ""
    if has_gemination:
        shadda_pos = madhi_huwa.find(SHADDA)
        if shadda_pos > 0 and shadda_pos + 1 < len(madhi_huwa):
            next_char = madhi_huwa[shadda_pos + 1]
            if next_char in (FATHA, KASRA, DAMMA):
                inter_vowel = next_char
        if not inter_vowel:
            inter_vowel = FATHA  # default: most madhi forms use fatha between geminated consonants

    if has_gemination and SHADDA in stem:
        unfolded_stem = _unfold_geminated_stem(stem)
        # If unfolded stem has no vowel between geminated consonants, insert one
        if inter_vowel and SHADDA not in unfolded_stem:
            # Find the geminated letter pair (two same letters in a row)
            # Skip diacritics — only check actual letter characters
            for i in range(1, len(unfolded_stem)):
                prev = unfolded_stem[i-1]
                curr = unfolded_stem[i]
                # Check if both are actual Arabic letters (not diacritics)
                if (prev not in (FATHA, KASRA, DAMMA, SUKUN, SHADDA)
                        and curr == prev
                        and prev not in ("\u064B", "\u064C", "\u064D", "\u0670")):  # tanwin markers
                    # The second occurrence of the geminated letter is at position i
                    # Insert the inter-vowel before it
                    unfolded_stem = unfolded_stem[:i] + inter_vowel + unfolded_stem[i:]
                    break
    else:
        unfolded_stem = None

    result = {}
    for pronoun, desc in PRONOUNS_13:
        suffix = _MADHI_SUFFIXES.get(pronoun, "")
        if not suffix:
            result[pronoun] = ""
            continue

        if pronoun == "هو":
            result[pronoun] = madhi_huwa
        elif pronoun == "هي":
            # For geminated verbs: اِحْمَرَّتْ (keep shadda)
            if has_gemination:
                result[pronoun] = stem + "َتْ"
            else:
                result[pronoun] = stem + suffix
        elif pronoun in ("هما (m)", "هما (f)", "هم"):
            # Vowel-initial suffixes: keep shadda for geminated verbs
            if pronoun == "هما (m)":
                sfx = "َا"
            elif pronoun == "هما (f)":
                sfx = "َتَا"
            else:  # هم
                sfx = "ُوا"
            if has_gemination:
                result[pronoun] = stem + sfx
            else:
                result[pronoun] = stem + sfx
        else:
            # Consonant-initial suffixes: unfold shadda if geminated
            if has_gemination and unfolded_stem:
                result[pronoun] = unfolded_stem + suffix
            else:
                result[pronoun] = stem + suffix

    return result


# Standard present tense prefixes and suffixes
_PRESENT_PREFIXES: dict[str, str] = {
    "أنا": "أ",          # أَفْعَلُ
    "نحن": "ن",          # نَفْعَلُ
    "أنت": "ت",          # تَفْعَلُ
    "أنتِ": "ت",         # تَفْعَلِينَ
    "أنتما": "ت",        # تَفْعَلَانِ
    "أنتم": "ت",         # تَفْعَلُونَ
    "أنتن": "ت",         # تَفْعَلْنَ
    "هو": "ي",           # يَفْعَلُ
    "هي": "ت",           # تَفْعَلُ
    "هما (m)": "ي",      # يَفْعَلَانِ
    "هما (f)": "ت",      # تَفْعَلَانِ
    "هم": "ي",           # يَفْعَلُونَ
    "هن": "ي",           # يَفْعَلْنَ
}

_PRESENT_SUFFIXES: dict[str, str] = {
    "أنا": "ُ",           # أَفْعَلُ
    "نحن": "ُ",           # نَفْعَلُ
    "أنت": "ُ",           # تَفْعَلُ
    "أنتِ": "ِينَ",       # تَفْعَلِينَ
    "أنتما": "َانِ",      # تَفْعَلَانِ
    "أنتم": "ُونَ",       # تَفْعَلُونَ
    "أنتن": "ْنَ",        # تَفْعَلْنَ
    "هو": "ُ",            # يَفْعَلُ
    "هي": "ُ",            # تَفْعَلُ
    "هما (m)": "َانِ",    # يَفْعَلَانِ
    "هما (f)": "َانِ",    # تَفْعَلَانِ
    "هم": "ُونَ",         # يَفْعَلُونَ
    "هن": "ْنَ",          # يَفْعَلْنَ
}

# Subjunctive: change final damma → fatha (for most)
_SUBJUNCTIVE_SUFFIXES: dict[str, str] = {
    "أنا": "َ",           # أَفْعَلَ
    "نحن": "َ",           # نَفْعَلَ
    "أنت": "َ",           # تَفْعَلَ
    "أنتِ": "ِي",         # تَفْعَلِي
    "أنتما": "َا",        # تَفْعَلَا
    "أنتم": "ُوا",        # تَفْعَلُوا
    "أنتن": "ْنَ",        # تَفْعَلْنَ (same)
    "هو": "َ",            # يَفْعَلَ
    "هي": "َ",            # تَفْعَلَ
    "هما (m)": "َا",      # يَفْعَلَا
    "هما (f)": "َا",      # تَفْعَلَا
    "هم": "ُوا",          # يَفْعَلُوا
    "هن": "ْنَ",          # يَفْعَلْنَ (same)
}

# Jussive: change final damma → sukun (for most)
_JUSSIVE_SUFFIXES: dict[str, str] = {
    "أنا": "ْ",           # أَفْعَلْ
    "نحن": "ْ",           # نَفْعَلْ
    "أنت": "ْ",           # تَفْعَلْ
    "أنتِ": "ِي",         # تَفْعَلِي (same as subjunctive)
    "أنتما": "َا",        # تَفْعَلَا (same as subjunctive)
    "أنتم": "ُوا",        # تَفْعَلُوا (same as subjunctive)
    "أنتن": "ْنَ",        # تَفْعَلْنَ (same)
    "هو": "ْ",            # يَفْعَلْ
    "هي": "ْ",            # تَفْعَلْ
    "هما (m)": "َا",      # يَفْعَلَا
    "هما (f)": "َا",      # تَفْعَلَا
    "هم": "ُوا",          # يَفْعَلُوا
    "هن": "ْنَ",          # يَفْعَلْنَ
}


def _conjugate_present(
    mudhari_huwa: str,
    suffix_map: dict[str, str],
) -> dict[str, str]:
    """Conjugate a verb in present tense for all 13 pronouns using suffix map.

    mudhari_huwa: the 3rd m sg present form (e.g., يَفْعَلُ)
    suffix_map: the suffix patterns for each pronoun

    Extracts the prefix vowel from the huwa form (the vowel after ي)
    and applies it to all person prefixes. This correctly handles
    different prefix vowels (fatha for R3, damma for 4A/4C, etc.).
    """
    if not mudhari_huwa:
        return {p[0]: "" for p in PRONOUNS_13}

    # Extract prefix vowel from huwa form (vowel after first letter)
    prefix_vowel = ""
    if len(mudhari_huwa) >= 2 and mudhari_huwa[1] in (FATHA, KASRA, DAMMA):
        prefix_vowel = mudhari_huwa[1]

    # Check for gemination (shadda) on the last letter (5E pattern)
    has_gemination = SHADDA in mudhari_huwa

    # Stem = huwa form without the first letter and without the prefix vowel
    stem_start = 2 if prefix_vowel else 1
    stem_part = mudhari_huwa[stem_start:]

    # Remove final vowel from stem
    while stem_part and stem_part[-1] in (FATHA, KASRA, DAMMA):
        stem_part = stem_part[:-1]

    # For geminated verbs: the final shadda implies a vowel, so the stem
    # correctly includes the shadda. Don't strip the vowel from shadda.

    result = {}
    for pronoun, desc in PRONOUNS_13:
        pfx = _PRESENT_PREFIXES.get(pronoun, "")
        sfx = suffix_map.get(pronoun, "")

        if not sfx:
            result[pronoun] = ""
            continue

        # Build the form: prefix + prefix_vowel + stem + suffix
        conjugated = pfx + prefix_vowel + stem_part + sfx

        # Clean invalid diacritic sequences
        conjugated = _clean_diacritics(conjugated)

        result[pronoun] = conjugated

    return result


# ═══════════════════════════════════════════════════════════════════════════
# Imperative Conjugation for Augmented Verbs (Wazan-Based)
# ═══════════════════════════════════════════════════════════════════════════

def _conjugate_amr_from_wazan(
    amr_base: str,
) -> dict[str, str]:
    """Conjugate imperative (amr) for all 6 pronouns from the base form.

    The amr_base is the m sg imperative form from the wazan (e.g., فَعِّلْ for 4A,
    أَفْعِلْ for 4C, تَفَعَّلْ for 5A).

    For other pronouns, strip the final sukun and add gender/number suffixes.
    """
    result: dict[str, str] = {}

    # Strip the final sukun to get the conjugation base
    base = amr_base
    if base.endswith(SUKUN):
        base = base[:-1]

    for pronoun, desc in PRONOUNS_6:
        sfx = _AMR_SUFFIXES.get(pronoun, "")
        if pronoun == "أنت":
            # m sg: base + sukun (just the base form as-is)
            result[pronoun] = amr_base
        else:
            result[pronoun] = base + sfx

    return result


# ═══════════════════════════════════════════════════════════════════════════
# Main Conjugation Function
# ═══════════════════════════════════════════════════════════════════════════

def conjugate_lughowi(
    root: str,
    rumus: str,
    bab: int = 1,
) -> dict[str, Any]:
    """Generate full Tashrif Lughowi (pronoun conjugation) tables.

    Args:
        root: Root letters (3 for triliteral, 4 for quadriliteral).
        rumus: Rumus code ("3A", "3B", "3C", "4A", ..., "6").
        bab: Conjugation bab (1-6, only for Rumus 3).

    Returns:
        Dict with keys:
            - past_tense: list of {pronoun, text, description}
            - present_tense: same
            - present_subjunctive: same
            - present_jussive: same
            - imperative: list of {pronoun, text, description} (6 pronouns)
            - nahi: same (6 pronouns)
            - source: "sarf" | "pattern" | "hybrid"
    """
    letters = _get_root_letters(root)
    c1, c2, c3 = letters[0], letters[1], letters[2]
    c4 = letters[3] if len(letters) >= 4 else ""

    source = "pattern"

    # ── For Rumus 3: Use Sarf CLI for full conjugation ──
    if rumus in ("3A", "3B", "3C") and HAS_SARF:
        sarf_data = _get_sarf_full(c1 + c2 + c3, bab)
        if sarf_data:
            source = "sarf"
            return {
                "past_tense": _format_sarf_table(sarf_data.get("pastTense"), PRONOUNS_13),
                "present_tense": _format_sarf_table(sarf_data.get("presentTense"), PRONOUNS_13),
                "present_subjunctive": _format_sarf_table(sarf_data.get("presentSubjunctive"), PRONOUNS_13),
                "present_jussive": _format_sarf_table(sarf_data.get("presentJussive"), PRONOUNS_13),
                "imperative": _derive_amr_from_jussive(
                    sarf_data.get("presentJussive"), bab, "", c1, c2, c3
                ),
                "nahi": _derive_nahi_from_jussive(sarf_data.get("presentJussive")),
                "source": "sarf",
            }

    # ── For 4D (Ruba'i): Use Sarf CLI quadriliteral ──
    elif rumus == "4D" and HAS_SARF:
        try:
            sarf_data = _SARF.analyze(c1 + c2 + c3 + c4, bab)
            if sarf_data:
                return {
                    "past_tense": _format_sarf_table(sarf_data.get("pastTense"), PRONOUNS_13),
                    "present_tense": _format_sarf_table(sarf_data.get("presentTense"), PRONOUNS_13),
                    "present_subjunctive": _format_sarf_table(sarf_data.get("presentSubjunctive"), PRONOUNS_13),
                    "present_jussive": _format_sarf_table(sarf_data.get("presentJussive"), PRONOUNS_13),
                    "imperative": _derive_amr_from_jussive(
                        sarf_data.get("presentJussive"), 1, "", c1, c2, c3
                    ),
                    "nahi": _derive_nahi_from_jussive(sarf_data.get("presentJussive")),
                    "source": "sarf",
                }
        except Exception:
            pass

    # ── For augmented rumus (4A-5E, 6): Pattern-based ──
    rumus_data = WAZAN.get(rumus, {})
    if not rumus_data:
        return {"error": f"Unknown rumus: {rumus}"}

    if bab in rumus_data:
        patterns = rumus_data[bab]
    elif "default" in rumus_data:
        patterns = rumus_data["default"]
    else:
        patterns = next(iter(rumus_data.values()))

    madhi_huwa = apply_wazan(patterns.get("fiil_madhi", ""), c1, c2, c3, c4)
    mudhari_huwa = apply_wazan(patterns.get("fiil_mudhari", ""), c1, c2, c3, c4)

    # Conjugate tenses
    past_table = _conjugate_madhi(madhi_huwa)
    pres_table = _conjugate_present(mudhari_huwa, _PRESENT_SUFFIXES)
    subj_table = _conjugate_present(mudhari_huwa, _SUBJUNCTIVE_SUFFIXES)
    juss_table = _conjugate_present(mudhari_huwa, _JUSSIVE_SUFFIXES)

    # Conjugate imperative from wazan base form
    amr_wazan_base = patterns.get("fiil_amr", "")
    if amr_wazan_base:
        amr_base_form = apply_wazan(amr_wazan_base, c1, c2, c3, c4)
        amr_dict = _conjugate_amr_from_wazan(amr_base_form)
        amr_rows = [
            {"pronoun": p[0], "text": amr_dict.get(p[0], ""), "description": p[1]}
            for p in PRONOUNS_6
        ]
    else:
        amr_rows = [{"pronoun": p[0], "text": "", "description": p[1]} for p in PRONOUNS_6]

    # Nahi: لا + jussive form for each 2nd person pronoun
    nahi_rows = []
    for pronoun, desc in PRONOUNS_6:
        juss_form = juss_table.get(pronoun, "")
        if juss_form:
            nahi_rows.append({
                "pronoun": pronoun,
                "text": "لا " + juss_form,
                "description": desc,
            })
        else:
            nahi_rows.append({"pronoun": pronoun, "text": "", "description": desc})

    # Format results
    def _to_list(table: dict[str, str]) -> list[dict[str, str]]:
        return [
            {"pronoun": p[0], "text": table.get(p[0], ""), "description": p[1]}
            for p in PRONOUNS_13
        ]

    return {
        "past_tense": _to_list(past_table),
        "present_tense": _to_list(pres_table),
        "present_subjunctive": _to_list(subj_table),
        "present_jussive": _to_list(juss_table),
        "imperative": amr_rows,
        "nahi": nahi_rows,
        "source": source,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Demo / Test
# ═══════════════════════════════════════════════════════════════════════════

def _demo(output_path: str = ""):
    """Generate Lughowi tables for all 13 rumus and display."""
    lines = []
    lines.append("=" * 100)
    lines.append("  TASHRIF LUGHOWI GENERATOR — Phase 3 Demo")
    lines.append("=" * 100)

    test_cases = [
        ("فتح", "3A", 1, "فَتَحَ"),
        ("ضرب", "3B", 2, "ضَرَبَ"),
        ("كتب", "3C", 3, "كَتَبَ"),
        ("علم", "4A", 1, "عَلَّمَ"),
        ("شور", "4B", 1, "شَاوَرَ"),
        ("سلم", "4C", 1, "أَسْلَمَ"),
        ("زلزل", "4D", 1, "زَلْزَلَ"),
        ("علم", "5A", 1, "تَعَلَّمَ"),
        ("عرف", "5B", 1, "تَعَارَفَ"),
        ("حرم", "5C", 1, "اِحْتَرَمَ"),
        ("كسر", "5D", 1, "اِنْكَسَرَ"),
        ("حمر", "5E", 1, "اِحْمَرَّ"),
        ("غفر", "6",  1, "اِسْتَغْفَرَ"),
    ]

    for root, rumus, bab, example in test_cases:
        lines.append("")
        lines.append("-" * 100)
        lines.append(f"  {example}  |  Root: {root}  |  Rumus: {rumus}  |  Bab: {bab}")
        lines.append("-" * 100)

        result = conjugate_lughowi(root, rumus, bab)
        if "error" in result:
            lines.append(f"  ❌ {result['error']}")
            continue

        src = result.get("source", "?")
        lines.append(f"  Source: {src}")
        lines.append("")

        # Show past tense sample (first 4 pronouns)
        lines.append("  Past Tense (Fi'il Madhi):")
        for row in result.get("past_tense", [])[:4]:
            lines.append(f"    {row['pronoun']:<8} {row['text']}")

        # Show present tense sample
        lines.append("  Present Tense (Fi'il Mudhari'):")
        for row in result.get("present_tense", [])[:4]:
            lines.append(f"    {row['pronoun']:<8} {row['text']}")

        # Show subjunctive sample
        lines.append("  Present Subjunctive:")
        for row in result.get("present_subjunctive", [])[:4]:
            lines.append(f"    {row['pronoun']:<8} {row['text']}")

        # Show jussive sample
        lines.append("  Present Jussive:")
        for row in result.get("present_jussive", [])[:4]:
            lines.append(f"    {row['pronoun']:<8} {row['text']}")

        # Show imperative (all 6)
        lines.append("  Imperative (Fi'il Amr):")
        for row in result.get("imperative", []):
            lines.append(f"    {row['pronoun']:<8} {row['text']}")

        # Show nahi (all 6)
        lines.append("  Prohibitive (Fi'il Nahi):")
        for row in result.get("nahi", []):
            lines.append(f"    {row['pronoun']:<8} {row['text']}")

    lines.append("")
    lines.append("=" * 100)
    lines.append(f"  Generated {len(test_cases)} Lughowi conjugation tables.")
    lines.append("=" * 100)

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
