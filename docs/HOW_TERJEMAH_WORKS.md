# Cara Kerja Terjemah (Translation)

This document explains how translation ("Terjemah") works in Penerjemah Kitab — both in the **Analisis Teks** tab and the **Scan PDF** tab.

---

## 1. Ringkasan Alur (Flow Overview)

```
[Arabic Text]
     │
     ▼
 ┌─────────────┐
 │  Frontend   │  Nuxt 3 (index.vue) — sends POST to backend
 └──────┬──────┘
        │  HTTP POST (JSON)
        ▼
 ┌─────────────┐
 │   Backend   │  FastAPI (main.py) — translates using Google Translate
 │             │  via deep-translator library (free, no model download)
 └──────┬──────┘
        │
        ├──→ Google Translate (Arabic → Indonesian)
        ├──→ Google Translate (Arabic → English)
        │
        ▼
 ┌─────────────┐
 │  Database   │  SQLite (ocr_texts.db) — saves translation per page
 └─────────────┘
        │
        ▼
  Frontend displays:
  - BAHASA INDONESIA
  - ENGLISH (English)
```

---

## 2. Translation Engine: `deep-translator`

### Library: `deep-translator`

- **Package:** `deep-translator` (installed via pip)
- **Source:** Free Google Translate API wrapper — no API key, no model download, no GPU needed
- **Engine:** Uses Google Translate's unofficial public API
- **Requirements:** Internet connection

### Translator Initialization

In `backend/main.py`, two translators are created as singletons (thread-safe):

```python
def _get_translators():
    """Get or create both Google Translate translators (thread-safe)."""
    global _translator, _translator_en
    if _translator is not None and _translator_en is not None:
        return _translator, _translator_en
    with _translator_lock:
        if _translator is not None and _translator_en is not None:
            return _translator, _translator_en
        from deep_translator import GoogleTranslator
        _translator = GoogleTranslator(source='ar', target='id')
        _translator_en = GoogleTranslator(source='ar', target='en')
        return _translator, _translator_en
```

Both translators are created lazily on the first request and reused. Locks ensure only one thread initializes them.

---

## 3. Tab Analisis Teks — Whole Sentence Translation

### Frontend Flow

1. User types Arabic text → clicks **☾ Analisis Teks**
2. `analyze()` function:
   - Sends `POST /api/analyze` with `{ text: "..." }` → gets harakat + word analysis
   - Then automatically calls `translateText(inputText.value)` to start translation
3. `translateText()` function:
   - Sends `POST /api/translate` with `{ text: "..." }`
   - Uses a request counter (`_translateId`) to avoid stale responses
   - On response, sets `translation.value = { translation_id, translation_en }`

### Backend Endpoint: `POST /api/translate`

```
Request:  { "text": "السلام عليكم ورحمة الله وبركاته" }
Response: {
  "source": "السلام عليكم ورحمة الله وبركاته",
  "translation_id": "Semoga keselamatan, rahmat Allah, dan berkah-Nya tercurah kepada kalian",
  "translation_en": "Peace be upon you and the mercy of Allah and His blessings",
  "engine": "google-translate"
}
```

The endpoint:
1. Calls `_get_translators()` to get both ID and EN translators
2. Translates Arabic → Indonesian (`trans_id.translate(text)`)
3. Sleeps 0.3s to avoid rate limiting
4. Translates Arabic → English (`trans_en.translate(text)`)
5. Returns both translations

### Frontend Display

The result is shown as a styled card with:
- **TEKS ARAB** (original with harakat)
- **BAHASA INDONESIA** (Indonesian translation)
- **ENGLISH** (English translation)

---

## 4. Tab Scan PDF — Per-Page Translation

### Two Types of Translation in Scan PDF Tab

#### A. Per-Page "Terjemah" Button (User clicks per page)

**Frontend:** `translatePage(pageId, pageNumber, text)`

```javascript
async function translatePage(pageId, _pn, text) {
  if (!text) return;
  translatingPageId.value = pageId;
  try {
    const res = await fetch(`${config.public.apiBase}/api/ocr/translate-page`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page_id: pageId, text })
    });
    if (res.ok) {
      // Find which PDF this page belongs to, then reload pages
      for (const [pid, pages] of Object.entries(pagesCache.value)) {
        if (pages.some(p => p.id === pageId)) {
          await loadPages(Number(pid));
          toggleEdit(pageId, false);
          break;
        }
      }
    }
  } catch { /* ignore */ }
  finally { translatingPageId.value = null }
}
```

**Backend:** `POST /api/ocr/translate-page`

```
Request:  { "page_id": 5, "text": "النص العربي المصحح" }
Response: {
  "page_number": 1,
  "translation_id": "Teks Arab yang telah diperbaiki",
  "translation_en": "The corrected Arabic text"
}
```

The endpoint:
1. Looks up the page by `page_id` using `ocr_db.get_page_by_id()`
2. Translates the (user-edited) text using `deep-translator`
3. Saves the edited text as `cleaned_text` via `ocr_db.save_page()`
4. Saves both translations via `ocr_db.save_translation()`
5. Returns the translations

**IMPORTANT:** The `save_page()` method uses `INSERT ... ON CONFLICT DO UPDATE` (NOT `INSERT OR REPLACE`) to preserve the row ID and existing translation columns. This was a critical bug fix — read [BUG_FIX.md] for details.

#### B. Bulk "Terjemah Semua" Button (PDF-level batch translation)

**Frontend:** `translatePdf(pdfId)`

