# Development Breakdown: Incremental Tasks (PWA Approach)
## "Scholar's Kitab" Arabic → Indonesian Translation App

**Architecture:** Python backend API (FastAPI) + Nuxt.js frontend with Tailwind CSS.
**Philosophy:** Every step produces a working feature you can test in your browser via the PWA.

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                   Your Machine (localhost)                        │
│                                                                  │
│  ┌──────────────────────┐       ┌──────────────────────────────┐ │
│  │   Frontend (PWA)     │       │   Backend API                │ │
│  │                      │       │                              │ │
│  │   Nuxt.js + Tailwind │◄─────►│   Python FastAPI             │ │
│  │   Port: 3000         │  REST │   Port: 8000                 │ │
│  │                      │  JSON │                              │ │
│  │   - Paste Arabic     │       │   - Mishkal (tashkeel)       │ │
│  │   - See harakat      │       │   - Qalsadi (analysis)       │ │
│  │   - Word-by-word     │       │   - CAMeL Tools (grammar)    │ │
│  │   - Scholar display  │       │   - NLLB-200 (translation)   │ │
│  │   - PWA (offline)    │       │   - Dictionary (gloss)       │ │
│  └──────────────────────┘       └──────────────────────────────┘ │
│                                                                  │
│  Run with:                        Run with:                      │
│  npm run dev                      uvicorn main:app --reload      │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🗺️ The Big Picture

```
Step 1:  Setup project         ────►  Nuxt + Tailwind + FastAPI running
Step 2:  Backend tashkeel      ────►  POST /api/tashkeel returns harakat
Step 3:  Frontend tashkeel     ────►  Paste Arabic → see harakat in PWA
Step 4:  + Tokenize words      ────►  Also see words in cards/boxes
Step 5:  + Analyze words       ────►  Also see fi'il/isim/harf + lemma
Step 6:  + Word gloss          ────►  Also see Indonesian per word
Step 7:  + Full translation    ────►  Also see NLLB-200 sentence translation
Step 8:  + Scholar display     ────►  Beautiful kitab-style layout
Step 9:  + PWA features        ────►  Installable, offline, manifest
Step 10: + Package & polish    ────►  Production-ready
```

---

## ✅ Step 1: Project Setup

**Goal:** Both backend and frontend projects created and running.

**Terminals needed (2):**
- **Terminal 1:** Backend API (Python FastAPI)
- **Terminal 2:** Frontend (Nuxt.js)

### Tasks

#### 1A. Create Backend Project Structure

- [ ] 1A.1 Create the backend directory:

```bash
mkdir -p backend
cd backend
```

- [ ] 1A.2 Install Python packages:

```bash
pip install fastapi uvicorn mishkal pyarabic qalsadi
```

- [ ] 1A.3 Create `backend/main.py`:

```python
# backend/main.py — Step 1: Tashkeel API only

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mishkal.tashkeel import TashkeelClass

app = FastAPI(title="Penerjemah Kitab API")

# Allow frontend (localhost:3000) to call backend (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Mishkal once (heavy initialization)
vocalizer = TashkeelClass()


class TashkeelRequest(BaseModel):
    text: str


class TashkeelResponse(BaseModel):
    original: str
    harakat: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/tashkeel", response_model=TashkeelResponse)
def tashkeel(request: TashkeelRequest):
    """Add harakat (diacritics) to Arabic text."""
    result = vocalizer.tashkeel(request.text)
    return TashkeelResponse(original=request.text, harakat=result)
```

- [ ] 1A.4 **Test the backend:**

```bash
cd backend
uvicorn main:app --reload --port 8000
```

- [ ] 1A.5 Open http://localhost:8000/docs — you should see Swagger UI
- [ ] 1A.6 Test the API: Click `POST /api/tashkeel` → "Try it out" → enter `{"text": "يكتب الطالب الدرس في المكتبة"}` → Execute
- [ ] 1A.7 ✅ **Done when:** You see the response with `harakat` field containing diacritized text

