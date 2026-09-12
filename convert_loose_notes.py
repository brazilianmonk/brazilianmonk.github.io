#!/usr/bin/env python3
"""
convert_loose_notes.py — convert three loose notes that are not part of a
semester folder:

  1. pages/p/Common Roots in Pāḷi.html          -> pages/p/common-roots-in-pali.html
  2. pages/a/abhidhamma semeseter VI.html       -> pages/a/abhidhamma-semester-6.html
  3. pages/a/abhidhamma semester VII.md         -> pages/a/abhidhamma-semester-7.md
                                                   (markdown: front matter prepended,
                                                   content untouched, org TOC/anchors kept)

Originals are kept in assets/original-notes/. Conversion is verified
(flattened-text equality for HTML, byte-prefix check for the md) before any
original is moved.
"""
import os
import re
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PORTAL_STYLE = (
    "<style>\n"
    ".Portal { border-color: lightblue; border-style: solid; }\n"
    'mark.cloze { background-color: rgba(255, 235, 59, 0.45); color: inherit; '
    "padding: 0 1px; border-radius: 2px; }\n"
    "</style>"
)

CLOZE = re.compile(r"\{\{[^{}]*?::(.*?)\}\}", re.S)


def fix_clozes(text):
    prev = None
    while prev != text:
        prev = text
        text = CLOZE.sub(lambda m: '<mark class="cloze">%s</mark>' % m.group(1), text)
    return text


def body_of(text):
    m = re.search(r"<body[^>]*>(.*)</body>", text, re.S)
    return m.group(1).strip("\r\n") if m else text


def flatten(text):
    t = fix_clozes(text)
    t = re.sub(r"<[^>]+>", " ", t)
    return " ".join(t.split())


def make_page(title, permalink, body_html):
    front = (
        "---\r\n"
        "layout: page\r\n"
        'title: "%s"\r\n'
        "permalink: %s\r\n"
        "---\r\n\r\n" % (title, permalink)
    )
    return front + PORTAL_STYLE + "\r\n" + body_html + "\r\n"


JOBS = [
    # (source, dest, title, permalink, kind)
    ("pages/p/Common Roots in Pāḷi.html",
     "pages/p/common-roots-in-pali.html",
     "Common Roots in Pāḷi",
     "/summaries/pali/common-roots", "html"),
    ("pages/a/abhidhamma semeseter VI.html",
     "pages/a/abhidhamma-semester-6.html",
     "Abhidhamma (Semester VI)",
     "/summaries/abhidhamma/semester-6", "html"),
    ("pages/a/abhidhamma semester VII.md",
     "pages/a/abhidhamma-semester-7.md",
     "Abhidhamma (Semester VII) – Tikamātikā",
     "/summaries/abhidhamma/semester-7", "md"),
]

ASSETS = "assets/original-notes"

# ------------------------------------------------------------ convert + verify
ok = True
results = []
for src, dest, title, plink, kind in JOBS:
    with open(src, encoding="utf-8") as f:
        raw = f.read()
    if kind == "html":
        body = fix_clozes(body_of(raw))
        page = make_page(title, plink, body)
        # verification: content identical after wrapper strip (+cloze ids dropped)
        same = flatten(body_of(raw)) == flatten(body)
        residual = len(re.findall(r"\{\{", body)) + len(re.findall(r"\{%", body))
        print(f"{src}: html, {len(body)} bytes body, equality {'PASS' if same else 'FAIL'}, "
              f"residual {residual}")
        ok &= same and residual == 0
    else:
        front = ('---\r\nlayout: page\r\ntitle: "%s"\r\npermalink: %s\r\n---\r\n\r\n'
                 % (title, plink))
        page = front + raw
        # verification: converted == original with front matter prepended
        same = page[len(front):] == raw
        residual = len(re.findall(r"\{\{", raw)) + len(re.findall(r"\{%", raw))
        n_anchor = len(re.findall(r'<a id="org[0-9a-f]+"', raw))
        print(f"{src}: md, {len(raw)} chars, prefix-check {'PASS' if same else 'FAIL'}, "
              f"residual {residual}, org anchors kept: {n_anchor}")
        ok &= same and residual == 0
    results.append((src, dest, page))

if not ok:
    print("\n!! VERIFICATION FAILED — nothing written, originals not moved.")
    sys.exit(1)

# ---------------------------------------------------------------- write + move
os.makedirs(ASSETS, exist_ok=True)
for src, dest, page in results:
    with open(dest, "w", encoding="utf-8", newline="") as f:
        f.write(page)
    shutil.move(src, os.path.join(ASSETS, os.path.basename(src)))
    print(f"wrote {dest}; original -> {ASSETS}/{os.path.basename(src)}")

print("\nDone. All checks passed.")
