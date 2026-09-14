#!/usr/bin/env python3
"""Verify that no source content was lost in the reorganization.

For every bullet text in the source HTML (build/organizer/*.source.txt),
check that a normalized sample appears in one of:
- the corresponding .converted.md (full conversion, pre vocab-extraction)
- pages/pali/vocabulary.md (where vocab blocks were moved)

Also checks that every generated page has balanced HTML comments and no
leftover hashtag noise.
"""

from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "build" / "organizer"
PALI = ROOT / "pages" / "pali"

PAGE_MAP = {
    "pali-patha-sikkha-ch1-3": ["pps-ch*-part*.md", "pps-ch3-reading.md",
                                "pps-vocab-archive.md", "vocabulary.md"],
    "pali-semester-2": ["semester-2-part1.md", "semester-2-part2.md",
                        "pps-final-exam-1st-year.md", "vocabulary.md"],
    "pali-semester-3": ["niruttidipani-part-1.md", "dhammapada-atthakatha-1.md",
                        "itivuttaka-1.md", "anguttara-1.md", "nominal-declensions.md",
                        "semester-3-notes.md", "vocabulary.md"],
    "pali-semester-4": ["niruttidipani-part-2.md", "dhammapada-atthakatha-2.md", "vocabulary.md"],
    "pali-semester-5": ["niruttidipani-namakanda-notes.md", "dhammapada-reading-1.md",
                        "translation-notes.md", "vocabulary.md"],
    "pali-semester-6": ["semester-6-grammar.md", "semester-6-reading.md", "vocabulary.md"],
    "common-roots-in-pali": ["common-roots.md", "vocabulary.md"],
}


EMOJI_RE = re.compile(r"[\U0001F000-\U0001FAFF\U0001F3FB-\U0001F3FF\u2640\u2642\uFE0F\u200D]+")


def norm(s: str) -> str:
    # apply the same intentional transformations as the organizer
    s = re.sub(r"#\[\[[^\]]*\]\]", "", s)
    s = re.sub(r"#\s*(edited|editing|homeworks)\b", "", s, flags=re.I)
    s = re.sub(r"#\s*q\b", "", s, flags=re.I)
    s = EMOJI_RE.sub("", s)
    if re.match(r"^\**\s*vocab\b", s, re.I):
        # vocab labels become pointer bullets; accounted for structurally
        return ""
    s = re.sub(r"[\u2013\u2014\u2015]", "-", s)
    # intentional text fixes (see organizer.strip_misc_text)
    s = s.replace("rassa sara", "rasa sara")
    s = re.sub(r"\^\^[*\s]*declension", "declension", s)  # RemNote markup glyph
    s = re.sub(r"^\s*\*+\s*(?=declension\b)", "", s)
    # the source extractor keeps spaces that RemNote injects inside bold/italic
    # spans ("us u mā"), while the organizer rejoins them ("usumā"); compare
    # with all whitespace removed so that doesn't create false misses
    s = re.sub(r"[^a-z0-9āīūṅñṭḍṇḷṁ]+", "", s.lower())
    return s


def load_texts(txt_path: Path) -> list[str]:
    out = []
    for line in txt_path.read_text(encoding="utf-8").splitlines():
        t = re.sub(r"^\s*- ", "", line).strip()
        if t:
            out.append(t)
    return out


def main() -> int:
    missing_total = 0
    for stem, pages in PAGE_MAP.items():
        src = AUDIT / f"{stem}.source.txt"
        conv = AUDIT / f"{stem}.converted.md"
        if not src.exists():
            continue
        corpus = norm(conv.read_text(encoding="utf-8"))
        used_pages: list[str] = []
        for p in pages:
            if "*" in p:
                fps = sorted(PALI.glob(p))
            else:
                fps = [PALI / p]
            for fp in fps:
                used_pages.append(fp.name)
                if fp.exists():
                    corpus += "\n" + norm(fp.read_text(encoding="utf-8"))
        vocab_labels = 0
        missing = []
        for text in load_texts(src):
            n = norm(text)
            if not n:
                vocab_labels += 1
                continue
            # take a stable sample: middle 40 chars of the normalized text
            if len(n) <= 40:
                sample = n
            else:
                mid = len(n) // 2
                sample = n[max(0, mid - 20): mid + 20].strip()
            if sample and sample not in corpus:
                missing.append(text)
        status = "OK " if not missing else "MISS"
        print(f"{status} {stem}: {len(missing)} missing of "
              f"{len(load_texts(src))} source bullets "
              f"({vocab_labels} vocab labels) -> {'+'.join(used_pages)}")
        for t in missing[:12]:
            print("   -", t[:130])
        missing_total += len(missing)

    print()
    # comment balance + noise checks on *generated* pages only (the pre-existing
    # curated pages legitimately still carry RemNote tags)
    generated = {p for pages in PAGE_MAP.values() for p in pages}
    bad = 0
    for fp in sorted(PALI.glob("*.md")):
        if not any(fnmatch.fnmatch(fp.name, g) for g in generated):
            continue
        text = fp.read_text(encoding="utf-8")
        if text.count("<!--") != text.count("-->"):
            print(f"UNBALANCED comments: {fp.name}")
            bad += 1
        for pat, label in ((r"#\s*q\b", "#q remnant"),
                           (r"#\[\[", "#[[ remnant"),
                           (r"#\s*(edited|editing|homeworks)\b", "tag remnant"),
                           (r"remnoteMark", "remnote attr")):
            if re.search(pat, text, re.I):
                print(f"NOISE ({label}): {fp.name}")
                bad += 1
    print(f"\ntotal missing: {missing_total}, noise/balance problems: {bad}")
    return 1 if (missing_total or bad) else 0


if __name__ == "__main__":
    sys.exit(main())