```javascript
async function translatePdf(pdfId) {
  translatingPdfId.value = pdfId;
  try {
    const res = await fetch(`${config.public.apiBase}/api/ocr/translate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pdf_id: pdfId })
    });
    if (res.ok) {
      await loadPdfList();
      await loadPages(pdfId);
    }
  } catch { /* ignore */ }
  finally { translatingPdfId.value = null }
}
```

**Backend:** `POST /api/ocr/translate`

```
Request:  { "pdf_id": 1, "target": "id" }
Response: {
  "pdf_id": 1,
  "translated": 3,  // pages translated
  "results": [
    { "page_number": 1, "translation_id": "...", "translation_en": "..." },
    { "page_number": 2, "translation_id": "...", "translation_en": "..." },
    { "page_number": 12, "translation_id": "...", "translation_en": "..." }
  ]
}
```

The endpoint:
1. Gets all **untranslated** pages for the PDF (where `translated_id IS NULL OR translated_id = ''`)
2. For each page, translates using the `cleaned_text` (or fallback to `raw_text`)
3. Saves translation via `ocr_db.save_translation()` (UPDATE only)
4. Returns results list

Each page translation is spaced 0.3s apart to avoid Google rate limiting.

---

## 5. SQLite Database Schema

### `pages` Table (relevant columns)

```sql
CREATE TABLE pages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_id          INTEGER NOT NULL,
    page_number     INTEGER NOT NULL,
    raw_text        TEXT,              -- Original OCR output
    cleaned_text    TEXT,              -- User-edited or corrected text
    confidence      REAL DEFAULT 0.0,  -- OCR confidence score
    processed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    translated_id   TEXT,              -- Indonesian translation
    translated_en   TEXT,              -- English translation
    translated_at   TIMESTAMP,         -- When translation happened
    UNIQUE(pdf_id, page_number),
    FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE
);
```

### Translation Operations

| Operation | SQL | Method |
|---|---|---|
| Save translation | `UPDATE pages SET translated_id=?, translated_en=?, translated_at=CURRENT_TIMESTAMP WHERE id=?` | `save_translation()` |
| Save page text | `INSERT ... ON CONFLICT(pdf_id, page_number) DO UPDATE SET ...` | `save_page()` |
| Get untranslated pages | `SELECT * FROM pages WHERE translated_id IS NULL OR translated_id = ''` | `get_untranslated_pages()` |

---

## 6. Frontend Display Flow

When pages are loaded from the API, the `loadPages()` function:

1. Fetches `GET /api/ocr/pages/{pdfId}` which returns all pages with translations
2. Stores them in `pagesCache.value[pdfId]`
3. The Vue template shows translations using `v-if="page.translated_id"`:

```html
<div v-if="page.translated_id" class="pt-2 mt-2" style="border-top: 1px dashed #e0d5c0;">
  <p class="text-[10px] tracking-wider mb-1" style="color: #3a7a4d;">BAHASA INDONESIA</p>
  <p class="text-sm leading-relaxed" style="color: #2a4a3a;">{{ page.translated_id }}</p>
</div>
<div v-if="page.translated_en" class="pt-1">
  <p class="text-[10px] tracking-wider mb-1" style="color: #4a6a8a;">ENGLISH</p>
  <p class="text-xs leading-relaxed" style="color: #2a3a4a;">{{ page.translated_en }}</p>
</div>
```

The accordion header also shows a ✓ checkmark when translated:
```html
<span v-if="page.translated_id" class="text-[9px]" style="color: #3a7a4d;">✓</span>
```

---

## 7. Complete Data Flow Diagram

```
 User clicks "☾ Terjemah" (per page)
         │
         ▼
  Frontend: translatePage(pageId, text)
         │
         ├──→ Check text is not empty
         ├──→ Set translatingPageId = pageId (shows spinner)
         │
         ▼
  POST /api/ocr/translate-page { page_id, text }
         │
         ▼
  Backend: ocr_translate_page()
         │
         ├──1. Lookup page by id → get page_row
         ├──2. Get translators (ar→id, ar→en)
         ├──3. Translate to Indonesian → tid
         ├──4. Translate to English → ten
         ├──5. Save edited text → save_page()
         │     (INSERT ... ON CONFLICT DO UPDATE)
         ├──6. Save translations → save_translation()
         │     (UPDATE ... SET translated_id, translated_en)
         └──7. Return OCRTranslatePage
         │
         ▼
  Frontend receives response
         │
         ├──→ res.ok = true
         ├──→ Find which PDF this page belongs to
         ├──→ loadPages(pdfId) — re-fetch pages from server
         │     (now includes translated_id and translated_en)
         └──→ toggleEdit(pageId, false) — exit edit mode
         │
         ▼
  Vue reactivity updates:
  - page.translated_id is now truthy
  - Translation section appears (v-if="page.translated_id")
  - ✓ checkmark appears in accordion header
```

---

## 8. Rate Limiting & Errors

- Google Translate has **no official rate limits** for the free API, but rapid sequential calls may trigger short temporary blocks
- A 0.3s delay is added between translations in batch mode
- If translation fails, `translated_id` shows `[Translation error: ...]`
- The `analyse()` function calls auto-translate; if it fails, it silently ignores the error (user can retry)
- Empty text translations return empty strings, not errors

---

## 9. Key Files

| File | Purpose |
|---|---|
| `backend/main.py` | All backend endpoints, translator singleton, `_get_translators()` |
| `backend/ocr_database.py` | SQLite CRUD: `save_translation()`, `get_untranslated_pages()`, `save_page()` |
| `frontend/pages/index.vue` | Frontend translation UI, `translatePage()`, `translatePdf()`, `translateText()` |
| `docs/HOW_TERJEMAH_WORKS.md` | This document |
