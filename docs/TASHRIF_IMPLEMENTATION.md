# Assessment: Implementing Tashrif Ishthilahi System
## Based on "Al-Arabiyyah Al-Qaribah — At-Tashrif Al-Mujaz" by Andy Satiyo Ahmad

**Date:** July 28, 2026  
**Source:** `docs/tashrif.pdf` (53 pages) + `docs/wazan.md` (logic reference)  
**Context:** Integrate the Rumus-based Tashrif Ishthilahi system into the Penerjemah Kitab app, building on the existing Sarf morphology engine integration.

---

## Table of Contents

1. [PDF Overview & Key Concepts](#1-pdf-overview--key-concepts)
2. [Rumus System (Formula Patterns)](#2-rumus-system-formula-patterns)
3. [8 Forms of Tashrif Ishthilahi](#3-8-forms-of-tashrif-ishthilahi)
4. [Tashrif Lughowi (Full Pronoun Conjugation)](#4-tashrif-lughowi-full-pronoun-conjugation)
5. [Current Integration Point: Sarf CLI](#5-current-integration-point-sarf-cli)
6. [Implementation Strategy](#6-implementation-strategy)
7. [New API Design](#7-new-api-design)
8. [Frontend UI Mockup](#8-frontend-ui-mockup)
9. [Phased Implementation Plan](#9-phased-implementation-plan)
10. [Files to Create/Modify](#10-files-to-createmodify)
11. [Risks & Challenges](#11-risks--challenges)
12. [Final Verdict](#12-final-verdict)

---

## 1. PDF Overview & Key Concepts

The PDF `docs/tashrif.pdf` is in two parts:

### Part 1: "Al-Arabiyyah Al-Qaribah" (The Close Arabic)
- **12 lessons** of basic Arabic sentences with Indonesian translations
- Covers: mubtada'-khabar (nominal sentences), fi'il fa'il (verbal sentences), amr (imperatives), question words (أدوات الاستفهام), kana and her sisters
- Serves as contextual reading material

### Part 2: "At-Tashrif Al-Mujaz" (The Concise Tashrif)
- **Core contribution**: A simplified, systematic approach to Arabic morphology (صرف)
- Uses the **Rumus (Formula)** system with numbers 3-6 and letters A-E
- Covers both **Tashrif Ishthilahi** (Terminological conjugation — the 8-form pattern table) and **Tashrif Lughowi** (Linguistic conjugation — 14 pronoun tables)
- Indonesian explanations and translations throughout

### Key Terminology from the PDF

| Term | Arabic | Meaning |
|------|--------|---------|
| Fi'il Madhi | الفعل الماضي | Past tense verb |
| Fi'il Mudhari' | الفعل المضارع | Present/future tense verb |
| Fi'il Amr | فعل الأمر | Imperative |
| Fi'il Nahi | فعل النهي | Prohibitive (negative command) |
| Mashdar | المصدر | Gerund/verbal noun |
| Ism Fa'il | اسم الفاعل | Active participle |
| Ism Maf'ul | اسم المفعول | Passive participle |
| Zamami | الزمني | Time/place noun (ism zaman/makan) |
| Rumus | الروموس | Formula/pattern number |
| Wazan | الوزن | Pattern/meter |
| Fi'il Tsulatsi Mujarrad | فعل ثلاثي مجرد | Simple 3-letter verb |
| Fi'il Ruba'i Mujarrad | فعل رباعي مجرد | Simple 4-letter verb |
| Fi'il Mazid | فعل مزيد | Augmented verb (with extra letters) |

---

## 2. Rumus System (Formula Patterns)

The PDF defines a hierarchical pattern system. Below is the complete mapping extracted from the PDF:

### Rumus 3: Basic Triliteral (3 Huruf)

| Code | Madhi (Past) | Mudhari' (Present) | Amr (Imperative) | Nahi (Prohibitive) | Mashdar (Gerund) | Ism Fa'il (Act. Part.) | Ism Maf'ul (Pass. Part.) | Zamami (Time/Place) |
|------|-------------|-------------------|-----------------|-------------------|-----------------|----------------------|-----------------------|-------------------|
| **3A** | فَعَلَ | يَفْعَلُ | اِفْعَلْ | لا تَفْعَلْ | فَعْلاً | فَاعِلٌ | مَفْعُولٌ | مَفْعَلٌ |
| **3B** | فَعَلَ | يَفْعِلُ | اِفْعِلْ | لا تَفْعِلْ | فَعْلاً | فَاعِلٌ | مَفْعُولٌ | مَفْعِلٌ |
| **3C** | فَعَلَ | يَفْعُلُ | اُفْعُلْ | لا تَفْعُلْ | فَعْلاً | فَاعِلٌ | مَفْعُولٌ | مَفْعَلٌ |

**Bab classification:** Rumus 3A = Bab 1 (فتح يفتح), 3B = Bab 2 (ضرب يضرب), 3C = Bab 3 (نصر ينصر)

**Sub-patterns:**
| Bab | Madhi | Mudhari' | Example | Indonesian |
|-----|-------|---------|---------|------------|
| فَعَلَ يَفْعَلُ | فَعَلَ | يَفْعَلُ | فَتَحَ يَفْتَحُ | membuka |
| فَعَلَ يَفْعِلُ | فَعَلَ | يَفْعِلُ | ضَرَبَ يَضْرِبُ | memukul |
| فَعَلَ يَفْعُلُ | فَعَلَ | يَفْعُلُ | نَصَرَ يَنْصُرُ | menolong |
| فَعِلَ يَفْعَلُ | فَعِلَ | يَفْعَلُ | عَلِمَ يَعْلَمُ | mengetahui |
| فَعِلَ يَفْعِلُ | فَعِلَ | يَفْعِلُ | حَسِبَ يَحْسِبُ | menghitung |
| فَعُلَ يَفْعُلُ | فَعُلَ | يَفْعُلُ | كَرُمَ يَكْرُمُ | mulia |

**Note:** The last 3 (فَعِلَ يَفْعَلُ, فَعِلَ يَفْعِلُ, فَعُلَ يَفْعُلُ) are documented as sharing the same Tashrif Ishthilahi patterns as 3A, 3B, 3C respectively (see PDF page 20 note 3 and page 23 note 2).

### Rumus 4: Augmented with 1 Letter or 4-Letter Base

| Code | Pattern | Example | Meaning | Extra Letter |
|------|---------|---------|---------|-------------|
| **4A** | فَعَّلَ | عَلَّمَ | mengajar | Tasydid on 'ain |
| **4B** | فَاعَلَ | شَاوَرَ | berunding | Alif after fa |
| **4C** | أَفْعَلَ | أَسْلَمَ | menyerahkan diri | Hamzah before fa |
| **4D** | فَعْلَلَ | زَلْزَلَ | mengguncang | 4-letter root (ruba'i) |

### Rumus 5: Augmented with 2 Letters

| Code | Pattern | Example | Meaning | Extra Letters |
|------|---------|---------|---------|--------------|
| **5A** | تَفَعَّلَ | تَعَلَّمَ | belajar | Ta + tasydid |
| **5B** | تَفَاعَلَ | تَعَارَفَ | saling mengenal | Ta + alif |
| **5C** | اِفْتَعَلَ | اِحْتَرَمَ | memuliakan | Alif + ta |
| **5D** | اِنْفَعَلَ | اِنْكَسَرَ | patah (intransitive) | Alif + nun |
| **5E** | اِفْعَلَّ | اِحْمَرَّ | memerah (color) | Alif + tasydid on lam |

### Rumus 6: Augmented with 3 Letters

| Code | Pattern | Example | Meaning | Extra Letters |
|------|---------|---------|---------|--------------|
| **6** | اِسْتَفْعَلَ | اِسْتَغْفَرَ | meminta ampun | Alif + sin + ta |

### Complete Wazan Summary (from PDF page 45)

```
RUMUS 3:   فَعَلَ    يَفْعَلُ    اِفْعَلْ    لا تَفْعَلْ    فَعْلاً    فَاعِلٌ    مَفْعُولٌ    مَفْعَلٌ
            فَعَلَ    يَفْعِلُ    اِفْعِلْ    لا تَفْعِلْ    فَعْلاً    فَاعِلٌ    مَفْعُولٌ    مَفْعِلٌ
            فَعَلَ    يَفْعُلُ    اُفْعُلْ    لا تَفْعُلْ    فَعْلاً    فَاعِلٌ    مَفْعُولٌ    مَفْعَلٌ

RUMUS 4:   فَعَّلَ    يُفَعِّلُ    فَعِّلْ    لا تُفَعِّلْ    تَفْعِيلاً    مُفَعِّلٌ    مُفَعَّلٌ    مُفَعَّلٌ
            فَاعَلَ    يُفَاعِلُ    فَاعِلْ    لا تُفَاعِلْ    مُفَاعَلَةً   مُفَاعِلٌ    مُفَاعَلٌ    مُفَاعَلٌ
            أَفْعَلَ   يُفْعِلُ     أَفْعِلْ   لا تُفْعِلْ     إِفْعَالاً   مُفْعِلٌ     مُفْعَلٌ     مُفْعَلٌ
            فَعْلَلَ   يُفَعْلِلُ   فَعْلِلْ   لا تُفَعْلِلْ   فَعْلَلَةً   مُفَعْلِلٌ   مُفَعْلَلٌ   مُفَعْلَلٌ

RUMUS 5:   تَفَعَّلَ   يَتَفَعَّلُ   تَفَعَّلْ   لا تَتَفَعَّلْ   تَفَعُّلاً   مُتَفَعِّلٌ   مُتَفَعَّلٌ   مُتَفَعَّلٌ
            تَفَاعَلَ   يَتَفَاعَلُ   تَفَاعَلْ   لا تَتَفَاعَلْ   تَفَاعُلاً   مُتَفَاعِلٌ   مُتَفَاعَلٌ   مُتَفَاعَلٌ
            اِفْتَعَلَ  يَفْتَعِلُ    اِفْتَعِلْ  لا تَفْتَعِلْ    اِفْتِعَالاً  مُفْتَعِلٌ   مُفْتَعَلٌ   مُفْتَعَلٌ
            اِنْفَعَلَ  يَنْفَعِلُ    اِنْفَعِلْ  لا تَنْفَعِلْ    اِنْفِعَالاً  مُنْفَعِلٌ   مُنْفَعَلٌ   مُنْفَعَلٌ
            اِفْعَلَّ   يَفْعَلُّ     اِفْعَلَّ   لا تَفْعَلَّ     اِفْعِلاَلاً  مُفْعَلٌّ    مُفْعَلٌّ    مُفْعَلٌّ

RUMUS 6:   اِسْتَفْعَلَ  يَسْتَفْعِلُ  اِسْتَفْعِلْ  لا تَسْتَفْعِلْ  اِسْتِفْعَالاً  مُسْتَفْعِلٌ  مُسْتَفْعَلٌ  مُسْتَفْعَلٌ
```

---

## 3. 8 Forms of Tashrif Ishthilahi

The **8 columns** of Tashrif Ishthilahi represent the core paradigm. Every verb root can potentially generate all 8 forms (some have gaps, marked with 'x' in the PDF exercises):

| # | Column Name | Arabic | English Function |
|---|-------------|--------|-----------------|
| 1 | Fi'il Madhi | الفعل الماضي | Past tense (telah ...) |
| 2 | Fi'il Mudhari' | الفعل المضارع | Present/future (sedang/akan ...) |
| 3 | Fi'il Amr | فعل الأمر | Command (... lah) |
| 4 | Fi'il Nahi | فعل النهي | Prohibition (jangan ...) |
| 5 | Mashdar | المصدر | Verbal noun (pe ... an) |
| 6 | Ism Fa'il | اسم الفاعل | Active participle (yang me ...) |
| 7 | Ism Maf'ul | اسم المفعول | Passive participle (yang di ...) |
| 8 | Zamami | الزمني | Time/place noun |

### Special Cases

- **Fi'il Tsulatsi Mujarrad** (Rumus 3): Columns 6, 7, 8 use fa'ala pattern WITHOUT the mu- prefix
- **Rumus 4, 5, 6**: Columns 6, 7, 8 ALL start with مُـ (mu-) prefix
- **Sifat verbs** (فَعُلَ يَفْعُلُ): Only 4 forms — Madhi, Mudhari', Mashdar, and Shifat Musyabbahah (resembling Ism Fa'il)

---

## 4. Tashrif Lughowi (Full Pronoun Conjugation)

The PDF (pages 48-52) provides full 14-pronoun conjugation for all tenses, using 4 example wazans (عَلِمَ, عَلَّمَ, تَعَلَّمَ, اِسْتَعْلَمَ).

### Past Tense Pronouns (14 forms)

| Pronoun | Arabic | Singular | Dual | Plural |
|---------|--------|----------|------|--------|
| He (3rd m) | هو | فَعَلَ | فَعَلَا | فَعَلُوا |
| She (3rd f) | هي | فَعَلَتْ | فَعَلَتَا | فَعَلْنَ |
| You (2nd m) | أنت | فَعَلْتَ | فَعَلْتُمَا | فَعَلْتُمْ |
| You (2nd f) | أنتِ | فَعَلْتِ | فَعَلْتُمَا | فَعَلْتُنَّ |
| I (1st) | أنا | فَعَلْتُ | — | فَعَلْنَا |

### Present Tense Pronouns (14 forms)

| Pronoun | Arabic | Singular | Dual | Plural |
|---------|--------|----------|------|--------|
| He (3rd m) | هو | يَفْعَلُ | يَفْعَلَانِ | يَفْعَلُونَ |
| She (3rd f) | هي | تَفْعَلُ | تَفْعَلَانِ | يَفْعَلْنَ |
| You (2nd m) | أنت | تَفْعَلُ | تَفْعَلَانِ | تَفْعَلُونَ |
| You (2nd f) | أنتِ | تَفْعَلِينَ | تَفْعَلَانِ | تَفْعَلْنَ |
| I (1st) | أنا | أَفْعَلُ | — | نَفْعَلُ |

### Imperative Pronouns (6 forms)

Only for the 2nd person pronouns (أنت through أنتن).

### Noun Declension (Ism Fa'il, Ism Maf'ul, Zamami)

| Number/Gender | Singular | Dual | Plural |
|--------------|----------|------|--------|
| Masc. | فَاعِلٌ | فَاعِلَانِ | فَاعِلُونَ |
| Fem. | فَاعِلَةٌ | فَاعِلَتَانِ | فَاعِلَاتٌ |

---

## 5. Current Integration Point: Sarf CLI

The Sarf CLI (`sarf-source/sarf-library/src/main/java/sarf/SarfCLI.java`) already provides:

### Current Capabilities (Triliteral)
```java
POST /api/sarf/analyze { root: "كتب", bab: 1 }
→ pastTense, presentTense, presentSubjunctive, presentJussive, masdars
```

### Current Capabilities (Quadriliteral) — via `conjugateQuadriliteral()`
```java
POST /api/sarf/analyze { root: "زلزل", bab: 1 }
→ pastTense, presentTense, presentSubjunctive, presentJussive, masdars: []
```

### What's Missing for the Tashrif System

| Feature | Sarf CLI | Tashrif PDF | Gap |
|---------|----------|-------------|-----|
| 8-column Ishthilahi table | ❌ | ✅ | Sarf returns conjugated forms by pronoun, not by pattern |
| Imperative (Amr) | ❌ (for quadriliteral) | ✅ | Missing for 4-letter roots |
| Prohibitive (Nahi) | ❌ | ✅ | Not generated at all |
| Active participle (Ism Fa'il) | ❌ | ✅ | Not included |
| Passive participle (Ism Maf'ul) | ❌ | ✅ | Not included |
| Time/place noun (Zamami) | ❌ | ✅ | Not included |
| Indonesian translation | ❌ | ✅ | Sarf is Arabic-only |
| Rumus classification | ❌ | ✅ | Sarf uses standard Sarfi classification |

---

## 6. Implementation Strategy

### Option A: Extend Sarf CLI (Recommended)
Enhance the existing `SarfCLI.java` to also generate Ism Fa'il, Ism Maf'ul, Zamami, Amr, Nahi, and the 8-column Ishthilahi format.

**Pros:** Deep integration, diacritized output, handles weak verbs  
**Cons:** Requires Java changes, recompilation needed

### Option B: Python Rule Engine
Build a Python-based tashrif engine using the wazan patterns as rules.

**Pros:** Fast to build, easy to customize, no Java dependency  
**Cons:** Less accurate for weak/defective/hamzated verbs, no diacritization

### Option C: Hybrid
Use Sarf CLI for conjugation tables (past/present tenses) and a Python rule engine for the 8-column Ishthilahi patterns and derived nouns.

**Pros:** Best of both worlds  
**Cons:** More complex, two systems to maintain

### Recommendation: **Option A + Option C (Hybrid)**

Phase 1: Extend Sarf CLI to generate all 8 columns and Amr/Nahi  
Phase 2: Add a Python rule engine for the Ishthilahi pattern mapping (which pattern → which Rumus)  
Phase 3: Add Indonesian translation overlay using existing dictionary

---

## 7. New API Design

### Extended `POST /api/sarf/analyze` Response

```json
{
  "root": "كتب",
  "bab": 1,
  "classification": "فعل ثلاثي مجرد — فتح يفتح (Rumus 3A)",
  "rumus": "3A",
  
  "ishthilahi": {
    "fiil_madhi": "كَتَبَ",
    "fiil_mudhari": "يَكْتُبُ",
    "fiil_amr": "اُكْتُبْ",
    "fiil_nahi": "لا تَكْتُبْ",
    "mashdar": "كَتْبًا",
    "ism_fail": "كَاتِبٌ",
    "ism_maful": "مَكْتُوبٌ",
    "zamami": "مَكْتَبٌ"
  },
  
  "lughowi": {
    "past_tense": [
      { "pronoun": "هو", "text": "كَتَبَ", "translation_id": "telah menulis" },
      { "pronoun": "هي", "text": "كَتَبَتْ", "translation_id": "telah menulis" },
      { "pronoun": "هما (m)", "text": "كَتَبَا", "translation_id": "telah menulis" },
      ...
    ],
    "present_tense": [ ... ],
    "present_subjunctive": [ ... ],
    "present_jussive": [ ... ],
    "imperative": [ ... ],
    "nahi": [ ... ]
  },
  
  "derived_nouns": {
    "ism_fail": {
      "mufrad_mudhakkar": "كَاتِبٌ",
      "mufrad_muannats": "كَاتِبَةٌ",
      "mutsanna_mudhakkar": "كَاتِبَانِ",
      "jamak_mudhakkar": "كَاتِبُونَ"
    },
    "ism_maful": { ... },
    "zamami": { ... }
  },
  
  "masdars": ["كَتْبًا", "كِتَابَةً"],
  "translations": {
    "id": {
      "fiil_madhi": "telah menulis",
      "fiil_mudhari": "sedang/akan menulis",
      "fiil_amr": "tulislah",
      "fiil_nahi": "jangan tulis",
      "mashdar": "tulisan",
      "ism_fail": "penulis",
      "ism_maful": "yang ditulis",
      "zamami": "tempat/waktu menulis"
    }
  }
}
```

### New Endpoint: `POST /api/tashrif/analyze`

```json
// Request
{
  "word": "يَكْتُبُ",
  "root": "كتب",
  "pos_type": "verb"
}

// Response
{
  "word": "يَكْتُبُ",
  "root": "كتب",
  "rumus": "3C",
  "bab": 3,
  "classification": "فعل ثلاثي مجرد — نصر ينصر",
  
  "ishthilahi_table": { /* 8-column table */ },
  "lughowi": { /* Full pronoun conjugation */ },
  
  "rules_applied": [
    "Rumus 3C: الفتحة على عين الكلمة في الماضي والضمة في المضارع",
    "Fi'il Tsulatsi Mujarrad: لا أحرف زائدة"
  ],
  
  "meaning_id": "menulis",
  "meaning_en": "to write"
}
```

---

## 8. Frontend UI Mockup

### Tashrif Modal (replacing/expanding the current Sarf modal)

```
┌───────────────────────────────────────────────────────────────────────┐
│  ✕  📖 Tashrif Ishthilahi: كَتَبَ                                │
│  ─────────────────────────────────────────────────────────────────   │
│                                                                      │
│  Root: كتب  │  Rumus: 3C (نصر ينصر)  │  Jenis: Fi'il Tsulatsi Mujarrad│
│  ┌─── 8 KOLOM TASHRIF ISHTHILAHI ───────────────────────────────┐   │
│  │  1. Madhi     │  2. Mudhari'  │  3. Amr     │  4. Nahi     │   │
│  │  كَتَبَ       │  يَكْتُبُ     │  اُكْتُبْ   │  لا تَكْتُبْ │   │
│  │  (telah       │  (sedang/akan │  (tulislah) │  (jangan      │   │
│  │   menulis)    │   menulis)    │             │   tulis)      │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │  5. Mashdar   │  6. Ism Fa'il │  7. Ism     │  8. Zamami   │   │
│  │  كَتْبًا      │  كَاتِبٌ     │  مَفْعُولٌ  │  مَفْعَلٌ    │   │
│  │  (tulisan)    │  (penulis)    │  (yang      │  (tempat      │   │
│  │               │               │   ditulis)  │   menulis)    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─── TASHRIF LUGHOWI — Fi'il Madhi ──────────────────────────┐     │
│  │  هو  كَتَبَ    │  هما  كَتَبَا     │  هم  كَتَبُوا       │     │
│  │  هي  كَتَبَتْ  │  هما  كَتَبَتَا   │  هن  كَتَبْنَ       │     │
│  │  أنت كَتَبْتَ  │  أنتما كَتَبْتُمَا│  أنتم كَتَبْتُمْ    │     │
│  │  أنتِ كَتَبْتِ │  أنتما كَتَبْتُمَا│  أنتن كَتَبْتُنَّ   │     │
│  │  أنا كَتَبْتُ  │                    │  نحن كَتَبْنَا      │     │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─── DAFTAR KATA KERJA Rumus 3C ─────────────────────────────┐     │
│  │  أَخَذَ (mengambil)  │  دَخَلَ (masuk)    │  كَتَبَ (menulis)  │
│  │  بَلَغَ (sampai)     │  دَرَسَ (belajar)  │  كَفَرَ (ingkar)   │
│  │  بَطَلَ (batal)      │  رَزَقَ (memberi)  │  ...               │
│  └──────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
```

### Tab: Tashrif Lughowi Full (expandable detail)

```
┌─── TASHRIF LUGHOWI — Fi'il Mudhari' ───────────────────────────┐
│  ▸ Klik untuk perluas ke 13 pronoun + subjunctive + jussive   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  TENSE        │  MARFU' (Indicative)  │  MANSUB        │ │
│  │               │                       │  (Subjunctive)  │ │
│  ├───────────────┼───────────────────────┼─────────────────┤ │
│  │  هو           │  يَكْتُبُ            │  يَكْتُبَ       │ │
│  │  هي           │  تَكْتُبُ            │  تَكْتُبَ       │ │
│  │  ...          │  ...                 │  ...            │ │
│  └───────────────┴───────────────────────┴─────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

---

## 9. Phased Implementation Plan

### Phase 1: Rule-Based Rumus Classifier (2-3 days)
Build a Python classifier that takes an Arabic word and determines its Rumus:

```python
# backend/tashrif_classifier.py

def classify(word: str, root: str) -> RumusResult:
    """Determine the Rumus number and letter for a given word."""
    # Step 1: Remove prefixes (ي, ت, أ, ن, س, etc.)
    # Step 2: Remove suffixes (ون, ين, ات, etc.)
    # Step 3: Compare stem to known wazan patterns
    # Step 4: Return Rumus (3A-6) and Form (1-8)
    pass
```

### Phase 2: 8-Column Ishthilahi Generator (3-4 days)
Build a pattern-based generator that produces the 8-column table:

```python
# backend/tashrif_generator.py

def generate_ishthilahi(root: str, rumus: str, bab: int) -> dict:
    """Generate the 8-column Tashrif Ishthilahi table."""
    # Map root letters onto the wazan pattern
    # Apply vowel rules based on bab/rumus
    # Return all 8 forms with diacritics
    pass
```

### Phase 3: Tashrif Lughowi Generator (4-5 days)
Extend Sarf CLI or build a Python-based full pronoun conjugator:

```python
# backend/tashrif_lughowi.py

def conjugate_lughowi(root: str, rumus: str) -> dict:
    """Generate full 14-pronoun conjugation tables."""
    # Past tense (14 pronouns)
    # Present tense (14 pronouns × 3 moods)
    # Imperative (6 pronouns)
    # Prohibitive (6 pronouns)
    pass
```

### Phase 4: Indonesian Translation Overlay (2-3 days)
Add Indonesian translations to all generated forms:

```python
# backend/tashrif_translate.py

def translate_ishthilahi(root: str, rumus: str) -> dict:
    """Add Indonesian meanings to each column."""
    # Look up root meaning in dictionary
    # Apply rumus-specific semantic rules
    # Return translated table
    pass
```

### Phase 5: Frontend UI (2-3 days)

| Step | Task |
|:----:|------|
| 1 | Add "Tashrif" tab/button in the analyze view |
| 2 | Create TashrifIshthilahi component (8-column grid) |
| 3 | Create TashrifLughowi component (14-pronoun tables) |
| 4 | Add toggle between Ishthilahi and Lughowi views |
| 5 | Add vocabulary list from the matching Rumus |

---

## 10. Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/tashrif_classifier.py` | **Create** | Rumus/pattern classification engine |
| `backend/tashrif_generator.py` | **Create** | 8-column Ishthilahi generation |
| `backend/tashrif_lughowi.py` | **Create** | Full pronoun conjugation tables |
| `backend/tashrif_translate.py` | **Create** | Indonesian translations for tashrif forms |
| `backend/main.py` | **Modify** | Add `POST /api/tashrif/analyze` endpoint |
| `backend/sarf_client.py` | **Modify** | Add 8-column and Lughowi methods |
| `sarf-source/sarf-library/.../SarfCLI.java` | **Modify** | Add imperative, nahi, ism fa'il, ism maf'ul, zamami to `conjugateQuadriliteral()` |
| `frontend/pages/index.vue` | **Modify** | Add Tashrif Ishthilahi + Lughowi modal |
| `frontend/components/TashrifModal.vue` | **Create** | Reusable tashrif display component |
| `docs/TASHRIF_IMPLEMENTATION.md` | **Create** | This document |

---

## 11. Risks & Challenges

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Diacritization accuracy** for generated forms | High | Use Sarf CLI (which provides full harakat) as primary generator |
| **Weak/defective/hamzated roots** (أخو, قضى, بدأ) have irregular patterns | High | Start with سالم (sound) roots only; add special rules incrementally |
| **Rumus classification** may be ambiguous for some words | Medium | Show multiple possible Rumus to user; let them select |
| **Indonesian translations** need to vary by context/form | Medium | Use root meaning + semantic rule for each Rumus/form |
| **Mashdar forms** are often irregular (سماعي not قياسي) | Medium | Always show dictionary lookup first, pattern as fallback |
| **Performance** generating all 8 + 14-14-14-6 forms per request | Low | Cache results per root+rumus combination |

---

## 12. Final Verdict

| Question | Answer |
|----------|--------|
| **Is the PDF content sufficient for implementation?** | ✅ **Yes** — All 12 wazan patterns (3A-6), 8 Ishthilahi columns, and 14-pronoun Lughowi conjugations are documented with full diacritics and Indonesian translations |
| **Can we leverage the existing Sarf CLI?** | ✅ **Yes** — The Sarf CLI already generates past/present tenses. We can extend it for the full 8 columns. The `conjugateQuadriliteral()` method can serve as a template. |
| **Is the Rumus system compatible with Sarf?** | ⚠️ **Mostly** — The Sarf system uses standard Arabic grammar terminology (باب 1-6 for triliteral, augmented verb formulas). The Rumus system is a pedagogical simplification that maps well to Sarf's internal categories. |
| **What's the hardest part?** | ⭐⭐⭐ **Mashdar irregularity** — Many gerunds don't follow the qiyasi (regular) pattern and must be looked up in a dictionary |
| **Total effort estimate** | ~20-30 hours across all 5 phases |

### Immediate Next Steps

1. **Build the Rumus classifier** — This is the foundational piece. Without knowing which Rumus a word follows, we can't generate the 8-column table.
2. **Extend SarfCLI.java** — Add `generateAmr()`, `generateNahi()`, `generateIsmFail()`, `generateIsmMafUl()`, `generateZamami()` methods for both triliteral and quadriliteral roots.
3. **Build the 8-column renderer** — Map the generated forms onto the 8-column Ishthilahi grid.
4. **Add Indonesian translations** to each form using root meaning lookup + Rumus-specific semantic rules.

---

## Appendix: Wazan Pattern Mapping to Indonesian Meanings

| Rumus | Meaning Pattern | Example |
|-------|----------------|---------|
| 3A-C | Root meaning | كَتَبَ → menulis |
| 4A | Membuat jadi / mengulang | عَلَّمَ → mengajar (menjadikan ilmu) |
| 4B | Saling / berbalasan | شَاوَرَ → berunding (saling memberi pendapat) |
| 4C | Menjadikan / transitif | أَسْلَمَ → menyerahkan diri |
| 4D | 4-letter root meaning | زَلْزَلَ → mengguncang |
| 5A | Intransitif / refleksif | تَعَلَّمَ → belajar (mengajar diri sendiri) |
| 5B | Saling melakukan | تَعَارَفَ → saling mengenal |
| 5C | Melakukan pada diri sendiri | اِحْتَرَمَ → memuliakan |
| 5D | Pasif / intransitif | اِنْكَسَرَ → patah (ter-) |
| 5E | Warna / sifat menjadi | اِحْمَرَّ → memerah |
| 6 | Meminta / menganggap | اِسْتَغْفَرَ → meminta ampun |

---

*Assessment prepared by analyzing `docs/tashrif.pdf` (53 pages) by Andy Satiyo Ahmad, `docs/wazan.md` (AI system prompt for Tashrif Ishthilahi analysis), and the existing Penerjemah Kitab codebase (Sarf CLI integration, CAMeL Tools pipeline, Indonesian dictionary).*
