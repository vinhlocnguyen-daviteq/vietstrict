#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import Tuple, List

# -----------------------------
# VietStrict (VS1D) v1.1 - reference implementation (spec-driven)
# -----------------------------

TONE_SUFFIXES = {"s", "f", "r", "x", "j"}  # sắc, huyền, hỏi, ngã, nặng

# Marker vowels (no tone)
VOWEL_MARKERS = {
    "ă": "av",
    "â": "az",
    "ê": "ez",
    "ô": "oz",
    "ơ": "ow",
    "ư": "uw",
    "đ": "dd",
}
REV_VOWEL_MARKERS = {v: k for k, v in VOWEL_MARKERS.items()}

# Vowel clusters (no tone) - v1.1
CLUSTERS_QN_TO_VS = {
    "uyê": "uyez",
    "iê": "iez",
    "yê": "yez",
    "uô": "uoz",
    "ươ": "uow",
    "ưa": "uwa",
    "uê": "uez",
}
CLUSTERS_VS_TO_QN = {v: k for k, v in CLUSTERS_QN_TO_VS.items()}

# Vietnamese codas supported in spec
CODAS = ["ng", "nh", "p", "t", "c", "m", "n"]

# Onset list for splitting Quốc ngữ (encode) and parsing VS (decode)
# Order: longest first
ONSETS = [
    "ngh", "ch", "gh", "kh", "nh", "ng",
    "ph", "th", "tr", "qu", "gi",
    "dd",  # for đ after marker conversion (rare as onset in VS form)
    "b", "c", "d", "g", "h", "k", "l", "m", "n", "p", "q", "r", "s", "t", "v", "x",
]

# Build accented vowel maps: accented -> (base, tone) and (base, tone) -> accented
def _build_accent_maps() -> Tuple[dict[str, Tuple[str, str]], dict[Tuple[str, str], str]]:
    groups = {
        "a":  {"": "a", "s": "á", "f": "à", "r": "ả", "x": "ã", "j": "ạ"},
        "ă":  {"": "ă", "s": "ắ", "f": "ằ", "r": "ẳ", "x": "ẵ", "j": "ặ"},
        "â":  {"": "â", "s": "ấ", "f": "ầ", "r": "ẩ", "x": "ẫ", "j": "ậ"},
        "e":  {"": "e", "s": "é", "f": "è", "r": "ẻ", "x": "ẽ", "j": "ẹ"},
        "ê":  {"": "ê", "s": "ế", "f": "ề", "r": "ể", "x": "ễ", "j": "ệ"},
        "i":  {"": "i", "s": "í", "f": "ì", "r": "ỉ", "x": "ĩ", "j": "ị"},
        "o":  {"": "o", "s": "ó", "f": "ò", "r": "ỏ", "x": "õ", "j": "ọ"},
        "ô":  {"": "ô", "s": "ố", "f": "ồ", "r": "ổ", "x": "ỗ", "j": "ộ"},
        "ơ":  {"": "ơ", "s": "ớ", "f": "ờ", "r": "ở", "x": "ỡ", "j": "ợ"},
        "u":  {"": "u", "s": "ú", "f": "ù", "r": "ủ", "x": "ũ", "j": "ụ"},
        "ư":  {"": "ư", "s": "ứ", "f": "ừ", "r": "ử", "x": "ữ", "j": "ự"},
        "y":  {"": "y", "s": "ý", "f": "ỳ", "r": "ỷ", "x": "ỹ", "j": "ỵ"},
    }

    accent_to_base: dict[str, Tuple[str, str]] = {}
    base_to_accent: dict[Tuple[str, str], str] = {}

    for base, mp in groups.items():
        for tone, ch in mp.items():
            accent_to_base[ch] = (base, tone)
            base_to_accent[(base, tone)] = ch

        # uppercase variants
        base_u = base.upper()
        for tone, ch in mp.items():
            ch_u = ch.upper()
            accent_to_base[ch_u] = (base_u, tone)
            base_to_accent[(base_u, tone)] = ch_u

    return accent_to_base, base_to_accent

