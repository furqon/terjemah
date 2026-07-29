"""
tashrif_generator.py — 8-Column Tashrif Ishthilahi Generator.

Generates the 8-column Tashrif Ishthilahi conjugation table for a given
root + Rumus combination, using:

  - Sarf CLI (when available) for Forms 1-2 (accurate diacritization)
  - Pattern-based wazan substitution for Forms 3-8

Reference: "At-Tashrif Al-Mujaz" by Andy Satiyo Ahmad (docs/tashrif.pdf)
Complete wazan table is on PDF page 45.

Usage:
    from tashrif_generator import generate_ishthilahi
    table = generate_ishthilahi("كتب", "3C", bab=3)
    print(table["fiil_madhi"])   # كَتَبَ
    print(table["fiil_mudhari"]) # يَكْتُبُ
"""

from __future__ import annotations

from typing import Any

from tashrif_classifier import FORM_LABELS, FORM_LABELS_ID, FormNumber, RUMUS_MEANING, ALIF, LAM

try:
    import pyarabic.araby as araby
    HAS_PYARABIC = True
except ImportError:
    HAS_PYARABIC = False

# Try to import Sarf client (soft dependency)
try:
    from sarf_client import SarfClient
    _SARF = SarfClient()
    HAS_SARF = _SARF.is_available()
except Exception:
    _SARF = None
    HAS_SARF = False


# ═══════════════════════════════════════════════════════════════════════════
# Constants — reused from tashrif_classifier
# ═══════════════════════════════════════════════════════════════════════════

FATHA = "\u064E"
KASRA = "\u0650"
DAMMA = "\u064F"
SUKUN = "\u0652"
SHADDA = "\u0651"




# ═══════════════════════════════════════════════════════════════════════════
# Wazan Pattern Database
# ═══════════════════════════════════════════════════════════════════════════

# Each rumus entry has a dict of form_name -> wazan_string
# Placeholders: ف → C1, ع → C2, L → C3 (third letter), ل → C3 or C4
# For quad roots: ف → C1, ع → C2, ل → C3, L → C4
# Prefixes and suffixes are literal Arabic text.
# Diacritics are included in the patterns.

FORM_NAMES = [
    "fiil_madhi",      # Form 1
    "fiil_mudhari",    # Form 2
    "fiil_amr",        # Form 3
    "fiil_nahi",       # Form 4
    "mashdar",         # Form 5
    "ism_fail",        # Form 6
    "ism_maful",       # Form 7
    "zamami",          # Form 8
]

