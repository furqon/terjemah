# Assessment: Building an Arabic → Indonesian Word-by-Word Translation App
## (The "Scholar's Kitab Translator")

**Date:** July 24, 2026
**Repo Assessed:** [Qalsadi](https://github.com/linuxscout/qalsadi) by Taha Zerrouki (linuxscout)
**Context:** You want to build an app where a user pastes an Arabic paragraph and gets:
1. ✅ Tashkeel (harakat/diacritics) added
2. ✅ Sentence split into individual words
3. ✅ Each word analyzed (fi'il, isim, dhomir, harf, grammatical status)
4. ✅ Each word translated to Indonesian
5. ✅ Combined into a full sentence translation
6. ✅ Displayed like a scholar reading/translating a kitab for students

---

## Part 1: What Qalsadi Does (and Doesn't Do)

### ✅ What Qalsadi IS Good For

Qalsadi is a **morphological analyzer and lemmatizer** for Arabic. It can:

| Feature | How it works | Example Output |
|---|---|---|
| **Lemma extraction** | Reduces words to dictionary form | `يَكْتُبُونَ` → `كَتَبَ` |
| **POS tagging** | Classifies words by type | returns `type`: Noun, Verb, Stopword (حرف) |
| **Root extraction** | Finds triliteral/quadriliteral root | `مَكْتَبَةٌ` → root: `كتب` |
| **Vocalized output** | Returns diacritized lemmas | `كتب` → `كَتَبَ` |
| **Morphological analysis** | Breaks down affixes | Via `Analex.check_text()` + `ResultFormatter` |

### ❌ What Qalsadi Does NOT Do

- ❌ **No tashkeel generation** — it can analyze vocalized text, but it doesn't *add* harakat to bare text
- ❌ **No translation** — zero translation capability (Arabic → anything)
- ❌ **No i'rab (syntactic analysis)** — doesn't tell you word position in sentence (rafa', nasab, jar)
- ❌ **No dhomir (pronoun) classification** beyond basic POS tagging
- ❌ **No Indonesian language support** at all
- ❌ **No word-by-word gloss creation**

### 🧩 Dependencies

Qalsadi relies on other libraries by the same author:
- **PyArabic** (`pyarabic`) — Arabic text utilities
- **Tashaphyne** (`tashaphyne`) — Arabic light stemmer
- **LibQutrub** (`libqutrub`) — verb conjugation

---

## Part 2: The Full Toolchain Needed for Your Vision

For your "scholar translating a kitab" app, Qalsadi alone covers **only one piece** (POS/lemma analysis). Here's the complete stack:

### Layer 1: Tashkeel (Diacritization)

| Tool | Type | Python Integration | Accuracy | Notes |
|---|---|---|---|---|
| **Mishkal** | Rule-based | ✅ Native Python (`pip install mishkal`) | Good for MSA | Same author as Qalsadi — smooth integration |
| **CAMeL Tools** (`camel_diac`) | Rule+ML | ✅ `pip install camel-tools` | Very good | Requires data download (`camel_data`) |
| **Shakkala** | Deep Learning | ⚠️ Moderate | Excellent | Heavier setup, needs model weights |
| **Farasa** | ML | ⚠️ Via API/Java | Excellent | Harder Python integration |

**Recommendation:** Use **Mishkal** (same author as Qalsadi, consistent stack) or **CAMeL Tools** (more modern, better accuracy).

### Layer 2: Word Tokenization

| Tool | Approach |
|---|---|
| **PyArabic** (`pyarabic.araby.tokenize`) | Simple whitespace/punctuation split |
| **Qalsadi** (built-in) | Tokenizes as part of `check_text()` |
| **CAMeL Tools** | `simple_word_tokenize()` |

**Recommendation:** Qalsadi's `check_text()` already tokenizes as part of analysis — no extra tool needed.

### Layer 3: Morphological Analysis (Fi'il / Isim / Dhomir / Harf)

| Tool | POS Categories | Detail Level |
|---|---|---|
| **Qalsadi** | Noun, Verb, Stopword (حرف) | Basic — only 3 categories |
| **CAMeL Tools** | ~20+ categories (noun, verb, particle, pronoun, etc.) | Detailed — includes gender, number, person, aspect |
| **Quranic Arabic Corpus** | Full i'rab (grammatical analysis) | Most detailed — but only for Quran |

**Limitation:** Qalsadi only gives 3 broad types (noun/verb/stopword). It won't distinguish:
- Isim → isim fa'il, isim maf'ul, masdar, etc.
- Fi'il → fi'il madhi, fi'il mudhari', fi'il amr
- Dhomir → attached, detached, rafa', nasab, jar

**Recommendation:** For true "scholar-level" grammatical analysis, you need **CAMeL Tools**, not just Qalsadi. CAMeL Tools provides much richer morphological features.

### Layer 4: Word-by-Word Translation (Arabic → Indonesian)

This is the **hardest piece**. No off-the-shelf Python library provides Arabic-Indonesian word translation.

| Approach | Pros | Cons | Feasibility |
|---|---|---|---|
| **Google Translate API** (per word) | High quality, covers everything | Paid, needs internet, per-word limits | ⭐⭐⭐ High |
| **Custom bilingual dictionary** | Free, offline, fast | Needs to be built from scratch | ⭐⭐ Medium |
| **NLLB-200 (Hugging Face)** | Free, 200 languages incl. Arabic & Indonesian | Heavy model (600MB-2.4GB) | ⭐⭐⭐ High |
| **mBART-50** | Free, built for translation | Large model | ⭐⭐ Medium |
| **Helsinki-NLP OPUS-MT** (`ar-id`) | Lightweight, specialized | May not have Arabic-Indonesian pair | ⭐ Low |
| **Manual dictionary (KBBI + Arabic roots)** | Most "scholarly" | Enormous effort | ⭐ Low |

**Recommendation:** 
- For **word gloss**: Extract the lemma via Qalsadi/CAMeL Tools, then look up in a custom Arabic-Indonesian dictionary (or call an API per word).
- For **full sentence**: Use **NLLB-200** or **Google Translate** for the complete translation.
- For **pedagogical display**: Show the word-by-word gloss *alongside* the full sentence translation — like the Quranic Arabic Corpus does.

### Layer 5: Sentence Translation (Full)

| Tool | Notes |
|---|---|
| **Google Cloud Translation** | Best quality for Arabic-Indonesian |
| **NLLB-200** | Good quality, free, runs locally |
| **GPT-4 / Claude** | Excellent for contextual translation |

---

## Part 3: Recommended Architecture

```
                    ┌──────────────────────┐
                    │  User pastes Arabic   │
                    │  paragraph/sentence   │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │  Layer 1: Tashkeel    │
                    │  (Mishkal or          │
                    │   camel_diac)         │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │  Layer 2: Tokenize    │
                    │  (Qalsadi/PyArabic)   │
                    └──────────┬───────────┘
                               ▼
               ┌───────────────┴───────────────┐
               ▼                                ▼
    ┌──────────────────────┐       ┌──────────────────────┐
    │  Layer 3a: Analyze   │       │  Layer 3b: Translate  │
    │  Each Word           │       │  Each Word (lemma →  │
    │  (Qalsadi or         │       │  Indonesian via       │
    │   CAMeL Tools)       │       │  dictionary/API)      │
    │  → POS, root, lemma  │       │  → terjemahan per     │
    │  → fi'il/isim/harf   │       │    kata               │
    └──────────┬───────────┘       └──────────┬───────────┘
               ▼                                ▼
               └───────────────┬───────────────┘
                               ▼
                    ┌──────────────────────┐
                    │  Layer 4: Display     │
                    │  Word-by-word gloss   │
                    │  + full translation   │
                    │  (like kitab tafsir)  │
                    └──────────────────────┘
```

### Display Concept (Like a Scholar's Kitab)

```
═══════════════════════════════════════════════════════
  يَكْتُبُ   الطَّالِبُ   الدَّرْسَ     فِي     الْمَكْتَبَةِ
 ───────   ─────────   ───────   ─────   ────────────
  menulis   siswa       pelajaran  di      perpustakaan
  fi'il     isim        isim      harf    isim
  mudhari'  marfu'      manshub   jar     majrur

  Terjemahan: "Siswa menulis pelajaran di perpustakaan"
═══════════════════════════════════════════════════════
```

---

## Part 4: Where Qalsadi Fits Best

| Step in Your Pipeline | Qalsadi's Role | Better Alternative? |
|---|---|---|
| Tashkeel (harakat) | ❌ Not supported | Mishkal or CAMeL Tools |
| Word tokenization | ✅ Yes (built-in) | — |
| POS tagging (fi'il/isim/harf) | ⚠️ Basic (3 categories) | **CAMeL Tools** (20+ categories) |
| Root extraction | ✅ Yes | CAMeL Tools also does this |
| Lemma extraction | ✅ Yes (vocalized too) | — |
| Word translation | ❌ Not supported | NLLB-200 / Google Translate |
| I'rab (syntactic position) | ❌ Not supported | Quranic Arabic Corpus (Quran only) |
| Dhomir identification | ❌ Not supported | CAMeL Tools (person, number, gender) |

### Verdict on Qalsadi

**Qalsadi is a solid choice for basic lemmatization and POS tagging**, but it's too limited for your full vision. The main issues:

1. **Only 3 POS categories** — can't distinguish fi'il madhi vs mudhari', isim fa'il vs maf'ul, dhomir types, etc.
2. **No tashkeel generation** — you'd need Mishkal (same author) as a separate dependency
3. **No i'rab** — no syntactic position analysis (important for "scholar-level" display)
4. **No translation** — obviously, since it's Arabic-only

---

## Part 5: Recommended Approach (Two Paths)

### Path A: Best "Scholar-Level" Quality 🎓

Use **CAMeL Tools** as the primary analyzer instead of Qalsadi:

```
1. Tashkeel     → CAMeL Tools (camel_diac)
2. Tokenize     → CAMeL Tools (simple_word_tokenize)
3. Analyze      → CAMeL Tools (morphological analyzer)
   → Gives: root, lemma, POS (detailed), gender, number, person, aspect, state
4. Word gloss   → Custom dictionary lookup on lemma + Google Translate API
5. Translation  → NLLB-200 (Hugging Face) for full sentence
6. Display      → Word table with gloss + grammar tags + full translation
```

**Pros:** Richer grammatical detail (closer to true i'rab), better accuracy, one unified toolkit  
**Cons:** Heavier dependency, needs data download (~500MB)

### Path B: Lightweight & Integrated (Qalsadi + Mishkal) 💨

Use **Qalsadi + Mishkal** (both by same author, consistent stack):

```
1. Tashkeel     → Mishkal
2. Tokenize     → Qalsadi (built-in check_text())
3. Analyze      → Qalsadi (lemmatize_text(return_pos=True))
   → Gives: root, lemma, POS (noun/verb/stopword)
4. Word gloss   → Dictionary lookup + Google Translate API
5. Translation  → Google Translate API or NLLB-200
6. Display      → Word table with gloss + basic POS + full translation
```

**Pros:** Lighter, simpler, fewer dependencies, same author ecosystem  
**Cons:** Less grammatical detail, only 3 POS categories, no i'rab

### Path C: Hybrid (Recommended) ⭐

```
Layer 1: Tashkeel      → Mishkal (lightweight, no data download)
Layer 2: Tokenize      → Qalsadi (lightweight, fast)
Layer 3: Analyze       → CAMeL Tools (for richer POS/grammar detail)
Layer 4: Word gloss    → Custom dictionary (lemma → Indonesian)
Layer 5: Translation   → NLLB-200 (Hugging Face)
Layer 6: Display       → Streamlit / Gradio web UI
```

---

## Part 6: What Qalsadi's Author Ecosystem Offers

Taha Zerrouki (linuxscout) has built a **family of complementary tools**:

| Library | GitHub | Purpose | Useful for You? |
|---|---|---|---|
| **PyArabic** | [linuxscout/pyarabic](https://github.com/linuxscout/pyarabic) | Arabic text utilities | ✅ Tokenization, normalization |
| **Qalsadi** | [linuxscout/qalsadi](https://github.com/linuxscout/qalsadi) | Morphological analysis, lemmatization | ✅ POS tagging, lemma extraction |
| **Mishkal** | [linuxscout/mishkal](https://github.com/linuxscout/mishkal) | Tashkeel (diacritization) | ✅ Add harakat |
| **Tashaphyne** | [linuxscout/tashaphyne](https://github.com/linuxscout/tashaphyne) | Light stemming | ⚠️ Partial |
| **LibQutrub** | [linuxscout/libqutrub](https://github.com/linuxscout/libqutrub) | Verb conjugation | ⚠️ Partial |
| **Adiyan** | [linuxscout/adiyan](https://github.com/linuxscout/adiyan) | Arabic text correction | ⚠️ Optional |
| **Nafitha** | [linuxscout/nafitha](https://github.com/linuxscout/nafitha) | OCR correction | ❌ Not needed |

All are MIT-licensed and well-maintained.

---

## Part 7: Gaps That Need Custom Work

These pieces don't exist as off-the-shelf Python libraries and would need to be built:

### 1. Arabic-Indonesian Bilingual Dictionary
- No comprehensive open-source digital dictionary exists
- Options:
  - Scrape existing online dictionaries
  - Use Google Translate API as a "dictionary" (query lemma → get Indonesian)
  - Build from parallel corpus
  - Use existing Quranic translations (terjemahan Kemenag) as a seed corpus

### 2. I'rab (Syntactic Position) Analysis
- No Python library provides full i'rab for general Arabic text
- For Quran: [Quranic Arabic Corpus](https://corpus.quran.com/) has it pre-annotated
- For general text: would need a dependency parser (CAMeL Tools has limited support)

### 3. Word-by-Word Display UI
- Need to build a table/grid showing:
  - Arabic word (with harakat)
  - Indonesian gloss
  - POS/grammar tag
  - Syntactic position
- Similar to: [Quranic Arabic Corpus word view](https://corpus.quran.com/wordbyword.jsp)

---

## Part 8: Sample Python Workflow (Qalsadi + Mishkal)

```python
# pip install qalsadi mishkal camel-tools

from pyarabic.araby import tokenize
from qalsadi.lemmatizer import Lemmatizer

# Step 1: Tashkeel (using Mishkal)
import mishkal.tashkeel as tashkeel
vocalizer = tashkeel.Tashkeel()
text = "يكتب الطالب الدرس في المكتبة"
text_with_harakat = vocalizer.tashkeel(text)
# → "يَكْتُبُ الطَّالِبُ الدَّرْسَ فِي الْمَكْتَبَةِ"

# Step 2: Tokenize
words = tokenize(text_with_harakat)

# Step 3: Analyze each word
lemmer = Lemmatizer()
for word in words:
    analysis = lemmer.lemmatize_text(word, return_pos=True)
    # Returns: [(word, lemma, pos)]

# Step 4: Word translation (custom dictionary or API)
# Step 5: Full sentence translation (NLLB-200 or Google Translate)
# Step 6: Display in word-by-word table
```

---

## Part 9: Final Verdict

| Question | Answer |
|---|---|
| Can Qalsadi alone do what you want? | **No** — it covers only 1 of 6 parts (word analysis) |
| Is Qalsadi a useful piece of the puzzle? | **Yes** — for lemmatization and basic POS tagging |
| What's the best overall toolkit? | **CAMeL Tools** — richer analysis, includes diacritization |
| Should you use Taha Zerrouki's ecosystem? | **Yes** — Mishkal + PyArabic + Qalsadi is a solid, consistent stack for the Arabic side |
| Does an Arabic-Indonesian word dictionary exist? | **No** — this needs to be built or use an API |
| Is this project feasible? | **Yes** — with a combination of 3-4 tools + custom glue code |

---

## Quick-Start Recommendations

1. **Start with Mishkal** for tashkeel (most lightweight, same ecosystem)
2. **Use CAMeL Tools** for morphological analysis (not Qalsadi — you need richer POS tags)
3. **Use NLLB-200** (Hugging Face) for full sentence translation
4. **Build or source** an Arabic-Indonesian lemma dictionary for word glosses
5. **Build a Streamlit UI** for the scholar-style word-by-word display

---

*Assessment prepared by assessing [Qalsadi](https://github.com/linuxscout/qalsadi), [Mishkal](https://github.com/linuxscout/mishkal), [CAMeL Tools](https://github.com/CAMeL-Lab/camel_tools), and the broader Arabic NLP Python ecosystem.*
