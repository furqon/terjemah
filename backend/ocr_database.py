"""ocr_database.py — SQLite database layer for OCR results.

Stores:
  - pdfs        (metadata per uploaded file)
  - pages       (OCR text per page)
  - paragraphs  (per-paragraph translations, optional)
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, Any


DB_PATH = Path(__file__).parent / "ocr_texts.db"


class OCRDatabase:
    """Thread-safe SQLite database for OCR data."""

    def __init__(self, db_path: str | Path = DB_PATH):
        raw = str(db_path)
        # Use shared-cache URI so multiple connections share the same in-memory DB
        if raw == ":memory:":
            self.db_path = "file::memory:?cache=shared"
        else:
            self.db_path = raw
            Path(raw).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── Schema ───────────────────────────────────────────────────────

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS pdfs (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename    TEXT NOT NULL,
                    filepath    TEXT NOT NULL,
                    total_pages INTEGER NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status      TEXT DEFAULT 'active'
                );

                CREATE TABLE IF NOT EXISTS pages (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    pdf_id          INTEGER NOT NULL,
                    page_number     INTEGER NOT NULL,
                    raw_text        TEXT,
                    cleaned_text    TEXT,
                    confidence      REAL DEFAULT 0.0,
                    processed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    translated_id   TEXT,
                    translated_en   TEXT,
                    translated_at   TIMESTAMP,
                    UNIQUE(pdf_id, page_number),
                    FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS paragraphs (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_id         INTEGER NOT NULL,
                    paragraph_index INTEGER NOT NULL,
                    arabic_text     TEXT NOT NULL,
                    translation_id   TEXT,
                    translation_en  TEXT,
                    UNIQUE(page_id, paragraph_index),
                    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
                );
            """)

    # ── Connection helper ────────────────────────────────────────────

    @contextmanager
    def _conn(self):
        use_uri = self.db_path.startswith("file:")
        conn = sqlite3.connect(self.db_path, uri=use_uri)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ── PDF operations ───────────────────────────────────────────────

    def save_pdf(self, filename: str, filepath: str, total_pages: int) -> int:
        """Insert a new PDF record.  Returns the new pdf_id."""
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO pdfs (filename, filepath, total_pages) VALUES (?, ?, ?)",
                (filename, filepath, total_pages),
            )
            return cur.lastrowid

    def get_pdf(self, pdf_id: int) -> Optional[dict[str, Any]]:
        """Get a single PDF record by id."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM pdfs WHERE id = ?", (pdf_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_all_pdfs(self) -> list[dict[str, Any]]:
        """Return all active PDFs, newest first."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM pdfs WHERE status = 'active' ORDER BY uploaded_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_pdf(self, pdf_id: int) -> None:
        """Soft-delete a PDF and its pages (via CASCADE)."""
        with self._conn() as conn:
            conn.execute("UPDATE pdfs SET status = 'deleted' WHERE id = ?", (pdf_id,))

    # ── Page operations ──────────────────────────────────────────────

    def get_page_by_id(self, page_id: int) -> Optional[dict[str, Any]]:
        """Get a single page record by its id (direct SQL lookup)."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM pages WHERE id = ?", (page_id,)
            ).fetchone()
            return dict(row) if row else None

    def save_page(
        self,
        pdf_id: int,
        page_number: int,
        raw_text: str,
        cleaned_text: str,
        confidence: float,
    ) -> None:
        """Insert or update a page record.

        Uses INSERT ... ON CONFLICT DO UPDATE instead of INSERT OR REPLACE
        so that existing columns (translated_id, translated_en, id) are
        preserved rather than wiped out.
        """
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO pages (pdf_id, page_number, raw_text, cleaned_text, confidence)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(pdf_id, page_number) DO UPDATE SET
                       raw_text = excluded.raw_text,
                       cleaned_text = excluded.cleaned_text,
                       confidence = excluded.confidence,
                       processed_at = CURRENT_TIMESTAMP""",
                (pdf_id, page_number, raw_text, cleaned_text, confidence),
            )

    def get_pages_for_pdf(self, pdf_id: int) -> list[dict[str, Any]]:
        """Return all pages for a PDF, ordered by page_number."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM pages WHERE pdf_id = ? ORDER BY page_number",
                (pdf_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_untranslated_pages(self, pdf_id: Optional[int] = None) -> list[dict[str, Any]]:
        """Return pages where Indonesian translation is missing."""
        with self._conn() as conn:
            if pdf_id:
                rows = conn.execute(
                    """SELECT * FROM pages
                       WHERE pdf_id = ? AND (translated_id IS NULL OR translated_id = '')
                       ORDER BY page_number""",
                    (pdf_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM pages
                       WHERE translated_id IS NULL OR translated_id = ''
                       ORDER BY pdf_id, page_number"""
                ).fetchall()
            return [dict(r) for r in rows]

    def save_translation(
        self, page_id: int, translated_id: str, translated_en: str,
    ) -> None:
        """Update a page with its translations."""
        with self._conn() as conn:
            conn.execute(
                """UPDATE pages
                   SET translated_id = ?, translated_en = ?, translated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (translated_id, translated_en, page_id),
            )

    # ── Paragraph operations ─────────────────────────────────────────

    def delete_paragraphs_for_page(self, page_id: int) -> None:
        """Delete all paragraphs for a page (e.g., before re-translating)."""
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM paragraphs WHERE page_id = ?", (page_id,)
            )

    def save_paragraph(
        self,
        page_id: int,
        paragraph_index: int,
        arabic_text: str,
        translation_id: str = "",
        translation_en: str = "",
    ) -> None:
        """Insert or replace a paragraph record."""
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO paragraphs
                   (page_id, paragraph_index, arabic_text, translation_id, translation_en)
                   VALUES (?, ?, ?, ?, ?)""",
                (page_id, paragraph_index, arabic_text, translation_id, translation_en),
            )

    def get_paragraphs_for_page(self, page_id: int) -> list[dict[str, Any]]:
        """Return all paragraphs for a page, ordered by index."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM paragraphs WHERE page_id = ? ORDER BY paragraph_index",
                (page_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Stats ────────────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """Return summary statistics."""
        with self._conn() as conn:
            pdf_count = conn.execute(
                "SELECT COUNT(*) FROM pdfs WHERE status = 'active'"
            ).fetchone()[0]
            page_count = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
            translated_count = conn.execute(
                "SELECT COUNT(*) FROM pages WHERE translated_id IS NOT NULL AND translated_id != ''"
            ).fetchone()[0]
            return {
                "pdfs": pdf_count,
                "pages": page_count,
                "translated": translated_count,
            }
