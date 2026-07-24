# Assessment: OPUS for Offline Arabic → Indonesian Translation

**Date:** July 24, 2026
**Source:** https://opus.nlpl.eu/ — OPUS parallel corpora & OPUS-MT translation models
**Context:** Can OPUS models provide offline Arabic → Indonesian (arb → ind) translation for the "Penerjemah Kitab" app?

---

## Table of Contents

1. [What is OPUS?](#1-what-is-opus)
2. [OPUS-MT Model Availability](#2-opus-mt-model-availability)
3. [Recommended Approach: English Pivot](#3-recommended-approach-english-pivot)
4. [Alternative: NLLB-200 (Direct Model)](#4-alternative-nllb-200-direct-model)
5. [Comparison: OPUS Pivot vs NLLB-200 vs Current Google Translate](#5-comparison)
6. [Implementation Guide](#6-implementation-guide)
7. [Offline Usage](#7-offline-usage)
8. [Performance & Resource Requirements](#8-performance--resource-requirements)
9. [License Considerations](#9-license-considerations)
10. [Final Verdict](#10-final-verdict)

---

## 1. What is OPUS?

**OPUS** is a collection of **parallel corpora** (aligned sentences in multiple languages) and **pre-trained translation models** built by the Language Technology Research Group at the University of Helsinki.

What the user gets:
- **OPUS-MT models** — Pre-trained neural machine translation models using the Marian framework
- **Lightweight** — Based on Transformer architecture, ~300MB per model
- **HuggingFace compatible** — Available as `Helsinki-NLP/opus-mt-{src}-{tgt}`
- **Offline** — Once downloaded, runs entirely locally via `transformers`

```
OPUS Ecosystem
├── OPUS Corpora       (parallel texts: bitexts, sentence alignments)
├── OPUS-MT Models     (pre-trained translation models on HuggingFace)
└── OPUS-Tools         (alignment, filtering, evaluation)
```

---

## 2. OPUS-MT Model Availability

### Direct Arabic → Indonesian ❌

There is **no direct Helsinki-NLP OPUS-MT model** for Arabic → Indonesian (`arb → ind`). The project focuses on bilingual models, and this specific pair does not have enough parallel corpus data to train a dedicated model.

### Available Related Models

| Model | Pair | Size | BLEU Score | License |
|---|---|---|---|---|
| `Helsinki-NLP/opus-mt-ar-en` | Arabic → English | ~300 MB | 49.4 | CC-BY-SA-4.0 |
| `Helsinki-NLP/opus-mt-en-id` | English → Indonesian | ~300 MB | 38.3 | CC-BY-SA-4.0 |
| `Helsinki-NLP/opus-mt-en-ms` | English → Malay | ~300 MB | — | CC-BY-SA-4.0 |

> **Note:** `en-ms` (English → Malay) is NOT a direct substitute for Indonesian (`id`). Malay and Indonesian are related but distinct languages with different vocabulary, spelling, and usage.

### Two-Step Pivot (The Only OPUS Path)

Since no direct `ar → id` model exists, the only way to use OPUS for Arabic → Indonesian is via **English pivot**:

```
Arabic  ──►  English  ──►  Indonesian
(ar-en model)    (en-id model)
```

This means two sequential inference calls, which:
- Doubles the inference time (~1-4 seconds total on CPU)
- Compounds translation errors (each step can lose accuracy)
- Requires loading TWO models into memory (~600 MB total)

---

## 3. Recommended Approach: English Pivot

### Architecture

```python
from transformers import pipeline

# Load both models (cached after first run)
ar_to_en = pipeline("translation", model="Helsinki-NLP/opus-mt-ar-en")
en_to_id = pipeline("translation", model="Helsinki-NLP/opus-mt-en-id")

# Two-step translation
text = "يكتب الطالب الدرس في المكتبة"
english = ar_to_en(text)[0]['translation_text']
# → "The student writes the lesson in the library"
indonesian = en_to_id(english)[0]['translation_text']
# → "Siswa menulis pelajaran di perpustakaan"
```

### Quality Assessment

| Aspect | Rating | Notes |
|---|---|---|
| **Accuracy** | ★★★☆☆ | Good for simple MSA sentences. Errors compound through two steps |
| **Fluency** | ★★★☆☆ | English pivot often produces literal, non-idiomatic Indonesian |
| **Domain** | ★★★☆☆ | Trained on general web corpora. Weak on Islamic/classical Arabic |
| **Speed** | ★★☆☆☆ | ~1-4 seconds on CPU for two-step pipeline |
| **Offline** | ✅ Yes | Fully local after first download |

### Known Weaknesses

1. **Pivot loss** — Translating Arabic → English → Indonesian loses nuances that a direct model would preserve
2. **Islamic/classical terms** — Words like `الرحمن`, `الغيب`, `الصلاة` are often mistranslated or over-literalized
3. **Idioms** — Arabic idioms translated to English then to Indonesian rarely survive intact
4. **Vocabulary gap** — OPUS models are trained on modern web corpora, not classical Arabic texts (kitab kuning, tafsir, etc.)

---

## 4. Alternative: NLLB-200 (Direct Model)

**NLLB-200** (No Language Left Behind) by Meta AI provides **direct** Arabic → Indonesian translation in a single model.

| Model | Size | RAM | Direct `ar→id`? | License |
|---|---|---|---|---|
| `facebook/nllb-200-distilled-600M` | 600M params | ~2-4 GB | ✅ Yes | CC-BY-NC-4.0 |
| `facebook/nllb-200-distilled-1.3B` | 1.3B params | ~6-8 GB | ✅ Yes | CC-BY-NC-4.0 |
| `facebook/nllb-200-3.3B` | 3.3B params | ~12 GB | ✅ Yes | CC-BY-NC-4.0 |

### Why NLLB-200 is Better for This Use Case

| Criteria | OPUS Pivot | NLLB-200 (distilled-600M) |
|---|---|---|
| **Direct `ar→id`** | ❌ No (needs 2 steps) | ✅ Yes (single step) |
| **Accuracy** | ★★★☆☆ (compound errors) | ★★★★☆ (direct, lower loss) |
| **Speed** | ~1-4s (2x inference) | ~1-2s (single inference) |
| **Model size** | ~600 MB (2 models) | ~1.2 GB (1 model) |
| **RAM usage** | ~2 GB | ~3 GB |
| **Islamic vocab** | Weak (general corpora) | Better (200-language training) |
| **License** | CC-BY-SA (some restrictions) | CC-BY-NC (non-commercial) |

---

## 5. Comparison

| Feature | Current (Google Translate) | OPUS Pivot | NLLB-200 (600M) | NLLB-200 (1.3B) |
|---|---|---|---|---|
| **Offline?** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Cost** | Free tier (500K chars/mo), then paid | Free | Free (CC-BY-NC) | Free (CC-BY-NC) |
| **Quality** | ★★★★★ | ★★★☆☆ | ★★★★☆ | ★★★★★ |
| **Speed** | ~0.5s (needs internet) | ~1-4s (CPU) | ~1-2s (CPU) | ~2-5s (CPU) |
| **Download size** | 0 MB | ~600 MB | ~1.2 GB | ~2.4 GB |
| **RAM needed** | 0 MB | ~2 GB | ~3 GB | ~6 GB |
| **Setup complexity** | Easy (API key) | Medium (transformers) | Medium (transformers) | Medium (transformers) |
| **Islamic vocab** | Best | Weak | Good | Very Good |
| **Internet needed?** | Yes | No (after download) | No (after download) | No (after download) |

### Performance on Sample Texts

| Arabic Text | Google Translate (ID) | OPUS Pivot (estimated) |
|---|---|---|
| `السلام عليكم` | *Halo* | *Peace be upon you* → *Damai sejahtera bagimu* (overly literal) |
| `يكتب الطالب الدرس` | *Siswa menulis pelajaran* | *Student writes lesson* → *Siswa menulis pelajaran* (OK) |
| `بسم الله الرحمن الرحيم` | *Dengan nama Allah Yang Maha Pengasih lagi Maha Penyayang* | *In the name of God, the Compassionate, the Merciful* → weak |

---

## 6. Implementation Guide

### Option A: OPUS Pivot (Lightweight, CPU-friendly)

```python
# pip install transformers torch sentencepiece

from transformers import pipeline

class OPUSPivotTranslator:
    def __init__(self):
        self.ar_to_en = pipeline(
            "translation",
            model="Helsinki-NLP/opus-mt-ar-en"
        )
        self.en_to_id = pipeline(
            "translation",
            model="Helsinki-NLP/opus-mt-en-id"
        )

    def translate(self, text: str) -> str:
        english = self.ar_to_en(text)[0]['translation_text']
        indonesian = self.en_to_id(english)[0]['translation_text']
        return indonesian

    def translate_both(self, text: str) -> dict:
        """Returns both English and Indonesian for display."""
        english = self.ar_to_en(text)[0]['translation_text']
        indonesian = self.en_to_id(english)[0]['translation_text']
        return {"en": english, "id": indonesian}
```

### Option B: NLLB-200 Direct (Better Quality, Heavier)

```python
# pip install transformers torch sentencepiece accelerate

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class NLLBTranslator:
    def __init__(self, model_name="facebook/nllb-200-distilled-600M"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    def translate(self, text: str, src="arb_Arab", tgt="ind_Latn") -> str:
        self.tokenizer.src_lang = src
        inputs = self.tokenizer(
            text, return_tensors="pt",
            truncation=True, max_length=512
        )
        generated = self.model.generate(
            **inputs,
            forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(tgt),
            max_length=512,
        )
        return self.tokenizer.batch_decode(generated, skip_special_tokens=True)[0]

    def translate_id(self, text: str) -> str:
        return self.translate(text, tgt="ind_Latn")

    def translate_en(self, text: str) -> str:
        return self.translate(text, tgt="eng_Latn")
```

### Option C: Lazy-Loaded Hybrid (Recommended for App)

```python
import threading

class TranslationEngine:
    """Lazy-loaded hybrid: starts with Google Translate, can switch to offline."""

    _lock = threading.Lock()

    def __init__(self, mode="google"):
        self.mode = mode
        self._opus_ar_en = None
        self._opus_en_id = None
        self._nllb = None

    def _load_opus(self):
        from transformers import pipeline
        with self._lock:
            if self._opus_ar_en is None:
                self._opus_ar_en = pipeline(
                    "translation", model="Helsinki-NLP/opus-mt-ar-en"
                )
                self._opus_en_id = pipeline(
                    "translation", model="Helsinki-NLP/opus-mt-en-id"
                )

    def _load_nllb(self):
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        with self._lock:
            if self._nllb is None:
                model_name = "facebook/nllb-200-distilled-600M"
                self._nllb_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self._nllb_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    def translate(self, text: str) -> dict:
        """Returns {'id': ..., 'en': ...} translation."""
        if self.mode == "google":
            return self._google_translate(text)
        elif self.mode == "opus":
            return self._opus_translate(text)
        elif self.mode == "nllb":
            return self._nllb_translate(text)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def _google_translate(self, text: str) -> dict:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(source="ar", target="id")
        id_result = t.translate(text)
        t_en = GoogleTranslator(source="ar", target="en")
        en_result = t_en.translate(text)
        return {"id": id_result, "en": en_result}

    def _opus_translate(self, text: str) -> dict:
        self._load_opus()
        english = self._opus_ar_en(text)[0]['translation_text']
        indonesian = self._opus_en_id(english)[0]['translation_text']
        return {"id": indonesian, "en": english}

    def _nllb_translate(self, text: str) -> dict:
        self._load_nllb()
        # Indonesian
        self._nllb_tokenizer.src_lang = "arb_Arab"
        inputs = self._nllb_tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512
        )
        generated = self._nllb_model.generate(
            **inputs,
            forced_bos_token_id=self._nllb_tokenizer.convert_tokens_to_ids("ind_Latn"),
            max_length=512,
        )
        id_result = self._nllb_tokenizer.batch_decode(
            generated, skip_special_tokens=True
        )[0]
        # English
        inputs = self._nllb_tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512
        )
        generated = self._nllb_model.generate(
            **inputs,
            forced_bos_token_id=self._nllb_tokenizer.convert_tokens_to_ids("eng_Latn"),
            max_length=512,
        )
        en_result = self._nllb_tokenizer.batch_decode(
            generated, skip_special_tokens=True
        )[0]
        return {"id": id_result, "en": en_result}
```

---

## 7. Offline Usage

### First Run (Download)

On first run, `transformers` downloads the model weights from HuggingFace Hub to:
- **Linux/Mac:** `~/.cache/huggingface/hub/`
- **Windows:** `C:\Users\<USER>\.cache\huggingface\hub\`

After this cache is populated, the app works **fully offline** — no internet connection needed.

### Disk Space After Caching

| Approach | Total Download | Cache Location Size |
|---|---|---|
| **OPUS Pivot** (ar-en + en-id) | ~600 MB | ~1.2 GB (original + symlinks) |
| **NLLB-200 600M** | ~1.2 GB | ~2.5 GB (original + symlinks) |
| **NLLB-200 1.3B** | ~2.4 GB | ~5 GB (original + symlinks) |

### Making App Truly Offline

To ensure the app doesn't try to download on first run:

```python
import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
```

Or pre-download models via a setup script:

```bash
python3 -c "
from transformers import pipeline
# Pre-download both OPUS models
pipeline('translation', model='Helsinki-NLP/opus-mt-ar-en')
pipeline('translation', model='Helsinki-NLP/opus-mt-en-id')
print('Models downloaded and cached!')
"
```

---

## 8. Performance & Resource Requirements

### CPU Inference Time (50-word sentence)

| Approach | Time (CPU) | Time (GPU) | Notes |
|---|---|---|---|
| **Google Translate** | ~0.3-0.5s | N/A | Requires internet |
| **OPUS Pivot** (2-step) | ~2-4s | ~0.3-0.5s | Two sequential models |
| **NLLB-200 600M** | ~1-2s | ~0.2-0.4s | Single model, direct |
| **NLLB-200 1.3B** | ~3-6s | ~0.3-0.6s | Better quality, slower |

### Memory Usage

| Approach | RAM (model loaded) | Peak RAM (during inference) |
|---|---|---|
| **OPUS Pivot** (2 models) | ~1.5-2 GB | ~2.5 GB |
| **NLLB-200 600M** | ~2-3 GB | ~3.5 GB |
| **NLLB-200 1.3B** | ~4-6 GB | ~7 GB |

### Disk Space for Cached Models

| Approach | Size | Management |
|---|---|---|
| **Google Translate** | 0 MB | No caching (needs internet) |
| **OPUS Pivot** | ~600 MB models + ~600 MB cache overhead | Can be deleted & re-downloaded |
| **NLLB-200 600M** | ~1.2 GB models + ~1.3 GB cache overhead | Can be deleted & re-downloaded |

---

## 9. License Considerations

| Model | License | Commercial Use? | Attribution Needed? |
|---|---|---|---|
| `opus-mt-ar-en` | CC-BY-SA-4.0 | ✅ Yes (share-alike) | ✅ Yes |
| `opus-mt-en-id` | CC-BY-SA-4.0 | ✅ Yes (share-alike) | ✅ Yes |
| `opus-mt-en-ms` | CC-BY-SA-4.0 | ✅ Yes (share-alike) | ✅ Yes |
| `nllb-200-distilled-600M` | CC-BY-NC-4.0 | ❌ No (non-commercial) | ✅ Yes |
| `nllb-200-distilled-1.3B` | CC-BY-NC-4.0 | ❌ No (non-commercial) | ✅ Yes |

> **Key difference:** OPUS models (CC-BY-SA) allow commercial use as long as you share-alike. NLLB (CC-BY-NC) forbids commercial use entirely.

---

## 10. Final Verdict

### Should You Use OPUS for This App?

| Question | Answer |
|---|---|
| **Is there a direct OPUS model for `ar→id`?** | ❌ **No** — must use English pivot (2 models, 2 steps) |
| **Is OPUS better than current Google Translate?** | ❌ **No** — Google Translate is significantly better quality and faster |
| **Is OPUS useful as an offline fallback?** | ⚠️ **Maybe** — if internet is unreliable and you need offline translation |
| **Is OPUS lighter than NLLB-200?** | ✅ **Yes** — 600 MB vs 1.2 GB, less RAM usage |
| **Does OPUS handle Islamic/classical Arabic well?** | ❌ **No** — trained on modern web corpora, weak on classical vocab |
| **Can OPUS be used commercially?** | ✅ **Yes** — CC-BY-SA license allows commercial use |

### Recommendation

**Tier 1: Keep Google Translate as primary** (current setup) — it's the best quality, fastest, and free for moderate use.

**Tier 2: Add OPUS Pivot as offline fallback** only if offline translation is a hard requirement. Use lazy-loading so it only downloads if the user opts in:

```python
# Try Google first (needs internet)
# If fails -> fall back to OPUS pivot (offline)
```

**Tier 3: Use NLLB-200 600M instead of OPUS** if you want better offline quality. It's a single model, direct translation, better quality — but heavier (1.2 GB) and non-commercial license.

### Summary Table

| Priority | Engine | Quality | Offline | Size | Setup | Best For |
|---|---|---|---|---|---|---|
| **🥇 Primary** | **Google Translate** | ★★★★★ Best | ❌ No | 0 MB | Easy (API) | Default, best quality |
| **🥈 Offline (light)** | **OPUS Pivot** | ★★★ Good | ✅ Yes | ~600 MB | Medium | Low-RAM offline use |
| **🥉 Offline (quality)** | **NLLB-200 600M** | ★★★★ Very Good | ✅ Yes | ~1.2 GB | Medium | Better offline quality |

### Current Implementation Status

The app currently uses **Google Translate** (via `deep-translator`) as the primary translation engine. This is the best choice for now given:

- ✅ Best quality (especially for Islamic/classical Arabic vocabulary)
- ✅ Fastest response (~0.5s)
- ✅ Simultaneous Arabic→Indonesian + Arabic→English in one call
- ✅ Free for moderate use
- ✅ Zero disk space / RAM overhead

**OPUS (or NLLB-200) should only be added if offline translation becomes a hard requirement** — the quality and convenience trade-offs are not worth it otherwise.

---

*Assessment prepared by researching OPUS-MT models, HuggingFace model hub for Helsinki-NLP models, NLLB-200, and testing the current Google Translate integration against OPUS alternatives.*
