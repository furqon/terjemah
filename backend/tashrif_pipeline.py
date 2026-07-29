"""
tashrif_pipeline.py — End-to-end Tashrif Ishthilahi Pipeline.

Combines Phase 1 (Rumus classifier) and Phase 2 (Ishthilahi table generator)
into a single function that:

  1. Classifies a word into its Rumus pattern (3A-6) and Form (1-8)
  2. Generates the complete 8-column Ishthilahi table for that Rumus

Usage:
    from tashrif_pipeline import tashrif_analyze
    result = tashrif_analyze("يَكْتُبُ", root="كتب")
    print(result["rumus"])                 # "3C"
    print(result["ishthilahi_table"])      # 8-column table
    print(result["ishthilahi_dict"]["fiil_madhi"])  # كَتَبَ
"""

from __future__ import annotations

from typing import Any

from tashrif_classifier import (
    classify_rumus,
    R3A, R3B, R3C,
)
from tashrif_generator import generate_ishthilahi


# ═══════════════════════════════════════════════════════════════════════════
# Rumus → Bab Mapping
# ═══════════════════════════════════════════════════════════════════════════

# For Rumus 3, the bab determines the vowel pattern.
# Rumus 3A = Bab 1 (فتح يفتح), 3B = Bab 2 (ضرب يضرب), 3C = Bab 3 (نصر ينصر)
_RUMUS_TO_DEFAULT_BAB: dict[str, int] = {
    R3A: 1,
    R3B: 2,
    R3C: 3,
}


# ═══════════════════════════════════════════════════════════════════════════
# Main Pipeline Function
# ═══════════════════════════════════════════════════════════════════════════

