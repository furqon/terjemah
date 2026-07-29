# Check Result — يضربون وجوههم

## ✅ Issue 1 & 2: Rumus & Form Classification — FIXED

**Input:** يَضْرِبُونَ (root: ضرب)

| Check | Result |
|-------|--------|
| **Rumus** | **3B** ✅ (ضرب يضرب — Bab 2) |
| **C2 vowel (ر)** | **Kasrah (ِ)** ✅ |
| **Form** | **2 — Fi'il Mudhari' (الفعل المضارع)** ✅ |
| **Confidence** | 0.82 ✅ |
| **Suffix ون stripped** | ✅ |
| **Fi'il Mudhari' column** | Now shows the actual word **يَضْرِبُونَ** (not base form يَضْرِبُ) |

**Changes made:**
1. Added `ون` to SUFFIXES list in `tashrif_classifier.py` — allows stripping the masculine plural suffix properly
2. Fixed `_classify_form` dead code (`if "mudhari" in pref` → `if analysis.get("has_mudhari_prefix") and rumus in (R3A,R3B,R3C)`)
3. Changed fallback bab default from 3→1 in `main.py`
4. Frontend now passes word form to Tashrif API
5. `main.py` now overrides the Ishthilahi column with the actual input word when form matches

## ❌ Issue 3: Tashkeel of وجوههم — NOT FIXED (CAMeL limitation)

CAMeL outputs `وُجُوهِهِم` (kasrah on ه — genitive) instead of `وُجُوهَهُم` (fatha on ه — accusative/maf'ul bih).

Both forms are valid Arabic. CAMeL doesn't do full syntactic parsing to detect the maf'ul bih context. User chose **not** to add a word override since it would be incorrect in genitive contexts (e.g., after a preposition).

## ✅ Bonus Fix: Nahi column لا preservation — FIXED

The nahi (Form 4) column was showing `با تَضْرِبْ` instead of `لا تَضْرِبْ`. The `apply_wazan()` function was incorrectly substituting the `ل` in the negation prefix `لا` with the root's C3 letter (`ب`).

**Fix**: `apply_wazan()` now preserves the `لا` 2-character sequence as a unit before doing single-character letter substitution. Now shows `لا تَضْرِبْ` correctly.

## Summary of Code Changes

| File | Change |
|------|--------|
| `backend/tashrif_classifier.py` | Added `ون` to SUFFIXES; fixed `_classify_form` dead code; added `LAM` constant |
| `backend/tashrif_generator.py` | Fixed `apply_wazan()` to preserve `لا` (negation prefix) from letter substitution |
| `backend/main.py` | Fixed indentation bug; changed bab default from 3→1; added input word override in Ishthilahi column |
| `frontend/pages/index.vue` | Pass word form to Tashrif API |
| `frontend/components/TashrifModal.vue` | Accept word prop, send in API call |
| `docs/RUMUS_CLASSIFICATION.md` | New — comprehensive guide to classification logic |

## Server Status

Backend is running on **port 8000** with all fixes applied. Frontend needs to be restarted (if not already running): `cd frontend && npm run dev`