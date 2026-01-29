#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import Optional, Tuple, List

# -----------------------------
# VS1D v1.1 - reference implementation (spec-driven)
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

# Vowel clusters (no tone)
# v1.1: uyê is uyez; iê is iez; yê is yez; uô is uoz; ươ is uow; ưa is uwa; uê is uez
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

# Onset list for splitting Quốc ngữ (encode)
# Order: longest first
ONSETS = [
    "ngh", "ch", "gh", "kh", "nh", "ng",
    "ph", "th", "tr", "qu", "gi",
    "dd",  # for đ after marker conversion
    "b", "c", "d", "g", "h", "k", "l", "m", "n", "p", "q", "r", "s", "t", "v", "x",
]

# Map accented Vietnamese vowels to (base_without_tone, tone_suffix)
# base retains vowel quality diacritics (ă â ê ô ơ ư)
_ACCENT_MAP: dict[str, Tuple[str, str]] = {}

def _build_accent_maps() -> Tuple[dict[str, Tuple[str, str]], dict[Tuple[str, str], str]]:
    # Build from explicit sets (covers uppercase too).
    # tone: s f r x j (sắc, huyền, hỏi, ngã, nặng), "" = ngang
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

        # uppercase
        base_u = base.upper()
        mp_u = {}
        for tone, ch in mp.items():
            ch_u = ch.upper()
            mp_u[tone] = ch_u
            accent_to_base[ch_u] = (base_u, tone)
            base_to_accent[(base_u, tone)] = ch_u

    return accent_to_base, base_to_accent

ACCENT_TO_BASE, BASE_TO_ACCENT = _build_accent_maps()

VOWELS_QN = set("aăâeêioôơuưyAĂÂEÊIOÔƠUƯY")

@dataclass(frozen=True)
class ParsedVS:
    onset: str
    vowel_cluster: str
    coda: str
    tone: str  # s f r x j or ""

def _split_onset_qn(s: str) -> Tuple[str, str]:
    """Split Quốc ngữ syllable into onset + rest (rhyme) using orthographic onsets qu/gi etc."""
    s_lower = s.lower()
    for o in sorted(ONSETS, key=len, reverse=True):
        if s_lower.startswith(o):
            return s[:len(o)], s[len(o):]
    return "", s

def _strip_tone_qn(s: str) -> Tuple[str, str]:
    """Return (string without tone marks, tone_suffix). Tone is determined by any accented vowel."""
    tone = ""
    out = []
    for ch in s:
        if ch in ACCENT_TO_BASE:
            base, t = ACCENT_TO_BASE[ch]
            if t != "":
                if tone != "" and tone != t:
                    raise ValueError(f"Multiple different tones in one syllable: {s!r}")
                tone = t
            out.append(base)
        else:
            out.append(ch)
    return "".join(out), tone