#### 1B. Create Frontend Project (Nuxt + Tailwind)

- [ ] 1B.1 Open a **new terminal** and create the Nuxt project:

```bash
npx nuxi@latest init frontend
```

When prompted:
- Package manager: `npm`
- Choose defaults for all questions

- [ ] 1B.2 Install Tailwind CSS:

```bash
cd frontend
npm install @nuxtjs/tailwindcss
```

- [ ] 1B.3 Add to `nuxt.config.ts`:

```ts
export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss'],
})
```

- [ ] 1B.4 Create `frontend/tailwind.config.ts`:

```ts
export default {
  content: [
    "./components/**/*.{js,vue,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./app.vue",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

- [ ] 1B.5 Test the frontend:

```bash
cd frontend
npm run dev
```

- [ ] 1B.6 Open http://localhost:3000 — you should see a blank Nuxt page
- [ ] 1B.7 ✅ **Done when:** Both servers are running:
  - Backend: http://localhost:8000/docs (Swagger UI)
  - Frontend: http://localhost:3000 (Nuxt page)

---

## ✅ Step 2: Frontend — Tashkeel Page

**Goal:** A proper PWA page where you paste Arabic text and see harakat.

**File:** `frontend/pages/index.vue`

### Tasks

- [ ] 2.1 Create/update `frontend/pages/index.vue`:

```vue
<template>
  <div class="min-h-screen bg-amber-50">
    <header class="bg-emerald-800 text-white py-6 shadow-lg">
      <div class="max-w-4xl mx-auto px-4">
        <h1 class="text-3xl font-bold text-center">📖 Penerjemah Kitab</h1>
        <p class="text-emerald-200 text-center mt-1">Langkah 1: Tashkeel (Harakat)</p>
      </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-8">
      <!-- Input -->
      <div class="bg-white rounded-xl shadow-md p-6 mb-6">
        <label class="block text-lg font-semibold text-gray-700 mb-2">
          Masukkan teks Arab:
        </label>
        <textarea
          v-model="inputText"
          placeholder="يكتب الطالب الدرس في المكتبة..."
          class="w-full h-32 p-4 border-2 border-amber-200 rounded-lg text-lg
                 focus:border-emerald-500 focus:outline-none resize-y
                 font-arabic"
          dir="rtl"
        ></textarea>

        <button
          @click="getTashkeel"
          :disabled="loading || !inputText.trim()"
          class="mt-4 w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300
                 text-white font-bold py-3 px-6 rounded-lg transition-colors
                 text-lg"
        >
          <span v-if="loading">⏳ Memproses...</span>
          <span v-else>🌟 Beri Harakat</span>
        </button>
      </div>

      <!-- Error -->
      <div
        v-if="error"
        class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6"
      >
        {{ error }}
      </div>

      <!-- Result -->
      <div v-if="result" class="bg-white rounded-xl shadow-md p-6">
        <h2 class="text-xl font-bold text-gray-700 mb-4">✅ Hasil</h2>

        <div class="grid md:grid-cols-2 gap-6">
          <!-- Before -->
          <div>
            <p class="text-sm text-gray-500 mb-2">Sebelum:</p>
            <div
              class="bg-gray-50 rounded-lg p-4 text-right"
              dir="rtl"
            >
              <p class="text-2xl">{{ result.original }}</p>
            </div>
          </div>

          <!-- After -->
          <div>
            <p class="text-sm text-gray-500 mb-2">Sesudah (dengan Harakat):</p>
            <div
              class="bg-emerald-50 border-2 border-emerald-200 rounded-lg p-4 text-right"
              dir="rtl"
            >
              <p class="text-2xl text-emerald-700 font-arabic">{{ result.harakat }}</p>
            </div>
          </div>
        </div>

        <!-- Copy button -->
        <button
          @click="copyResult"
          class="mt-4 bg-amber-100 hover:bg-amber-200 text-amber-800
                 font-medium py-2 px-4 rounded-lg transition-colors"
        >
          📋 Salin Teks
        </button>
      </div>
    </main>

    <footer class="text-center text-gray-400 text-sm py-6">
      Penerjemah Kitab — Dibangun langkah demi langkah
    </footer>
  </div>
