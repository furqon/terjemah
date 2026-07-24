"""ocr_engine.py — PDF → images → Arabic text using Tesseract OCR.

Pipeline:
  1. PDF → image (PyMuPDF / fitz)
  2. Image preprocessing (OpenCV: CLAHE + Otsu + deskew)
  3. Tesseract OCR (Arabic language pack)
  4. Post-processing (clean common OCR errors)
"""

import os
import re
from typing import Iterator, Optional, Tuple

import cv2
import fitz  # PyMuPDF
import numpy as np
import pytesseract
from PIL import Image


# ── Tesseract auto-detection ─────────────────────────────────────────

# Common Windows install paths, tried in order
POSSIBLE_PATHS: list[str] = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\BEELINK\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    r"C:\Users\BEELINK\AppData\Local\Tesseract-OCR\tesseract.exe",
]

_tesseract_found: bool = False
for _path in POSSIBLE_PATHS:
    if os.path.isfile(_path):
        pytesseract.pytesseract.tesseract_cmd = _path
        _tesseract_found = True
        break


def is_tesseract_available() -> bool:
    """Return True if a Tesseract executable is configured and reachable."""
    if not _tesseract_found:
        return False
    try:
        import subprocess
        subprocess.run(
            [pytesseract.pytesseract.tesseract_cmd, "--version"],
            capture_output=True, timeout=5, check=False,
        )
        return True
    except Exception:
        return False


def tesseract_version() -> str:
    """Return the installed Tesseract version string, or 'Not installed'."""
    try:
        import subprocess
        r = subprocess.run(
            [pytesseract.pytesseract.tesseract_cmd, "--version"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout.splitlines()[0] if r.stdout else "Unknown"
    except Exception:
        return "Not installed"


# ── OCR Engine ───────────────────────────────────────────────────────

class OCREngine:
    """Convert PDF pages to Arabic text via Tesseract OCR."""

    def __init__(self, dpi: int = 300):
        self.dpi = dpi

    # ── PDF helpers ──

    def get_page_count(self, pdf_path: str) -> int:
        """Return total number of pages in a PDF."""
        doc = fitz.open(pdf_path)
        count = doc.page_count
        doc.close()
        return count

    def page_to_image(self, pdf_path: str, page_num: int) -> Image.Image:
        """Render a single PDF page to a PIL Image (RGB)."""
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)  # 0-indexed
        pix = page.get_pixmap(dpi=self.dpi)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        doc.close()
        return img

    def try_direct_text(self, pdf_path: str, page_num: int) -> Optional[str]:
        """Try to extract text directly from a born-digital PDF page.

        Returns the text string if available, or None if the page is a
        scanned image (no embedded text).
        """
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)
        text = page.get_text().strip()
        doc.close()
        return text if text else None

    # ── Image preprocessing ──

    def preprocess(self, image: Image.Image) -> np.ndarray:
        """Enhance image for Arabic OCR using OpenCV.

        Pipeline: grayscale → CLAHE contrast enhancement → Otsu
        binarization → deskew (minor rotation correction).
        """
        # Convert PIL → numpy & grayscale
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

        # CLAHE (contrast-limited adaptive histogram equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced, h=30)

        # Otsu binarization
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Deskew
        binary = self._deskew(binary)

        return binary

    @staticmethod
    def _deskew(img: np.ndarray) -> np.ndarray:
        """Correct slight rotation in a binary image."""
        coords = np.column_stack(np.where(img > 0))
        if len(coords) < 100:  # Too few foreground pixels — skip
            return img
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) > 0.5:
            h, w = img.shape
            matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
            img = cv2.warpAffine(
                img, matrix, (w, h),
                flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE,
            )
        return img

    # ── OCR ──

    def ocr_image(self, image: np.ndarray) -> Tuple[str, float]:
        """Extract Arabic text from a preprocessed image.

        Returns:
            (text, confidence) where confidence is a float 0.0–1.0.
        """
        data = pytesseract.image_to_data(
            image,
            lang="ara",
            config="--psm 6 --oem 3",
            output_type=pytesseract.Output.DICT,
        )

        words: list[str] = []
        confs: list[int] = []
        for i, conf_str in enumerate(data["conf"]):
            if conf_str != "-1":
                conf = int(conf_str)
                if conf > 0:
                    words.append(data["text"][i])
                    confs.append(conf)

        text = " ".join(words)
        avg_conf = sum(confs) / len(confs) if confs else 0.0
        return self._clean_text(text), avg_conf / 100.0

    # ── Page-level processing ──

    def process_page(self, pdf_path: str, page_num: int) -> Tuple[str, float]:
        """Process a single PDF page.  Tries direct text first, then OCR.

        Args:
            pdf_path: Path to the PDF file.
            page_num: 1-based page number.

        Returns:
            (text, confidence)
        """
        page_idx = page_num - 1  # Convert to 0-indexed

        # Try direct text extraction first (born-digital PDFs)
        direct = self.try_direct_text(pdf_path, page_idx)
        if direct:
            return self._clean_text(direct), 1.0

        # Fall back to OCR for scanned pages
        img = self.page_to_image(pdf_path, page_idx)
        processed = self.preprocess(img)
        text, conf = self.ocr_image(processed)
        return text, conf

    def process_page_range(
        self, pdf_path: str, start: int, end: int,
    ) -> Iterator[Tuple[int, str, float]]:
        """Process a range of pages, yielding (page_num, text, conf) objects.

        Args:
            pdf_path: Path to the PDF file.
            start: First page (1-based).
            end: Last page (1-based, inclusive).
        """
        for page_num in range(start, end + 1):
            text, conf = self.process_page(pdf_path, page_num)
            yield page_num, text, conf

    # ── Post-processing ──

    @staticmethod
    def _clean_text(text: str) -> str:
        """Post-process Tesseract output to fix common Arabic errors."""
        # Normalise whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Replace common Tesseract artefacts
        replacements = {
            "للها": "لله",
            "اللّه": "الله",
            "اللَّه": "الله",
            "الرّحمن": "الرحمن",
            "الرّحيم": "الرحيم",
            "بسم": "بسم",
        }
        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)

        # Remove very short lines (likely noise)
        lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 2]
        return "\n".join(lines) if lines else text
