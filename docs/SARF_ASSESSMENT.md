# Assessment: Integrating Sarf Arabic Morphology System
## Adding Verb Conjugation (تصريف) & Noun Derivation (اشتقاق) to Penerjemah Kitab

**Date:** July 27, 2026
**Repo Assessed:** [alsaydi/sarf](https://github.com/alsaydi/sarf) by Abdalaziz Alsaydi
**Demo:** [sarf.one](https://sarf.one/)
**Context:** Add a button per word in the "Detail Lengkap" table to open a Sarf-powered morphology view showing verb conjugation (تصريف), noun derivation (اشتقاق), root classification, and grammatical analysis — similar to the sarf.one demo.

---

## Table of Contents

1. [What Sarf Does](#1-what-sarf-does)
2. [Sarf API Architecture](#2-sarf-api-architecture)
3. [Current App Integration Point](#3-current-app-integration-point)
4. [Proposed Feature: "Analisis Sarf" Button in Detail Lengkap](#4-proposed-feature-analisis-sarf-button-in-detail-lengkap)
5. [Data Flow](#5-data-flow)
6. [Sarf API Response Structure (Estimated)](#6-sarf-api-response-structure-estimated)
7. [Frontend UI Mockup](#7-frontend-ui-mockup)
8. [Implementation Phases](#8-implementation-phases)
9. [Dependencies & Setup](#9-dependencies--setup)
10. [Risks & Challenges](#10-risks--challenges)
11. [Files to Create/Modify](#11-files-to-createmodify)
12. [Final Verdict](#12-final-verdict)

---

## 1. What Sarf Does

**Sarf** (صرف — Arabic morphology) is a comprehensive Arabic morphology and verb conjugation system. Originally developed under the Arab League Educational, Cultural and Scientific Organization (ALECSO/ألكسو), it was ported to modern Java/Spring Boot by Abdalaziz Alsaydi.

### Capabilities

| Feature | Arabic | Description | Covers |
|---|---|---|---|
| **Verb Conjugation** | تصريف الأفعال | Conjugate verbs across all pronouns | Past (ماضي), Present (مضارع), Imperative (أمر) |
| **Active/Passive** | مبني للمعلوم/المجهول | Both voices for all tenses | All verb forms |
| **Augmented Verbs** | الفعل المزيد | Verbs with extra letters (افتعل, استفعل, etc.) | All 15 forms of الثلاثي المزيد |
| **Noun Derivation** | اشتقاق الأسماء | Generate derived nouns | Ism Fa'il, Ism Maf'ul, Ism Zaman/Makan, etc. |
| **Gerunds** | المصادر | Generate masdar forms | Qiyasi (قياسي) and Samai'i (سماعي) |
| **Full Diacritization** | الضبط بالشكل | Complete harakat on all output | All generated forms |
| **Root Database** | قواعد الجذور | 24,000+ triliteral and quadriliteral roots | Includes conjugation class (باب) info |
| **Nahw/Sarf Rules** | قواعد النحو والصرف | 80,000+ derived forms | الاعلال, الابدال, الادغام |

### What Sarf Does NOT Do

- ❌ No semantic translation (no Indonesian/English)
- ❌ No i'rab (syntactic position analysis)
- ❌ No tashkeel on arbitrary input text (it conjugates from roots, not diacritize)
- ❌ No word-by-word gloss or dictionary lookup
- ❌ No OCR or PDF processing

### How Sarf Complements Current System

```
Current System (Penerjemah Kitab):
  Input:  يكتب الطالب الدرس في المكتبة
  Output: Word-by-word analysis (lemma, root, POS, gloss ID/EN)
          + Full sentence translation (ID + EN)

Sarf Addition:
  Input:  Root كتب (from CAMeL analysis)
  Output: Full verb conjugation table:
          - Past tense (كتب, كتبت, كتبنا, ...)
          - Present tense (يكتب, تكتب, نكتب, ...)
          - Active & passive voice
          - Masdar (مصدر), Ism Fa'il (اسم فاعل), etc.
```

---

## 2. Sarf API Architecture

### Technology Stack

```
┌─────────────────────────────────────────────┐
│         alsaydi/sarf Docker Container        │
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │   sarf-ui (Angular) — Port 80           │ │
│  │   Frontend at sarf.one                   │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │   sarf-web-service (Spring Boot)        │ │
│  │   REST API — Port 8080                  │ │
│  │                                          │ │
│  │   Controllers:                          │ │
│  │   - SarfController (main API)           │ │
│  │   - RootController (root discovery)     │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │   sarf-library (Java)                   │ │
│  │   Core morphology engine                │ │
│  │   - 24,000+ root database              │ │
│  │   - Conjugation rules                   │ │
│  │   - Derivation rules                    │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Running Sarf

Sarf runs as a Docker container:

```bash
docker run --rm -p 8080:8080 alsaydi/sarf:1.4
```

After starting, the API is available at `http://localhost:8080/`.

### REST API Endpoints

Based on source code analysis of `SarfController.java` and the repo structure:

| Endpoint | Method | Parameters | Description |
|---|---|---|---|
| `/sarf/{rootLetters}` | GET | `rootLetters` (3-4 Arabic chars, path) | Root discovery — returns conjugation classes available for this root |
| `/sarf/active/{rootLetters}` | GET | `rootLetters`, `augmented` (bool), `cclass` (int), `formula` (int) | Active voice verb conjugation for a specific class |
| `/sarf/passive/{rootLetters}` | GET | Same as above | Passive voice verb conjugation |
| `/sarf/nouns/{rootLetters}` | GET | Same as above | Derive all noun forms |
| `/sarf/gerunds/{rootLetters}` | GET | Same as above | Generate masdar (gerund) forms |
| `/sarf/roots/{rootLetters}` | GET | `rootLetters` | Get root info and available conjugation patterns |

**Key Parameters:**

| Parameter | Type | Description | Example |
|---|---|---|---|
| `rootLetters` | String (3-4 Arabic chars) | The triliteral/quadriliteral root | `كتب` |
| `augmented` | Boolean | Whether the verb is augmented (مزيد) | `false` |
| `cclass` | Integer | Conjugation class number (باب) | `1` (فتح يفتح) |
| `formula` | Integer | Formula index within the class | `0` |

### Internal Data Model

The library organizes conjugation data using specialized container classes:

| Container | Purpose | Key Data |
|---|---|---|
| `PastConjugationDataContainer` | Past tense (الماضي) | Vowel patterns, connected pronouns (ت, نا, etc.) |
| `PresentConjugationDataContainer` | Present tense (المضارع) | Prefixes (ي, ت, أ, ن), suffixes, vowel patterns |
| `ImperativeConjugationDataContainer` | Imperative (الأمر) | Prefix/suffix patterns for command forms |

The `getConjugation()` method on root objects returns the Sarfi pattern (door/bab) which determines how vowel patterns are applied.

---

## 3. Current App Integration Point

### Current `POST /api/analyze` Response

The existing `analyze_words()` function returns:

```json
{
  "original": "يكتب الطالب الدرس",
  "harakat": "يَكْتُبُ الطَّالِبُ الدَّرْسَ",
  "words": [
    {
      "word": "يَكْتُبُ",
      "lemma": "كتب",
      "root": "كتب",
      "pos_type": "verb",
      "pos_arabic": "فعل",
      "gloss_id": "menulis",
      "gloss_en": "to write"
    },
    {
      "word": "الطَّالِبُ",
      "lemma": "طالب",
      "root": "طلب",
      "pos_type": "noun",
      "pos_arabic": "إسم",
      "gloss_id": "siswa",
      "gloss_en": "student"
    }
  ],
  "word_count": 2
}
```

### Integration Points

1. **`root` field** — CAMeL Tools already extracts the triliteral/quadriliteral root (e.g., `كتب`, `طلب`). This is the EXACT input Sarf needs.
2. **`lemma` field** — Could be used to determine augmented vs. non-augmented and to guide class selection.
3. **`pos_type` field** — Verbs should get conjugation tables, nouns should get derivation tables, etc.

### Current "Detail Lengkap" UI

The "Detail Lengkap" section is a `<details>` element in `frontend/pages/index.vue` (around line 123) containing a table:

```
┌────────────────────────────────────────────┐
│  ▸ Detail Lengkap                  3 kata  │
├────────────────────────────────────────────┤
│  # │ Arab  │ Lemma │ Akar │ Jenis │ ID │ EN│
│  1 │ يكتب  │ كتب   │ كتب  │ فعل   │ .. │ ..│
│  2 │ الطالب│ طالب  │ طلب  │ إسم   │ .. │ ..│
│  3 │ الدرس │ درس   │ درس  │ إسم   │ .. │ ..│
└────────────────────────────────────────────┘
```

**Proposed: Each row gets a "🔬 صرف" button** that opens a Sarf morphology modal/panel.

---

## 4. Proposed Feature: "Analisis Sarf" Button in Detail Lengkap

### What the User Sees

In the "Detail Lengkap" table, each word row gets a new action button:

```
┌──────────────────────────────────────────────────────────────┐
│  # │ Arab    │ Lemma │ Akar │ Jenis │ ID    │ EN      │ صرف │
├──────────────────────────────────────────────────────────────┤
│  1 │ يَكْتُبُ │ كتب   │ كتب  │ فعل   │menulis│to write│ 🔬  │
│  2 │ الطَّالِبُ│ طالب  │ طلب  │ إسم   │siswa  │student │ 🔬  │
│  3 │ الدَّرْسَ │ درس   │ درس  │ إسم   │pelajaran│lesson │ 🔬  │
└──────────────────────────────────────────────────────────────┘
```

Clicking 🔬 on a verb like `يَكْتُبُ` (root: `كتب`) opens a Sarf modal showing:

### Sarf Modal Output (for verb كتب)

```
┌─────────────────────────────────────────────────────────────┐
│  🔬 ANALISIS SARF: كَتَبَ                                   │
│  ─────────────────────────────────────────────────────────  │
│  Jenis: Fi'il Tsulatsi Mujarrad (فعل ثلاثي مجرد)             │
│  Bab: فتح يفتح (Bab 1)                                       │
│                                                             │
│  ┌─── TASRIF FI'IL MADHI (Past Tense) ──────────────────┐  │
│  │ هُوَ  كَتَبَ     | هُمْ   كَتَبُوا                    │  │
│  │ هِيَ  كَتَبَتْ   | هُنَّ  كَتَبْنَ                     │  │
│  │ أَنْتَ كَتَبْتَ   | أَنْتُمْ كَتَبْتُمْ                 │  │
│  │ أَنَا كَتَبْتُ    | نَحْنُ  كَتَبْنَا                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─── TASRIF FI'IL MUDHARI' (Present Tense) ───────────┐  │
│  │ هُوَ  يَكْتُبُ    | هُمْ   يَكْتُبُونَ                 │  │
│  │ هِيَ  تَكْتُبُ    | هُنَّ  يَكْتُبْنَ                  │  │
│  │ أَنْتَ تَكْتُبُ   | أَنْتُمْ تَكْتُبُونَ                │  │
│  │ أَنَا أَكْتُبُ    | نَحْنُ  نَكْتُبُ                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─── MUSHTAQQAT (Derived Nouns) ───────────────────────┐  │
│  │ • Ism Fa'il:  كَاتِبٌ    (penulis)                   │  │
│  │ • Ism Maf'ul: مَكْتُوبٌ  (yang ditulis)              │  │
│  │ • Masdar:     كِتَابَةٌ  (tulisan) / كَتْبًا         │  │
│  │ • Ism Zaman:  مَكْتَبٌ   (waktu/tempat menulis)      │  │
│  │ • Ism Makan:  مَكْتَبٌ   (meja/tempat menulis)       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─── INFORMASI TAMBAHAN ──────────────────────────────┐  │
│  │ • Root: كتب (Kaf-Ta-Ba)                              │  │
│  │ • Huruf: Tsulatsi (3 huruf)                          │  │
│  │ • Mujarrad: Tidak ada huruf tambahan                 │  │
│  │ • Lazim/Muta'addi: Muta'addi (memerlukan objek)       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### For Nouns

For nouns like `الطَّالِبُ` (root: `طلب`), the modal would show:

```
┌─────────────────────────────────────────────────────────────┐
│  🔬 ANALISIS SARF: طَالِبٌ                                  │
│  ─────────────────────────────────────────────────────────  │
│  Jenis: Ism Fa'il (اسم فاعل)                                │
│  Root: طلب                                                  │
│                                                             │
│  ┌─── TASRIF ISM (Noun Conjugation) ────────────────────┐  │
│  │ Mufrad:  طَالِبٌ     (satu)                           │  │
│  │ Mutsanna: طَالِبَانِ  (dua)                           │  │
│  │ Jamak:    طُلَّابٌ / طَالِبُونَ  (banyak)              │  │
│  │                                                       │  │
│  │ Rafa':  طَالِبٌ    | Nasab: طَالِبًا   | Jar: طَالِبٍ  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─── FI'IL TERKAIT ───────────────────────────────────┐  │
│  │ Madhi:  طَلَبَ       (mencari/meminta)               │  │
│  │ Mudhari': يَطْلُبُ   (mencari/meminta)               │  │
│  │ Masdar: طَلَبًا      (permintaan)                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW                                     │
│                                                                      │
│  ┌─────────┐    POST /api/analyze     ┌──────────────────────┐      │
│  │ Frontend │ ──────────────────────► │   Backend (FastAPI)   │      │
│  │ (Nuxt)   │                        │                       │      │
│  │          │ ◄──── AnalyzeResponse ─ │   analyze_words()     │      │
│  │          │    (with root, lemma)  │   via CAMeL Tools     │      │
│  │          │                        └──────────────────────┘      │
│  │          │                                                       │
│  │          │    POST /api/sarf/analyze                             │
│  │          │    { root: "كتب", word: "يَكْتُبُ", pos: "verb" }      │
│  │          │                        ┌──────────────────────┐      │
│  │          │ ──────────────────────► │   Backend Sari API   │      │
│  │          │                        │                      │      │
│  │          │                        │  ┌─────────────────┐ │      │
│  │          │                        │  │  Sarf Docker     │ │      │
│  │          │                        │  │  localhost:8080  │ │      │
│  │          │                        │  │  /sarf/active/   │ │      │
│  │          │                        │  │  /sarf/passive/  │ │      │
│  │          │                        │  │  /sarf/nouns/    │ │      │
│  │          │                        │  │  /sarf/gerunds/  │ │      │
│  │          │                        │  └─────────────────┘ │      │
│  │          │ ◄── SarfAnalysisResponse └──────────────────────┘      │
│  │          │    (conjugation tables,                                 │
│  │          │     derived nouns, etc.)                                │
│  │          │                                                       │
│  │          │  ┌──────────────────────────────────────┐            │
│  │          │  │  Sarf Modal Display                  │            │
│  │          │  │  - Verb conjugation tables           │            │
│  │          │  │  - Noun declension tables            │            │
│  │          │  │  - Grammatical classification        │            │
│  │          │  │  - Translation overlay (ID/EN)       │            │
│  │          │  └──────────────────────────────────────┘            │
│  └─────────┘                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Detailed Step-by-Step

1. **User pastes Arabic text** → clicks "Analisis Teks"
2. **Frontend calls** `POST /api/analyze`
3. **Backend** runs CAMeL Tools → returns `WordAnalysis[]` with `root`, `lemma`, `pos_type`
4. **Frontend** displays "Detail Lengkap" table with word rows
5. **User clicks 🔬 (Sarf)** on a specific word (e.g., `يَكْتُبُ` — root: `كتب`, POS: `verb`)
6. **Frontend calls** `POST /api/sarf/analyze` with `{ root: "كتب", word: "يَكْتُبُ", pos_type: "verb" }`
7. **Backend Sarf Proxy:**
   - Determines conjugation class from word form (e.g., Bab 1 — فتح يفتح)
   - Calls Sarf API endpoints:
     - `GET /sarf/active/كتب?augmented=false&cclass=1&formula=0`
     - `GET /sarf/passive/كتب?augmented=false&cclass=1&formula=0`
     - `GET /sarf/nouns/كتب?augmented=false&cclass=1&formula=0`
     - `GET /sarf/gerunds/كتب?augmented=false&cclass=1&formula=0`
   - Merges results + adds Indonesian translation overlay from dictionary
   - Returns structured response
8. **Frontend** renders Sarf modal with conjugation tables, derived nouns, grammatical info

---

## 6. Sarf API Response Structure (Estimated)

Based on the source code analysis and the demo behavior, the expected JSON response structure:

### Active Conjugation Response

```json
{
  "root": "كتب",
  "transitiveType": "MUTAADDI",
  "conjugationClass": 1,
  "augmented": false,
  "pastTense": {
    "هو": "كَتَبَ",
    "هي": "كَتَبَتْ",
    "هما_m": "كَتَبَا",
    "هما_f": "كَتَبَتَا",
    "هم": "كَتَبُوا",
    "هن": "كَتَبْنَ",
    "أنت": "كَتَبْتَ",
    "أنتِ": "كَتَبْتِ",
    "أنتما": "كَتَبْتُمَا",
    "أنتم": "كَتَبْتُمْ",
    "أنتن": "كَتَبْتُنَّ",
    "أنا": "كَتَبْتُ",
    "نحن": "كَتَبْنَا"
  },
  "presentTense": {
    "هو": "يَكْتُبُ",
    "هي": "تَكْتُبُ",
    "هما_m": "يَكْتُبَانِ",
    "هما_f": "تَكْتُبَانِ",
    "هم": "يَكْتُبُونَ",
    "هن": "يَكْتُبْنَ",
    "أنت": "تَكْتُبُ",
    "أنتِ": "تَكْتُبِينَ",
    "أنتما": "تَكْتُبَانِ",
    "أنتم": "تَكْتُبُونَ",
    "أنتن": "تَكْتُبْنَ",
    "أنا": "أَكْتُبُ",
    "نحن": "نَكْتُبُ"
  },
  "imperative": {
    "أنت": "اكْتُبْ",
    "أنتِ": "اكْتُبِي",
    "أنتما": "اكْتُبَا",
    "أنتم": "اكْتُبُوا",
    "أنتن": "اكْتُبْنَ"
  }
}
```

### Noun Derivation Response (Estimated)

```json
{
  "root": "كتب",
  "nouns": {
    "ism_fail": "كَاتِبٌ",
    "ism_maful": "مَكْتُوبٌ",
    "ism_zaman": "مَكْتَبٌ",
    "ism_makan": "مَكْتَبٌ",
    "ism_ala": "مِكْتَبٌ",
    "masdar": "كِتَابَةٌ",
    "masdar_mimmi": "مَكْتَبًا",
    "ism_tafdil": null
  }
}
```

**Note:** These are estimated structures. The exact JSON schema would need to be confirmed by running the Sarf Docker container and hitting the actual API endpoints.

---

## 7. Frontend UI Mockup

### Button Placement in Detail Lengkap Table

```
┌──────────────────────────────────────────────────────────────────────┐
│  ▸ Detail Lengkap                                          3 kata  │
├──────────────────────────────────────────────────────────────────────┤
│  # │ Arab    │ Lemma │ Akar │ Jenis │ ID    │ EN      │   صرف      │
├──────────────────────────────────────────────────────────────────────┤
│  1 │يَكْتُبُ │ كتب   │ كتب  │ فعل   │menulis│to write │ [🔬]      │
│  2 │الطَّالِبُ│ طالب  │ طلب  │ إسم   │siswa  │student  │ [🔬]      │
│  3 │الدَّرْسَ │ درس   │ درس  │ إسم   │pelajaran│lesson │ [🔬]      │
└──────────────────────────────────────────────────────────────────────┘
```

### Sarf Modal (Slide-over panel)

```
┌─────────────────────────────────────────────────────────────────────┐
│  ✕  🔬 Analisis Sarf: كَتَبَ                                   │
│  ─────────────────────────────────────────────────────────────── │
│                                                                   │
│  Root: كتب │ Jenis: Fi'il Tsulatsi Mujarrad │ Bab: فتح يفتح     │
│                                                                   │
│  ┌─── اَلْمَاضِي (Past Tense) ───────────────────────────────┐   │
│  │  ┌─────────┬───────────┬──────────┬───────────┐          │   │
│  │  │         │  Mufrad   │ Mutsanna │  Jam'     │          │   │
│  │  ├─────────┼───────────┼──────────┼───────────┤          │   │
│  │  │ Ghaib   │ كَتَبَ    │ كَتَبَا  │ كَتَبُوا  │          │   │
│  │  │ Ghaibah │ كَتَبَتْ  │ كَتَبَتَا│ كَتَبْنَ   │          │   │
│  │  │ Khitab  │ كَتَبْتَ  │ كَتَبْتُمَا│ كَتَبْتُمْ│         │   │
│  │  │ Khitabah│ كَتَبْتِ  │ كَتَبْتُمَا│ كَتَبْتُنَّ│         │   │
│  │  │ Mutakallim│ كَتَبْتُ │ ─        │ كَتَبْنَا  │          │   │
│  │  └─────────┴───────────┴──────────┴───────────┘          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─── اَلْمُضَارِع (Present Tense) ──────────────────────────┐   │
│  │  ┌─────────┬───────────┬──────────┬───────────┐          │   │
│  │  │         │  Mufrad   │ Mutsanna │  Jam'     │          │   │
│  │  ├─────────┼───────────┼──────────┼───────────┤          │   │
│  │  │ Ghaib   │ يَكْتُبُ  │ يَكْتُبَانِ│ يَكْتُبُونَ│         │   │
│  │  │ Ghaibah │ تَكْتُبُ  │ تَكْتُبَانِ│ يَكْتُبْنَ │         │   │
│  │  │ Khitab  │ تَكْتُبُ  │ تَكْتُبَانِ│ تَكْتُبُونَ│         │   │
│  │  │ Khitabah│ تَكْتُبِينَ│ تَكْتُبَانِ│ تَكْتُبْنَ │         │   │
│  │  │ Mutakallim│ أَكْتُبُ │ ─        │ نَكْتُبُ   │          │   │
│  │  └─────────┴───────────┴──────────┴───────────┘          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─── اَلْأَمْر (Imperative) ───────────────────────────────┐   │
│  │  أنت: اكْتُبْ  │  أنتما: اكْتُبَا  │  أنتم: اكْتُبُوا    │   │
│  │  أنتِ: اكْتُبِي │  أنتما: اكْتُبَا  │  أنتن: اكْتُبْنَ     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─── اَلْمُشْتَقَّات (Derived Words) ─────────────────────┐   │
│  │  • Ism Fa'il:  كَاتِبٌ    (menulis — writer)            │   │
│  │  • Ism Maf'ul: مَكْتُوبٌ  (ditulis — written)          │   │
│  │  • Masdar:     كِتَابَةٌ  (tulisan — writing)          │   │
│  │  • Ism Zaman/Makan: مَكْتَبٌ (meja — desk)            │   │
│  │  • Ism Alat:   مِكْتَبٌ   (alat tulis — writing tool)  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Implementation Phases

### Phase 1: Backend — Sarf Proxy Service (2-3 hours)

| Step | Task | Files |
|:----:|---|---|
| 1 | Create `backend/sarf_client.py` — HTTP client for Sarf Docker API | `backend/sarf_client.py` |
| 2 | Implement root analysis: determine conjugation class from word form | `backend/sarf_client.py` |
| 3 | Add `POST /api/sarf/analyze` endpoint to `main.py` | `backend/main.py` |
| 4 | Add `GET /api/sarf/health` endpoint (check if Sarf container is running) | `backend/main.py` |

#### `sarf_client.py` Structure

```python
"""sarf_client.py — Client for alsaydi/sarf Arabic morphology API.

Connects to a local or remote Sarf Docker container to get verb
conjugation tables, noun derivations, and gerund forms.

Sarf runs at: http://localhost:8080 (via Docker)
"""

import httpx
from typing import Optional, Any

SARF_BASE_URL = "http://localhost:8080"

# Basic conjugation classes for triliteral roots (الأبواب الثلاثة)
# Mapping from common patterns to bab numbers
CONJUGATION_CLASSES = {
    "فَعَلَ يَفْعَلُ": 1,   # فتح يفتح
    "فَعَلَ يَفْعِلُ": 2,   # ضرب يضرب
    "فَعَلَ يَفْعُلُ": 3,   # نصر ينصر
    "فَعِلَ يَفْعَلُ": 4,   # علم يعلم
    "فَعِلَ يَفْعِلُ": 5,   # حسب يحسب
    "فَعُلَ يَفْعُلُ": 6,   # كرم يكرم
    "فَعَلَ يَفْعَلُ": 7,   # (another)
    # ... more classes
}


class SarfClient:
    """Client for the Sarf morphology REST API."""

    def __init__(self, base_url: str = SARF_BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)

    def is_available(self) -> bool:
        """Check if the Sarf Docker container is running."""
        try:
            resp = self.client.get(f"{self.base_url}/sarf/health", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def get_root_info(self, root: str) -> dict[str, Any]:
        """Get root information and available conjugation classes."""
        resp = self.client.get(f"{self.base_url}/sarf/{root}")
        resp.raise_for_status()
        return resp.json()

    def get_active_conjugation(
        self, root: str, augmented: bool = False,
        cclass: int = 1, formula: int = 0,
    ) -> dict[str, Any]:
        """Get active voice verb conjugation table."""
        resp = self.client.get(
            f"{self.base_url}/sarf/active/{root}",
            params={"augmented": str(augmented).lower(), "cclass": cclass, "formula": formula},
        )
        resp.raise_for_status()
        return resp.json()

    def get_passive_conjugation(
        self, root: str, augmented: bool = False,
        cclass: int = 1, formula: int = 0,
    ) -> dict[str, Any]:
        """Get passive voice verb conjugation table."""
        resp = self.client.get(
            f"{self.base_url}/sarf/passive/{root}",
            params={"augmented": str(augmented).lower(), "cclass": cclass, "formula": formula},
        )
        resp.raise_for_status()
        return resp.json()

    def get_nouns(self, root: str, augmented: bool = False, cclass: int = 1) -> dict[str, Any]:
        """Get all derived noun forms for a root."""
        resp = self.client.get(
            f"{self.base_url}/sarf/nouns/{root}",
            params={"augmented": str(augmented).lower(), "cclass": cclass},
        )
        resp.raise_for_status()
        return resp.json()

    def get_gerunds(self, root: str, augmented: bool = False, cclass: int = 1) -> dict[str, Any]:
        """Get gerund/masdar forms for a root."""
        resp = self.client.get(
            f"{self.base_url}/sarf/gerunds/{root}",
            params={"augmented": str(augmented).lower(), "cclass": cclass},
        )
        resp.raise_for_status()
        return resp.json()

    def analyze_word(self, root: str, word: str = "", pos_type: str = "verb") -> dict[str, Any]:
        """Full morphological analysis: determine class, then fetch all conjugation data."""
        # Step 1: Get root info to find available classes
        root_info = self.get_root_info(root)

        # Step 2: Determine the best conjugation class from the word form
        cclass = self._determine_class(root, word, pos_type, root_info)

        # Step 3: Fetch conjugation data
        result = {
            "root": root,
            "conjugation_class": cclass,
            "pos_type": pos_type,
            "is_augmented": len(root) > 3,
        }

        if pos_type == "verb":
            result["active"] = self.get_active_conjugation(root, augmented=False, cclass=cclass)
            try:
                result["passive"] = self.get_passive_conjugation(root, augmented=False, cclass=cclass)
            except Exception:
                result["passive"] = None
            result["nouns"] = self.get_nouns(root, augmented=False, cclass=cclass)
            result["gerunds"] = self.get_gerunds(root, augmented=False, cclass=cclass)
        elif pos_type == "noun":
            result["conjugation"] = self.get_nouns(root, augmented=False, cclass=cclass)

        return result

    def _determine_class(self, root: str, word: str, pos_type: str, root_info: dict) -> int:
        """Determine the conjugation class/bab from the word form."""
        # Logic: analyze the word's pattern to determine which bab it follows
        # For now, default to class 1 (فتح يفتح) — the most common
        # Future: implement pattern matching against known bab patterns
        return 1
```

### Phase 2: Backend — API Endpoint (1 hour)

Add to `backend/main.py`:

```python
# ── Sarf models ──

class SarfAnalyzeRequest(BaseModel):
    root: str          # e.g., "كتب"
    word: str = ""     # e.g., "يَكْتُبُ" (for class detection)
    pos_type: str = "verb"  # "verb" or "noun"

class SarfAnalyzeResponse(BaseModel):
    root: str
    word: str
    pos_type: str
    conjugation_class: int
    is_augmented: bool
    active: Optional[dict] = None       # Verb conjugation tables
    passive: Optional[dict] = None
    nouns: Optional[dict] = None        # Derived nouns
    gerunds: Optional[dict] = None      # Masdar forms
    classification: str = ""            # e.g., "Fi'il Tsulatsi Mujarrad"
    bab_name: str = ""                  # e.g., "فتح يفتح"

# ── Sarf endpoint ──

SARF_CLIENT: Optional[SarfClient] = None
_sarf_lock = threading.Lock()

def get_sarf_client() -> Optional[SarfClient]:
    """Get the Sarf client singleton (lazy init)."""
    global SARF_CLIENT
    if SARF_CLIENT is not None:
        return SARF_CLIENT
    with _sarf_lock:
        if SARF_CLIENT is not None:
            return SARF_CLIENT
        try:
            from sarf_client import SarfClient
            client = SarfClient()
            if client.is_available():
                SARF_CLIENT = client
                return SARF_CLIENT
        except Exception:
            pass
    return None

@app.post("/api/sarf/analyze", response_model=SarfAnalyzeResponse)
def sarf_analyze(request: SarfAnalyzeRequest):
    """Analyze a word using the Sarf morphology system.

    Requires the Sarf Docker container to be running on port 8080.
    Returns verb conjugation tables, derived nouns, and grammatical
    classification.
    """
    client = get_sarf_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Sarf morphology service is not available. "
                   "Run: docker run --rm -p 8080:8080 alsaydi/sarf:1.4"
        )

    result = client.analyze_word(
        root=request.root,
        word=request.word or request.root,
        pos_type=request.pos_type,
    )

    return SarfAnalyzeResponse(
        root=result["root"],
        word=request.word or request.root,
        pos_type=request.pos_type,
        conjugation_class=result.get("conjugation_class", 1),
        is_augmented=result.get("is_augmented", False),
        active=result.get("active"),
        passive=result.get("passive"),
        nouns=result.get("nouns"),
        gerunds=result.get("gerunds"),
        classification=_classify_verb(request.root, request.pos_type, result.get("conjugation_class", 1)),
        bab_name=_get_bab_name(result.get("conjugation_class", 1)),
    )

def _classify_verb(root: str, pos_type: str, cclass: int) -> str:
    """Generate Arabic classification string."""
    if pos_type != "verb":
        return ""
    if len(root) == 3:
        return f"فعل ثلاثي مجرد (باب {cclass})"
    elif len(root) == 4:
        return "فعل رباعي مجرد"
    else:
        return f"فعل (جذر: {root})"

def _get_bab_name(cclass: int) -> str:
    """Get the Arabic bab name for a conjugation class."""
    BAB_NAMES = {
        1: "فَعَلَ يَفْعَلُ (فتح يفتح)",
        2: "فَعَلَ يَفْعِلُ (ضرب يضرب)",
        3: "فَعَلَ يَفْعُلُ (نصر ينصر)",
        4: "فَعِلَ يَفْعَلُ (علم يعلم)",
        5: "فَعِلَ يَفْعِلُ (حسب يحسب)",
        6: "فَعُلَ يَفْعُلُ (كرم يكرم)",
    }
    return BAB_NAMES.get(cclass, f"Bab {cclass}")
```

### Phase 3: Frontend — Button + Modal (2-3 hours)

| Step | Task | Files |
|:----:|---|---|
| 5 | Add 🔬 button to "Detail Lengkap" table rows | `frontend/pages/index.vue` |
| 6 | Create Sarf modal component with conjugation tables | `frontend/pages/index.vue` or `frontend/components/SarfModal.vue` |
| 7 | Add `sarfAnalyze()` function to call new endpoint | `frontend/pages/index.vue` |
| 8 | Add Sarf health check on page load | `frontend/pages/index.vue` |

### Phase 4: Polish & Refinement (1-2 hours)

| Step | Task |
|:----:|---|
| 9 | Add loading states and error handling for Sarf API |
| 10 | Cache Sarf results (per root) to avoid redundant API calls |
| 11 | Add "Sarf available" indicator in the UI header |
| 12 | Handle edge cases: non-Arabic words, unknown roots, non-conjugable words |

---

## 9. Dependencies & Setup

### Required Components

| Component | Installation | Purpose |
|---|---|---|
| **Docker Desktop** | [docker.com](https://www.docker.com/products/docker-desktop/) | Run Sarf container |
| **alsaydi/sarf:1.4** | `docker pull alsaydi/sarf:1.4` | Sarf morphology engine |
| **httpx** (Python) | `pip install httpx` | Async HTTP client for Sarf API |

### Docker Setup

```bash
# Pull and run Sarf
docker pull alsaydi/sarf:1.4
docker run --rm -p 8080:8080 alsaydi/sarf:1.4

# Verify it's running
curl http://localhost:8080/sarf/كتب
# Should return HTML (Angular SPA)  OR  JSON if API responds directly
```

### Python Dependency

```bash
pip install httpx
```

### Startup Script Update

Update `start.bat` to optionally launch Sarf:

```batch
REM Optional: Start Sarf Docker container
echo [Optional] Starting Sarf morphology engine...
docker start sarf-container 2>nul || docker run -d --name sarf-container -p 8080:8080 alsaydi/sarf:1.4
timeout /t 5 /nobreak >nul
```

---

## 10. Risks & Challenges

### Risk Matrix

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| **Docker dependency** — user needs Docker installed | Medium | High | Make Sarf optional; app works without it, only 🔬 button is disabled |
| **Conjugation class detection** — determining the correct bab from word form | High | Medium | Start with basic pattern matching; add manual class override in UI |
| **Sarf API response schema unknown** — exact JSON structure not documented | Medium | High | Test with live Docker container first; build flexible parser |
| **Java/Spring Boot resource usage** — Sarf container uses ~1-2GB RAM | Medium | Medium | Document system requirements; lazy-load only when user clicks 🔬 |
| **Incomplete root coverage** — some classical/rare roots may not be in Sarf DB | Low | Low | Show graceful "Root not found" message; allow fallback to basic analysis |
| **Performance** — multiple API calls per word (active, passive, nouns, gerunds) | Low | Medium | Cache results per root; parallel API calls with httpx async |

### Key Unknowns

Before full implementation, these need to be resolved:

1. **Exact API schema** — Run `docker run --rm -p 8080:8080 alsaydi/sarf:1.4` and test:
   - `curl http://localhost:8080/sarf/كتب` → what JSON does the root discovery endpoint return?
   - Does the API return JSON or HTML? (The Angular UI is at `/`, API may be at a different prefix)
   - What are the exact parameter names and formats?

2. **CORS configuration** — The Spring Boot controller is configured for CORS with `sarf.one` and `localhost`. May need to add our frontend origin or use a backend proxy.

3. **Augmented verb handling** — How to detect if a word is augmented (مزيد) vs. simple (مجرّد)?

### Strategies for Class Detection

Determining the conjugation class (باب) from the input word form:

```python
def detect_bab(root: str, word: str) -> int:
    """Detect conjugation class from the word's vowel pattern."""
    # Remove any prefixes (ي, ت, أ, ن, س, etc.)
    # Analyze the remaining pattern against known bab patterns
    # For initial implementation, default to bab 1 (most common)
    # Future: use pattern matching
    
    # Known patterns for mudhari' (present tense):
    # يَفْعَلُ → bab 1 (فتح)
    # يَفْعِلُ → bab 2 (كسر)
    # يَفْعُلُ → bab 3 (ضم)
    # يَفْعَلُ (with kasra on عين in madhi) → bab 4 (علم)
    pass
```

**Alternative:** Show all available bab options to the user and let them select:

```
🔬 Analisis Sarf: كَتَبَ
Pilih Bab:
○ Bab 1: فتح يفتح (most likely) ← default
○ Bab 2: ضرب يضرب
○ Bab 3: نصر ينصر
○ Bab 4: علم يعلم
○ Bab 5: حسب يحسب
○ Bab 6: كرم يكرم
```

---

## 11. Files to Create/Modify

| File | Action | Purpose |
|---|---|---|
| `backend/sarf_client.py` | **Create** | HTTP client for Sarf Docker API |
| `backend/main.py` | **Modify** | Add `POST /api/sarf/analyze` endpoint + models |
| `frontend/pages/index.vue` | **Modify** | Add 🔬 button to Detail Lengkap table + Sarf modal |
| `frontend/components/SarfModal.vue` | **Create** | Reusable Sarf morphology modal component |
| `frontend/package.json` | **Modify** | Add any new frontend dependencies (optional) |
| `docs/SARF_ASSESSMENT.md` | **Create** | This document |
| `start.bat` | **Modify** | Optional: auto-start Sarf Docker container |

---

## 12. Final Verdict

| Question | Answer |
|---|---|
| **Is Sarf a good fit for this app?** | ✅ **Excellent fit** — Sarf provides exactly what's missing: full verb conjugation tables and noun derivation based on the root that CAMeL Tools already extracts |
| **Does Sarf complement CAMeL Tools?** | ✅ **Yes** — CAMeL handles diacritization + POS tagging; Sarf handles deep morphology + conjugation |
| **Is the Docker dependency a problem?** | ⚠️ **Manageable** — Make it optional; the app works without it, only the 🔬 button is disabled |
| **How hard is the integration?** | ⭐⭐⭐ **Medium** — ~6-8 hours total for all 4 phases |
| **Is there a lighter alternative?** | ❌ **No** — No Python library provides equivalent coverage. Qalsadi has basic POS but no conjugation tables |
| **Is the API documented?** | ⚠️ **Partially** — Source code is available on GitHub; exact JSON schema needs to be reverse-engineered from the Docker container |

### Recommendation

**Proceed with Phase 1 first** — Create `sarf_client.py` with the basic client and test against the actual Docker container to reverse-engineer the API schema. This de-risks the entire integration before investing in the frontend UI.

**Make Sarf optional** — The 🔬 button should be gracefully disabled (grayed out) when the Sarf container is not running, with a tooltip: "Jalankan Docker Sarf untuk fitur ini" (Run Sarf Docker for this feature).

**Use a backend proxy** — Rather than calling Sarf directly from the frontend (CORS issues), always proxy through the Python backend. This also allows caching, error handling, and adding Indonesian/English translation overlays to Sarf results.

### Effort Estimate

| Phase | Hours | Dependencies |
|---|---|---|
| Phase 1: Backend client + API probing | 2-3 | Docker + Sarf container running |
| Phase 2: API endpoint + models | 1 | Phase 1 complete |
| Phase 3: Frontend button + modal | 2-3 | Phase 2 complete |
| Phase 4: Polish + error handling | 1-2 | Phase 3 complete |
| **Total** | **6-9 hours** | |

---

*Assessment prepared by researching the [alsaydi/sarf](https://github.com/alsaydi/sarf) repository, analyzing the [sarf.one](https://sarf.one/) demo, reviewing the existing Penerjemah Kitab codebase (CAMeL Tools integration, analyze_words function, Detail Lengkap UI), and assessing the Arabic NLP Python ecosystem.*
