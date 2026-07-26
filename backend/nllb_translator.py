"""nllb_translator.py — NLLB-200 offline translator (fallback when Google fails).

Uses Meta's NLLB-200 distilled 600M model for Arabic ↔ Indonesian/English
translation entirely offline. Loaded lazily (on first use) to avoid slowing
down app startup.

Requires:
  - transformers >= 4.30
  - torch (CPU is fine)
  - sentencepiece
  - huggingface_hub

Model download (~1.2 GB on first run, cached in ~/.cache/huggingface/hub/).
"""

import logging
import threading
from typing import Optional

MODEL_NAME = "facebook/nllb-200-distilled-600M"

# NLLB uses BCP-47 language codes
LANG_CODES: dict[str, str] = {
    "id": "ind_Latn",  # Arabic → Indonesian
    "en": "eng_Latn",  # Arabic → English
}

# Suppress verbose HF logs after first load
logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)


class NLLBTranslator:
    """Singleton NLLB-200 translator loaded lazily on first use.

    Usage:
        nllb = NLLBTranslator()
        id_result = nllb.translate("السلام عليكم", target="id")  # Indonesian
        en_result = nllb.translate("السلام عليكم", target="en")  # English
    """

    _instance: Optional["NLLBTranslator"] = None
    _init_lock = threading.Lock()

    def __new__(cls) -> "NLLBTranslator":
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._model = None
                    cls._instance._tokenizer = None
                    cls._instance._loaded = False
                    cls._instance._load_lock = threading.Lock()  # guards model loading
                    cls._instance._gen_lock = threading.Lock()   # guards model.generate()
        return cls._instance

    # ── Lazy loading ─────────────────────────────────────────────────

    def _load(self) -> None:
        """Load the model and tokenizer from Hugging Face Hub (once)."""
        if self._loaded:
            return
        with self._load_lock:
            if self._loaded:
                return
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            logging.info("Loading NLLB-200 model (first time may take a while)...")
            self._tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
            self._model.eval()  # Switch to inference mode
            self._loaded = True
            logging.info("NLLB-200 model loaded successfully.")

    # ── Public API ───────────────────────────────────────────────────

    def translate(self, text: str, target: str = "id") -> str:
        """Translate Arabic text to the target language.

        Args:
            text: Arabic text to translate.
            target: Target language code — "id" (Indonesian) or "en" (English).

        Returns:
            Translated text string, or empty string on failure.

        Raises:
            RuntimeError: If model fails to load or translate.
        """
        if not text.strip():
            return ""

        try:
            self._load()
        except Exception as e:
            raise RuntimeError(f"Failed to load NLLB-200 model: {e}") from e

        lang_code = LANG_CODES.get(target)
        if not lang_code:
            raise ValueError(f"Unsupported target language: {target!r}")

        try:
            inputs = self._tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
            )
            with self._gen_lock:  # model.generate() is not thread-safe
                translated = self._model.generate(
                    **inputs,
                    forced_bos_token_id=self._tokenizer.convert_tokens_to_ids(lang_code),
                    max_length=256,
                    num_beams=4,
                    early_stopping=True,
                )
            return self._tokenizer.batch_decode(
                translated, skip_special_tokens=True
            )[0]
        except Exception as e:
            raise RuntimeError(f"NLLB-200 translation failed: {e}") from e

    @property
    def is_available(self) -> bool:
        """Check if the NLLB-200 model can be loaded (e.g., during health check)."""
        try:
            self._load()
            return True
        except Exception:
            return False

    @property
    def model_name(self) -> str:
        return MODEL_NAME