ACCENT_TO_BASE, BASE_TO_ACCENT = _build_accent_maps()

@dataclass(frozen=True)
class ParsedVS:
    onset: str
    vowel_part: str   # VS vowel part (may include clusters + markers + plain vowels), no tone
    coda: str
    tone: str         # s f r x j or ""

# -----------------------------
# Encode (Quốc ngữ -> VS)
# -----------------------------

def _split_onset_qn(s: str) -> Tuple[str, str]:
    """Split Quốc ngữ syllable into onset + rest (rhyme) using orthographic onsets."""
    s_lower = s.lower()
    for o in sorted(ONSETS, key=len, reverse=True):
        if s_lower.startswith(o):
            return s[:len(o)], s[len(o):]
    return "", s

def _strip_tone_qn(s: str) -> Tuple[str, str]:
    """Return (string without tone marks, tone_suffix)."""
    tone = ""
    out = []
    for ch in s:
        if ch in ACCENT_TO_BASE:
            base, t = ACCENT_TO_BASE[ch]
            if t:
                if tone and tone != t:
                    raise ValueError(f"Multiple tones in one syllable: {s!r}")
                tone = t
            out.append(base)
        else:
            out.append(ch)
    return "".join(out), tone

def _apply_vowel_markers_encode(qn_no_tone: str) -> str:
    """Apply dd + av/az/ez/oz/ow/uw markers on single letters."""
    res: List[str] = []
    for ch in qn_no_tone:
        if ch in ("đ", "Đ"):
            res.append("dd" if ch == "đ" else "DD")
            continue

        low = ch.lower()
        if low in VOWEL_MARKERS:
            token = VOWEL_MARKERS[low]
            res.append(token.upper() if ch.isupper() else token)
        else:
            res.append(ch)
    return "".join(res)

def encode(qn: str) -> str:
    """
    Encode a single Vietnamese syllable (Quốc ngữ) into VS1D.
    Assumes input is one syllable (no spaces).
    """
    if not qn:
        return qn

    qn_no_tone, tone = _strip_tone_qn(qn)

    onset, rhyme = _split_onset_qn(qn_no_tone)

    # Replace vowel clusters in the rhyme (orthography-preserving)
    rhyme_lower = rhyme.lower()
    for qn_cluster, vs_cluster in sorted(CLUSTERS_QN_TO_VS.items(), key=lambda kv: len(kv[0]), reverse=True):
        rhyme_lower = rhyme_lower.replace(qn_cluster, vs_cluster)

    vs = onset.lower() + rhyme_lower

    # Apply markers (ă â ê ô ơ ư, đ) across the whole syllable
    vs = _apply_vowel_markers_encode(vs)

    # Append tone suffix
    if tone:
        vs = vs + tone

    return vs

# -----------------------------
# Parse VS (VS -> components)
# -----------------------------

def _has_vowel_signal(s: str) -> bool:
    if not s:
        return False
    if re.search(r"[aeiouy]", s):
        return True
    if any(tok in s for tok in REV_VOWEL_MARKERS.keys()):
        return True
    if any(tok in s for tok in CLUSTERS_VS_TO_QN.keys()):
        return True
    return False

def _parse_vs(vs: str) -> ParsedVS:
    """
    Deterministic parse following spec spirit:
    1) tone suffix (if any) at end
    2) coda (if any) at end (longest-match)
    3) remaining stem = onset + vowel_part
       onset is longest-match from ONSETS such that remaining has vowel signal;
       otherwise onset is empty.
    """
    if not vs:
        raise ValueError("Empty syllable")

    core = vs.lower()

    # 1) tone suffix
    tone = ""
    if core[-1] in TONE_SUFFIXES:
        tone = core[-1]
        core = core[:-1]

    # 2) coda suffix (longest-match)
    coda = ""
    stem = core
    for cd in sorted(CODAS, key=len, reverse=True):
        if stem.endswith(cd):
            coda = cd
            stem = stem[:-len(cd)]
            break

    # stem = onset + vowel_part
    onset = ""
    vowel_part = stem

    # choose onset (longest-match) only if remainder has vowel signal
    for o in sorted(ONSETS, key=len, reverse=True):
        if stem.startswith(o):
            rem = stem[len(o):]
            if _has_vowel_signal(rem):
                onset = o
                vowel_part = rem
                break

    # if no onset matched, onset is empty; ensure vowel_part has vowel signal
    if onset == "":
        vowel_part = stem
        if not _has_vowel_signal(vowel_part):
            raise ValueError(f"Cannot find vowel part in {vs!r}")

    return ParsedVS(onset=onset, vowel_part=vowel_part, coda=coda, tone=tone)

