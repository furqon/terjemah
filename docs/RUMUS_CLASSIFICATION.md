# Rumus Classification Logic
## How the Classifier Decides 3A/3B/3C, 4A–4D, 5A–5E & 6

**Source:** `backend/tashrif_classifier.py`  
**Reference:** `docs/tashrif.pdf` — "At-Tashrif Al-Mujaz" by Andy Satiyo Ahmad  
**Last updated:** July 29, 2026

---

## Overview

The Rumus classifier takes an Arabic word (optionally with its root) and determines:

1. **Rumus (Formula)**: The morphological pattern — 3A, 3B, 3C, 4A, 4B, 4C, 4D, 5A, 5B, 5C, 5D, 5E, or 6.
2. **Form (Column)**: Which of the 8 Tashrif Ishthilahi columns the word belongs to — Fi'il Madhi (1), Fi'il Mudhari' (2), Fi'il Amr (3), Fi'il Nahi (4), Mashdar (5), Ism Fa'il (6), Ism Maf'ul (7), or Zamami (8).

The classifier works by **affix stripping + pattern matching**. It removes known suffixes and non-morphological prefixes, then compares the remaining stem against the standard "Wazan" patterns.

---

## Step 1: Affix Stripping

Before classifying, the word is stripped down to its core letters:

### What gets stripped

| Affix Type | Items Stripped | Example |
|------------|---------------|---------|
| **Negation لا** | لا at start | لا تَكْتُبُ → تَكْتُبُ |
| **Future س** | س at start | سَيَكْتُبُ → يَكْتُبُ |
| **Definite ال** | ال at start (only if 3+ letters remain) | الْكِتَابُ → كِتَابُ |
| **Suffixes** | See suffix list below | يَكْتُبُونَ → يَكْتُبُ |

### Suffix list (ordered longest-first)

| Suffix | Type | Example |
|--------|------|---------|
| تما | Dual past 2nd/3rd f | فَعَلْتُمَا → فَعَلْ |
| تم | Plural past 2nd m | فَعَلْتُمْ → فَعَلْ |
| تنّ | Plural past 2nd f | فَعَلْتُنَّ → فَعَلْ |
| وا | Plural past 3rd m | كَتَبُوا → كَتَبْ |
| **ون** | **Plural masc. present/participle** | **يَكْتُبُونَ → يَكْتُبُ** |
| ين | Plural/feminine suffix | مُسْلِمِينَ → مُسْلِم |
| نا | Plural past 1st | كَتَبْنَا → كَتَبْ |
| ات | Feminine plural | مُسْلِمَاتٌ → مُسْلِم |
| تم | Past 2nd m sg | كَتَبْتَ → كَتَبْ |
| تن | Past 2nd f sg | كَتَبْتِ → كَتَبْ |
| كم | Suffix "you" | كِتَابُكُمْ → كِتَابُ |
| هم | Suffix "them" | كِتَابُهُمْ → كِتَابُ |
| ها | Suffix "her" | كِتَابُهَا → كِتَابُ |
| ت | Past 2nd/3rd f sg | كَتَبَتْ → كَتَب |
| ا | Dual/phural marker | كَتَبَا → كَتَب |
| ن | 1st pl / feminine pl | كَتَبْنَ → كَتَب |
| و | Masculine pl (3rd past) | كَتَبُوا → كَتَب |
| ك | Suffix "you" | كِتَابُكَ → كِتَابُ |
| ه | Suffix "him" | كِتَابُهُ → كِتَابُ |

**Critical note on `ون`**: This masculine plural suffix was added to fix a bug where words like `يَضْرِبُونَ` (from root ضرب) were not being properly parsed. Without `ون` in the suffix list, the suffix stripper would only strip `و` (1 character), leaving a 5-letter stem `يضربن`, which would never match any 3-letter pattern. With `ون` properly stripped, the stem becomes `يضرب` (4 letters), and after removing the mudhari' prefix ي in Pass 2, we get `ضرب` (3 letters) → **Rumus 3B**.

### What does NOT get stripped