</template>

<script setup>
const inputText = ref('')
const result = ref(null)
const loading = ref(false)
const error = ref(null)

async function getTashkeel() {
  loading.value = true
  error.value = null
  result.value = null

  try {
    const res = await fetch('http://localhost:8000/api/tashkeel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: inputText.value }),
    })
    if (!res.ok) throw new Error(`Error: ${res.status}`)
    result.value = await res.json()
  } catch (e) {
    error.value = e.message || 'Gagal menghubungi server'
  } finally {
    loading.value = false
  }
}

async function copyResult() {
  if (result.value?.harakat) {
    await navigator.clipboard.writeText(result.value.harakat)
    alert('Teks berhasil disalin!')
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap');

.font-arabic {
  font-family: 'Amiri', 'Traditional Arabic', serif;
}
</style>
```

- [ ] 2.2 **Test it:** Make sure both servers are running:
  - Terminal 1: `cd backend && uvicorn main:app --reload --port 8000`
  - Terminal 2: `cd frontend && npm run dev`

- [ ] 2.3 Open http://localhost:3000
- [ ] 2.4 Paste Arabic text and click "Beri Harakat"
- [ ] 2.5 ✅ **Done when:** You see:
  - Before (original text) on the left
  - After (with harakat) on the right
  - Copy button works

---

## ✅ Step 3: Backend — Add Tokenization & Word Analysis

**Goal:** The API returns not just harakat, but also tokenized words with analysis.

**File:** `backend/main.py` (add to it)

### Tasks

- [ ] 3.1 Open `backend/main.py` and add the following **at the top (after the existing imports)**:

```python
from pyarabic.araby import tokenize
from qalsadi.lemmatizer import Lemmatizer
```

- [ ] 3.2 **After the `vocalizer = TashkeelClass()` line**, add:

```python
lemmer = Lemmatizer()
```

- [ ] 3.3 **Before the `@app.get`/`@app.post` decorators**, add these new Pydantic models:

```python
class AnalyzeRequest(BaseModel):
    text: str

class WordAnalysis(BaseModel):
    word: str
    lemma: str
    root: str
    pos_type: str
    pos_arabic: str

class AnalyzeResponse(BaseModel):
    original: str
    harakat: str
    words: list[WordAnalysis]
    word_count: int
```

- [ ] 3.4 **At the end of the file (after the tashkeel endpoint)**, add the new endpoint:

```python
@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    """Get harakat + word-by-word analysis."""
    harakat_text = vocalizer.tashkeel(request.text)
    words = tokenize(harakat_text)

    word_list = []
    for w in words:
        analysis = lemmer.lemmatize_text(w, return_pos=True)
        if analysis:
            lemma = analysis[0][1]
            pos_info = analysis[0][2]
            pos_type = pos_info.get('type', 'unknown') if isinstance(pos_info, dict) else 'unknown'
            root = pos_info.get('root', '—') if isinstance(pos_info, dict) else '—'
        else:
            lemma = root = '—'
            pos_type = 'unknown'

        pos_map = {'noun': 'إسم', 'verb': 'فعل', 'stopword': 'حرف'}
        pos_arabic = pos_map.get(pos_type, pos_type)

        word_list.append(WordAnalysis(
            word=w,
            lemma=lemma,
            root=root,
            pos_type=pos_type,
            pos_arabic=pos_arabic,
        ))

    return AnalyzeResponse(
        original=request.text,
        harakat=harakat_text,
        words=word_list,
        word_count=len(word_list),
    )
```

- [ ] 3.2 Restart the backend (it auto-restarts with `--reload`)
- [ ] 3.3 Test at http://localhost:8000/docs → `POST /api/analyze`
- [ ] 3.4 ✅ **Done when:** The response includes `words` array with `word`, `lemma`, `root`, `pos_type`, `pos_arabic`

---

## ✅ Step 4: Frontend — Show Word Analysis

**Goal:** The PWA shows each word in a card with its lemma, root, and type (Isim/Fi'il/Harf).

**File:** `frontend/pages/index.vue` (update)

### Tasks

- [ ] 4.1 Update the page to use `/api/analyze` instead of `/api/tashkeel`
- [ ] 4.2 Add word cards display below the harakat result:

```vue
<!-- Add after the result section, inside the v-if="result" block -->

<div v-if="result.words" class="mt-8">
  <h3 class="text-lg font-bold text-gray-700 mb-4">📝 Kata Per Kata</h3>

  <div class="flex flex-wrap gap-3 justify-center">
    <div
      v-for="(word, i) in result.words"
      :key="i"
      class="bg-white border-2 border-emerald-300 rounded-xl p-4 text-center min-w-[120px]
             shadow-sm hover:shadow-md transition-shadow"
    >
      <!-- Arabic word -->
      <p class="text-xl font-arabic" dir="rtl">{{ word.word }}</p>

      <!-- Divider -->
      <hr class="my-2 border-emerald-100">

      <!-- Lemma -->
      <p class="text-sm font-semibold text-emerald-700">{{ word.lemma }}</p>

      <!-- Root -->
      <p class="text-xs text-gray-400">({{ word.root }})</p>

      <!-- POS type -->
      <span
        class="inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-bold"
        :class="posClass(word.pos_type)"
      >
        {{ word.pos_arabic }}
      </span>
    </div>
  </div>
</div>
```

- [ ] 4.3 Add the `posClass` function in the script:

```ts
function posClass(type: string) {
  const map: Record<string, string> = {
    'noun': 'bg-blue-100 text-blue-700',
    'verb': 'bg-orange-100 text-orange-700',
    'stopword': 'bg-purple-100 text-purple-700',
  }
  return map[type] || 'bg-gray-100 text-gray-700'
}
```

- [ ] 4.4 ✅ **Test in browser:** Refresh http://localhost:3000, paste Arabic, click button
- [ ] 4.5 ✅ **Done when:** Each word shows in a card with:
  - Arabic word (large)
  - Lemma
  - Root in parentheses
  - Colored badge: إسم (blue) / فعل (orange) / حرف (purple)

---

## ✅ Step 5: Backend — Add Word Gloss (Dictionary)

**Goal:** The API returns Indonesian translations for each word.

**File:** `backend/dictionary.py` (new) + `backend/main.py` (update)

### Tasks

- [ ] 5.1 Create `backend/dictionary.py` with this content (100+ entries ready to use):

<details>
<summary>📁 Click to expand dictionary.py (100+ entries)</summary>

```python
# backend/dictionary.py — Arabic → Indonesian word dictionary
# Add words here! Each entry: 'lemma_vocalized': 'terjemahan'

ARABIC_INDONESIAN = {
    # Kata Kerja (Fi'il)
    'كَتَبَ': 'menulis',
    'قَرَأَ': 'membaca',
    'فَتَحَ': 'membuka',
    'أَغْلَقَ': 'menutup',
    'ذَهَبَ': 'pergi',
    'جَاءَ': 'datang',
    'دَخَلَ': 'masuk',
    'خَرَجَ': 'keluar',
    'جَلَسَ': 'duduk',
    'وَقَفَ': 'berdiri',
    'أَكَلَ': 'makan',
    'شَرِبَ': 'minum',
    'رَجَعَ': 'kembali',
    'ضَرَبَ': 'memukul',
    'عَلِمَ': 'mengetahui',
    'قَالَ': 'berkata',
    'كَانَ': 'adalah',
    'جَعَلَ': 'menjadikan',
    'رَأَى': 'melihat',
    'سَمِعَ': 'mendengar',

    # Kata Benda (Isim)
    'طَالِبٌ': 'siswa',
    'طَالِبَةٌ': 'siswi',
    'مُدَرِّسٌ': 'pengajar',
    'أُسْتَاذٌ': 'guru',
    'دَرْسٌ': 'pelajaran',
    'مَكْتَبَةٌ': 'perpustakaan',
    'مَدْرَسَةٌ': 'sekolah',
    'كِتَابٌ': 'buku',
    'قَلَمٌ': 'pena',
    'بَابٌ': 'pintu',
    'مِفْتَاحٌ': 'kunci',
    'كُرْسِيٌّ': 'kursi',
    'مَكْتَبٌ': 'meja',
    'فَصْلٌ': 'kelas',
    'وَلَدٌ': 'anak laki',
    'بِنْتٌ': 'anak perempuan',
    'رَجُلٌ': 'laki-laki',
    'اِمْرَأَةٌ': 'perempuan',
    'بَيْتٌ': 'rumah',
    'مَسْجِدٌ': 'masjid',
    'قَمَرٌ': 'bulan',
    'شَمْسٌ': 'matahari',
    'مَاءٌ': 'air',
    'نَارٌ': 'api',
    'رَأْسٌ': 'kepala',
    'يَدٌ': 'tangan',
    'رِجْلٌ': 'kaki',
    'عَيْنٌ': 'mata',
    'قَلْبٌ': 'hati',
    'يَوْمٌ': 'hari',
    'لَيْلَةٌ': 'malam',

    # Huruf / Preposisi (Harf)
    'فِي': 'di',
    'عَلَى': 'di atas',
    'مِنْ': 'dari',
    'إِلَى': 'ke',
    'عَنْ': 'tentang',
    'بِ': 'dengan',
    'لِ': 'untuk',
    'كَ': 'seperti',
    'وَ': 'dan',
    'فَ': 'maka',
    'ثُمَّ': 'kemudian',
    'أَوْ': 'atau',
    'لَا': 'tidak',
    'قَدْ': 'sungguh',
    'سَوْفَ': 'akan',
    'هَلْ': 'apakah',
    'أَنَّ': 'bahwa',
    'إِنَّ': 'sesungguhnya',
    'لَيْسَ': 'bukan',

    # Kata Tanya
    'مَنْ': 'siapa',
    'مَا': 'apa',
    'أَيْنَ': 'di mana',
    'كَيْفَ': 'bagaimana',
    'لِمَاذَا': 'mengapa',
    'مَتَى': 'kapan',
    'كَمْ': 'berapa',

    # Lain-lain
    'هَذَا': 'ini',
    'هَذِهِ': 'ini (pr)',
    'ذَلِكَ': 'itu',
    'تِلْكَ': 'itu (pr)',
    'نَعَمْ': 'ya',
    'كَلَّا': 'tidak',
    'جِدًّا': 'sangat',
    'فَقَطْ': 'saja',
}


def lookup(lemma: str) -> str:
    """Look up Indonesian translation for an Arabic lemma."""
    if lemma in ARABIC_INDONESIAN:
        return ARABIC_INDONESIAN[lemma]
    from pyarabic.araby import strip_tashkeel
    stripped = strip_tashkeel(lemma)
    for key, val in ARABIC_INDONESIAN.items():
        if strip_tashkeel(key) == stripped:
            return f"{val}?"
    return f"???"


def size() -> int:
    return len(ARABIC_INDONESIAN)
```
</details>

- [ ] 5.2 Update `backend/main.py` — add the import at the top with the other imports:

```python
# Add this at the TOP of main.py (after existing imports):
from dictionary import lookup
```

- [ ] 5.3 Also update the `WordAnalysis` model in `backend/main.py` to include a gloss field:

```python
class WordAnalysis(BaseModel):
    word: str
    lemma: str
    root: str
    pos_type: str
    pos_arabic: str
    gloss: str = ""   # ← add this line
```

- [ ] 5.4 And in the `analyze` endpoint, inside the word loop add:

```python
gloss = lookup(lemma)  # ← add after `root = ...`

# Then add to WordAnalysis construction:
word_list.append(WordAnalysis(
    word=w,
    lemma=lemma,
    root=root,
    pos_type=pos_type,
    pos_arabic=pos_arabic,
    gloss=gloss,  # ← add this line
))
```

- [ ] 5.5 ✅ **Test:** Restart backend, refresh frontend
- [ ] 5.6 ✅ **Done when:** Each word card shows the Indonesian translation below it

---

## ✅ Step 6: Backend — Add NLLB-200 Translation

**Goal:** Full sentence translation using NLLB-200.

**File:** `backend/main.py`

### Tasks

- [ ] 6.1 Install: `pip install transformers torch sentencepiece`
- [ ] 6.2 Add NLLB translation endpoint:

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Load NLLB (first time downloads ~1.2GB)
nllb_model_name = "facebook/nllb-200-distilled-600M"
nllb_tokenizer = AutoTokenizer.from_pretrained(nllb_model_name)
nllb_model = AutoModelForSeq2SeqLM.from_pretrained(nllb_model_name)

class TranslateRequest(BaseModel):
    text: str

class TranslateResponse(BaseModel):
    source: str
    translation: str

@app.post("/api/translate")
def translate(request: TranslateRequest):
    """Full Arabic → Indonesian translation."""
    nllb_tokenizer.src_lang = "arb_Arab"
    inputs = nllb_tokenizer(request.text, return_tensors="pt", truncation=True, max_length=512)
    translated = nllb_model.generate(
        **inputs,
        forced_bos_token_id=nllb_tokenizer.convert_tokens_to_ids("ind_Latn"),
        max_length=512,
    )
    result = nllb_tokenizer.batch_decode(translated, skip_special_tokens=True)[0]
    return TranslateResponse(source=request.text, translation=result)
```

- [ ] 6.3 ✅ **Test:** Restart backend, test at `/api/translate`
- [ ] 6.4 ✅ **Done when:** API returns proper Indonesian translation for Arabic input

---

## ✅ Step 7: Frontend — Scholar Display

**Goal:** Beautiful kitab-style layout like a scholar's book.

**File:** `frontend/pages/index.vue`

### Tasks

- [ ] 7.1 Redesign the result section to look like a traditional kitab:

```vue
<!-- Scholar-style word table -->
<div v-if="result.words" class="mt-8 bg-amber-50 border border-amber-300 rounded-xl p-6">
  <h3 class="text-center text-amber-800 font-bold text-lg mb-6">📜 Analisis Kata Per Kata</h3>

  <!-- Row 1: Arabic words (traditional font) -->
  <div class="flex justify-center gap-4 flex-wrap">
    <div v-for="(word, i) in result.words" :key="i" class="text-center">
      <p class="text-3xl font-arabic text-amber-900" dir="rtl">{{ word.word }}</p>
    </div>
  </div>

  <!-- Decorative line -->
  <div class="border-t-2 border-amber-700 my-4"></div>

  <!-- Row 2: Gloss -->
  <div class="flex justify-center gap-4 flex-wrap">
    <div v-for="(word, i) in result.words" :key="'g'+i" class="text-center min-w-[100px]">
      <p class="text-sm italic text-emerald-700">{{ word.gloss }}</p>
    </div>
  </div>

  <!-- Row 3: POS type -->
  <div class="flex justify-center gap-4 flex-wrap mt-2">
    <div v-for="(word, i) in result.words" :key="'p'+i" class="text-center min-w-[100px]">
      <span class="text-xs font-bold" :class="posTextClass(word.pos_type)">
        {{ word.pos_arabic }}
      </span>
    </div>
  </div>

  <!-- Row 4: Root -->
  <div class="flex justify-center gap-4 flex-wrap mt-1">
    <div v-for="(word, i) in result.words" :key="'r'+i" class="text-center min-w-[100px]">
      <p class="text-xs text-gray-400">{{ word.root }}</p>
    </div>
  </div>

  <!-- Detail expandable table -->
  <details class="mt-6">
    <summary class="cursor-pointer text-amber-700 hover:text-amber-900 font-medium">
      📋 Lihat detail lengkap
    </summary>
    <div class="mt-4 overflow-x-auto">
      <table class="w-full text-sm bg-white rounded-lg">
        <thead>
          <tr class="bg-amber-100">
            <th class="p-2">#</th>
            <th class="p-2">Arab</th>
            <th class="p-2">Lemma</th>
            <th class="p-2">Akar</th>
            <th class="p-2">Jenis</th>
            <th class="p-2">Indonesia</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(word, i) in result.words" :key="'t'+i" class="border-t">
            <td class="p-2 text-center">{{ i + 1 }}</td>
            <td class="p-2 text-center font-arabic" dir="rtl">{{ word.word }}</td>
            <td class="p-2 text-center">{{ word.lemma }}</td>
            <td class="p-2 text-center text-gray-400">{{ word.root }}</td>
            <td class="p-2 text-center">{{ word.pos_arabic }}</td>
            <td class="p-2 text-center text-emerald-700">{{ word.gloss }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </details>
</div>
```

- [ ] 7.2 Add `posTextClass` function:

```ts
function posTextClass(type: string) {
  const map: Record<string, string> = {
    'noun': 'text-blue-600',
    'verb': 'text-orange-600',
    'stopword': 'text-purple-600',
  }
  return map[type] || 'text-gray-600'
}
```

- [ ] 7.3 ✅ **Test:** Refresh frontend
- [ ] 7.4 ✅ **Done when:** The display looks like a traditional kitab with:
  - Large Arabic text with traditional font
  - Green gloss below each word
  - Colored POS type below
  - Root in gray
  - Expandable detail table

---

## ✅ Step 8: Full Translation Display

**Goal:** Show the complete sentence translation below the word analysis.

### Tasks

- [ ] 8.1 Add translation section in frontend:

```vue
<div v-if="result.translation" class="mt-6 bg-white rounded-xl shadow-md p-6">
  <h3 class="text-lg font-bold text-gray-700 mb-4">🌟 Terjemahan Lengkap</h3>
  <div class="grid md:grid-cols-2 gap-4">
    <div>
      <p class="text-sm text-gray-500">Teks Arab:</p>
      <p class="text-xl font-arabic text-right" dir="rtl">{{ result.harakat }}</p>
    </div>
    <div>
      <p class="text-sm text-gray-500">Terjemahan:</p>
      <p class="text-xl text-blue-700">{{ result.translation }}</p>
    </div>
  </div>
</div>
```

- [ ] 8.2 Update the API call to also hit `/api/translate`
- [ ] 8.3 ✅ **Done when:** Full translation appears below the word analysis

---

## ✅ Step 9: PWA Features

**Goal:** The app is installable as a PWA with offline support.

**File:** `frontend/nuxt.config.ts` + `frontend/public/manifest.json`

### Tasks

- [ ] 9.1 Install PWA module:

```bash
cd frontend
npm install @vite-pwa/nuxt
```

- [ ] 9.2 Update `nuxt.config.ts`:

```ts
export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss', '@vite-pwa/nuxt'],
  pwa: {
    manifest: {
      name: 'Penerjemah Kitab',
      short_name: 'KitabTerj',
      description: 'Terjemah Arab kata-per-kata seperti ulama membaca kitab',
      theme_color: '#065f46',
      background_color: '#fffbeb',
      display: 'standalone',
      orientation: 'portrait',
      icons: [
        {
          src: '/icon-192.png',
          sizes: '192x192',
          type: 'image/png',
        },
        {
          src: '/icon-512.png',
          sizes: '512x512',
          type: 'image/png',
        },
      ],
    },
    workbox: {
      globPatterns: ['**/*.{js,css,html,png,svg,ico}'],
    },
  },
})
```

- [ ] 9.3 Create PWA icons using a simple command (requires ImageMagick or any tool that generates PNGs):

```bash
cd frontend/public

# Option A: Using ImageMagick to generate colored square icons
# (adjust if you have ImageMagick installed)
# convert -size 192x192 xc:'#065f46' -fill white -font Arial -pointsize 100 \
#   -gravity center -annotate 0 '📖' icon-192.png

# Option B: Just create minimal placeholder PNGs using Python
cd frontend && python3 -c "
# Generate minimal valid 1x1 pixel PNG icons as placeholders
import struct, zlib

def create_png(width, height, color=(6, 95, 70)):
    r, g, b = color
    # Create a solid-color RGBA pixel row
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # filter byte
        for x in range(width):
            raw_data += bytes([r, g, b, 255])
    
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc
    
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
    idat = chunk(b'IDAT', zlib.compress(raw_data))
    iend = chunk(b'IEND', b'')
    
    return sig + ihdr + idat + iend

for size in [192, 512]:
    png = create_png(size, size)
    with open(f'public/icon-{size}.png', 'wb') as f:
        f.write(png)
    print(f'Created icon-{size}.png')
"
```

> 💡 Replace these placeholder icons with proper kitab/book icons later (use a free icon service like https://realfavicongenerator.net/)

- [ ] 9.4 Enable PWA in dev mode by adding to `nuxt.config.ts`:

```ts
pwa: {
  registerType: 'autoUpdate',  // ← add this line
  // ... existing manifest config ...
}
```

- [ ] 9.5 ✅ **Test:** Run `npm run build && npx serve .output/public` to see the PWA install prompt
- [ ] 9.6 ✅ **Done when:** You can install the app on your phone/desktop via browser install prompt

---

## ✅ Step 10: Package & Polish

### Tasks

- [ ] 10.1 Create `backend/requirements.txt`:

```txt
fastapi>=0.104.0
uvicorn>=0.24.0
mishkal>=0.4.0
pyarabic>=0.6.0
qalsadi>=0.5.0
camel-tools>=1.5.0
transformers>=4.30.0
torch>=2.0.0
sentencepiece>=0.1.99
```

- [ ] 10.2 Create `frontend/README.md` with setup instructions
- [ ] 10.3 Add loading states and error boundaries
- [ ] 10.4 Add RTL support for Arabic text
- [ ] 10.5 ✅ **Done when:** App looks polished and works smoothly

---

## 📊 Progress Tracker

```
Step 1:  Project setup            ✅  ▶  fastapi + nuxt running
Step 2:  Frontend tashkeel        ✅  ▶  Paste → harakat in browser
Step 3:  Backend analysis         ✅  ▶  API returns words + pos
Step 4:  Show word cards          ✅  ▶  Cards with lemma/root/pos
Step 5:  Dictionary/gloss         ☐  ▶  Indonesian per word
Step 6:  NLLB translation         ☐  ▶  Full sentence translated
Step 7:  Scholar display          ☐  ▶  Beautiful kitab layout
Step 8:  Full translation UI      ☐  ▶  Translation in result
Step 9:  PWA features             ☐  ▶  Installable, manifest
Step 10: Package & polish         ☐  ▶  Production-ready
```

---

## 💡 Running the App (After Each Step)

You'll always need **two terminals**:

```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Then open: http://localhost:3000

---

## 📁 Final Project Structure

```
camel/
├── backend/
│   ├── main.py              # FastAPI server (grows with each step)
│   ├── dictionary.py        # Arabic → Indonesian dictionary
│   └── requirements.txt     # Python dependencies
│
├── frontend/
│   ├── pages/
│   │   └── index.vue        # Main PWA page (grows with each step)
│   ├── nuxt.config.ts       # Nuxt config (PWA, Tailwind)
│   ├── tailwind.config.ts   # Tailwind theme
│   ├── package.json
│   └── public/
│       └── icon-*.png       # PWA icons
│
└── docs/
    ├── ASSESSMENT.md
    ├── TRANSLATION_RECOMMENDATION.md
    └── DEV_BREAKDOWN.md      ← You are here
```

---

*Happy building! 📖✨*
