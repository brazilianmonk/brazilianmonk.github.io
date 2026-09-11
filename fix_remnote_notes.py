#!/usr/bin/env python3
"""
fix_remnote_notes.py — one-off conversion of the semester HTML notes:

1. strips the surrounding <html>/<head>/<style>/<body> wrapper
2. converts RemNote cloze spans  {{id::text}}  ->  <mark class="cloze">text</mark>
   (information preserved exactly; only the internal RemNote id is removed)
3. prepends Jekyll front matter (layout: page) with title + permalink,
   including the .Portal border style so portal boxes keep their look

Original untouched copies are kept in /tmp/note-backup/.

Usage:  python fix_remnote_notes.py            # do the conversion
        python fix_remnote_notes.py --check    # only verify, write nothing
"""
import re
import sys
from pathlib import Path

FILES = {
    "pages/a/fundamentals-of-theravada.html": (
        "Fundamentals of Theravāda – bhante Maggavihāri",
        "/summaries/abhidhamma/fundamentals",
    ),
    "pages/kha/vinaya-entrance-notes.html": (
        "Vibhaṅga & Khandhaka Entrance Notes – bhante Maggavihāri",
        "/summaries/vinaya/entrance-notes",
    ),
    "pages/khu/khuddaka-nikaya.html": (
        "Khuddaka Nikāya – āvuso Sumana",
        "/summaries/khuddaka/khuddaka-nikaya",
    ),
    "pages/p/pali-patha-sikkha-ch1-3.html": (
        "Pāḷi Pāṭha Sikkhā: Chapters 1–3 – bhante Vijitānanda",
        "/summaries/pali/pps-ch1-3-notes",
    ),
    "pages/recitation/recitation.html": (
        "Recitation Schedule",
        "/summaries/recitation/schedule",
    ),
    "pages/recitation/bhikkhupatimokkha.html": (
        "Bhikkhupātimokkha (detailed recitation)",
        "/summaries/recitation/bhikkhupatimokkha",
    ),
    "pages/su/dhammanuloma.html": (
        "Dhammānuloma – bhante Devānanda",
        "/summaries/suttanta/dhammanuloma",
    ),
}

CLOZE_RE = re.compile(r"\{\{[^{}]*?::(.*?)\}\}", re.S)

PORTAL_STYLE = """<style>
.Portal { border-color: lightblue; border-style: solid; }
mark.cloze { background-color: rgba(255, 235, 59, 0.45); color: inherit; padding: 0 1px; border-radius: 2px; }
</style>"""


def convert(text):
    text = CLOZE_RE.sub(lambda m: f'<mark class="cloze">{m.group(1)}</mark>', text)
    return text


def build_page(text, title, permalink):
    inner = re.sub(
        r"^.*?<body>(.*?)</body>.*$",
        lambda m: m.group(1).strip("\r\n"),
        text,
        count=1,
        flags=re.S,
    )
    front = (
        "---\r\n"
        "layout: page\r\n"
        f'title: "{title}"\r\n'
        f"permalink: {permalink}\r\n"
        "---\r\n\r\n"
    )
    return front + PORTAL_STYLE + "\r\n" + inner + "\r\n"


def main():
    check_only = "--check" in sys.argv
    leftovers = {}
    for path, (title, permalink) in FILES.items():
        p = Path(path)
        raw = p.read_text(encoding="utf-8")
        fixed = build_page(convert(raw), title, permalink)
        remaining = CLOZE_RE.findall(fixed)
        if remaining:
            leftovers[path] = len(remaining)
        print(f"{path}: cloze spans converted, {len(remaining)} remaining, "
              f"{len(fixed.splitlines())} lines")
        if not check_only:
            p.write_text(fixed, encoding="utf-8", newline="")
    if leftovers:
        print("\nWARNING — leftover cloze spans in:")
        for f, n in leftovers.items():
            print(f"  {f}: {n}")
        sys.exit(1)
    print("\nAll cloze spans converted.")


if __name__ == "__main__":
    main()