def tashrif_analyze(
    word: str,
    root: str = "",
    pos_type: str = "",
    bab: int | None = None,
) -> dict[str, Any]:
    """Full Tashrif analysis: classify + generate 8-column table.

    Steps:
      1. Classify the word into its Rumus pattern using `classify_rumus()`.
      2. Map the Rumus to a default bab number (for Rumus 3).
      3. Generate the 8-column Ishthilahi table using `generate_ishthilahi()`.

    Args:
        word: The Arabic word to analyze (may have diacritics).
        root: The root letters (3 or 4). If empty, inferred by classifier.
        pos_type: POS hint ("verb", "noun", or "").
        bab: Override the default bab number (mainly for Rumus 3: 1-6).

    Returns:
        Dict with:
            - word, root, rumus, bab
            - classification, meaning_pattern
            - ishthilahi_table: list of 8 rows
            - ishthilahi_dict: dict of form_name -> value
            - current_form: form info of the input word
            - confidence: overall confidence
            - source: per-form source info
    """
    # Step 1: Classify the word
    classification = classify_rumus(word, root, pos_type)
    rumus = classification.rumus
    root_detected = classification.root

    if not rumus:
        return {
            "word": word,
            "root": root_detected or root,
            "rumus": "",
            "bab": 0,
            "classification": "Unknown",
            "meaning_pattern": "",
            "ishthilahi_table": [],
            "ishthilahi_dict": {},
            "current_form": {
                "number": classification.form,
                "label": classification.form_label,
                "label_id": classification.form_label_id,
            },
            "confidence": 0.0,
            "source": {},
            "reasons": classification.reasons,
            "error": "Could not classify this word. Try providing the root.",
        }

    # Step 2: Determine bab number
    if bab is not None:
        bab_num = bab
    else:
        bab_num = _RUMUS_TO_DEFAULT_BAB.get(rumus, 1)

    # Step 3: Generate the Ishthilahi table
    gen_root = root_detected if root_detected else (root if root else "")
    gen_result = generate_ishthilahi(gen_root, rumus, bab_num)

    return {
        "word": word,
        "root": root_detected,
        "rumus": rumus,
        "bab": bab_num,
        "classification": classification.classification,
        "meaning_pattern": classification.meaning_pattern,
        "ishthilahi_table": gen_result.get("table", []),
        "ishthilahi_dict": gen_result.get("table_dict", {}),
        "current_form": {
            "number": classification.form,
            "label": classification.form_label,
            "label_id": classification.form_label_id,
        },
        "confidence": classification.confidence,
        "source": gen_result.get("source", {}),
        "stem": classification.stem,
        "reasons": classification.reasons,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Demo / Test
# ═══════════════════════════════════════════════════════════════════════════

def _demo(output_path: str = ""):
    """Run the full pipeline on test words and display results."""
    lines = []
    lines.append("=" * 110)
    lines.append("  TASHRIF PIPELINE — Phase 1 + Phase 2 Integration Demo")
    lines.append("=" * 110)

    test_words = [
        # (word, root, rumus, note) — same cases as classifier demo
        ("فَتَحَ",   "فتح", "3A", "Madhi"),
        ("يَفتَحُ",  "فتح", "3A", "Mudhari'"),
        ("اِفتَحْ",  "فتح", "3A", "Amr"),
        ("فَتْحًا",  "فتح", "3A", "Mashdar"),
        ("فَاتِحٌ",  "فتح", "3A", "Ism Fa'il"),
        ("مَفْتُوحٌ","فتح", "3A", "Ism Maf'ul"),
        ("ضَرَبَ",   "ضرب", "3B", "Madhi"),
        ("يَضرِبُ",  "ضرب", "3B", "Mudhari'"),
        ("نَصَرَ",   "نصر", "3C", "Madhi"),
        ("يَنصُرُ",  "نصر", "3C", "Mudhari'"),
        ("كَتَبَ",   "كتب", "3C", "Madhi"),
        ("يَكتُبُ",  "كتب", "3C", "Mudhari'"),
        ("عَلَّمَ",  "علم", "4A", "Madhi"),
        ("يُعَلِّمُ","علم", "4A", "Mudhari'"),
        ("مُعَلِّمٌ","علم", "4A", "Ism Fa'il"),
        ("مُعَلَّمٌ","علم", "4A", "Ism Maf'ul"),
        ("شَاوَرَ",  "شور", "4B", "Madhi"),
        ("يُشَاوِرُ","شور", "4B", "Mudhari'"),
        ("أَسْلَمَ", "سلم", "4C", "Madhi"),
        ("يُسْلِمُ", "سلم", "4C", "Mudhari'"),
        ("مُسْلِمٌ", "سلم", "4C", "Ism Fa'il"),
        ("زَلْزَلَ", "زلزل","4D", "Madhi"),
        ("يُزَلْزِلُ","زلزل","4D", "Mudhari'"),
        ("تَعَلَّمَ", "علم", "5A", "Madhi"),
        ("يَتَعَلَّمُ","علم", "5A", "Mudhari'"),
        ("تَعَارَفَ", "عرف", "5B", "Madhi"),
        ("يَتَعَارَفُ","عرف", "5B", "Mudhari'"),
        ("اِحتَرَمَ", "حرم", "5C", "Madhi"),
        ("يَحتَرِمُ", "حرم", "5C", "Mudhari'"),
        ("اِنْكَسَرَ","كسر", "5D", "Madhi"),
        ("يَنكَسِرُ", "كسر", "5D", "Mudhari'"),
        ("اِحمَرَّ",  "حمر", "5E", "Madhi"),
        ("اِستَغْفَرَ","غفر", "6",  "Madhi"),
        ("يَستَغْفِرُ","غفر", "6",  "Mudhari'"),
        ("مُستَغْفِرٌ","غفر", "6",  "Ism Fa'il"),
    ]

    for word, root, expected, note in test_words:
        lines.append("")
        lines.append("-" * 110)
        lines.append(f"  [{note}] {word}  |  Root: {root}  |  Expected Rumus: {expected}")
        lines.append("-" * 110)

        result = tashrif_analyze(word, root)

        if "error" in result:
            lines.append(f"  ❌ {result['error']}")
            continue

        rumus = result["rumus"]
        rumus_ok = "✅" if rumus == expected else "❌"
        lines.append(f"  Detected Rumus: {rumus} {rumus_ok}  |  Bab: {result['bab']}  |  Confidence: {result['confidence']}")
        lines.append(f"  Classification: {result['classification']}")

        # Display the 8-column table
        header = f"  {'#':<2} {'Form':<14} {'Arabic':<22} {'ID Label':<22} {'Source':<10}"
        lines.append(header)
        lines.append("  " + "-" * 70)

        for row in result["ishthilahi_table"]:
            value = row["value"] if row["value"] else "—"
            lines.append(
                f"  {row['form_number']:<2} {row['form_name']:<14} {value:<22} "
                f"{row['form_label_id']:<22} {row['source']:<10}"
            )

        lines.append(f"  Meaning: {result['meaning_pattern']}")

    lines.append("")
    lines.append("=" * 110)
    lines.append(f"  Processed {len(test_words)} words through the full Tashrif pipeline.")
    lines.append("=" * 110)

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
