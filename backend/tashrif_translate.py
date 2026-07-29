"""
tashrif_translate.py — Phase 4: Indonesian & English Translation Overlay.

Adds meaningful Indonesian and English translations to each of the 8 columns
in the Tashrif Ishthilahi table by combining:

  1. Root meaning lookup from dictionary (Arabic → Indonesian & English)
  2. Rumus-specific semantic overlay (e.g., 4A = "membuat jadi", 5D = "ter-")
  3. Form-level templates (e.g., madhi = "telah {base}", nahi = "jangan {base}")

Usage:
    from tashrif_translate import translate_ishthilahi
    trans = translate_ishthilahi("كتب", "3C", bab=3)
    print(trans["translations"]["id"]["fiil_madhi"])   # "telah menulis"
    print(trans["translations"]["en"]["fiil_madhi"])   # "has written"

Reference: "At-Tashrif Al-Mujaz" by Andy Satiyo Ahmad (docs/tashrif.pdf)
Appendix: Wazan Pattern Mapping to Indonesian Meanings (PDF page 53)
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Any

from tashrif_classifier import FormNumber, FORM_LABELS_ID, RUMUS_MEANING

try:
    import pyarabic.araby as araby
    HAS_PYARABIC = True
except ImportError:
    HAS_PYARABIC = False

# ── Try importing dictionary lookups (soft dependency) ──────────────────

try:
    from dictionary import lookup as dict_lookup_id
    HAS_DICT_ID = True
except ImportError:
    HAS_DICT_ID = False

    def dict_lookup_id(_word: str) -> str:
        return ""

try:
    from dictionary_en import lookup as dict_lookup_en
    HAS_DICT_EN = True
except ImportError:
    HAS_DICT_EN = False

    def dict_lookup_en(_word: str) -> str:
        return ""


# ═══════════════════════════════════════════════════════════════════════════
# Constants — Form names matching tashrif_generator.py
# ═══════════════════════════════════════════════════════════════════════════

FORM_NAMES = [
    "fiil_madhi",      # Form 1
    "fiil_mudhari",    # Form 2
    "fiil_amr",        # Form 3
    "fiil_nahi",       # Form 4
    "mashdar",         # Form 5
    "ism_fail",        # Form 6
    "ism_maful",       # Form 7
    "zamami",          # Form 8
]

# ═══════════════════════════════════════════════════════════════════════════
# Rumus Semantic Overlay — Indonesian
# ═══════════════════════════════════════════════════════════════════════════

# Each Rumus has:
#   - meaning_id: the Rumus-level semantic description in Indonesian
#   - meaning_en: the Rumus-level semantic description in English
#   - verb_base_fn: function(root_meaning) -> Rumus-specific verb meaning
#     e.g., for 5A تَفَعَّلَ, root "ajar" → "belajar" (not "mengajar sendiri")
#   - special_cases: dict of root -> override meaning for well-known exceptions

@dataclass
class RumusSemantics:
    """Semantic description and verb derivation for a Rumus pattern."""

    meaning_id: str
    """Indonesian description of what this Rumus does (e.g., 'intransitif / refleksif')."""

    meaning_en: str
    """English description of what this Rumus does (e.g., 'intransitive / reflexive')."""

    verb_formula_id: str = "{root}"
    """Template using {root} to produce the base Indonesian verb meaning for this Rumus.
    E.g., for 6: 'meminta {root}' → root ampuni → 'meminta ampun'.
    The {root} placeholder is replaced with the root meaning from the dictionary."""

    verb_formula_en: str = "{root}"
    """Template using {root} to produce the base English verb meaning."""

    special_cases_id: dict[str, str] = field(default_factory=dict)
    """Root-specific overrides for the Indonesian verb meaning.
    E.g., for Rumus 4A, root 'علم' → 'mengajar' (instead of formulaic 'menjadikan ilmu')."""

    special_cases_en: dict[str, str] = field(default_factory=dict)
    """Root-specific overrides for the English verb meaning."""


# ── Indonesian semantics ─────────────────────────────────────────────

RUMUS_SEMANTICS_ID: dict[str, RumusSemantics] = {
    "3A": RumusSemantics(
        meaning_id="Makna dasar akar kata (fi'il tsulatsi mujarrad)",
        meaning_en="Basic root meaning (simple triliteral verb)",
        # Root meaning is used as-is from the dictionary
        special_cases_id={
            "علم": "mengetahui",
            "فعل": "melakukan",
            "ذكر": "mengingat",
            "عبد": "menyembah",
        },
    ),
    "3B": RumusSemantics(
        meaning_id="Makna dasar akar kata (fi'il tsulatsi mujarrad)",
        meaning_en="Basic root meaning (simple triliteral verb)",
        special_cases_id={
            "ضرب": "memukul",
            "حسب": "mengira",
            "جلس": "duduk",
        },
    ),
    "3C": RumusSemantics(
        meaning_id="Makna dasar akar kata (fi'il tsulatsi mujarrad)",
        meaning_en="Basic root meaning (simple triliteral verb)",
        special_cases_id={
            "كتب": "menulis",
            "نصر": "menolong",
            "فتح": "membuka",
            "دخل": "masuk",
            "كفر": "kafir",
            "شكر": "bersyukur",
            "صبر": "sabar",
            "ظلم": "menganiaya",
        },
    ),
    "4A": RumusSemantics(
        meaning_id="Membuat jadi / mengulang (men...kan)",
        meaning_en="Causative / intensive (make someone do / do repeatedly)",
        verb_formula_id="menjadikan {root}",
        verb_formula_en="to make {root}",
        special_cases_id={
            "علم": "mengajar",         # menjadikan ilmu → mengajar
            "كرم": "memuliakan",       # menjadikan mulia
            "حرم": "mengharamkan",
            "سلم": "menyerahkan",
            "قدر": "menentukan",
            "كذب": "mendustakan",
            "صدق": "membenarkan",
            "جدد": "memperbarui",
            "قرب": "mendekatkan",
            "بعد": "menjauhkan",
            "حسن": "memperbaiki",
            "كبر": "membesarkan",
            "صغر": "memperkecil",
            "وحد": "mengesakan",
            "قدس": "mensucikan",
        },
    ),
    "4B": RumusSemantics(
        meaning_id="Saling / berbalasan (ber...an)",
        meaning_en="Reciprocal (doing with each other)",
        verb_formula_id="ber{root}an",
        verb_formula_en="to mutually {root}",
        special_cases_id={
            "شور": "berunding",         # شاور → berunding
            "عرف": "saling mengenal",   # عارف → saling mengenal
            "حرب": "berperang",
            "علم": "saling mengajar",
            "كتب": "berkorespondensi",
            "عمل": "bekerja sama",
        },
    ),
    "4C": RumusSemantics(
        meaning_id="Menjadikan / transitif (me...kan)",
        meaning_en="Causative / transitive (make someone/something ___)",
        verb_formula_id="men{root}kan",
        verb_formula_en="to cause to {root}",
        special_cases_id={
            "سلم": "menyerahkan diri",  # أسلم → menyerahkan diri (masuk Islam)
            "علم": "memberitahu",
            "خرج": "mengeluarkan",
            "دخل": "memasukkan",
            "كثر": "memperbanyak",
            "حسن": "memperbaiki",
            "نزل": "menurunkan",
            "رسل": "mengutus",
            "شرك": "mempersekutukan",
            "عان": "menolong",
            "مر": "memerintahkan",
            "قيم": "mendirikan",
            "جلس": "mendudukkan",
            "وقف": "memberhentikan",
            "كرم": "memuliakan",
            "حق": "mewajibkan/mengharuskan",
        },
    ),
    "4D": RumusSemantics(
        meaning_id="Makna dasar akar 4 huruf (fi'il ruba'i)",
        meaning_en="Basic meaning of 4-letter root",
        special_cases_id={
            "زلزل": "mengguncang",
            "وسوس": "membisikkan",
            "جعجع": "menghentikan",
            "بعبع": "menakut-nakuti",
            "صلصل": "berbunyi",
        },
    ),
    "5A": RumusSemantics(
        meaning_id="Intransitif / refleksif (ber... / melakukan pada diri sendiri)",
        meaning_en="Intransitive / reflexive (doing to oneself)",
        verb_formula_id="ber{root}",
        verb_formula_en="to {root} oneself",
        special_cases_id={
            "علم": "belajar",                    # تعلم → belajar
            "كلم": "berbicara",
            "قدم": "bersungguh-sungguh",
            "بصر": "merenungkan",
            "فكر": "berpikir",
            "ذكر": "mengingat-ingat",
            "عمد": "sengaja",
            "بعد": "menjauhkan diri",
            "قرب": "mendekatkan diri",
            "وكل": "bertawakkal",
            "حفظ": "menghafal",
        },
    ),
    "5B": RumusSemantics(
        meaning_id="Saling melakukan (saling ber...)",
        meaning_en="Reciprocal action (doing with each other)",
        verb_formula_id="saling ber{root}",
        verb_formula_en="to mutually {root} each other",
        special_cases_id={
            "عرف": "saling mengenal",  # تعارف → saling mengenal
            "علم": "saling mengajar",
            "كتب": "berkorespondensi",
            "فهم": "saling memahami",
            "زوج": "menikah",
            "قاتل": "saling membunuh",
            "خصم": "berselisih",
            "باعد": "saling menjauh",
            "قرب": "saling mendekat",
            "عاون": "saling membantu",
        },
    ),
    "5C": RumusSemantics(
        meaning_id="Melakukan pada diri sendiri (ber... / men...i)",
        meaning_en="Action done for oneself",
        verb_formula_id="ber{root}",
        verb_formula_en="to {root} for oneself",
        special_cases_id={
            "حرم": "memuliakan",       # احترم → memuliakan/menghormati
            "جمع": "mengumpulkan",
            "كسب": "mengusahakan",
            "حفظ": "menjaga diri",
            "عذر": "meminta maaf",
            "تفق": "bersepakat",
            "قسم": "membagi",
            "طبع": "mencetak",
            "نفع": "memanfaatkan",
            "كتسب": "berusaha",
        },
    ),
    "5D": RumusSemantics(
        meaning_id="Pasif / intransitif (ter... / menjadi ...)",
        meaning_en="Passive / intransitive (unintentional action)",
        verb_formula_id="ter{root}",
        verb_formula_en="to get {root}ed",
        special_cases_id={
            "كسر": "pecah",           # انكسر → pecah (terpatahkan)
            "قلب": "terbalik",
            "فتح": "terbuka",
            "غلق": "tertutup",
            "قطع": "terputus",
            "صرف": "berpaling",
            "قاد": "dipimpin",
            "طلق": "terlepas",
            "حل": "terurai",
            "عقد": "tersimpul",
            "هزم": "kalah",
            "كشف": "tersingkap",
            "جمع": "berkumpul",
            "فصل": "terpisah",
            "صدم": "tertabrak",
        },
    ),
    "5E": RumusSemantics(
        meaning_id="Menjadi warna/sifat (menjadi ...)",
        meaning_en="Becoming a color / quality",
        verb_formula_id="menjadi {root}",
        verb_formula_en="to become {root}",
        special_cases_id={
            "حمر": "memerah",     # احمر → memerah
            "صفر": "menguning",
            "خضر": "menghijau",
            "زرق": "membiru",
            "بيض": "memutih",
            "سود": "menghitam",
            "عوج": "bengkok",
            "حول": "berubah",
            "طول": "memanjang",
            "عرض": "melebar",
        },
    ),
    "6": RumusSemantics(
        meaning_id="Meminta / menganggap (meminta ... / menganggap ...)",
        meaning_en="To ask for / to consider (something)",
        verb_formula_id="meminta {root}",
        verb_formula_en="to ask for {root}",
        special_cases_id={
            "غفر": "meminta ampun",     # استغفر → meminta ampun
            "علم": "meminta tahu",
            "عان": "meminta tolong",
            "خرج": "meminta keluar",
            "قدر": "merasa mampu",
            "كبر": "menganggap besar",
            "حسن": "menganggap baik",
            "عظم": "mengagungkan",
            "عجل": "tergesa-gesa",
            "قام": "minta berdiri",
            "فتح": "meminta dibukakan",
            "نصر": "meminta pertolongan",
            "هدى": "meminta petunjuk",
            "رحم": "meminta rahmat",
            "غنى": "merasa cukup",
            "ضعف": "merasa lemah",
        },
    ),
}

# ── English semantics ────────────────────────────────────────────────

RUMUS_SEMANTICS_EN: dict[str, RumusSemantics] = {
    "3A": RumusSemantics(
        meaning_id="Basic root meaning (simple triliteral verb)",
        meaning_en="Basic root meaning (simple triliteral verb)",
        special_cases_id={
            "علم": "to know",
            "فعل": "to do",
            "ذكر": "to remember",
            "عبد": "to worship",
        },
    ),
    "3B": RumusSemantics(
        meaning_id="Basic root meaning (simple triliteral verb)",
        meaning_en="Basic root meaning (simple triliteral verb)",
        special_cases_id={
            "ضرب": "to hit",
            "حسب": "to reckon",
            "جلس": "to sit",
        },
    ),
    "3C": RumusSemantics(
        meaning_id="Basic root meaning (simple triliteral verb)",
        meaning_en="Basic root meaning (simple triliteral verb)",
        special_cases_id={
            "كتب": "to write",
            "نصر": "to help",
            "فتح": "to open",
            "دخل": "to enter",
            "كفر": "to disbelieve",
            "شكر": "to thank",
            "صبر": "to be patient",
            "ظلم": "to oppress",
            "علم": "to know",
            "سلم": "to be safe",
            "رزق": "to provide",
        },
    ),
    "4A": RumusSemantics(
        meaning_id="Causative / intensive (make someone do / do repeatedly)",
        meaning_en="Causative / intensive (make someone do / do repeatedly)",
        verb_formula_id="to make {root}",
        verb_formula_en="to make {root}",
        special_cases_id={
            "علم": "to teach",
            "كرم": "to honor",
            "حرم": "to forbid",
            "سلم": "to submit",
            "قدر": "to determine",
            "كذب": "to deny",
            "صدق": "to affirm",
            "جدد": "to renew",
            "قرب": "to bring near",
            "بعد": "to distance",
            "حسن": "to improve",
            "كبر": "to magnify",
            "وحد": "to unify",
            "قدس": "to sanctify",
        },
    ),
    "4B": RumusSemantics(
        meaning_id="Reciprocal (doing with each other)",
        meaning_en="Reciprocal (doing with each other)",
        verb_formula_id="to mutually {root}",
        verb_formula_en="to mutually {root}",
        special_cases_id={
            "شور": "to consult",
            "عرف": "to know each other",
            "حرب": "to wage war",
            "علم": "to teach each other",
            "كتب": "to correspond",
            "عمل": "to cooperate",
        },
    ),
    "4C": RumusSemantics(
        meaning_id="Causative / transitive (make someone/something ___)",
        meaning_en="Causative / transitive (make someone/something ___)",
        verb_formula_id="to cause to {root}",
        verb_formula_en="to cause to {root}",
        special_cases_id={
            "سلم": "to submit (become Muslim)",
            "علم": "to inform",
            "خرج": "to bring out",
            "دخل": "to bring in",
            "كثر": "to multiply",
            "حسن": "to improve",
            "نزل": "to send down",
            "رسل": "to send",
            "شرك": "to associate partners",
            "عان": "to help",
            "مر": "to command",
            "قيم": "to establish",
            "جلس": "to seat",
            "وقف": "to stop",
            "كرم": "to honor",
            "حق": "to obligate",
        },
    ),
    "4D": RumusSemantics(
        meaning_id="Basic meaning of 4-letter root",
        meaning_en="Basic meaning of 4-letter root",
        special_cases_id={
            "زلزل": "to shake violently",
            "وسوس": "to whisper (evil)",
            "جعجع": "to halt",
            "بعبع": "to terrify",
            "صلصل": "to ring",
        },
    ),
    "5A": RumusSemantics(
        meaning_id="Intransitive / reflexive (doing to oneself)",
        meaning_en="Intransitive / reflexive (doing to oneself)",
        verb_formula_id="to {root} oneself",
        verb_formula_en="to {root} oneself",
        special_cases_id={
            "علم": "to learn",
            "كلم": "to speak",
            "قدم": "to advance",
            "بصر": "to reflect",
            "فكر": "to think",
            "ذكر": "to remember well",
            "عمد": "to intend",
            "بعد": "to keep away",
            "قرب": "to draw near",
            "وكل": "to rely on Allah",
            "حفظ": "to memorize",
            "ربي": "to be brought up",
        },
    ),
    "5B": RumusSemantics(
        meaning_id="Reciprocal action (doing with each other)",
        meaning_en="Reciprocal action (doing with each other)",
        verb_formula_id="to {root} each other",
        verb_formula_en="to {root} each other",
        special_cases_id={
            "عرف": "to know one another",
            "علم": "to teach each other",
            "كتب": "to correspond",
            "فهم": "to understand each other",
            "زوج": "to marry",
            "قاتل": "to fight each other",
            "خصم": "to dispute",
            "باعد": "to distance from each other",
            "قرب": "to draw near each other",
            "عاون": "to cooperate",
        },
    ),
    "5C": RumusSemantics(
        meaning_id="Action done for oneself",
        meaning_en="Action done for oneself",
        verb_formula_id="to {root} for oneself",
        verb_formula_en="to {root} for oneself",
        special_cases_id={
            "حرم": "to honor",
            "جمع": "to gather",
            "كسب": "to earn",
            "حفظ": "to guard oneself",
            "عذر": "to apologize",
            "تفق": "to agree",
            "قسم": "to divide",
            "طبع": "to print",
            "نفع": "to benefit",
            "كتسب": "to strive",
        },
    ),
    "5D": RumusSemantics(
        meaning_id="Passive / intransitive (unintentional action)",
        meaning_en="Passive / intransitive (unintentional action)",
        verb_formula_id="to get {root}ed",
        verb_formula_en="to get {root}ed",
        special_cases_id={
            "كسر": "to break (intr.)",
            "قلب": "to overturn",
            "فتح": "to open (intr.)",
            "غلق": "to close (intr.)",
            "قطع": "to be cut off",
            "صرف": "to turn away",
            "قاد": "to be led",
            "طلق": "to be released",
            "حل": "to be untied",
            "عقد": "to be tied",
            "هزم": "to be defeated",
            "كشف": "to be uncovered",
            "جمع": "to gather (intr.)",
            "فصل": "to be separated",
        },
    ),
    "5E": RumusSemantics(
        meaning_id="Becoming a color / quality",
        meaning_en="Becoming a color / quality",
        verb_formula_id="to become {root}",
        verb_formula_en="to become {root}",
        special_cases_id={
            "حمر": "to become red",
            "صفر": "to become yellow",
            "خضر": "to become green",
            "زرق": "to become blue",
            "بيض": "to become white",
            "سود": "to become black",
            "عوج": "to become crooked",
            "حول": "to change",
            "طول": "to become long",
            "عرض": "to become wide",
        },
    ),
    "6": RumusSemantics(
        meaning_id="To ask for / to consider (something)",
        meaning_en="To ask for / to consider (something)",
        verb_formula_id="to ask for {root}",
        verb_formula_en="to ask for {root}",
        special_cases_id={
            "غفر": "to ask for forgiveness",
            "علم": "to inquire",
            "عان": "to ask for help",
            "خرج": "to ask to exit",
            "قدر": "to deem capable",
            "كبر": "to deem great",
            "حسن": "to deem good",
            "عظم": "to glorify",
            "عجل": "to hasten",
            "قام": "to ask to stand",
            "فتح": "to ask to open",
            "نصر": "to ask for victory",
            "هدى": "to ask for guidance",
            "رحم": "to ask for mercy",
            "غنى": "to be self-sufficient",
            "ضعف": "to deem weak",
        },
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
# Indonesian Verb Stem Extraction
# ═══════════════════════════════════════════════════════════════════════════

# Indonesian verbs commonly take the meN- prefix which assimilates:
#   me- + l, m, n, r, w, y → me- (no change): me-lafal, me-nulis
#   me- + d, c, j, sy, z → men-: men-dapat, men-cari
#   me- + t → men- (t drops): menulis (from tulis)
#   me- + s → meny- (s drops): menyapu (from sapu)
#   me- + p → mem- (p drops): memukul (from pukul)
#   me- + b, f → mem-: mem-buka, mem-fasilitasi
#   me- + k, g, h, kh → meng-: meng-ambil (k drops), meng-gambar
#   me- + a, i, u, e, o → meng-: meng-isi, meng-ukur

# We only need the REVERSE (stem extraction) for imperative and derived forms.
# This is imprecise — we use heuristics.

# Mapping of meN- prefix patterns to their dropped consonants.
# Each entry: (prefix_chars, dropped_consonant)
# The function checks verb[:len(prefix)] == prefix, then prepends
# dropped_consonant (if any) to the remaining stem.
#
# IMPORTANT:
#   - For 'meng' prefix (me- + k OR me- + vowel): the verb form looks the same
#     (mengXXXX) for both cases. We can't distinguish without a dictionary.
#     Since Arabic roots are more often vowel-initial, we default to NO dropped
#     consonant (removing 'meng' only). This is correct for vowel-initial,
#     slightly wrong for k-drop verbs (e.g., mengirim → 'irim' instead of 'kirim').
#   - For 'mengg' prefix: me- + g (g kept, geminated) → prepend 'g'
#   - Users can add special case overrides below for common words.
_ME_PREFIX_RULES: list[tuple[str, str]] = [
    # menge- + 1-syllable words: mengecat → cat
    ("menge", ""),
    # me- + s → meny- (s drops): menyapu → sapu
    ("menyu", "s"),
    ("meny", "s"),
    # me- + b → mem- (b kept): membuka → buka
    # me- + m → mem- (m kept): memakan → makan
    # NOTE: me- + p → mem- (p drops): memukul → pukul cannot be detected
    #   because 'p' was dropped from the verb form (memukul, not mempukul).
    #   Heuristic below gives 'mukul' instead of 'pukul'.
    ("memb", "b"),
    ("mem", "m"),
    # me- + vowel/k/g/kh → meng-: all produce 'mengXXXX' in verb form.
    # Can't distinguish without dictionary. Default: no prepended consonant.
    ("meng", ""),
    # me- + t → men- (t drops): menulis → tulis
    # me- + d → men- (d kept, but prepend anyway): mendapat → dapat...
    #     Actually mendapat → 'd' + 'apat' = 'dapat' ✓
    # me- + c → men- (c kept): mencuci → 'c' + 'uci' = 'cuci'... 'men' prefix, 'c' prepended
    ("mend", "d"),
    ("ment", "t"),
    ("men", "t"),    # most common: me- + t → men- (t drops)
    # Fallback: just strip 'me'
    ("me", ""),
]


def _extract_verb_stem_id(verb_meaning: str) -> str:
    """Extract the bare stem from an Indonesian me- verb.

    Examples:
        'menulis' → 'tulis'
        'memukul' → 'pukul'
        'membuka' → 'buka'
        'mengambil' → 'ambil'
        'menyapu' → 'sapu'
        'mendapat' → 'dapat'
        'mengajar' → 'ajar'

    Returns the verb meaning as-is if it doesn't start with 'me'.
    """
    if not verb_meaning or not verb_meaning.startswith("me"):
        return verb_meaning

    for prefix, dropped in _ME_PREFIX_RULES:
        idx = len(prefix)
        if len(verb_meaning) >= idx and verb_meaning[:idx] == prefix:
            stem = verb_meaning[idx:]
            if stem:
                if dropped:
                    return dropped + stem
                return stem

    return verb_meaning[2:] if verb_meaning.startswith("me") else verb_meaning


def _extract_verb_stem_en(verb_meaning: str) -> str:
    """Extract the bare verb from an English 'to ___' phrase.

    Examples:
        'to write' → 'write'
        'to teach' → 'teach'
        'menulis' → 'menulis'  (not English, return as-is)

    Returns the verb meaning as-is if it doesn't start with 'to '.
    """
    if verb_meaning.startswith("to "):
        return verb_meaning[3:]
    return verb_meaning


# ═══════════════════════════════════════════════════════════════════════════
# Form-Level Translation Templates
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class FormTemplate:
    """Template for translating a single Ishthilahi column."""

    id_template: str
    """Indonesian template. Placeholders:
    {verb} — Rumus-level verb meaning (e.g., 'menulis', 'mengajar')
    {stem} — Bare stem extracted from verb (e.g., 'tulis', 'ajar')
    {root} — Root meaning from dictionary (e.g., 'tulis')
    """

    en_template: str
    """English template. Same placeholders.
    {verb} — Rumus-level verb meaning (e.g., 'to write', 'to teach')
    {stem} — Bare stem (e.g., 'write', 'teach')
    {root} — Root meaning from dictionary (e.g., 'write')
    """


# Default templates for all Rumus (can be overridden per-Rumus)
# ── English Irregular Verb Past Participles ────────────────────────
# Past participle for irregular verbs used in templates like "has {pp}"
_IRREGULAR_PP: dict[str, str] = {
    "write": "written",
    "hit": "hit",
    "open": "opened",
    "help": "helped",
    "read": "read",
    "teach": "taught",
    "learn": "learned",
    "eat": "eaten",
    "drink": "drunk",
    "go": "gone",
    "come": "come",
    "see": "seen",
    "hear": "heard",
    "take": "taken",
    "give": "given",
    "know": "known",
    "tell": "told",
    "say": "said",
    "speak": "spoken",
    "do": "done",
    "make": "made",
    "find": "found",
    "send": "sent",
    "forgive": "forgiven",
    "forbid": "forbidden",
    "forget": "forgotten",
    "begin": "begun",
    "break": "broken",
    "bring": "brought",
    "build": "built",
    "buy": "bought",
    "choose": "chosen",
    "cut": "cut",
    "draw": "drawn",
    "fall": "fallen",
    "feel": "felt",
    "fight": "fought",
    "fly": "flown",
    "get": "gotten",
    "grow": "grown",
    "hide": "hidden",
    "keep": "kept",
    "lead": "led",
    "leave": "left",
    "lose": "lost",
    "meet": "met",
    "pay": "paid",
    "put": "put",
    "run": "run",
    "sell": "sold",
    "show": "shown",
    "shut": "shut",
    "sing": "sung",
    "sit": "sat",
    "stand": "stood",
    "tear": "torn",
    "think": "thought",
    "understand": "understood",
    "win": "won",
}


def _get_past_participle(stem: str) -> str:
    """Get the English past participle for a verb stem.
    Handles irregular verbs; falls back to -ed for regular ones."""
    if stem in _IRREGULAR_PP:
        return _IRREGULAR_PP[stem]
    # Regular: add -ed (with basic doubling rules)
    if stem.endswith("e"):
        return stem + "d"
    if stem.endswith("y") and len(stem) > 2 and stem[-2] not in "aeiou":
        return stem[:-1] + "ied"
    # Simple -ed for everything else
    return stem + "ed"


def _get_gerund(stem: str) -> str:
    """Get the English gerund (-ing form) for a verb stem."""
    if stem.endswith("e") and not stem.endswith("ee"):
        return stem[:-1] + "ing"
    return stem + "ing"


def _get_third_person(stem: str) -> str:
    """Get the third person singular form (-s form) for a verb stem."""
    if stem.endswith(('s', 'sh', 'ch', 'x', 'z', 'o')):
        return stem + "es"
    if stem.endswith("y") and len(stem) > 2 and stem[-2] not in "aeiou":
        return stem[:-1] + "ies"
    return stem + "s"


# Form templates with English placeholders:
# {verb} — Rumus-level verb meaning (e.g., 'to write', 'to teach')
# {stem} — Bare stem (e.g., 'write', 'teach')
# {root} — Root meaning from dictionary (e.g., 'write')
# {pp} — Past participle (e.g., 'written', 'helped')
# {ger} — Gerund (-ing form: 'writing', 'helping')
# {3sg} — Third person singular (e.g., 'writes', 'helps')

_FORM_TEMPLATES: dict[str, FormTemplate] = {
    "fiil_madhi": FormTemplate(
        id_template="telah {verb}",
        en_template="has {pp}",
    ),
    "fiil_mudhari": FormTemplate(
        id_template="sedang/akan {verb}",
        en_template="is {ger}",
    ),
    "fiil_amr": FormTemplate(
        id_template="{stem}lah",
        en_template="{stem}!",
    ),
    "fiil_nahi": FormTemplate(
        id_template="jangan {stem}",
        en_template="don't {stem}!",
    ),
    "mashdar": FormTemplate(
        id_template="{stem}an",
        en_template="{ger}",
    ),
    "ism_fail": FormTemplate(
        id_template="pe{stem}",
        en_template="one who {3sg}",
    ),
    "ism_maful": FormTemplate(
        id_template="yang di{stem}",
        en_template="that which is {pp}",
    ),
    "zamami": FormTemplate(
        id_template="waktu/tempat {verb}",
        en_template="time/place of {ger}",
    ),
}

# Override templates for specific Rumus where the pattern differs
_RUMUS_FORM_TEMPLATES: dict[str, dict[str, FormTemplate]] = {
    "4A": {
        "mashdar": FormTemplate(
            id_template="pe{stem}an / {stem}an",
            en_template="{stem}ing / act of {stem}ing",
        ),
        "ism_fail": FormTemplate(
            id_template="pe{stem} / peng{stem}",
            en_template="one who {stem}s (repeatedly)",
        ),
        "ism_maful": FormTemplate(
            id_template="yang di{stem} / yang diajar",
            en_template="one who is {stem}ed",
        ),
    },
    "5A": {
        "mashdar": FormTemplate(
            id_template="pe{stem}an / {stem}",
            en_template="{stem}ing / act of {stem}ing",
        ),
        "ism_fail": FormTemplate(
            id_template="yang me{stem} / pelajar",
            en_template="one who {stem}s / learner",
        ),
    },
    "5D": {
        "fiil_madhi": FormTemplate(
            id_template="telah {verb} / ter{stem}",
            en_template="has been {stem}ed / got {stem}ed",
        ),
        "mashdar": FormTemplate(
            id_template="ke{stem}an / pe{stem}an",
            en_template="being {stem}ed / state of {stem}ing",
        ),
        "ism_fail": FormTemplate(
            id_template="yang ter{stem}",
            en_template="that which gets {stem}ed",
        ),
        "ism_maful": FormTemplate(
            id_template="yang ter{stem}",
            en_template="that which is {stem}ed (unintentionally)",
        ),
    },
    "5E": {
        "fiil_madhi": FormTemplate(
            id_template="telah {verb} / menjadi {stem}",
            en_template="has become {stem}",
        ),
        "mashdar": FormTemplate(
            id_template="ke{stem}an",
            en_template="{stem}ness / state of being {stem}",
        ),
        "ism_fail": FormTemplate(
            id_template="yang {stem}",
            en_template="that which is {stem}",
        ),
    },
    "6": {
        "fiil_madhi": FormTemplate(
            id_template="telah {verb}",
            en_template="has asked for {stem} / sought {stem}",
        ),
        "mashdar": FormTemplate(
            id_template="permintaan {stem}",
            en_template="request for {stem}ing",
        ),
        "ism_fail": FormTemplate(
            id_template="yang meminta {stem}",
            en_template="one who asks for {stem}",
        ),
        "ism_maful": FormTemplate(
            id_template="yang dimintai {stem}",
            en_template="that which is asked for {stem}",
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# Root Meaning Helpers
# ═══════════════════════════════════════════════════════════════════════════

# Some root meanings can't be found in the dictionary (e.g., 4-letter roots).
# Provide a fallback that at least returns the root letters.
_FALLBACK_ROOTS_ID: dict[str, str] = {
    "زلزل": "guncang",
    "وسوس": "bisik",
    "جعجع": "henti",
    "بعبع": "takut",
    "صلصل": "bunyi",
    "حمر": "merah",
    "صفر": "kuning",
    "خضر": "hijau",
    "زرق": "biru",
    "بيض": "putih",
    "سود": "hitam",
    "شور": "runding",
    "غفر": "ampun",
    "حرم": "hormat",
    "كرم": "mulia",
    "جدد": "baru",
    "وحد": "esa",
    "قدس": "suci",
    "ربو": "tumbuh",
}

_FALLBACK_ROOTS_EN: dict[str, str] = {
    "زلزل": "shake",
    "وسوس": "whisper",
    "جعجع": "halt",
    "بعبع": "frighten",
    "صلصل": "ring",
    "حمر": "red",
    "صفر": "yellow",
    "خضر": "green",
    "زرق": "blue",
    "بيض": "white",
    "سود": "black",
    "شور": "consult",
    "غفر": "forgive",
    "حرم": "honor/forbid",
    "كرم": "noble",
    "جدد": "new",
    "وحد": "one",
    "قدس": "holy",
    "ربو": "grow",
}


def _get_root_meaning_id(root: str) -> str:
    """Get the Indonesian meaning of a root from the dictionary or fallback."""
    if not root:
        return ""

    # Try dictionary lookup first
    meaning = dict_lookup_id(root)
    if meaning:
        return meaning

    # Try fallback
    plain = root
    if HAS_PYARABIC:
        plain = araby.strip_tashkeel(root)
    plain = "".join(c for c in plain if c.isalpha())

    if plain in _FALLBACK_ROOTS_ID:
        return _FALLBACK_ROOTS_ID[plain]

    return root  # Last resort: return the root letters


def _get_root_meaning_en(root: str) -> str:
    """Get the English meaning of a root from the dictionary or fallback."""
    if not root:
        return ""

    meaning = dict_lookup_en(root)
    if meaning:
        return meaning

    plain = root
    if HAS_PYARABIC:
        plain = araby.strip_tashkeel(root)
    plain = "".join(c for c in plain if c.isalpha())

    if plain in _FALLBACK_ROOTS_EN:
        return _FALLBACK_ROOTS_EN[plain]

    return root


# ═══════════════════════════════════════════════════════════════════════════
# Rumus-Specific Verb Meaning Derivation
# ═══════════════════════════════════════════════════════════════════════════

def _get_verb_meaning_id(rumus: str, root: str) -> str:
    """Derive the Rumus-specific base Indonesian verb meaning.

    Priority:
      1. Special case override (root + rumus specific)
      2. verb_formula_id with {root} replaced
      3. Root meaning from dictionary
      4. Fallback
    """
    root_plain = _get_plain_root(root)
    semantics = RUMUS_SEMANTICS_ID.get(rumus)

    # Priority 1: special case for this specific root + rumus
    if semantics and root_plain in semantics.special_cases_id:
        return semantics.special_cases_id[root_plain]

    # Priority 2: Use verb formula
    if semantics and semantics.verb_formula_id != "{root}":
        root_meaning = _get_root_meaning_id(root)
        formula = semantics.verb_formula_id
        return formula.replace("{root}", root_meaning)

    # Priority 3: Root meaning from dictionary (or root letters as fallback)
    # Even if root_meaning == root (no lookup found), prefer it over
    # the semantic description text to keep translation templates clean.
    root_meaning = _get_root_meaning_id(root)
    if root_meaning:
        return root_meaning

    # Priority 4: Semantic description (last resort)
    if semantics:
        return semantics.meaning_id

    return root or root_meaning


def _get_verb_meaning_en(rumus: str, root: str) -> str:
    """Derive the Rumus-specific base English verb meaning.

    Same priority structure as _get_verb_meaning_id.
    """
    root_plain = _get_plain_root(root)
    semantics = RUMUS_SEMANTICS_EN.get(rumus)

    if semantics and root_plain in semantics.special_cases_id:
        return semantics.special_cases_id[root_plain]

    if semantics and semantics.verb_formula_en != "{root}":
        root_meaning = _get_root_meaning_en(root)
        formula = semantics.verb_formula_en
        return formula.replace("{root}", root_meaning)

    root_meaning = _get_root_meaning_en(root)
    if root_meaning:
        return root_meaning

    if semantics:
        return semantics.meaning_en

    return root_meaning or root


def _get_plain_root(root: str) -> str:
    """Strip diacritics from root for lookup purposes."""
    if HAS_PYARABIC:
        return araby.strip_tashkeel(root)
    return "".join(c for c in root if c.isalpha() or not unicodedata.combining(c))


# ═══════════════════════════════════════════════════════════════════════════
# Template Application
# ═══════════════════════════════════════════════════════════════════════════

def _apply_template(
    template: str,
    verb: str,
    stem: str,
    root_meaning: str,
    pp: str = "",
    ger: str = "",
    sg3: str = "",
) -> str:
    """Replace placeholders in a template string.

    Placeholders:
      {verb} — full verb meaning
      {stem} — bare stem
      {root} — root meaning from dictionary
      {pp}   — past participle (English)
      {ger}  — gerund/-ing form (English)
      {3sg}  — third person singular (English)
    """
    return (
        template
        .replace("{verb}", verb)
        .replace("{stem}", stem)
        .replace("{root}", root_meaning)
        .replace("{pp}", pp)
        .replace("{ger}", ger)
        .replace("{3sg}", sg3)
    )


def _get_form_templates(rumus: str) -> dict[str, FormTemplate]:
    """Get the form templates for a given Rumus, with Rumus-specific overrides."""
    templates = dict(_FORM_TEMPLATES)
    overrides = _RUMUS_FORM_TEMPLATES.get(rumus, {})
    for form_name, form_template in overrides.items():
        templates[form_name] = form_template
    return templates


# ═══════════════════════════════════════════════════════════════════════════
# Main Translation Function
# ═══════════════════════════════════════════════════════════════════════════

def translate_ishthilahi(
    root: str,
    rumus: str,
    bab: int = 1,
    table_dict: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Generate Indonesian and English translations for all 8 Ishthilahi columns.

    Args:
        root: Root letters (3 for triliteral, 4 for quadriliteral).
        rumus: Rumus code ("3A", "3B", "3C", "4A", ..., "6").
        bab: Conjugation bab (1-6, only for Rumus 3). Used for context.
        table_dict: Optional dict of form_name -> Arabic text (from generate_ishthilahi).
            If provided, the output includes 'forms' with the Arabic forms.

    Returns:
        Dict with:
            - root: str
            - rumus: str
            - bab: int
            - root_meaning: dict with 'id' and 'en' root meanings
            - rumus_semantic: dict with 'id' and 'en' rumus descriptions
            - verb_base: dict with 'id' and 'en' Rumus-specific verb base
            - translation_formula: dict with 'id' and 'en' formula descriptions
            - form_templates: dict of form_name -> dict of template strings
            - translations: dict with 'id' and 'en' sections, each being
              list of {form_name, form_label_id, translation} dicts
            - forms: (only if table_dict provided) the Arabic forms alongside translations
    """
    # 1. Root meaning
    root_meaning_id = _get_root_meaning_id(root)
    root_meaning_en = _get_root_meaning_en(root)

    # 2. Rumus semantics
    sem_id = RUMUS_SEMANTICS_ID.get(rumus)
    sem_en = RUMUS_SEMANTICS_EN.get(rumus)

    rumus_meaning_id = sem_id.meaning_id if sem_id else RUMUS_MEANING.get(rumus, "")
    rumus_meaning_en = sem_en.meaning_en if sem_en else ""

    # 3. Rumus-specific verb base
    verb_id = _get_verb_meaning_id(rumus, root)
    verb_en = _get_verb_meaning_en(rumus, root)

    # 4. Extract stems
    stem_id = _extract_verb_stem_id(verb_id)
    stem_en = _extract_verb_stem_en(verb_en)

    # 5. Get form templates for this Rumus
    templates = _get_form_templates(rumus)

    # 6. Apply templates for all 8 forms
    translations_id: list[dict[str, str]] = []
    translations_en: list[dict[str, str]] = []
    trans_dict_id: dict[str, str] = {}
    trans_dict_en: dict[str, str] = {}
    formula_desc_id: dict[str, str] = {}
    formula_desc_en: dict[str, str] = {}

    for i, form_name in enumerate(FORM_NAMES):
        form_num = i + 1
        try:
            fn = FormNumber(form_num)
            label_id = FORM_LABELS_ID.get(fn, "")
        except (ValueError, KeyError):
            label_id = ""

        template = templates.get(form_name, _FORM_TEMPLATES[form_name])

        # Precompute English derived forms
        pp_en = _get_past_participle(stem_en)
        ger_en = _get_gerund(stem_en)
        sg3_en = _get_third_person(stem_en)

        # Apply ID template
        trans_id = _apply_template(
            template.id_template,
            verb_id, stem_id, root_meaning_id,
        )
        translations_id.append({
            "form_number": form_num,
            "form_name": form_name,
            "form_label_id": label_id,
            "translation": trans_id,
        })
        trans_dict_id[form_name] = trans_id
        formula_desc_id[form_name] = template.id_template

        # Apply EN template
        trans_en = _apply_template(
            template.en_template,
            verb_en, stem_en, root_meaning_en,
            pp=pp_en, ger=ger_en, sg3=sg3_en,
        )
        translations_en.append({
            "form_number": form_num,
            "form_name": form_name,
            "form_label_id": label_id,
            "translation": trans_en,
        })
        trans_dict_en[form_name] = trans_en
        formula_desc_en[form_name] = template.en_template

    # 7. Build result
    result: dict[str, Any] = {
        "root": root,
        "rumus": rumus,
        "bab": bab,
        "root_meaning": {
            "id": root_meaning_id,
            "en": root_meaning_en,
        },
        "rumus_semantic": {
            "id": rumus_meaning_id,
            "en": rumus_meaning_en,
        },
        "verb_base": {
            "id": verb_id,
            "en": verb_en,
        },
        "verb_stem": {
            "id": stem_id,
            "en": stem_en,
        },
        "translation_formula": {
            "id": formula_desc_id,
            "en": formula_desc_en,
        },
        "translations": {
            "id": translations_id,
            "en": translations_en,
        },
        "translations_dict": {
            "id": trans_dict_id,
            "en": trans_dict_en,
        },
    }

    # 8. Include Arabic forms if provided
    if table_dict:
        forms = []
        for i, form_name in enumerate(FORM_NAMES):
            forms.append({
                "form_number": i + 1,
                "form_name": form_name,
                "arabic": table_dict.get(form_name, ""),
                "translation_id": trans_dict_id.get(form_name, ""),
                "translation_en": trans_dict_en.get(form_name, ""),
            })
        result["forms"] = forms

    return result