**Mudhari' person prefixes** (أ, ن, ي, ت) are intentionally NOT stripped in this step. These prefixes can be part of the augmented stem (e.g., أ in 4C أَفْعَلَ, ت in 5A تَفَعَّلَ). Mudhari' prefix detection is handled by the classifier's Pass 2 logic instead.

---

## Step 2: Stem Analysis

After affix stripping, the classifier creates an analysis dict with key features:

```python
{
    "stem_letters": "كتب",       # Core stem letters
    "stem_letter_count": 3,      # Number of letters
    "has_shadda": False,         # Contains ّ?
    "has_mudhari_prefix": True,  # Starts with ي/ت/أ/ن?
    "starts_with_alif": True,    # Starts with any alif variant?
    "starts_with_ta": False,
    "starts_with_meem": False,
    "shadda_positions": [],      # Where ّ appears in original word
}
```

---

## Step 3: Rumus Classification — Two Passes

The classifier runs **two passes** over the stem letters:

### PASS 1: Check full stem against known patterns

The stem is checked in priority order. The **first matching pattern wins**.

#### 1a) 4-letter root → Rumus 4D

If the user provides a 4-letter root (e.g., `زلزل`), the result is always **Rumus 4D (Fa'lala)**.

```
Example: زَلْزَلَ (root: زلزل → 4 letters) → Rumus 4D
```

#### 1b) Alif-wasl patterns (stem starts with ا)

| Check | Condition | Rumus |
|-------|-----------|-------|
| 6 | Stem[1:3] = `ست` (س + ت) | **6** (Istaf'ala) |
| 5C | Stem[2] = ت (ت as infix) + 5+ letters | **5C** (Ifta'ala) |
| 5D | Stem[1] = ن (ن + 5+ letters) | **5D** (Infa'ala) |
| 5E | Shadda near end | **5E** (If'alla — colors/defects) |

**Examples:**
```
اِسْتَغْفَرَ  → ا + س + ت + غ + ف + ر → ا at 0, ت at 2... wait.
               Actually: stem = استغفر (6 letters)
               letters[1]=س, letters[2]=ت → pattern 'است' → Rumus 6 ✓

اِحْتَرَمَ    → ا + ح + ت + ر + م (5 letters)
               letters[0]=ا, letters[2]=ت → Rumus 5C ✓

اِنْكَسَرَ    → ا + ن + ك + س + ر (5 letters)
               letters[0]=ا, letters[1]=ن → Rumus 5D ✓

اِحْمَرَّ     → ا + ح + م + ر (shadda on ر at end)
               letters[0]=ا + has_shadda → Rumus 5E ✓
```

#### 1c) Ta-prefix patterns (stem starts with ت)

| Check | Condition | Rumus |
|-------|-----------|-------|
| 5A | Has shadda (tasydid) | **5A** (Tafa''ala) |
| 5B | No shadda, stem[2] = ا (alif at position 2) | **5B** (Tafa'ala) |

**Examples:**
```
تَعَلَّمَ    → ت + ع + ل + م (has shadda on ل? No — shadda on ع)
               Actually تَعَلَّمَ has shadda on ل → Rumus 5A ✓

تَعَارَفَ    → ت + ع + ا + ر + ف (no shadda, letters[2]=ا)
               → Rumus 5B ✓
```

#### 1d) Hamzah prefix → Rumus 4C

If the stem starts with `أ` (hamzah alif), 2–5 letters long, and no shadda:

```
أَسْلَمَ  → أ + س + ل + م (4 letters, no shadda) → Rumus 4C ✓
أَفْعَلَ  → أ + ف + ع + ل (4 letters, no shadda) → Rumus 4C ✓
```

**But**: If the word starts with `أ` AND has shadda, it's not 4C (it might be a different form).

#### 1e) Meem prefix → derived nouns

Words starting with `م` and 4+ letters are treated as derived nouns. Several sub-checks:

| Condition | Rumus |
|-----------|-------|
| م + ا at [1] | **4B** derived noun (مفاعل) |
| م + س + ت at [0:3] | **6** derived noun (مستفعل) |
| م + ت at [2] (no shadda) | **5C** derived noun (مفتعل) |
| م + ن at [2] | **5D** derived noun (منفعل) |
| Has shadda | **4A** derived noun (مفعلّ) |
| م + ت at [1] + 5+ letters + ا at [3] | **5B** (متفاعل) |
| م + ت at [1] + 5+ letters, no ا | **5A** (متفعل) |
| 4 letters total | **4C** (مفعل) |
| Other | **4C** (default) |

**Special exclusion**: `مَفْعُولٌ` pattern (م + C1 + C2 + و/ي + C3) is NOT classified here — it falls through to be classified as a Rumus 3 derived noun (Ism Maf'ul of R3).

```
مُعَلِّمٌ  → م + ع + ل + م (has shadda on ل) → Rumus 4A derived noun ✓
مُسْلِمٌ   → م + س + ل + م (4 letters) → Rumus 4C derived noun ✓
مُسْتَغْفِرٌ → م + س + ت + غ + ف + ر → pattern مست → Rumus 6 ✓
```

#### 1f) Alif-wasl 4-letter → possible Amr of R3

If stem starts with `ا` and has exactly 4 letters (and didn't match 5C/D/E/6 above):
```
اِفْتَحْ  → ا + ف + ت + ح (4 letters) → Amr of Rumus 3 (low confidence 0.50)
```

#### 1g) Alif after C1 → Rumus 4B (or Ism Fa'il of R3)

If letters[1] = ا (alif at the second letter position):
```
شَاوَرَ    → ش + ا + و + ر → letters[1]=ا → Rumus 4B ✓
فَاعِلٌ    → ف + ا + ع + ل → letters[1]=ا → Rumus 4B (same pattern as Ism Fa'il of R3)
```
**Ambiguity note**: R4B (فاعل) and Ism Fa'il of R3 (فَاعِل) are structurally identical. The classifier labels both as R4B with moderate confidence (0.70).

#### 1h) Shadda on C2 → Rumus 4A

If the word has shadda (ّ) and the shadda falls on the 2nd letter (C2):
```
عَلَّمَ  → ع + ل + م → shadda on ل (2nd letter) → Rumus 4A ✓
```

#### 1i) 3-letter stem → Rumus 3 (A/B/C)

This is the most important decision point. For 3-letter stems, the classifier checks the **vowel on the second consonant (C2)**:

| C2 Vowel | Rumus | Bab | Example |
|----------|-------|-----|---------|
| **Fatha (َ)** | **3A** | Bab 1 (فتح يفتح) | فَتَحَ |
| **Kasra (ِ)** | **3B** | Bab 2 (ضرب يضرب) | ضَرَبَ |
| **Damma (ُ)** | **3C** | Bab 3 (نصر ينصر) | نَصَرَ |
| **No vowel** | **3A** (fallback) | Bab 1 | (madhi-only forms) |

**How the vowel is found** (`_vowel_on_second_consonant` function):

1. Get the plain letters of the word
2. Determine C2 position:
   - If first letter is mudhari' prefix (ي/ت/أ/ن), then C2 = letters[2] (3rd char)
   - Otherwise, C2 = letters[1] (2nd char)
3. Walk through the **original diacritized text**, counting Arabic letters
4. When we reach C2, read the **next character** — that's the vowel

Example for `يَضْرِبُونَ`:
```
Letters: ي ض ر ب و ن (6 letters)
First letter ي → mudhari' prefix → C2 position = index 2 → ر
Original text: يَضْرِبُونَ
  ي → letter 0
  َ → fatha on C1
  ض → letter 1
  ر → letter 2 (C2)
  ِ → KASRA ✓ → Rumus 3B ✓
```

**⚠️ Limitation**: Madhi-only forms (past tense without vowel on C2) of R3B and R3C default to R3A because all three have the same `فَعَلَ` pattern. For example:
```
ضَرَبَ → word letters = ضرب (no vowel on ر after stripping)
       → no C2 vowel detected → defaults to Rumus 3A (fallback)
```
The fix: Pass the **mudhari' form** (e.g., يَضْرِبُ) alongside the root to disambiguate.

---

### PASS 2: Mudhari' prefix detected

If PASS 1 didn't find a match AND the word starts with a mudhari' prefix (ي/ت/أ/ن), the classifier strips the first letter and checks the **remaining letters** against patterns.

This handles mudhari' forms where the alif-wasl (used in madhi forms of 5C/5D/6) is replaced by the person prefix.

| Condition on `rest` | Rumus |
|---------------------|-------|
| rest[0:2] = `ست` → | **6** (يستفعل) |
| rest[1] = ت → | **5C** (يفتعل) |
| rest[0] = ن → | **5D** (ينفعل) |
| rest starts with ت + shadda → | **5A** (يتفعل) |
| rest starts with ت + ا at [2] → | **5B** (يتفاعل) |
| Shadda on C2 of rest → | **4A** (يفعّل) |
| Alif at rest[1] → | **4B** (يفاعل) |
| 4-letter rest + 4-letter root → | **4D** (يفعلل) |
| **3-letter rest** → | **R3A/B/C** (see below) |

**Critical: 3-letter rest in PASS 2** — When the mudhari' prefix is stripped and exactly 3 letters remain, this is structurally equivalent to `Rumus 3 + mudhari' prefix`. The vowel on C2 determines the Rumus:

```
يَضْرِبُ     → prefix ي stripped → rest = ضرب (3 letters)
               C2 vowel on ر = kasra → Rumus 3B ✓

يَنْصُرُ     → prefix ي stripped → rest = نصر (3 letters)
               C2 vowel on ص = damma → Rumus 3C ✓

يَفْتَحُ     → prefix ي stripped → rest = فتح (3 letters)
               C2 vowel on ت = fatha → Rumus 3A ✓
```

**⚠️ Ambiguity**: A 3-letter rest with mudhari' prefix could ALSO be a **4C mudhari'** form (e.g., يُسْلِمُ from root سلم). The classifier detects this when `rest == root` and lowers confidence from 0.90 to 0.70.

```
يُسْلِمُ     → prefix ي stripped → rest = سلم (3 letters)
               root = سلم → rest == root → could be R3C or 4C mudhari'
               → returns Rumus 3C with confidence 0.70
```

### Fallback

If neither pass finds a match, the classifier returns an empty rumus with 0.0 confidence. The calling code then falls back to Bab 1 (Rumus 3A).

---

## Step 4: Form Classification

After determining the Rumus, the classifier determines which of the 8 Tashrif Ishthilahi columns the word belongs to.

| Check | Condition | Form |
|-------|-----------|------|
| 1 | Prefix `لا` (negation) | **Form 4 — Fi'il Nahi** |
| 2 | Prefix `ال` (definite article) | **Form 5/6/7/8 — Noun** |
| 3 | Mudhari' prefix (ي/ت/أ/ن) + Rumus 3 | **Form 2 — Fi'il Mudhari'** |
| 4 | Ends with ت or نا (past suffixes) | **Form 1 — Fi'il Madhi** |
| 5 | Starts with ا (bare alif, not augmented) | **Form 3 — Fi'il Amr** |
| 6 | Starts with م (meem prefix) | **Form 6/7/8 — Derived noun** |
| 7 | Ends with ة (taa marbuta) | **Form 5 — Mashdar / noun** |
| 8 | Exactly 3 letters | **Form 1 — Fi'il Madhi** |
| 9 | 4+ letters | **Form 1 or 5 — Verb or noun** |

Key details:

- **Check 3 (Mudhari')**: Only applies to Rumus 3 (basic verbs). Augmented verbs (4-6) may start with the same letters but be past tense (e.g., تَعَلَّمَ starts with ت but is 5A madhi, not mudhari').
- **Check 5 (Amr)**: A bare alif at the start is assumed to be the imperative prefix (اِفْعَلْ), unless the word is Rumus 5C/5D/5E/6 where alif is part of the augmented stem.
- **Check 6 (Mu- prefix)**: For augmented verbs (Rumus 4-6), the vowel before the final consonant distinguishes Form 6 (ISM_FAIL, kasra) from Form 7/8 (ISM_MAFUL/ZAMAMI, fatha/damma).

---

## Complete Decision Flowchart

```
                    ┌─────────────────┐
                    │   Input Word    │
                    │  (with root)    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ 1. Strip affixes │
                    │ 2. Analyze stem │
                    └────────┬────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │ PASS 1: Match stem       │
              │ against known patterns   │
              └──────┬───────────┬───────┘
                     │           │
               Found?│     Not Found?
                     │           │
                     ▼           ▼
              ┌──────────┐  ┌─────────────────┐
              │ Return   │  │ PASS 2: Check   │
              │ Rumus    │  │ mudhari' prefix │
              └──────────┘  └──────┬──────────┘
                                  │
                          ┌───────┴───────┐
                          │               │
                      Found?          Not Found?
                          │               │
                          ▼               ▼
                   ┌──────────┐    ┌──────────────┐
                   │ Return   │    │ Fallback:    │
                   │ Rumus    │    │ Rumus 3A     │
                   └──────────┘    └──────────────┘
                          │
                          ▼
                   ┌──────────────────────────┐
                   │ 4. Classify Form (1-8)   │
                   └──────────────────────────┘
```

---

## Summary: Key Detectors at a Glance

| Rumus | Key Detector | Example |
|-------|-------------|---------|
| **3A** | 3-letter stem + C2 vowel = fatha (َ) | فَتَحَ, يَفْتَحُ |
| **3B** | 3-letter stem + C2 vowel = kasra (ِ) | ضَرَبَ, يَضْرِبُ |
| **3C** | 3-letter stem + C2 vowel = damma (ُ) | نَصَرَ, يَنْصُرُ |
| **4A** | Shadda (ّ) on C2 | عَلَّمَ, يُعَلِّمُ |
| **4B** | Alif after C1 (letters[1] = ا) | شَاوَرَ, فَاعِلٌ |
| **4C** | Starts with أ, 2–5 letters, no shadda | أَسْلَمَ, يُسْلِمُ |
| **4D** | 4-letter root | زَلْزَلَ, يُزَلْزِلُ |
| **5A** | Starts with ت + shadda | تَعَلَّمَ, يَتَعَلَّمُ |
| **5B** | Starts with ت + ا at position 2 | تَعَارَفَ, يَتَعَارَفُ |
| **5C** | Starts with ا, letters[2] = ت | اِحْتَرَمَ, يَحْتَرِمُ |
| **5D** | Starts with ا, letters[1] = ن | اِنْكَسَرَ, يَنْكَسِرُ |
| **5E** | Starts with ا + shadda on last letter | اِحْمَرَّ |
| **6** | Starts with ا, letters[1:3] = س + ت | اِسْتَغْفَرَ, يَسْتَغْفِرُ |

---

## Known Limitations

| Issue | Description | Workaround |
|-------|-------------|------------|
| **Madhi-only R3B/C → R3A** | Past tense forms of R3B (ضَرَبَ) and R3C (نَصَرَ) have the same pattern `فَعَلَ` as R3A. No C2 vowel visible. | Pass the mudhari' form (e.g., يَضْرِبُ) alongside the root |
| **R4B ↔ Ism Fa'il of R3** | فاعل pattern is identical for both Rumus 4B and Ism Fa'il of Rumus 3 | Context-dependent; check if root has augmented meaning |
| **4C mudhari' → R3** | يُسْلِمُ (4C mudhari') looks identical to R3 mudhari' (prefix ي + 3-letter root) | Detect when rest == root and lower confidence |
| **Weak/defective/hamzated roots** | Words with و, ي, or ء as root letters have irregular patterns | Not yet handled; only sound (سالم) roots supported in Phase 1 |
| **Mashdar irregularity** | Many gerunds don't follow the qiyasi (regular) pattern | Use dictionary lookup as primary, pattern as fallback |

---

## Verbose Debugging

To see exactly why a word was classified a certain way, check the `reasons` list in the ClassifierResult:

```python
from tashrif_classifier import classify_rumus
result = classify_rumus("يَضْرِبُونَ", root="ضرب")
print(result.rumus)       # "3B"
print(result.form)        # 2
print(result.reasons)
# [
#   "Stem letters: 'يضربون' | Shadda: False",
#   "Root: 'ضرب'",
#   "3-letter stem + C2 vowel kasra -> Rumus 3B",
#   "Mudhari' prefix -> Fi'il Mudhari' (Form 2)"
# ]
```
