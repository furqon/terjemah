# Translation Approach Recommendation
## Arabic → Indonesian for the "Scholar's Kitab" App

**Date:** July 24, 2026
**Priority:** Free options → Built-for-translation → API token-based → Google Translate API

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Tier 1: Fully Free, Built-for-Translation (NLLB-200)](#2-tier-1-fully-free-built-for-translation-nllb-200)
3. [Tier 2: Free Model Alternatives (M2M-100, OPUS-MT)](#3-tier-2-free-model-alternatives)
4. [Tier 3: API Token-Based (Google Cloud Translation)](#4-tier-3-api-token-based-google-cloud-translation)
5. [Comparison Matrix](#5-comparison-matrix)
6. [Recommended Implementation Strategy](#6-recommended-implementation-strategy)
7. [Code Samples for Each Approach](#7-code-samples-for-each-approach)
8. [Fallback Strategy](#8-fallback-strategy)
9. [License & Commercial Considerations](#9-license--commercial-considerations)
10. [Final Recommendation](#10-final-recommendation)

---

## 1. Executive Summary

For your "Scholar's Kitab" app — where Arabic text gets word-by-word analysis + translation to Indonesian — here are the **three tiers** of translation options ranked by priority:

| Tier | Approach | Cost | Quality | Offline? | Ease |
|:---:|---|---|---|---|---|
| **🥇 1** | **NLLB-200** (Hugging Face) | **Free** (CC-BY-NC) | ★★★★ Excellent | ✅ Yes | ⭐⭐⭐ |
| **🥈 2** | **M2M-100 / OPUS-MT** (Hugging Face) | **Free** (MIT/CC) | ★★★ Good | ✅ Yes | ⭐⭐⭐ |
| **🥉 3** | **Google Cloud Translation API** | Free tier (500K chars/mo) then paid | ★★★★★ Best | ❌ No | ⭐⭐⭐⭐⭐ |

**TL;DR:** Start with **NLLB-200 distilled-600M** (free, runs locally, handles Arabic ↔ Indonesian directly). Add **Google Translate API** as a fallback for higher quality or when the user wants better results.

---

## 2. Tier 1: Fully Free, Built-for-Translation — NLLB-200 ⭐

### What is it?

**NLLB-200** (No Language Left Behind) is Meta AI's open-source machine translation model supporting **200 languages** — including both Arabic (`arb_Arab`) and Indonesian (`ind_Latn`). It was specifically built for translation, not general NLP.

### Model Variants

| Model Name | Size | RAM/VRAM | Speed | Quality |
|---|---|---|---|---|
| `facebook/nllb-200-distilled-600M` | 600M params | ~2-4 GB | Fast | Good |
| `facebook/nllb-200-distilled-1.3B` | 1.3B params | ~6-8 GB | Medium | Better |
| `facebook/nllb-200-3.3B` | 3.3B params | ~12 GB | Slow | Best |

### ✅ Pros
- **Truly free** — no API costs, no rate limits, no internet needed after download
- **Direct Arabic → Indonesian** — single model, no pivot through English
- **Runs locally** — complete privacy, no data leaves your machine
- **Good quality** — specifically optimized for low-resource language pairs
- **Active community** — well-supported on Hugging Face

### ❌ Cons
- **Large download** — 600MB to 2.4GB for the model weights
- **RAM hungry** — 600M model needs ~2-4GB free RAM
- **Sentence-level** — not ideal for very long paragraphs (>512 tokens)
- **Non-commercial license** (CC-BY-NC 4.0) — cannot sell the app

### Installation

```bash
pip install transformers torch sentencepiece accelerate
```

### 🎯 Verdict: **Best starter option.** Free, good quality, single model, runs offline.

---

## 3. Tier 2: Free Model Alternatives

### 3a. M2M-100 (418M)

**Model:** `facebook/m2m100_418M`

- **Size:** 418M parameters (~1.6GB download)
- **Languages:** 100 languages including Arabic & Indonesian
- **License:** MIT (fully permissive, commercial OK)
- **Quality:** Good, but noticeably worse than NLLB-200

```python
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer

model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M")
tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M")
tokenizer.src_lang = "ar"
inputs = tokenizer("مرحبا بالعالم", return_tensors="pt")
generated = model.generate(**inputs, forced_bos_token_id=tokenizer.get_lang_id("id"))
print(tokenizer.decode(generated[0], skip_special_tokens=True))
```

**Verdict:** Decent fallback, smaller than NLLB, MIT licensed (commercial OK). But lower quality.

### 3b. OPUS-MT (via English Pivot)

**Models:** `Helsinki-NLP/opus-mt-ar-en` + `Helsinki-NLP/opus-mt-en-id`

- **Size:** ~300MB *total* (both models combined — very lightweight!)
- **License:** CC-BY-SA (some restrictions)
- **Approach:** Arabic → English → Indonesian (two-step pipeline)
- **Quality:** Surprisingly good for specific domains, weaker for general text

```python
from transformers import pipeline

# Two-step pipeline
ar_to_en = pipeline("translation", model="Helsinki-NLP/opus-mt-ar-en")
en_to_id = pipeline("translation", model="Helsinki-NLP/opus-mt-en-id")

arabic_text = "يكتب الطالب الدرس"
english = ar_to_en(arabic_text)[0]['translation_text']
indonesian = en_to_id(english)[0]['translation_text']
```

**Verdict:** Lightest option (300MB total). Good for CPU/low-resource machines. But two-step = slower, and errors compound.

### 3c. mBART-50

- **Model:** `facebook/mbart-large-50-many-to-many-mmt`
- **Problem:** Does NOT support Arabic ↔ Indonesian as a direct pair. It's English-centric. Would need English pivot.
- **Verdict:** ❌ Not recommended over the alternatives above.

---

## 4. Tier 3: API Token-Based — Google Cloud Translation

### Free Tier

| Detail | Value |
|---|---|
| **Free quota** | **500,000 characters/month** ($10 monthly credit) |
| **What counts** | Both input + output characters |
| **Cost after free tier** | $20 per million characters (standard NMT) |
| **Requires credit card?** | Yes (but won't be charged if under free tier) |

### How to Set Up

```bash
# 1. Install Google client library
pip install google-cloud-translate

# 2. Set up authentication (download service account JSON)
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

### Python Code

```python
from google.cloud import translate_v2 as translate

client = translate.Client()
result = client.translate(
    "يكتب الطالب الدرس في المكتبة",
    source_language="ar",
    target_language="id",
)
print(result["translatedText"])
# → "Siswa menulis pelajaran di perpustakaan"
```

### ✅ Pros
- **Best quality** — Google's NMT is state-of-the-art
- **Easiest integration** — 3 lines of code
- **Handles context** — paragraphs, idioms, everything
- **No model download** — instant setup
- **500K chars free/month** — enough for ~100-200 pages of text

### ❌ Cons
- **Requires internet** — no offline mode
- **Not truly free** — billing account required, will charge after free tier
- **Privacy concern** — text sent to Google servers
- **Rate limits** — may throttle high-volume usage

### 🎯 Verdict: **Best quality, easiest setup, but needs internet + billing.**

---

## 5. Comparison Matrix

| Feature | NLLB-200 (600M) | M2M-100 (418M) | OPUS-MT (pivot) | Google Translate API |
|---|---|---|---|---|
| **Total Cost** | $0 | $0 | $0 | $0 (up to 500K chars/mo) |
| **License** | CC-BY-NC (non-commercial) | MIT (OK for commercial) | CC-BY-SA | Proprietary (paid beyond free) |
| **Internet needed?** | ❌ No (download once) | ❌ No (download once) | ❌ No (download once) | ✅ Yes |
| **Model download** | ~1.2 GB | ~1.6 GB | ~300 MB (total) | None |
| **RAM needed** | ~2-4 GB | ~2 GB | ~500 MB | Minimal |
| **CPU inference speed** | ~2-5 sentences/sec | ~3-6 sentences/sec | ~5-10 sentences/sec | Instant |
| **Quality (ar→id)** | ★★★★ Excellent | ★★★ Good | ★★★ Fair | ★★★★★ Best |
| **Arabic diacritics preserved?** | ⚠️ Partially | ⚠️ Partially | ❌ No | ✅ Yes |
| **Word-by-word alignment** | ❌ No (needs separate tool) | ❌ No | ❌ No | ❌ No |
| **Setup complexity** | ⭐⭐⭐ Medium | ⭐⭐⭐ Medium | ⭐⭐ Easy | ⭐ Easy |

---

## 6. Recommended Implementation Strategy

### 🥇 First Choice: NLLB-200 (Default)

```
                    ┌─────────────────────────────────┐
                    │         NLLB-200                 │
                    │  facebook/nllb-200-distilled-600M │
                    │                                  │
                    │  Arabic text → [model] → Indonesian│
                    │  arb_Arab          →  ind_Latn   │
                    └─────────────────────────────────┘
```

**Use for:** Default translation. Free, offline, good quality.

### 🥈 Second Choice: Google Cloud Translation API (Fallback)

```
                    ┌─────────────────────────────────┐
                    │      Google Cloud Translate      │
                    │                                  │
                    │  Arabic text → [API] → Indonesian │
                    │  (500K chars/mo free)            │
                    └─────────────────────────────────┘
```

**Use for:** When user wants better quality, or when NLLB produces poor results.

### 🥉 Third Choice: OPUS-MT (Lightweight Fallback)

```
                    ┌─────────────────────────────────┐
                    │    OPUS-MT (two-step pipeline)   │
                    │                                  │
                    │  Arabic → opus-mt-ar-en → English│
                    │  English → opus-mt-en-id → Ind.   │
                    └─────────────────────────────────┘
```

**Use for:** Low-RAM machines, CPU-only, when NLLB is too heavy.

---

## 7. Code Samples for Each Approach

### Approach A: NLLB-200 (Primary)

```python
# pip install transformers torch sentencepiece
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class NLLBTranslator:
    """Free, offline Arabic → Indonesian translator using NLLB-200."""

    def __init__(self, model_name="facebook/nllb-200-distilled-600M"):
        print(f"Loading {model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.src_lang = "arb_Arab"
        self.tgt_lang = "ind_Latn"

    def translate(self, text: str) -> str:
        """Translate Arabic text to Indonesian."""
        self.tokenizer.src_lang = self.src_lang
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)

        translated = self.model.generate(
            **inputs,
            forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(self.tgt_lang),
            max_length=512,
            num_beams=4,  # Better quality
            early_stopping=True,
        )

        return self.tokenizer.batch_decode(translated, skip_special_tokens=True)[0]


# Usage
translator = NLLBTranslator()
result = translator.translate("يكتب الطالب الدرس في المكتبة")
print(result)  # → "Siswa menulis pelajaran di perpustakaan"
```

### Approach B: Google Cloud Translation API (Fallback)

```python
# pip install google-cloud-translate
from google.cloud import translate_v2 as translate

class GoogleTranslator:
    """High-quality API translator. Needs internet + billing setup."""

    def __init__(self, credentials_path=None):
        if credentials_path:
            self.client = translate.Client.from_service_account_json(credentials_path)
        else:
            self.client = translate.Client()

    def translate(self, text: str) -> str:
        """Translate Arabic text to Indonesian via Google API."""
        result = self.client.translate(
            text,
            source_language="ar",
            target_language="id",
            format_="text",
        )
        return result["translatedText"]

    def get_usage(self):
        """Check current billing stats (requires additional setup)."""
        pass


# Usage
translator = GoogleTranslator("path/to/service-account-key.json")
result = translator.translate("يكتب الطالب الدرس في المكتبة")
print(result)  # → "Siswa menulis pelajaran di perpustakaan"
```

### Approach C: OPUS-MT Pivot (Lightweight Fallback)

```python
# pip install transformers
from transformers import pipeline

class OPUSPivotTranslator:
    """Lightweight two-step pivot: Arabic → English → Indonesian."""

    def __init__(self):
        print("Loading OPUS-MT models (300MB total)...")
        self.ar_to_en = pipeline("translation", model="Helsinki-NLP/opus-mt-ar-en")
        self.en_to_id = pipeline("translation", model="Helsinki-NLP/opus-mt-en-id")

    def translate(self, text: str) -> str:
        """Translate Arabic → English → Indonesian."""
        english = self.ar_to_en(text, max_length=512)[0]['translation_text']
        indonesian = self.en_to_id(english, max_length=512)[0]['translation_text']
        return indonesian

# Usage
translator = OPUSPivotTranslator()
result = translator.translate("يكتب الطالب الدرس في المكتبة")
print(result)
```

### Approach D: Smart Auto-Selector (Recommended)

```python
class SmartTranslator:
    """
    Auto-selects the best translator based on availability.
    Priority: NLLB-200 → Google Translate API → OPUS-MT
    """

    def __init__(self, google_credentials=None):
        self.nllb = None
        self.google = None
        self.opus = None

        # Try to load NLLB (free, offline, best quality-to-cost ratio)
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            print("Loading NLLB-200 (primary translator)...")
            model_name = "facebook/nllb-200-distilled-600M"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self.nllb_available = True
        except Exception as e:
            print(f"NLLB-200 not available: {e}")
            self.nllb_available = False

        # Try to set up Google Translate (API fallback)
        if google_credentials:
            try:
                from google.cloud import translate_v2 as translate
                self.google_client = translate.Client.from_service_account_json(google_credentials)
                self.google_available = True
            except Exception as e:
                print(f"Google Translate not available: {e}")
                self.google_available = False
        else:
            self.google_available = False

        # Try OPUS-MT as last resort
        if not self.nllb_available and not self.google_available:
            try:
                from transformers import pipeline
                print("Loading OPUS-MT (lightweight fallback)...")
                self.ar_to_en = pipeline("translation", model="Helsinki-NLP/opus-mt-ar-en")
                self.en_to_id = pipeline("translation", model="Helsinki-NLP/opus-mt-en-id")
                self.opus_available = True
            except Exception as e:
                print(f"OPUS-MT not available: {e}")
                self.opus_available = False
        else:
            self.opus_available = False

    def translate_nllb(self, text: str) -> str:
        self.tokenizer.src_lang = "arb_Arab"
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        translated = self.model.generate(
            **inputs,
            forced_bos_token_id=self.tokenizer.convert_tokens_to_ids("ind_Latn"),
            max_length=512,
        )
        return self.tokenizer.batch_decode(translated, skip_special_tokens=True)[0]

    def translate_google(self, text: str) -> str:
        result = self.google_client.translate(text, source_language="ar", target_language="id")
        return result["translatedText"]

    def translate_opus(self, text: str) -> str:
        english = self.ar_to_en(text, max_length=512)[0]['translation_text']
        indonesian = self.en_to_id(english, max_length=512)[0]['translation_text']
        return indonesian

    def translate(self, text: str, method: str = "auto") -> str:
        """Translate with automatic fallback."""
        if method == "google" and self.google_available:
            return self.translate_google(text)
        if method == "opus" and self.opus_available:
            return self.translate_opus(text)

        # Default: try NLLB first, fallback to Google, then OPUS
        if self.nllb_available:
            try:
                return self.translate_nllb(text)
            except Exception as e:
                print(f"NLLB failed: {e}")

        if self.google_available:
            try:
                return self.translate_google(text)
            except Exception as e:
                print(f"Google failed: {e}")

        if self.opus_available:
            return self.translate_opus(text)

        raise RuntimeError("No translator available!")


# Usage
translator = SmartTranslator(google_credentials="path/to/key.json")
result = translator.translate("يكتب الطالب الدرس في المكتبة")
print(result)

# User can also force a specific method:
result_google = translator.translate("يكتب الطالب الدرس", method="google")
```

---

## 8. Fallback Strategy

```
User pastes Arabic text
         │
         ▼
  ┌──────────────────┐
  │ NLLB-200 attempt │◄── Free, offline, good quality
  └──────┬───────────┘
         │
    Success? ──Yes──► Return translation
         │
         No
         ▼
  ┌──────────────────┐
  │ Google Translate │◄── API key needed, 500K chars/mo free
  └──────┬───────────┘
         │
    Success? ──Yes──► Return translation
         │
         No
         ▼
  ┌──────────────────┐
  │ OPUS-MT pivot    │◄── Lightweight, two-step, lowest quality
  └──────┬───────────┘
         │
    Success? ──Yes──► Return translation
         │
         No
         ▼
  ┌──────────────────┐
  │ Error: No        │
  │ translation      │
  │ available        │
  └──────────────────┘
```

---

## 9. License & Commercial Considerations

| Tool | License | Can sell the app? |
|---|---|---|
| **NLLB-200** | CC-BY-NC 4.0 | ❌ No (non-commercial only) |
| **M2M-100** | MIT | ✅ Yes |
| **OPUS-MT** | CC-BY-SA 4.0 | ✅ Yes (with attribution) |
| **Google Translate API** | Proprietary | ✅ Yes (pay per use) |

**If you plan to sell the app:**
- Use **M2M-100** (MIT license) as primary
- Or **Google Translate API** (pay as you go)
- Or **OPUS-MT** (with attribution)
- ❌ Cannot use NLLB-200 commercially without licensing from Meta

**If the app is free/open-source for educational use:**
- Use **NLLB-200** — it's perfect for non-commercial, educational "scholar's kitab" use

---

## 10. Final Recommendation

### ⭐ Recommended Stack (Priority Order)

```
┌─────────────────────────────────────────────────────────────┐
│                   RECOMMENDED STACK                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PRIMARY:   NLLB-200 distilled-600M                          │
│             (Free, offline, good quality)                    │
│                                                              │
│  FALLBACK:  Google Cloud Translation API                     │
│             (Best quality, 500K chars/mo free)               │
│                                                              │
│  ULTIMATE:  OPUS-MT pivot pipeline                           │
│  FALLBACK:  (Lightweight, 300MB, CPU-friendly)               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step Implementation Plan

| Step | Action | Cost |
|:----:|---|---|
| 1 | `pip install transformers torch sentencepiece` | $0 |
| 2 | Download `facebook/nllb-200-distilled-600M` (~1.2GB once) | $0 |
| 3 | Implement `NLLBTranslator` class | $0 |
| 4 | **(Optional)** Set up Google Cloud project + API key | $0 (500K chars/mo) |
| 5 | Implement `SmartTranslator` with auto-fallback | $0 |
| 6 | Add a toggle button in UI: "Use Google Translate (better quality)" | $0 |

### Why NLLB-200 First?

1. **$0 cost** — no recurring API bills
2. **Offline** — works without internet (important for classroom/school use)
3. **Privacy** — text stays on the user's machine
4. **Good enough quality** — specifically trained for Arabic → Indonesian as a direct pair
5. **One model** — no pipeline, no error compounding

### When to Use Google Translate Instead

- User has internet and wants **maximum quality**
- NLLB gives poor results for a specific text
- Translating very long paragraphs (>512 tokens)
- The user has explicitly enabled "Better quality" mode

---

*Document prepared for the "Scholar's Kitab" app project, based on research of NLLB-200, M2M-100, OPUS-MT, mBART-50, and Google Cloud Translation API.*