# ═══════════════════════════════════════════════════════════════════════════
# Convenience: Pipeline Integration
# ═══════════════════════════════════════════════════════════════════════════

def add_translations_to_pipeline_result(
    pipeline_result: dict[str, Any],
) -> dict[str, Any]:
    """Add translation overlay to a tashrif_pipeline result.

    Takes the output of `tashrif_analyze()` and adds translations for
    each column.

    Returns the same dict with added 'translations' key.
    """
    root = pipeline_result.get("root", "")
    rumus = pipeline_result.get("rumus", "")
    bab = pipeline_result.get("bab", 1)
    table_dict = pipeline_result.get("ishthilahi_dict", {})

    trans = translate_ishthilahi(root, rumus, bab, table_dict)

    # Merge translations pipeline_result
    pipeline_result["translations"] = trans

    # Add per-form translations to each table row
    table = pipeline_result.get("ishthilahi_table", [])
    trans_dict_id = trans.get("translations_dict", {}).get("id", {})
    trans_dict_en = trans.get("translations_dict", {}).get("en", {})

    for row in table:
        fn = row.get("form_name", "")
        row["translation_id"] = trans_dict_id.get(fn, "")
        row["translation_en"] = trans_dict_en.get(fn, "")
        row["translation_formula_id"] = (
            trans.get("translation_formula", {})
            .get("id", {}).get(fn, "")
        )
        row["translation_formula_en"] = (
            trans.get("translation_formula", {})
            .get("en", {}).get(fn, "")
        )

    return pipeline_result