def _apply_vowel_markers_encode(qn_no_tone: str) -> str:
    """Apply dd + av/az/ez/oz/ow/uw markers on single letters (after cluster replacement)."""
    res = []
    for ch in qn_no_tone:
        # handle đ/Đ
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
    Assumes input is one syllable (no spaces). Keeps case as-is (best-effort).
    """
    if not qn:
        return qn

    qn_no_tone, tone = _strip_tone_qn(qn)

    onset, rhyme = _split_onset_qn(qn_no_tone)

    # Replace vowel clusters in the rhyme ONLY (protect qu/gi u/i)
    rhyme_lower = rhyme.lower()
    # longest first
    for qn_cluster, vs_cluster in sorted(CLUSTERS_QN_TO_VS.items(), key=lambda kv: len(kv[0]), reverse=True):
        # case handling: keep as lowercase tokens; case in spec is typically lowercase.
        rhyme_lower = rhyme_lower.replace(qn_cluster, vs_cluster)

    # restore original casing style for onset+rhyme? (keep onset original, rhyme tokens lowercase)
    vs = onset.lower() + rhyme_lower

    # Now apply single-letter markers (ă â ê ô ơ ư, đ) across the whole syllable
    # But our cluster replacement already consumed ê/ô/ơ in clusters; remaining standalone will be marked.
    vs = _apply_vowel_markers_encode(vs)

    # Append tone suffix at end
    if tone:
        vs = vs + tone

    return vs

def _parse_vs(vs: str) -> ParsedVS:
    if not vs:
        raise ValueError("Empty syllable")

    # Step 1: tone suffix
    tone = ""
    core = vs
    if core[-1] in TONE_SUFFIXES:
        tone = core[-1]
        core = core[:-1]

    core_l = core.lower()

    # Step 2: onset special (qu/gi) for decoding; treat them as onset if present
    onset = ""
    rest = core_l
    if rest.startswith("qu"):
        onset = "qu"
        rest = rest[2:]
    elif rest.startswith("gi"):
        onset = "gi"
        rest = rest[2:]

    # Step 3: vowel cluster longest-match
    # Candidates: cluster tokens + marker tokens + plain vowels.
    # We first try known clusters (uyez, iez, yez, uoz, uow, uwa, uez) then marker tokens then single vowels.
    clusters = sorted(CLUSTERS_VS_TO_QN.keys(), key=len, reverse=True)
    marker_tokens = sorted(REV_VOWEL_MARKERS.keys(), key=len, reverse=True)

    vowel_cluster_vs = ""
    for c in clusters:
        if rest.startswith(c):
            vowel_cluster_vs = c
            break

    # If no special cluster, we will take the first vowel-ish unit (marker token or single vowel letter)
    if not vowel_cluster_vs:
        for tok in marker_tokens:
            if rest.startswith(tok):
                vowel_cluster_vs = tok
                break
    if not vowel_cluster_vs:
        if rest and rest[0] in "aeiouy":
            vowel_cluster_vs = rest[0]

    if not vowel_cluster_vs:
        raise ValueError(f"Cannot find vowel cluster in {vs!r}")

    rest2 = rest[len(vowel_cluster_vs):]

    # Step 4: coda
    coda = ""
    for cd in sorted(CODAS, key=len, reverse=True):
        if rest2 == cd:
            coda = cd
            rest2 = ""
            break

    # Step 5: remaining must be onset (if we didn't consume qu/gi already)
    if rest2:
        # whatever remains is onset (before vowel cluster), but in our strategy we always chose vowel at start,
        # so rest2 should be "" if coda matched; otherwise invalid.
        raise ValueError(f"Invalid trailing characters after parsing in {vs!r}: {rest2!r}")

    return ParsedVS(onset=onset, vowel_cluster=vowel_cluster_vs, coda=coda, tone=tone)

def _vs_vowel_to_qn(vs_vowel: str) -> str:
    """Convert VS vowel cluster token to Quốc ngữ (no tone)."""
    if vs_vowel in CLUSTERS_VS_TO_QN:
        return CLUSTERS_VS_TO_QN[vs_vowel]
    if vs_vowel in REV_VOWEL_MARKERS:
        return REV_VOWEL_MARKERS[vs_vowel]
    # plain vowel
    return vs_vowel

def _choose_tone_target_index(vowel_seq: str) -> int:
    """
    Choose which vowel letter in the vowel sequence to carry tone mark.
    This is the Vietnamese orthography rule simplified but correct for the clusters in VS spec.
    """
    # Priority: ê ô ơ â ă ư (tone sits on these letters if present)
    priority = ["ê", "ô", "ơ", "â", "ă", "ư", "Ê", "Ô", "Ơ", "Â", "Ă", "Ư"]
    for p in priority:
        idx = vowel_seq.find(p)
        if idx != -1:
            return idx

    # Special sequences where tone goes on first vowel: ia, ua, ưa, uy (common rule)
    low = vowel_seq.lower()
    if low.startswith("ia") or low.startswith("ua") or low.startswith("ưa") or low.startswith("uy"):
        return 0

    # Default: first vowel
    return 0

def _apply_tone_to_vowel_seq(vowel_seq: str, tone: str) -> str:
    """Apply tone to one vowel inside vowel_seq (no tone -> with tone)."""
    if not tone:
        return vowel_seq

    idx = _choose_tone_target_index(vowel_seq)
    ch = vowel_seq[idx]
    if ch not in BASE_TO_ACCENT:
        # It might be a plain vowel without diacritic base mapping (still present in mapping)
        pass

    # Convert target char to accented char
    base = ch
    # base must be one of keys in BASE_TO_ACCENT: includes AĂÂEÊI OÔƠUƯY etc
    if (base, tone) not in BASE_TO_ACCENT:
        raise ValueError(f"Cannot apply tone {tone!r} to vowel {base!r} in {vowel_seq!r}")

    accented = BASE_TO_ACCENT[(base, tone)]
    return vowel_seq[:idx] + accented + vowel_seq[idx+1:]

def decode(vs: str) -> str:
    """
    Decode a single VS1D syllable into Quốc ngữ.
    """
    p = _parse_vs(vs)

    vowel_qn = _vs_vowel_to_qn(p.vowel_cluster)
    syllable_no_tone = p.onset + vowel_qn + p.coda

    # Apply tone onto vowel sequence (the rhyme's vowel part)
    toned_vowel = _apply_tone_to_vowel_seq(vowel_qn, p.tone)

    return p.onset + toned_vowel + p.coda

def encode_text(text: str) -> str:
    """Encode a text by splitting on whitespace; keeps punctuation attached (simple)."""
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