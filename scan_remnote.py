#!/usr/bin/env python3
"""
scan_remnote.py — find RemNote syntax artifacts in note files (HTML or Markdown).

Usage:
    python scan_remnote.py                # scan pages/ by default
    python scan_remnote.py <file|dir> ... # scan specific files/directories
    python scan_remnote.py --json         # machine-readable output

What it detects
---------------
cloze        : {{id::text}} spans — the inner text is the hidden answer; these
               are also the spans Liquid would choke on, so they must be fixed
               before a file can get Jekyll front matter.
portal       : <div class="Portal"> — an embedded copy of another RemNote
               document. Content is intact, only the container looks odd.
tag          : #[[...]] or #tag — RemNote tags/references, often with inline
               color <mark> markup that looks out of place.
ref          : [[...]] references (reported only when NOT part of a #[[...]] tag)
embed        : ![](remnote://...) or src="remnote://..." embeds of other notes
powerup      : ((powerup id)) codes
liquid       : {% ... %} or {{ ... }} that would break the Jekyll/Liquid build
               (any {{ that is NOT a well-formed RemNote cloze is reported here)
"""
import json
import re
import sys
from pathlib import Path

DEFAULT_DIRS = ["pages"]

CLOZE_RE = re.compile(r"\{\{[^{}]*?::[^{}]*?\}\}", re.S)
PORTAL_RE = re.compile(r'<div\s+class="Portal"', re.I)
# (?<!&) avoids matching HTML entities like &#x2013;
TAG_RE = re.compile(r"(?<!&)#\[\[[^\[\]]*\]\]|(?<!&)#[\wṀṁĀĪŪāīūṅṇṭḍṃ-]+")
REF_RE = re.compile(r"\[\[[^\[\]]+\]\]")
EMBED_RE = re.compile(r"remnote://\S+")
POWERUP_RE = re.compile(r"\(\([0-9a-zA-Z _-]+\)\)")


def find_line(text, pos):
    return text.count("\n", 0, pos) + 1


def excerpt(text, pos, span_len, width=60):
    """Short context: 60 chars before the match, the match, and a bit after."""
    start = max(0, pos - width)
    end = min(len(text), pos + span_len + width)
    s = " ".join(text[start:end].split())
    return ("…" if start > 0 else "") + s + ("…" if end < len(text) else "")


def scan_text(text):
    issues = []

    for m in CLOZE_RE.finditer(text):
        issues.append(dict(kind="cloze", line=find_line(text, m.start()),
                           match=" ".join(m.group(0).split()),
                           context=excerpt(text, m.start(), len(m.group(0)))))

    all_dbraces = [(m.start(), m.end()) for m in re.finditer(r"\{\{|\}\}", text)]
    consumed = [(m.start(), m.end()) for m in CLOZE_RE.finditer(text)]
    for start, _end in all_dbraces:
        if any(s <= start < e for s, e in consumed):
            continue
        issues.append(dict(kind="liquid", line=find_line(text, start),
                           match="{{",
                           context=excerpt(text, start, 2)))
    for m in re.finditer(r"\{%", text):
        issues.append(dict(kind="liquid", line=find_line(text, m.start()),
                           match=m.group(0), context=excerpt(text, m.start(), 2)))

    for m in PORTAL_RE.finditer(text):
        issues.append(dict(kind="portal", line=find_line(text, m.start()),
                           match='<div class="Portal">', context=excerpt(text, m.start(), 22)))

    tag_positions = [(m.start(), m.end()) for m in TAG_RE.finditer(text)]
    for pos, end in tag_positions:
        issues.append(dict(kind="tag", line=find_line(text, pos),
                           match=" ".join(text[pos:end].split())[:120],
                           context=excerpt(text, pos, end - pos)))
    for m in REF_RE.finditer(text):
        if any(s <= m.start() < e for s, e in tag_positions):
            continue  # already reported as tag
        issues.append(dict(kind="ref", line=find_line(text, m.start()),
                           match=" ".join(m.group(0).split())[:120],
                           context=excerpt(text, m.start(), len(m.group(0)))))

    for m in EMBED_RE.finditer(text):
        issues.append(dict(kind="embed", line=find_line(text, m.start()),
                           match=m.group(0)[:120], context=excerpt(text, m.start(), len(m.group(0)))))

    for m in POWERUP_RE.finditer(text):
        issues.append(dict(kind="powerup", line=find_line(text, m.start()),
                           match=m.group(0)[:120], context=excerpt(text, m.start(), len(m.group(0)))))

    return sorted(issues, key=lambda i: (i["line"], i["kind"]))


def has_front_matter(text):
    """True if the file starts with Jekyll front matter (it's a site page)."""
    return text.lstrip("\ufeff \t\r\n").startswith("---")


def scan_path(path, include_processed=False):
    path = Path(path)
    if path.is_dir():
        results = []
        for ext in ("*.html", "*.md"):
            for f in sorted(path.rglob(ext)):
                results.extend(scan_path(f, include_processed))
        return results
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    if not include_processed and has_front_matter(text):
        return []  # already a processed site page (has Jekyll front matter)
    issues = scan_text(text)
    return [dict(file=str(path), **i) for i in issues]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in flags
    include_processed = "--all" in flags  # also scan files that already have front matter
    targets = args or DEFAULT_DIRS

    results = []
    for t in targets:
        results.extend(scan_path(t, include_processed))

    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if not results:
        print("No RemNote syntax artifacts found. Files are ready for front matter.")
        return

    by_file = {}
    for r in results:
        by_file.setdefault(r["file"], []).append(r)

    for f, issues in sorted(by_file.items()):
        counts = {}
        for i in issues:
            counts[i["kind"]] = counts.get(i["kind"], 0) + 1
        summary = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
        print(f"\n{'=' * 78}\n{f}  ({summary})\n{'=' * 78}")
        last_key = None
        for i in issues:
            key = (i["line"], i["kind"])
            if key == last_key and len(i["match"]) < 20:
                continue  # skip near-duplicate short matches on the same line
            print(f"  [{i['kind']:7}] line {i['line']}: {i['match'][:100]}")
            last_key = key

    total = {}
    for r in results:
        total[r["kind"]] = total.get(r["kind"], 0) + 1
    print(f"\nTOTALS: " + ", ".join(f"{k}: {v}" for k, v in sorted(total.items())))


if __name__ == "__main__":
    main()