# -----------------------------
# Decode (VS -> Quốc ngữ)
# -----------------------------

def _vs_vowel_to_qn(vs_vowel_part: str) -> str:
    """
    Convert VS vowel_part (may contain cluster tokens and marker tokens) to Quốc ngữ (no tone).
    Example: 'ozi' -> 'ôi' ; 'uyez' -> 'uyê'
    """
    s = vs_vowel_part.lower()

    # Replace long clusters first
    for tok, qn in sorted(CLUSTERS_VS_TO_QN.items(), key=lambda kv: len(kv[0]), reverse=True):
        s = s.replace(tok, qn)

    # Replace marker tokens
    for tok, ch in sorted(REV_VOWEL_MARKERS.items(), key=lambda kv: len(kv[0]), reverse=True):
        s = s.replace(tok, ch)

    return s

def _choose_tone_target_index(vowel_seq: str) -> int:
    """
    Choose the vowel letter to carry tone mark (simplified but works for VS1D-defined clusters/markers).
    Priority: ê ô ơ â ă ư (tone sits there if present).
    Otherwise:
      - if starts with ia/ua/ưa/uy -> first vowel
      - else -> first vowel
    """
    priority = ["ê", "ô", "ơ", "â", "ă", "ư", "Ê", "Ô", "Ơ", "Â", "Ă", "Ư"]
    for p in priority:
        idx = vowel_seq.find(p)
        if idx != -1:
            return idx

    low = vowel_seq.lower()
    if low.startswith(("ia", "ua", "ưa", "uy")):
        return 0

    return 0

def _apply_tone_to_vowel_seq(vowel_seq: str, tone: str) -> str:
    if not tone:
        return vowel_seq

    idx = _choose_tone_target_index(vowel_seq)
    ch = vowel_seq[idx]

    if (ch, tone) not in BASE_TO_ACCENT:
        raise ValueError(f"Cannot apply tone {tone!r} to vowel {ch!r} in {vowel_seq!r}")

    accented = BASE_TO_ACCENT[(ch, tone)]
    return vowel_seq[:idx] + accented + vowel_seq[idx+1:]

def decode(vs: str) -> str:
    """
    Decode a single VS1D syllable into Quốc ngữ.
    """
    p = _parse_vs(vs)

    vowel_qn = _vs_vowel_to_qn(p.vowel_part)
    toned_vowel = _apply_tone_to_vowel_seq(vowel_qn, p.tone)

    return p.onset + toned_vowel + p.coda

# -----------------------------
# Simple text helpers + CLI
# -----------------------------

def encode_text(text: str) -> str:
    parts = text.split()
    return " ".join(encode(w) for w in parts)

def decode_text(text: str) -> str:
    parts = text.split()
    return " ".join(decode(w) for w in parts)

def _usage() -> None:
    print(
        "Usage:\n"
        "  python vietstrict.py encode <syllable-or-text>\n"
        "  python vietstrict.py decode <syllable-or-text>\n"
        "Examples:\n"
        "  python vietstrict.py encode quyền\n"
        "  python vietstrict.py decode quyeznf\n"
    )

def main(argv: List[str]) -> int:
    if len(argv) < 3 or argv[1] not in ("encode", "decode"):
        _usage()
        return 2
    cmd = argv[1]
    s = " ".join(argv[2:])
    if cmd == "encode":
        print(encode_text(s))
    else:
        print(decode_text(s))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))