# Each Rumus can have multiple sub-entries keyed by bab, or a single entry
# if bab doesn't matter. Use 'default' for bab-independent patterns.
WAZAN: dict[str, dict] = {
    # ═══════════════════════════════════════════════════════════════════
    # Rumus 3A-C: Fi'il Tsulatsi Mujarrad (Bab 1-6)
    # ═══════════════════════════════════════════════════════════════════
    "3A": {  # Bab 1: فَعَلَ يَفْعَلُ
        1: {
            "fiil_madhi": "فَعَلَ",
            "fiil_mudhari": "يَفْعَلُ",
            "fiil_amr": "اِفْعَلْ",
            "fiil_nahi": "لا تَفْعَلْ",
            "mashdar": "فَعْلًا",
            "ism_fail": "فَاعِلٌ",
            "ism_maful": "مَفْعُولٌ",
            "zamami": "مَفْعَلٌ",
        },
        4: {  # Bab 4: فَعِلَ يَفْعَلُ — Same Ishthilahi table as Bab 1 per PDF note
            "fiil_madhi": "فَعِلَ",
            "fiil_mudhari": "يَفْعَلُ",
            "fiil_amr": "اِفْعَلْ",
            "fiil_nahi": "لا تَفْعَلْ",
            "mashdar": "فَعْلًا",
            "ism_fail": "فَاعِلٌ",
            "ism_maful": "مَفْعُولٌ",
            "zamami": "مَفْعَلٌ",
        },
    },
    "3B": {  # Bab 2: فَعَلَ يَفْعِلُ
        2: {
            "fiil_madhi": "فَعَلَ",
            "fiil_mudhari": "يَفْعِلُ",
            "fiil_amr": "اِفْعِلْ",
            "fiil_nahi": "لا تَفْعِلْ",
            "mashdar": "فَعْلًا",
            "ism_fail": "فَاعِلٌ",
            "ism_maful": "مَفْعُولٌ",
            "zamami": "مَفْعِلٌ",
        },
        5: {  # Bab 5: فَعِلَ يَفْعِلُ — Same as Bab 2 per PDF note
            "fiil_madhi": "فَعِلَ",
            "fiil_mudhari": "يَفْعِلُ",
            "fiil_amr": "اِفْعِلْ",
            "fiil_nahi": "لا تَفْعِلْ",
            "mashdar": "فَعْلًا",
            "ism_fail": "فَاعِلٌ",
            "ism_maful": "مَفْعُولٌ",
            "zamami": "مَفْعِلٌ",
        },
    },
    "3C": {  # Bab 3: فَعَلَ يَفْعُلُ
        3: {
            "fiil_madhi": "فَعَلَ",
            "fiil_mudhari": "يَفْعُلُ",
            "fiil_amr": "اُفْعُلْ",
            "fiil_nahi": "لا تَفْعُلْ",
            "mashdar": "فَعْلًا",
            "ism_fail": "فَاعِلٌ",
            "ism_maful": "مَفْعُولٌ",
            "zamami": "مَفْعَلٌ",
        },
        6: {  # Bab 6: فَعُلَ يَفْعُلُ — Only 4 forms (madhi, mudhari', mashdar, shifat)
            "fiil_madhi": "فَعُلَ",
            "fiil_mudhari": "يَفْعُلُ",
            "fiil_amr": "اُفْعُلْ",
            "fiil_nahi": "لا تَفْعُلْ",
            "mashdar": "فَعْلًا",
            "ism_fail": "فَاعِلٌ",
            "ism_maful": "مَفْعُولٌ",
            "zamami": "مَفْعَلٌ",
        },
    },
    # ═══════════════════════════════════════════════════════════════════
    # Rumus 4A: Fa''ala (فَعَّلَ)
    # ═══════════════════════════════════════════════════════════════════
    "4A": {
        "default": {
            "fiil_madhi": "فَعَّلَ",
            "fiil_mudhari": "يُفَعِّلُ",
            "fiil_amr": "فَعِّلْ",
            "fiil_nahi": "لا تُفَعِّلْ",
            "mashdar": "تَفْعِيلًا",
            "ism_fail": "مُفَعِّلٌ",
            "ism_maful": "مُفَعَّلٌ",
            "zamami": "مُفَعَّلٌ",
        }
    },
    # ═══════════════════════════════════════════════════════════════════
    # Rumus 4B: Fa'ala (فَاعَلَ)
    # ═══════════════════════════════════════════════════════════════════
    "4B": {
        "default": {
            "fiil_madhi": "فَاعَلَ",
            "fiil_mudhari": "يُفَاعِلُ",
            "fiil_amr": "فَاعِلْ",
            "fiil_nahi": "لا تُفَاعِلْ",
            "mashdar": "مُفَاعَلَةً",
            "ism_fail": "مُفَاعِلٌ",
            "ism_maful": "مُفَاعَلٌ",
            "zamami": "مُفَاعَلٌ",
        }
    },
    # ═══════════════════════════════════════════════════════════════════
    # Rumus 4C: Af'ala (أَفْعَلَ)
    # ═══════════════════════════════════════════════════════════════════
    "4C": {
        "default": {
            "fiil_madhi": "أَفْعَلَ",
            "fiil_mudhari": "يُفْعِلُ",
            "fiil_amr": "أَفْعِلْ",
            "fiil_nahi": "لا تُفْعِلْ",
            "mashdar": "إِفْعَالًا",
            "ism_fail": "مُفْعِلٌ",
            "ism_maful": "مُفْعَلٌ",
            "zamami": "مُفْعَلٌ",
        }
    },
    # ═══════════════════════════════════════════════════════════════════
    # Rumus 4D: Fa'lala (رُبَاعِي — 4-letter root)
    # ═══════════════════════════════════════════════════════════════════
    "4D": {
        "default": {
            "fiil_madhi": "فَعْلَلَ",
            "fiil_mudhari": "يُفَعْلِلُ",
            "fiil_amr": "فَعْلِلْ",
            "fiil_nahi": "لا تُفَعْلِلْ",
            "mashdar": "فَعْلَلَةً",
            "ism_fail": "مُفَعْلِلٌ",
            "ism_maful": "مُفَعْلَلٌ",
            "zamami": "مُفَعْلَلٌ",
        }
    },
    # ═══════════════════════════════════════════════════════════════════
    # Rumus 5A: Tafa''ala (تَفَعَّلَ)
    # ═══════════════════════════════════════════════════════════════════
    "5A": {
        "default": {
            "fiil_madhi": "تَفَعَّلَ",
            "fiil_mudhari": "يَتَفَعَّلُ",
            "fiil_amr": "تَفَعَّلْ",
            "fiil_nahi": "لا تَتَفَعَّلْ",
            "mashdar": "تَفَعُّلًا",
            "ism_fail": "مُتَفَعِّلٌ",
            "ism_maful": "مُتَفَعَّلٌ",
            "zamami": "مُتَفَعَّلٌ",
        }
    },
    # ═══════════════════════════════════════════════════════════════════
    # Rumus 5B: Tafa'ala (تَفَاعَلَ)
    # ═══════════════════════════════════════════════════════════════════
    "5B": {
        "default": {
            "fiil_madhi": "تَفَاعَلَ",
            "fiil_mudhari": "يَتَفَاعَلُ",
            "fiil_amr": "تَفَاعَلْ",
            "fiil_nahi": "لا تَتَفَاعَلْ",
            "mashdar": "تَفَاعُلًا",
            "ism_fail": "مُتَفَاعِلٌ",
            "ism_maful": "مُتَفَاعَلٌ",
            "zamami": "مُتَفَاعَلٌ",
        }
    },
    # ═══════════════════════════════════════════════════════════════════
    # Rumus 5C: Ifta'ala (اِفْتَعَلَ)
    # ═══════════════════════════════════════════════════════════════════
    "5C": {
        "default": {
            "fiil_madhi": "اِفْتَعَلَ",
            "fiil_mudhari": "يَفْتَعِلُ",
            "fiil_amr": "اِفْتَعِلْ",
            "fiil_nahi": "لا تَفْتَعِلْ",
            "mashdar": "اِفْتِعَالًا",
            "ism_fail": "مُفْتَعِلٌ",
            "ism_maful": "مُفْتَعَلٌ",
            "zamami": "مُفْتَعَلٌ",
        }
    },
    # ═══════════════════════════════════════════════════════════════════
    # Rumus 5D: Infa'ala (اِنْفَعَلَ)
    # ═══════════════════════════════════════════════════════════════════
    "5D": {
        "default": {
            "fiil_madhi": "اِنْفَعَلَ",
            "fiil_mudhari": "يَنْفَعِلُ",
            "fiil_amr": "اِنْفَعِلْ",
            "fiil_nahi": "لا تَنْفَعِلْ",
            "mashdar": "اِنْفِعَالًا",
            "ism_fail": "مُنْفَعِلٌ",
            "ism_maful": "مُنْفَعَلٌ",
            "zamami": "مُنْفَعَلٌ",
        }
    },
    # ═══════════════════════════════════════════════════════════════════
    # Rumus 5E: If'alla (اِفْعَلَّ)
    # ═══════════════════════════════════════════════════════════════════
    "5E": {
        "default": {
            "fiil_madhi": "اِفْعَلَّ",
            "fiil_mudhari": "يَفْعَلُّ",
            "fiil_amr": "اِفْعَلَّ",
            "fiil_nahi": "لا تَفْعَلَّ",
            "mashdar": "اِفْعِلَالًا",
            "ism_fail": "مُفْعَلٌّ",
            "ism_maful": "مُفْعَلٌّ",
            "zamami": "مُفْعَلٌّ",
        }
    },
    # ═══════════════════════════════════════════════════════════════════
    # Rumus 6: Istaf'ala (اِسْتَفْعَلَ)
    # ═══════════════════════════════════════════════════════════════════
    "6": {
        "default": {
            "fiil_madhi": "اِسْتَفْعَلَ",
            "fiil_mudhari": "يَسْتَفْعِلُ",
            "fiil_amr": "اِسْتَفْعِلْ",
            "fiil_nahi": "لا تَسْتَفْعِلْ",
            "mashdar": "اِسْتِفْعَالًا",
            "ism_fail": "مُسْتَفْعِلٌ",
            "ism_maful": "مُسْتَفْعَلٌ",
            "zamami": "مُسْتَفْعَلٌ",
        }
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# Letter Substitution Engine
# ═══════════════════════════════════════════════════════════════════════════

def _get_root_letters(root: str) -> tuple[str, ...]:
    """Extract individual root letters (stripping diacritics)."""
    if HAS_PYARABIC:
        from pyarabic.araby import strip_tashkeel
        plain = strip_tashkeel(root)
    else:
        plain = "".join(ch for ch in root if ch not in {
            FATHA, KASRA, DAMMA, SUKUN, SHADDA,
            "\u064B", "\u064C", "\u064D", "\u0670"
        })
    return tuple(plain)



def apply_wazan(wazan_str: str, c1: str, c2: str, c3: str, c4: str = "") -> str:
    """Substitute root letters into a wazan pattern.

    Mapping rules:
      'ف' → C1 (first root letter)
      'ع' → C2 (second root letter)
      'ل' → C3 (third root letter) for triliteral
             C3 (first occurrence) or C4 (second occurrence) for quadriliteral

    Special handling:
      - The sequence 'لا' (negation prefix) is preserved as-is — its ل
        is NOT substituted because it's the negation particle, not a placeholder.
      - Single 'ل' outside of 'لا' IS substituted as the root's 3rd letter.
    """
    LAM_ALIF = LAM + ALIF  # لا

    if c4:
        # Quadriliteral: track which 'ل' we're on
        lam_count = 0
        result = []
        i = 0
        while i < len(wazan_str):
            ch = wazan_str[i]
            # Check for لا as a unit (negation prefix)
            if wazan_str[i:i+2] == LAM_ALIF:
                result.append(LAM_ALIF)
                i += 2
                continue
            if ch == "ف":
                result.append(c1)
            elif ch == "ع":
                result.append(c2)
            elif ch == "ل":
                if lam_count == 0:
                    result.append(c3)
                    lam_count = 1
                else:
                    result.append(c4)
            else:
                result.append(ch)
            i += 1
        return "".join(result)
    else:
        # Triliteral
        mapping = {"ف": c1, "ع": c2, "ل": c3}
        result = []
        i = 0
        while i < len(wazan_str):
            ch = wazan_str[i]
            # Check for لا as a unit (negation prefix) — preserve it
            if wazan_str[i:i+2] == LAM_ALIF:
                result.append(LAM_ALIF)
                i += 2
                continue
            result.append(mapping.get(ch, ch))
            i += 1
        return "".join(result)


# ═══════════════════════════════════════════════════════════════════════════
# Sarf CLI Integration
# ═══════════════════════════════════════════════════════════════════════════

def _get_madhi_huwa_from_sarf(c1: str, c2: str, c3: str, bab: int) -> str | None:
    """Get the 3rd person masc singular madhi form from Sarf CLI."""
    if not HAS_SARF:
        return None
    try:
        root = c1 + c2 + c3
        data = _SARF.analyze(root, bab)
        return data.get("pastTense", {}).get("هو", None)
    except Exception:
        pass
    return None


def _get_mudhari_huwa_from_sarf(c1: str, c2: str, c3: str, bab: int) -> str | None:
    """Get the 3rd person masc singular mudhari' form from Sarf CLI."""
    if not HAS_SARF:
        return None
    try:
        root = c1 + c2 + c3
        data = _SARF.analyze(root, bab)
        return data.get("presentTense", {}).get("هو", None)
    except Exception:
        pass
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Main Generation Functions
# ═══════════════════════════════════════════════════════════════════════════

def generate_ishthilahi(
    root: str,
    rumus: str,
    bab: int = 1,
) -> dict[str, Any]:
    """Generate the 8-column Tashrif Ishthilahi table.

    Args:
        root: Root letters (3 for triliteral, 4 for quadriliteral).
        rumus: Rumus code ("3A", "3B", "3C", "4A", ..., "6").
        bab: Conjugation bab (1-6, only for Rumus 3).

    Returns:
        Dict with:
            - root, rumus, bab
            - table: list of 8 rows (each with form_number, form_name, label, value)
            - table_dict: dict of form_name -> value (convenience)
            - source: dict of form_name -> "sarf" | "pattern"
    """
    # Get root letters
    letters = _get_root_letters(root)
    c1, c2, c3 = letters[0], letters[1], letters[2]
    c4 = letters[3] if len(letters) >= 4 else ""

    # Get wazan pattern for this rumus
    rumus_data = WAZAN.get(rumus, {})
    if not rumus_data:
        return {
            "root": root, "rumus": rumus, "bab": bab,
            "error": f"Unknown rumus: {rumus}",
            "table": [], "table_dict": {},
        }

    # Get the specific bab entry or default
    if bab in rumus_data:
        patterns = rumus_data[bab]
    elif "default" in rumus_data:
        patterns = rumus_data["default"]
    else:
        # Fallback: pick first available
        patterns = next(iter(rumus_data.values()))

    table_rows: list[dict] = []
    table_dict: dict[str, str] = {}
    source_info: dict[str, str] = {}

    for form_name in FORM_NAMES:
        wazan_str = patterns.get(form_name, "")
        if not wazan_str:
            table_rows.append({
                "form_number": FORM_NAMES.index(form_name) + 1,
                "form_name": form_name,
                "value": "",
                "source": "missing",
            })
            table_dict[form_name] = ""
            continue

        # Apply letter substitution
        gen_value = apply_wazan(wazan_str, c1, c2, c3, c4)

        # For forms 1-2, try Sarf CLI for more accurate diacritization
        sarf_value = None
        source = "pattern"

        if form_name == "fiil_madhi" and rumus in ("3A", "3B", "3C"):
            sv = _get_madhi_huwa_from_sarf(c1, c2, c3, bab)
            if sv:
                sarf_value = sv
                source = "sarf"

        elif form_name == "fiil_mudhari" and rumus in ("3A", "3B", "3C"):
            sv = _get_mudhari_huwa_from_sarf(c1, c2, c3, bab)
            if sv:
                sarf_value = sv
                source = "sarf"

        table_value = sarf_value if sarf_value else gen_value

        fn = FORM_NAMES.index(form_name) + 1
        fn_enum = FormNumber(fn) if fn <= 8 else None

        row = {
            "form_number": fn,
            "form_name": form_name,
            "form_label_ar": FORM_LABELS.get(fn_enum, ""),
            "form_label_id": FORM_LABELS_ID.get(fn_enum, ""),
            "value": table_value,
            "source": source,
        }
        table_rows.append(row)
        table_dict[form_name] = table_value
        source_info[form_name] = source

    return {
        "root": root,
        "rumus": rumus,
        "bab": bab,
        "table": table_rows,
        "table_dict": table_dict,
        "source": source_info,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Demo / Test
# ═══════════════════════════════════════════════════════════════════════════

def _demo(output_path: str = ""):
    """Generate Ishthilahi tables for all 13 rumus and display."""
    lines = []
    lines.append("=" * 100)
    lines.append("  TASHRIF ISHTHILAHI GENERATOR — Phase 2 Demo")
    lines.append("=" * 100)

    test_cases = [
        # (root, rumus, bab, example_word)
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

        result = generate_ishthilahi(root, rumus, bab)

        if "error" in result:
            lines.append(f"  ❌ {result['error']}")
            continue

        header = f"  {'#':<2} {'Form':<14} {'Arabic':<22} {'Indonesian':<22} {'Source':<10}"
        lines.append(header)
        lines.append("  " + "-" * 70)

        from tashrif_classifier import RUMUS_MEANING
        base_meaning = RUMUS_MEANING.get(rumus, "")

        for row in result["table"]:
            value = row["value"] if row["value"] else "—"
            src = row["source"]
            lines.append(
                f"  {row['form_number']:<2} {row['form_name']:<14} {value:<22} "
                f"{row['form_label_id']:<22} {src:<10}"
            )

        lines.append(f"  Meaning: {base_meaning}")

    lines.append("")
    lines.append("=" * 100)
    lines.append(f"  Generated {len(test_cases)} Ishthilahi tables.")
    if HAS_SARF:
        lines.append("  Sarf CLI available: Forms 1-2 use Sarf output")
    else:
        lines.append("  Sarf CLI NOT available: All forms use pattern generation")
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
