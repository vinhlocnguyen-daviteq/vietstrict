#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import sys
from pathlib import Path

from vietstrict import encode, decode

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    ROOT / "tests" / "words.tsv",
    ROOT / "tests" / "kieu_10_lines.tsv",
]

def iter_pairs(tsv_path: Path):
    with tsv_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if not row or len(row) < 2:
                continue
            qn = row[0].strip()
            vs = row[1].strip()
            if not qn or not vs:
                continue
            yield qn, vs

def main() -> int:
    total = 0
    fail = 0

    for path in TESTS:
        if not path.exists():
            print(f"[SKIP] Missing: {path}")
            continue

        print(f"[TEST] {path}")
        for qn, vs in iter_pairs(path):
            total += 1

            # 1) exact mapping check (optional but useful)
            vs2 = encode(qn)
            qn2 = decode(vs)

            if vs2 != vs:
                fail += 1
                print(f"FAIL encode: QN={qn!r} expected VS={vs!r} got {vs2!r}")
                continue

            if qn2 != qn:
                fail += 1
                print(f"FAIL decode: VS={vs!r} expected QN={qn!r} got {qn2!r}")
                continue

            # 2) round-trip guarantees
            if encode(decode(vs)) != vs:
                fail += 1
                print(f"FAIL roundtrip1: encode(decode({vs!r})) != {vs!r}")
                continue

            if decode(encode(qn)) != qn:
                fail += 1
                print(f"FAIL roundtrip2: decode(encode({qn!r})) != {qn!r}")
                continue

    if fail == 0:
        print(f"PASS: {total} cases")
        return 0
    print(f"FAIL: {fail}/{total} cases failed")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())