# ═══════════════════════════════════════════════════════════════════════════
# Demo / Test
# ═══════════════════════════════════════════════════════════════════════════

def _demo(output_path: str = ""):
    """Generate translations for all 13 rumus and display them."""
    lines = []
    lines.append("=" * 120)
    lines.append("  TASHRIF TRANSLATION OVERLAY — Phase 4 Demo")
    lines.append("  Indonesian + English translations for all 8 Ishthilahi columns")
    lines.append("=" * 120)

    test_cases = [
        # (root, rumus, bab, example_word)
        ("فتح", "3A", 1, "فَتَحَ"),
        ("ضرب", "3B", 2, "ضَرَبَ"),
        ("نصر", "3C", 3, "نَصَرَ"),
        ("كتب", "3C", 3, "كَتَبَ"),
        ("علم", "4A", 1, "عَلَّمَ"),
        ("شور", "4B", 1, "شَاوَرَ"),
        ("سلم", "4C", 1, "أَسْلَمَ"),
        ("زلزل", "4D", 1, "زَلْزَلَ"),
        ("علم", "5A", 1, "تَعَلَّمَ"),
        ("عرف", "5B", 1, "تَعَارَفَ"),
        ("حرم", "5C", 1, "اِحْتَرَمَ"),
        ("حمر", "5E", 1, "اِحْمَرَّ"),
        ("غفر", "6",  1, "اِسْتَغْفَرَ"),
        # Special: 5D with passive meaning
        ("كسر", "5D", 1, "اِنْكَسَرَ"),
    ]

    for root, rumus, bab, example in test_cases:
        lines.append("")
        lines.append("-" * 120)
        lines.append(f"  {example}  |  Root: {root}  |  Rumus: {rumus}  |  Bab: {bab}")
        lines.append("-" * 120)

        result = translate_ishthilahi(root, rumus, bab)

        id_meaning = result["root_meaning"]["id"]
        en_meaning = result["root_meaning"]["en"]
        verb_id = result["verb_base"]["id"]
        verb_en = result["verb_base"]["en"]
        rumus_sem = result["rumus_semantic"]["id"]

        lines.append(f"  Root meaning:    ID: {id_meaning:<30} EN: {en_meaning}")
        lines.append(f"  Rumus semantic:  {rumus_sem}")
        lines.append(f"  Verb base (ID):  {verb_id}")
        lines.append(f"  Verb base (EN):  {verb_en}")
        lines.append("")

        # Display the 8-column translation table
        header = (
            f"  {'#':<2} {'Form':<14} {'Indonesian Translation':<36} "
            f"{'English Translation':<36} {'ID Formula':<20}"
        )
        lines.append(header)
        lines.append("  " + "-" * 108)

        for row_id, row_en in zip(
            result["translations"]["id"],
            result["translations"]["en"],
        ):
            tr_id = row_id["translation"]
            tr_en = row_en["translation"]
            formula_id = result["translation_formula"]["id"].get(
                row_id["form_name"], ""
            )
            lines.append(
                f"  {row_id['form_number']:<2} {row_id['form_name']:<14} "
                f"{tr_id:<36} {tr_en:<36} {formula_id:<20}"
            )

    lines.append("")
    lines.append("=" * 120)
    lines.append(f"  Processed {len(test_cases)} roots through the translation overlay.")
    lines.append(f"  Dictionary ID: {'available' if HAS_DICT_ID else 'NOT available'}")
    lines.append(f"  Dictionary EN: {'available' if HAS_DICT_EN else 'NOT available'}")
    lines.append("=" * 120)

    # --- Also show the pipeline integration demo ---
    lines.append("")
    lines.append("=" * 120)
    lines.append("  PIPELINE INTEGRATION DEMO (translate_ishthilahi + table_dict)")
    lines.append("=" * 120)

    try:
        from tashrif_generator import generate_ishthilahi

        for root, rumus, bab, example in test_cases[:3]:  # Show first 3 with Arabic
            lines.append("")
            lines.append(f"  --- {example} (Root: {root}, Rumus: {rumus}, Bab: {bab}) ---")

            gen_result = generate_ishthilahi(root, rumus, bab)
            table_dict = gen_result.get("table_dict", {})

            combined = translate_ishthilahi(root, rumus, bab, table_dict)

            header = (
                f"  {'#':<2} {'Form':<14} {'Arabic':<22} "
                f"{'Indonesian':<30} {'English':<30}"
            )
            lines.append(header)
            lines.append("  " + "-" * 98)

            for form in combined.get("forms", []):
                lines.append(
                    f"  {form['form_number']:<2} {form['form_name']:<14} "
                    f"{form['arabic']:<22} {form['translation_id']:<30} "
                    f"{form['translation_en']:<30}"
                )

    except ImportError as e:
        lines.append(f"  (Integration demo skipped: {e})")

    text = "\n".join(lines)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Results written to {output_path}")
    else:
        try:
            print(text)
        except UnicodeEncodeError:
            print("(Unicode output not supported in this console)")


if __name__ == "__main__":
    import sys
    out = ""
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        out = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
    _demo(output_path=out)
