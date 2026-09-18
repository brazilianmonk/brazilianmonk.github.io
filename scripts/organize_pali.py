#!/usr/bin/env python3
"""Organize the RemNote HTML exports in pages/p/*.html into topic pages.

Outputs:
- pages/pali/*.md          final topic pages (front-matter + clean markdown)
- pages/pali/vocabulary.md collected vocabulary lists, grouped by semester
- build/organizer/*.txt    audit files (plain-text inventory for verification)
- pages/summaries.md       Pāḷi section rewritten to link the new pages

Conventions:
- Nested lists -> markdown bullets; label bullets -> headings per source rules.
- Purple-italic inline marks (personal questions) -> HTML comments, in place.
- Bullets hashtagged '#q' -> commented out; their sub-lists stay visible.
- #edited / #editing / #homeworks hashtags are dropped.
- **Vocab** blocks -> vocabulary page (<details> in place replaced); sub-bullets
  starting with * or / are exercise-specific vocab: they stay on the notes page,
  re-inserted right before the next exercise heading.
- <!-- ANCHOR:key --> comments mark split points; the driver splits on them.

Source: converted files are moved to raw/pali/ (kept in repo, excluded from the
Jekyll build) so their permalinks no longer collide with the new pages.
"""

from __future__ import annotations

import html as html_mod
import re
import shutil
import sys
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "raw" / "pali"
PALI = ROOT / "pages" / "pali"
AUDIT = ROOT / "build" / "organizer"
RAW = ROOT / "raw" / "pali"
VOCAB_MD = PALI / "vocabulary.md"
SUMMARIES_MD = ROOT / "pages" / "summaries.md"

FRONT = """---
layout: page
title: {title}
permalink: /summaries/pali/{permalink}
---
"""


# ---------------------------------------------------------------- text utils

def clean_text(s: str) -> str:
    return html_mod.unescape(s).replace("\u00a0", " ")


def esc(t: str) -> str:
    # '|' must be escaped: kramdown starts a table cell at every '|' in body
    # text, even inside bold/marks (rendered a stray bullet as a broken table).
    return t.replace("\u00a0", " ").replace("<", "&lt;").replace("|", "\\|")


def comment_safe(t: str) -> str:
    return t.replace("--", "\u2013\u2013")


def style_of(mark: Tag) -> str:
    v = mark.attrs.get("style", "")
    return " ".join(v) if isinstance(v, list) else str(v)


def is_purple(mark: Tag) -> bool:
    return "purple" in style_of(mark)


def is_italic_purple(mark: Tag) -> bool:
    return is_purple(mark) and mark.find("i") is not None


def is_q_mark(mark: Tag) -> bool:
    if not is_purple(mark) or not mark.find("b"):
        return False
    return mark.get_text().strip().lstrip().startswith("#q")


EMOJI_RE = re.compile(r"[\U0001F000-\U0001FAFF\U0001F3FB-\U0001F3FF\u2640\u2642\uFE0F\u200D]+")


def strip_q_remnants(inline: str) -> str:
    """Remove '#q' hashtag remnants and emoji from bullet text that will be
    commented out."""
    t = re.sub(r"#\s*q\b", "", inline, flags=re.I)
    t = EMOJI_RE.sub("", t)
    return normalize(t)


def q_comment_text(inline: str) -> str:
    """Prepare bullet text for wrapping in an HTML comment: neutralize any
    inner <!-- --> pairs (keep the text) and drop #q/emoji remnants."""
    t = re.sub(r"<!--\s*(.*?)\s*-->", r"(\1)", inline)
    return comment_safe(strip_q_remnants(t))


def is_tag_mark(mark: Tag) -> bool:
    if not mark.find("b"):
        return False
    return mark.get_text().strip().lstrip().startswith("#")


def is_vocab_label(text: str) -> bool:
    """True only for genuine vocab-list label bullets ("**Vocab**: #[[...]]" or
    "vocab :"). Single glosses merely tagged #[[pāḷi vocab (Nth year)]] do NOT
    count (they don't *start* with 'vocab')."""
    t = re.sub(r"#\[\[[^\]]*\]\]", "", text)  # ignore the hashtag part
    return bool(re.match(r"^\**\s*vocab\b", t, re.I))


def vocab_summary(text: str) -> str:
    t = re.sub(r"#\[\[[^\]]*\]\]", "", text)  # drop hashtag remnants
    m = re.search(r"vocab\s*:\s*(.*)$", t, re.I)
    label = m.group(1) if m and m.group(1).strip() else t
    label = label.replace("[[", "").replace("]]", "")
    label = re.sub(r"^\**vocab\b\s*:?\s*", "", label, flags=re.I).strip() or t
    label = normalize(label).strip(" :")
    return label or "Vocabulary"


def is_starred_bullet(text: str) -> bool:
    return bool(re.match(r"^[*/]\s{0,3}\S", text))


def href_of(a: Tag) -> str | None:
    href = a.attrs.get("href", "")
    href = " ".join(href) if isinstance(href, list) else str(href)
    if href.startswith("#"):
        return " ".join(a.get_text().split())
    return None


def img_src(img: Tag) -> str:
    src = img.attrs.get("src", "")
    return " ".join(src) if isinstance(src, list) else str(src)


def normalize(t: str) -> str:
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r" +([,.;:!?])", r"\1", t)
    t = re.sub(r"\(\s+", "(", t)
    t = re.sub(r"\s+\)", ")", t)
    return strip_misc_text(arrows_to_colon(t).strip())


# ---------------------------------------------------------------- node -> md

def node_to_md(node, depth: int) -> list[str]:
    if isinstance(node, NavigableString):
        t = esc(clean_text(str(node)))
        t = re.sub(r"[ \t\r\n]+", " ", t)  # collapse, but keep single spaces
        return [t] if t else []
    if not isinstance(node, Tag):
        return []
    name = node.name
    if name == "br":
        return ["\n"]
    if name == "img":
        src = img_src(node)
        if src and not re.match(r"^https?://", src):
            src = "https://remnote-user-data.s3.amazonaws.com/" + src
        return [f"![image]({src})"] if src else []
    if name in ("style", "script"):
        return []
    if name == "mark":
        if is_italic_purple(node):
            inner = " ".join(node.get_text().split())
            return [f"<!-- {comment_safe(esc(clean_text(inner)))} -->"] if inner else []
        if is_tag_mark(node):
            return []
        return inline_children(node, depth)
    if name == "q":
        inner = " ".join(node.get_text().split())
        return [f'"{inner}"'] if inner else []
    if name == "a":
        href = href_of(node)
        text = " ".join(node.get_text().split())
        if href and re.match(r"^https?://", href):
            return [f" [{text}]({href}) "]
        return [f" {text} "] if text else []
    if name == "ul":
        return list_to_md(node, depth + 1)
    if name == "table":
        return [table_to_md(node)]
    return inline_children(node, depth)


def inline_children(node: Tag, depth: int) -> list[str]:
    out: list[str] = []
    for child in node.children:
        out.extend(node_to_md(child, depth))
    return out


def table_to_md(table: Tag) -> str:
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = []
        for cell in tr.find_all(["th", "td"]):
            parts: list[str] = []
            for child in cell.children:
                parts.extend(node_to_md(child, 0))
            # '|' is already escaped by esc() in node_to_md.
            txt = " ".join("".join(parts).split())
            cells.append(txt)
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    ncols = max(len(r) for r in rows)
    for r in rows:
        r.extend([""] * (ncols - len(r)))
    lines = ["", "| " + " | ".join(rows[0]) + " |", "|" + "---|" * ncols]
    for r in rows[1:]:
        lines.append("| " + " | ".join(r) + " |")
    lines.append("")
    return "\n".join(lines)


def bullet_marker(depth: int) -> str:
    # keep every level <= 3 spaces relative to its parent so Jekyll/GFM
    # never mistakes a nested list for an indented code block
    return "  " * max(0, depth - 1) + "- "


# ---------------------------------------------------------------- list -> md

def emit_anchored_heading(text: str, anchor: str | None, level: int) -> list[str]:
    out = [f"{'#' * level} {normalize(text)}"]
    if anchor:
        out.insert(0, f"<!-- ANCHOR:{anchor} -->")
    return out


def _short(t: str, n: int) -> str:
    t = t.strip()
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def li_to_md(li: Tag, depth: int) -> list[str]:
    inline_parts: list[str] = []
    sub_lists: list[Tag] = []
    for child in li.children:
        if isinstance(child, Tag) and child.name == "ul":
            sub_lists.append(child)
        else:
            inline_parts.extend(node_to_md(child, depth))
    inline = normalize("".join(inline_parts).replace("{", "").replace("}", ""))
    lines: list[str] = []

    # '#q'-tagged bullet: comment out its own text, keep sub-lists visible.
    # The '#' of the hashtag may sit outside the purple mark, so match on the
    # final inline text, not on marks alone.
    if inline and re.search(r"#\s*q\b", inline, re.I):
        lines.append(f"<!-- {bullet_marker(depth)}{q_comment_text(inline)} (#q) -->")
        for sub in sub_lists:
            lines.extend(list_to_md(sub, depth + 1))
        return lines

    # vocab block: replace with a pointer bullet; content moves to vocabulary.md
    if is_vocab_label(inline):
        vkey = VOCAB_KEY[CUR_SOURCE[0]]
        parts = [a for a in (ANCESTORS[depth - 1], ANCESTORS[depth - 2]) if a]
        context = " \u00b7 ".join(_short(a, 40) for a in parts) if parts else vocab_summary(inline)
        if not parts:
            context = LAST_HEADING[0] or "Vocabulary"
        summary = vocab_summary(inline)
        label = context if "vocab" in context.lower() else f"{context} (vocab)"
        lines.append(f"<!-- VOCAB:{vkey}:{depth}:{esc(label)} -->")
        lines.append("<details open>")
        lines.append(f"<summary>{esc(summary)}</summary>")
        lines.append("")
        for sub in sub_lists:
            lines.extend(list_to_md(sub, depth + 1))
        lines.append("")
        lines.append("</details>")
        lines.append("")
        return lines

    heading, anchor, level = classify_heading(inline, li, depth)
    if heading is not None:
        if CUR_SOURCE[0] == "pali-semester-2.html" and re.match(r"chapter\s+[ivx]+", heading, re.I):
            # track which half of semester 2 we are in, so vocab blocks get a
            # working "↩ source" link after the chapter split
            PART_TAG[0] = "part2" if re.search(r"\biv\b", heading, re.I) else "part1"
        lines.extend(emit_anchored_heading(heading, anchor, level))
        if level <= 2:
            LAST_HEADING[0] = normalize(heading)
    elif inline:
        lines.append(bullet_marker(depth) + inline)
    while len(ANCESTORS) <= depth:
        ANCESTORS.append("")
    # strip hashtags here: a later _short() could otherwise cut a #[[… open in
    # half, and the global hashtag cleanup would then eat from that dangling
    # opener to some unrelated ]], swallowing following content.
    an = re.sub(r"#\[\[[^\]]*\]\]", "", inline)
    an = normalize(re.sub(r"#\s*\S+$", "", an).replace("[[", "").replace("]]", ""))
    ANCESTORS[depth] = an or ANCESTORS[depth]
    for sub in sub_lists:
        lines.extend(list_to_md(sub, depth + 1))
    return lines


def list_to_md(ul: Tag, depth: int) -> list[str]:
    lines: list[str] = []
    for li in ul.find_all("li", recursive=False):
        lines.extend(li_to_md(li, depth))
    return lines


# ---------------------------------------------------------------- classification

CUR_SOURCE = [""]
LAST_HEADING = [""]
ANCESTORS: list[str] = [""] * 12  # inline text of the li at each depth
VOCAB_KEY = {
    "pali-patha-sikkha-ch1-3.html": "s1",
    "pali-semester-2.html": "s2",
    "pali-semester-3.html": "s3",
    "pali-semester-4.html": "s3",
    "pali-semester-5.html": "s3",
    "pali-semester-6.html": "s3",
}

RULES = {
    "pali-semester-2.html": [
        (r"^final exam\b", ("final", 1)),
        (r"^chapter", (None, 1)),
    ],
    "pali-semester-3.html": [
        (r"^niruttidīpanīpāṭha", ("nirutti-1", 1)),
        (r"^dhammapadaṭṭhakathā", ("dhp-1", 1)),
        (r"^itivuttakapāḷi", ("iti-1", 1)),
        (r"^aṅguttaranikāyo", ("an-1", 1)),
        (r"^nominal declensions", ("declensions", 1)),
        (r"^(sāvanaṃ|vibhaṅgappakaraṇaṃ|upcoming test|final exam|notes)", ("misc-3", 1)),
    ],
    "pali-semester-4.html": [
        (r"^niruttidīpanī", ("nirutti-2", 1)),
        (r"^dhammapadaṭṭhakathā", ("dhp-2", 1)),
    ],
    "pali-semester-5.html": [
        (r"^niruttidīpaṇī", (None, 1)),
        (r"^reading", ("reading-1", 1)),
        (r"^regarding translation", ("translation-notes", 1)),
    ],
    "pali-semester-6.html": [
        (r"^pāḷi: reading", ("s6-reading", 1)),
        (r".*", (None, 1)),
    ],
    "common-roots-in-pali.html": [
        (r".*", (None, 1)),
    ],
    "pali-patha-sikkha-ch1-3.html": [],  # handled by pps_classify
}


def classify_heading(text: str, li: Tag, depth: int):
    t = normalize(text)
    tl = t.lower()
    if not t:
        return None, None, 0
    if CUR_SOURCE[0] == "pali-patha-sikkha-ch1-3.html":
        return pps_classify(t, depth)
    if depth != 0:
        if re.match(r"^lesson\s+\d+(\.\d+)?\b", tl):
            return t, None, 2
        return None, None, 0
    for pattern, (anchor, level) in RULES.get(CUR_SOURCE[0], []):
        if re.match(pattern, tl):
            return t, anchor, level
    return t, None, 1


def pps_classify(t: str, depth: int):
    tl = t.lower()
    if depth == 0:
        if tl.startswith("chapter"):
            return t, None, 1
        return t, None, 1  # top-level anything
    if depth == 1:
        if re.match(r"^lesson\s+\d+(\.\d+)?\s*[-–—]?\s*exercises?\b", tl):
            return "Exercises", None, 3
        if re.match(r"^lesson\s+\d+(\.\d+)?\b", tl):
            return t, None, 2
        return None, None, 0
    return None, None, 0


# ---------------------------------------------------------------- conversion

def convert_source(name: str) -> str:
    path = SRC / name
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    body = soup.body or soup
    top = None
    for ul in body.find_all("ul"):
        p = ul.parent
        if p is None or not (isinstance(p, Tag) and p.name == "li"):
            top = ul
            break
    lines: list[str] = []
    for li in top.find_all("li", recursive=False):
        lines.extend(li_to_md(li, 0))
        lines.append("")
    md = "\n".join(lines)
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = re.sub(r"[ \t]+\n", "\n", md)
    # drop RemNote hashtag remnants like #[[pāḷi vocab (3rd year)]], #edited, #homeworks
    md = re.sub(r"#\[\[[^\]]*\]\]", "", md)
    md = re.sub(r"#\s*(edited|editing|homeworks)\b", "", md, flags=re.I)
    md = re.sub(r"#\s*q\b", "", md, flags=re.I)
    md = EMOJI_RE.sub("", md)
    md = re.sub(r"[ \t]+\n", "\n", md)
    return md.strip() + "\n"


# ---------------------------------------------------------------- audit

def li_to_audit(li: Tag, depth: int) -> list[str]:
    parts: list[str] = []
    for c in li.children:
        if not (isinstance(c, Tag) and c.name == "ul"):
            parts.append(c.get_text(" ", strip=True))
    text = re.sub(r"\s+", " ", " ".join(parts)).strip()
    lines = ["  " * depth + "- " + text] if text else []
    for sub in [c for c in li.children if isinstance(c, Tag) and c.name == "ul"]:
        for child in sub.find_all("li", recursive=False):
            lines.extend(li_to_audit(child, depth + 1))
    return lines


def audit_text(name: str) -> str:
    soup = BeautifulSoup((SRC / name).read_text(encoding="utf-8"), "html.parser")
    body = soup.body or soup
    top = None
    for ul in body.find_all("ul"):
        p = ul.parent
        if p is None or not (isinstance(p, Tag) and p.name == "li"):
            top = ul
            break
    if top is None:
        return ""
    lines: list[str] = []
    for li in top.find_all("li", recursive=False):
        lines.extend(li_to_audit(li, 0))
    return "\n".join(lines) + "\n"


def write_audits(name: str, converted_md: str) -> None:
    stem = Path(name).stem
    (AUDIT / f"{stem}.source.txt").write_text(audit_text(name), encoding="utf-8", newline="\n")
    (AUDIT / f"{stem}.converted.md").write_text(converted_md, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- post-processing

VMARKER = re.compile(r"^<!-- VOCAB:(s\d+):(\d+):(.*?) -->$")
VOCAB_END = "<!-- /VOCAB -->"
ANCHOR_RE = re.compile(r"^<!-- ANCHOR:([a-z0-9\-]+) -->$")

# gloss arrows → colon+space (user preference); ⇒ (step-by-step derivations) untouched
ARROW_RE = re.compile(r"\s*[↔→←]\s*")
DOWN_ARROW_RE = re.compile(r"\s*↓\s*")


def arrows_to_colon(t: str) -> str:
    return ARROW_RE.sub(": ", t)


def strip_misc_text(t: str) -> str:
    """Per-word text fixes applied to every bullet: the ↓ pointer arrows are
    dropped completely; a '*' before 'declension' is the RemNote private-bullet
    glyph; and 'rassa sara' is a recurring typo for 'rasa sara' (short
    vowels). Numbering artifacts ('1.', '9.') are stripped only where they are
    pure list artifacts (fix_ch3_sannaa), not globally — sutta/vagga numbers
    elsewhere are meaningful."""
    t = DOWN_ARROW_RE.sub("", t)
    # the RemNote private-bullet glyph ('- *declension', markup form
    # '- ^^*****^^declension') is dropped and the word capitalized; a balanced
    # bold label ('**declension**: ...') can never match (the lookahead sees
    # a '*' or a colon, not 'declension')
    m2 = re.match(r"^(\s*(?:-\s*)?)(?:\^\^\*+\^\^|\*)(?=declension\b)", t)
    if m2:
        t = m2.group(1) + t[m2.end():]
    t = re.sub(r"^(\s*(?:-\s*)?)declension\b", r"\1Declension", t, count=1)
    t = t.replace("rassa sara", "rasa sara")
    return t
H_RE = re.compile(r"^(#{1,3}) (.+)$")
DETAILS_OPEN = re.compile(r"^<details open>$")

VOCAB_BLOCKS: list[dict] = []
AUDITED: dict = {}
PART_TAG = [""]  # which half of semester 2 the conversion is currently in


def is_exercise_heading(line: str) -> bool:
    m = H_RE.match(line.strip())
    return bool(m and "exercise" in m.group(2).lower())


def squeeze(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if line == "" and (not out or out[-1] == ""):
            continue
        out.append(line)
    while out and out[0] == "":
        out.pop(0)
    while out and out[-1] == "":
        out.pop()
    return out


def move_stars(lines: list[str]) -> tuple[list[str], list[str]]:
    """Split out */-prefixed vocabulary bullets (and one following blank)."""
    kept: list[str] = []
    stars: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if is_starred_bullet(line.strip()):
            stars.append(line)
            if i + 1 < n and lines[i + 1] == "":
                i += 1
            i += 1
            continue
        kept.append(line)
        i += 1
    return kept, stars


def process_vocab(lines: list[str], vkey: str, source_title: str, source_link: str,
                  audit_key: str, anchor_links: dict[str, str] | None = None) -> list[str]:
    """Extract VOCAB blocks: whole block -> vocabulary page; */-bullets stay on
    the notes page, re-inserted before the next exercise heading.
    anchor_links maps an ANCHOR id to the final page it became, so each vocab
    block's '↩ source' link points at the right page."""
    out: list[str] = []
    pending: dict[int, list[str]] = {}
    cur_anchor = ""
    i, n = 0, len(lines)
    while i < n:
        for idx in sorted(pending):
            if idx == i:
                out.extend(pending.pop(idx))
        line = lines[i]
        am = ANCHOR_RE.match(line.strip())
        if am:
            cur_anchor = am.group(1)
            out.append(line)
            i += 1
            continue
        m = VMARKER.match(line.strip())
        if m and m.group(1) == vkey:
            label = m.group(3).strip() or source_title
            block: list[str] = []
            j = i + 1
            while j < n and lines[j].strip() != VOCAB_END:
                block.append(lines[j])
                j += 1
            # block includes the <details> wrapper; drop it (content moves away)
            inner = [l for l in block if not DETAILS_OPEN.match(l.strip())
                     and l.strip() != "</details>"
                     and not l.strip().startswith("<summary>")]
            kept, stars = move_stars(inner)
            kept = squeeze(kept)
            if kept:
                link = (anchor_links or {}).get(cur_anchor, source_link)
                if CUR_SOURCE[0] == "pali-semester-2.html" and PART_TAG[0]:
                    # semester 2 is split per chapter/part; pick the page that
                    # now holds this lesson (Ch III: 11–17 / 18+,
                    #  Ch IV: 1–10 / 11+)
                    lm = re.match(r"[Ll]esson (\d+)", LAST_HEADING[0])
                    ln = int(lm.group(1)) if lm else 0
                    if PART_TAG[0] == "part1":          # still in Chapter III
                        tag = "ch3-part3" if ln < 18 else "ch3-part4"
                    else:                               # Chapter IV
                        tag = "ch4-part1" if ln < 11 else "ch4-part2"
                    link = f"/summaries/pali/pps-{tag}"
                # every block is recorded; s1 blocks go to the archive page only
                VOCAB_BLOCKS.append({
                    "vkey": vkey, "label": label,
                    "source_title": source_title, "source_link": link,
                    "lines": kept,
                })
            out.append("")
            out.append("")
            AUDITED.setdefault(audit_key, {}).setdefault(label, [])
            for st in stars:
                AUDITED[audit_key][label].append(re.sub(r"^[ \t]*[-*] ", "", st.strip()))
            if stars:
                k = j + 1
                while k < n and not is_exercise_heading(lines[k]):
                    k += 1
                if k < n:
                    pending.setdefault(k, stars + [""])
                else:
                    out.extend(stars + [""])
            i = j + 1
            continue
        out.append(line)
        i += 1
    for idx in sorted(pending):
        out.extend(pending.pop(idx))
    return out


def close_vocab_blocks(lines: list[str]) -> list[str]:
    """Close the <details> blocks emitted during conversion: the marker line is
    replaced by a pointer comment, and the block content is delimited so
    process_vocab can find it."""
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        m = VMARKER.match(line.strip())
        if m:
            out.append(line)
            # find the matching </details>
            j = i + 1
            while j < n and lines[j].strip() != "</details>":
                out.append(lines[j])
                j += 1
            out.append(VOCAB_END)
            i = j + 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def strip_anchors(lines: list[str]) -> list[str]:
    return [l for l in lines if not ANCHOR_RE.match(l.strip())]


def split_anchored(md: str) -> dict[str | None, list[str]]:
    parts: dict[str | None, list[str]] = {}
    key: str | None = None
    buf: list[str] = []
    for line in md.split("\n"):
        m = ANCHOR_RE.match(line.strip())
        if m:
            parts.setdefault(key, []).extend(buf)
            key = m.group(1)
            buf = []
        else:
            buf.append(line)
    parts.setdefault(key, []).extend(buf)
    return {k: squeeze(v) for k, v in parts.items()}


BULLET_LINE = re.compile(r"^( *)- (.*)$")


def rebase_lists(lines: list[str]) -> list[str]:
    """Re-indent bullet columns so a list never appears to start deeper than
    3 spaces (which markdown would render as a code block), while keeping
    true nesting intact.

    A bullet at the same raw indent as the previous bullet of its run is a
    SIBLING and keeps the run's depth - it must not be pushed one level
    deeper (that used to nest 'Vowels: sara' under 'Pāḷi means...', etc.).
    A blank line is also inserted before headings so renderers don't fold
    them into the preceding list item."""
    out: list[str] = []
    stack: list[int] = []  # raw indent columns of currently open levels
    for line in lines:
        m = BULLET_LINE.match(line)
        if m:
            c = len(m.group(1))
            while stack and c < stack[-1]:
                stack.pop()
            if stack and c == stack[-1]:
                depth = len(stack) - 1  # sibling: same depth as its level
            else:  # deeper than every open level: new child level
                stack.append(c)
                depth = len(stack) - 1
            out.append(" " * (depth * 2) + "- " + m.group(2))
            continue
        stripped = line.strip()
        if not stripped:
            out.append(line)  # blank lines don't close a list
            continue
        if line.startswith("#"):
            # keep headings out of the preceding list item / table row
            if (out and out[-1].strip()
                    and not out[-1].lstrip().startswith("#")):
                out.append("")
            stack = []
            out.append(line)
            continue
        if line.startswith(("<", "|", "    ")):
            stack = []
            out.append(line)
            continue
        stack = []
        out.append(line)
    return out


CAP_EXCEPTIONS = {
    "pāḷi", "dhamma", "kamma", "saṅkhāra", "nibbāna", "sutta", "attha",
    "magga", "viññāṇa", "saṅkhata", "niruttidīpaṇī", "pāḷi pāṭha sikkhā",
}


def capitalize_top_bullets(lines: list[str]) -> list[str]:
    """Capitalize the first alphabetic character of each depth-1 bullet
    ('- abc' → '- Abc'); leaves sub-bullets, headings, tables, comments,
    HTML blocks and words starting mid-sentence with an open quote alone."""
    out: list[str] = []
    for line in lines:
        if line.startswith("- ") and len(line) > 2:
            rest = line[2:]
            # letter enumerations like 'a, ā, i, ī…' or 'k, kh, g…' stay lowercase
            if not re.match(r"[a-z], ", rest) and rest and re.match(r"[a-z\u00e0-\u017f]", rest[0]):
                word = re.match(r"[\w'\u00c0-\u024f]+", rest)
                w = word.group(0) if word else ""
                if w.lower() not in CAP_EXCEPTIONS:
                    rest = rest[0].upper() + rest[1:]
            out.append("- " + rest)
        else:
            out.append(line)
    return out


def fix_ch1_lesson1(lines: list[str]) -> list[str]:
    """Lesson 1 (Alphabet) clean-up: drop the intro sentence duplicated as
    '1) …', and move the Sara/Vyañjana letter lists ('2) …') under the
    'Number of vowels' / 'Number of consonants' bullets."""
    vowels: list[str] = []
    consonants: list[str] = []
    kept: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()
        if s.startswith("- 1) ") and "Māgadhī" in s:
            i += 1  # duplicate of the lesson's opening bullet
            continue
        if s.startswith("- 2)"):
            mode = ""
            j = i + 1
            while j < n:
                t = lines[j]
                ts = t.strip()
                if not ts:
                    j += 1
                    continue
                if not t.startswith(("    - ", "      - ")):
                    break
                if ts.startswith("- Sara"):
                    mode = "v"
                elif ts.startswith("- Vyañjana"):
                    mode = "c"
                elif mode == "v":
                    vowels.append(ts[2:])
                elif mode == "c":
                    consonants.append(ts[2:])
                j += 1
            i = j
            continue
        kept.append(line)
        i += 1
    out: list[str] = []
    for line in kept:
        out.append(line)
        s = line.strip()
        if s.startswith("- Number of vowels:"):
            out.extend("    - " + v for v in vowels)
        elif s.startswith("- Number of consonants:"):
            out.extend("    - " + v for v in consonants)
    if vowels or consonants:
        print("fix_ch1_lesson1: moved", len(vowels), "vowel lines /",
              len(consonants), "consonant lines")
    return out


def fix_ch1_lesson7(lines: list[str]) -> list[str]:
    """Lesson 7 (Dative & Ablative): open a '### Dative' subsection right
    after the lesson heading, and turn the numbered '7.2 Ablative' bullet
    into a plain '### Ablative' heading (numbering dropped)."""
    out: list[str] = []
    for line in lines:
        if line.startswith("## Lesson 7"):
            out.append(line)
            out.append("### Dative")
            continue
        m = re.match(r"^  - \d+\.\d+\.?\s+(.+)$", line)
        if m and not re.match(r"(reading|grammar|exercise)", m.group(1), re.I):
            out.append("### " + m.group(1).strip())
            continue
        out.append(line)
    return out


def fix_ch1_lesson8(lines: list[str]) -> list[str]:
    """Lesson 8 (Genitive and Location): open a '### Genitive' subsection
    after the lesson heading and a '### Location' one before the location
    paragraph, mirroring the Lesson 7 structure."""
    out: list[str] = []
    for line in lines:
        if line.startswith("## Lesson 8"):
            out.append(line)
            out.append("### Genitive")
            continue
        if line.strip().startswith(
                "- The place where an action takes place is the location"):
            out.append("### Location")
        out.append(line)
    return out


PREFIX_LISTS = (
    "pa, parā, ni, nī, u, du,",
    "saṁ, vi, ava, anu,",
    "pari, adhi, abhi, pati, su, ā",
    "ati, api, apa, upa",
)


def fix_ch1_indeclinables(lines: list[str]) -> list[str]:
    """10.2 'Indeclinable particles and prefixes': the four prefix-group
    bullets are a plain enumeration, not a declension - render them as a
    4-row single-column table (no singular/plural columns) under an
    'upasaggas' header row (so the first vagga row does not render bold)
    below the 'Prefixes also do not undergo...' bullet."""
    dropped = 0
    out: list[str] = []
    for line in lines:
        if line.strip().lstrip("- ").rstrip() in PREFIX_LISTS:
            dropped += 1
            continue
        out.append(line)
        if line.strip().startswith(
                "- Prefixes also do not undergo any changes in declension"):
            out.append("")
            rows = [r.rstrip(",").strip() for r in PREFIX_LISTS]
            out.append("    | upasaggas |")
            out.append("    |---|")
            out.extend("    | " + r + " |" for r in rows)
            out.append("")
    if dropped:
        print(f"fix_ch1_indeclinables: tableized {len(PREFIX_LISTS)} prefix "
              f"rows (dropped {dropped} bullets)")
    return out


EXERCISE_BULLET_RE = re.compile(r"^(\s*)- Lesson \d+ - [Ee]xercises\s*$")


def _is_scaffold(s: str) -> bool:
    """Exercise scaffolding: author credit lines and 'already submitted'
    stubs (with or without __bold__ wrapping)."""
    t = s.replace("__", "").strip()
    return (t.startswith("by (Bra") and "Ariyañāṇa" in t) or \
        (t.startswith("Exercises pg.") and "already submitted" in t)


def salvage_exercise_notes(lines: list[str]) -> list[str]:
    """PPS chapters: the 'Lesson N - Exercises' bullets wrap unique grammar
    notes (worked visesana/visesya examples, extra declensions, definition
    recaps) in exercise scaffolding. Move the content under a
    '### Notes from the exercises' heading at the end of the lesson and drop
    the scaffolding ('by (Brazil) Ariyañāṇa Bhikkhu', 'Exercises pg. N
    (already submitted)') and bare numbering shells ('- 1)')."""
    out: list[str] = []
    moved = 0
    i, n = 0, len(lines)
    while i < n:
        m = EXERCISE_BULLET_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        base = len(m.group(1))
        # collect the block: everything until a line at/below the bullet's
        # own level (the next lesson heading). '____' lines are bold-marker
        # wrap continuations of the author credit, not content.
        j = i + 1
        while j < n and (not lines[j].strip()
                         or re.fullmatch(r"_+", lines[j].strip())
                         or len(lines[j]) - len(lines[j].lstrip()) > base):
            j += 1
        kept: list[str] = []
        for line in lines[i + 1:j]:
            s = line.strip()
            # drop the bullet marker so scaffold/numbering tests see the text
            t = re.sub(r"^-\s*", "", s)
            if not s or re.fullmatch(r"_+", s) or _is_scaffold(t):
                continue
            if re.fullmatch(r"1\)[.)]?", t):  # bare numbering shell
                continue
            # RemNote ':>' glue artifact inside a bullet's text
            line = line.replace(":>", ": ")
            # numbered exercise instruction ('2). Decline the following
            # nouns: …') → plain instruction bullet
            line = re.sub(r"^(\s*)-\s*\d+\)\.?\s+", r"\1- ", line)
            kept.append(line.rstrip())
        if kept:
            min_indent = min(len(k) - len(k.lstrip()) for k in kept)
            # notes bullets start at column 0 right under the heading (an
            # indented list after a heading can render as a code block)
            shift = min_indent
            kept = [k[shift:] if k.strip() else k for k in kept]
            out.append("")
            out.append("### Notes from the exercises")
            out.append("")
            out.extend(kept)
            out.append("")
            moved += 1
        i = j
    if moved:
        print(f"salvage_exercise_notes: {moved} exercise block(s) converted")
    return out


# ---------------------------------------------------------------- declension tables

CASE_LABEL = r"(?:nom|voc|acc|ins|dat|gen|abl|loc)"
CASE_ROW_RE = re.compile(
    r"^(?P<indent>\s*)- [*^_~]{0,8}\s*(?P<label>" + CASE_LABEL + r"\b\.?(?:[\s.,/*^_~]+"
    + CASE_LABEL + r"\b\.?)*(?:\s*&\s*" + CASE_LABEL + r"\b\.?)?)[*^_~]{0,8}\.?\s+(?P<rest>\S.*)$",
    re.I)
CASE_MONO_SPLIT_RE = re.compile(r"\s+(?=" + CASE_LABEL + r"\.)", re.I)
VERB_ROW_RE = re.compile(r"^(?P<indent>\s*)- (?P<rest>\S.*)$")
VERB_CELL_BAD = re.compile(r"[.\-:|>]| - |–|—|⇒|√|×|･")
VERB_COMMA_PAIR = re.compile(r"^[^,]+,[^,]+$")
_VERB_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)  # a single word
_ASCII_WORD_RE = re.compile(r"[A-Za-z]+")
_VERB_PERSONS = ["3rd pp.", "2nd pp.", "1st pp."]


def _table(rows: list[tuple[str, str]], labeled: bool = True) -> list[str]:
    """Render case rows as a markdown table with a fixed
    | case | singular | plural | header ('' instead of 'case' for unlabeled
    rows); '/' splits the columns. Trailing empty cells (stray '/') are
    dropped and surplus columns fold into the plural cell."""
    parsed = []
    for label, rest in rows:
        label = re.sub(r"[*^_~]", "", label)  # strip RemNote markers from labels
        # safety: a rest like '/ abl. forms...' means the label regex stopped
        # early - fold the leading label back into the row label
        m2 = re.match(r"^[.,/]+\s*(" + CASE_LABEL + r"\b\.?)\s+(.+)$", rest, re.I)
        if m2:
            label = label + " / " + m2.group(1)
            rest = m2.group(2)
        cells = [c.strip() for c in rest.split("/")]
        while len(cells) > 1 and not cells[-1]:
            cells.pop()
        if len(cells) > 2:
            cells = [cells[0], ", ".join(c for c in cells[1:] if c)]
        parsed.append([label.strip()] + cells)
    ncols = max(len(r) for r in parsed)
    for r in parsed:
        r.extend([""] * (ncols - len(r)))
    first = "case" if labeled else ""
    if ncols <= 3:
        header = [first, "singular", "plural"][:ncols]
    else:
        header = [first] + [""] * (ncols - 1)
    lines = ["| " + " | ".join(header) + " |",
             "|" + "---|" * ncols]
    for r in parsed:
        lines.append("| " + " | ".join(r) + " |")
    return lines


def _mono_rows(label: str, rest: str) -> list[tuple[str, str]]:
    """Split a one-bullet declension ('nom. go / ... voc. (he) go / ... acc. ...')
    into (label, forms) rows."""
    rows: list[tuple[str, str]] = []
    for seg in CASE_MONO_SPLIT_RE.split(label + " " + rest):
        sm = re.match(r"(?P<label>" + CASE_LABEL + r"\b[^\s]*)\s*(?P<rest>.*)$",
                      seg.strip(), re.I)
        if sm:
            rows.append((sm.group("label"), sm.group("rest")))
    return rows


def declension_tables(lines: list[str]) -> list[str]:
    """Turn runs of case-labeled bullets (nom./voc./acc./...) into markdown
    tables where '/' separates singular from plural. Also splits a single
    bullet holding a whole declension. Runs shorter than 3 rows (usually
    mem-aid notes) stay as bullets. Additionally converts unlabeled
    singular/plural bullet runs (gunavantu, yagu, taruni, ...), verbal
    conjugation runs (ajjatani/bhavissanti/sattami ...) and letter
    enumerations (the alphabet vagga rows) into tables."""
    return _case_tables(_termination_tables(_verb_tables(_noun_tables(
        _person_purisa_tables(_alphabet_tables(lines))))))


_PERSON_PURISA_RE = re.compile(
    r"^(?P<person>(?:paṭhama|pathama|majjhima|uttama)\s+purisa)\s+(?P<rest>\S.*)$", re.I)


def _person_purisa_tables(lines: list[str]) -> list[str]:
    """Conjugation bullets like 'paṭhama purisa (third person): ti / nti'
    carry the person label inside the singular cell; split it out so the run
    becomes a | person | singular | plural | table with all three persons.
    An English translation ('third person') stays in parenthesis on the
    first row only; later rows keep just the Pāḷi term."""
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        m = re.match(r"^(?P<indent>\s*)- (?P<rest>\S.*)$", lines[i])
        pm = _PERSON_PURISA_RE.match(m.group("rest")) if m else None
        if not pm or "/" not in pm.group("rest"):
            out.append(lines[i])
            i += 1
            continue
        indent = len(m.group("indent"))
        rows: list[tuple[str, str, str, str]] = []
        j = i
        while j < n:
            mm = re.match(r"^(?P<indent>\s*)- (?P<rest>\S.*)$", lines[j])
            if not mm or len(mm.group("indent")) != indent:
                break
            p2 = _PERSON_PURISA_RE.match(mm.group("rest"))
            if not p2:
                break
            person = p2.group("person").lower()
            rest = p2.group("rest")
            trans = ""
            mt = re.match(r"^\(([^()]*)\)\s*:?\s*(.*)$", rest)
            if mt and "person" in mt.group(1).lower():
                trans = mt.group(1)
                rest = mt.group(2)
            if "/" not in rest:
                break
            sg, pl = (x.strip() for x in rest.split("/", 1))
            if not sg or not pl:
                break
            rows.append((person, trans, sg, pl))
            j += 1
        if len(rows) >= 2:
            out.append("")
            out.append(" " * indent + "| person | singular | plural |")
            out.append(" " * indent + "|---|---|---|")
            for k, (person, trans, sg, pl) in enumerate(rows):
                label = person + (f" ({trans})" if k == 0 and trans else "")
                out.append(" " * indent + f"| {label} | {sg} | {pl} |")
            out.append("")
            i = j
        else:
            out.append(lines[i])
            i += 1
    return out


def _alpha_parts(text: str) -> str | None:
    """'k, kh, g, gh, ṅ' -> 'k kh g gh ṅ'; None if not a letter enumeration
    (items are 1-2 letter words, optionally with a '(...)' annotation)."""
    text = text.strip()
    if "," not in text or "/" in text or ":" in text:
        return None
    parts = [p.strip() for p in text.split(",")]
    if len(parts) < 3:
        return None
    for p in parts:
        if not re.fullmatch(r"[^\s,/]{1,2}\s*(\([^)]*\))?", p):
            return None
    return " ".join(parts)


def _alphabet_tables(lines: list[str]) -> list[str]:
    """Runs of >=2 letter-enumeration bullets (one vagga per bullet) become a
    single-column table without a header row: the first vagga row renders as
    the table head, exactly as '|' k kh g gh ṅ |'. Vowel lists (single rows)
    and vocab glosses stay bullets."""
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        m = re.match(r"^(?P<indent>\s*)- (?P<rest>\S.*)$", lines[i])
        if not m or _alpha_parts(m.group("rest")) is None:
            out.append(lines[i])
            i += 1
            continue
        indent = len(m.group("indent"))
        rows = [_alpha_parts(m.group("rest"))]
        j = i + 1
        while j < n:
            mm = re.match(r"^(?P<indent>\s*)- (?P<rest>\S.*)$", lines[j])
            if not mm or len(mm.group("indent")) != indent:
                break
            p = _alpha_parts(mm.group("rest"))
            if p is None:
                break
            rows.append(p)
            j += 1
        if len(rows) >= 2:
            out.append("")
            out.append(" " * indent + "| " + rows[0] + " |")
            out.append(" " * indent + "|---|")
            out.extend(" " * indent + "| " + r + " |" for r in rows[1:])
            out.append("")
            i = j
        else:
            out.append(lines[i])
            i += 1
    return out


_TERMINATION_TOKEN = re.compile(r"^[()\-a-zāīūṅñṭḍṇḷṁṃ]+$", re.I)
_INTERJ_RE = re.compile(r"\s\((?:bho|bhonto|bhavant[āa]|bhoti|bhotiyo)\)")


def _termination_row(text: str) -> list[str] | None:
    """A verbal-termination bullet like '-tu / -antu' or '(a)-hi / -tha':
    exactly two parts, each a single Pāḷi token carrying a hyphen or a
    parenthesis. Plain form pairs ('gacchati / gacchanti') never match."""
    text = text.strip().rstrip(":,").strip()
    if "/" not in text or ("-" not in text and "(" not in text):
        return None
    parts = [p.strip() for p in text.split("/")]
    if len(parts) != 2 or not all(parts):
        return None
    cells = [re.sub(r"\s+", "", p) for p in parts]
    if not all(_TERMINATION_TOKEN.fullmatch(c) for c in cells):
        return None
    return cells


def _termination_tables(lines: list[str]) -> list[str]:
    """Runs of >=2 hyphenated verbal-termination bullets ('-tu / -antu',
    '(a)-hi / -tha', '(ā)-mi / (ā)-ma') become a | person | singular |
    plural | table (3rd, 2nd, 1st pp.). Single rows and prose stay bullets."""
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        m = re.match(r"^(?P<indent>\s*)- (?P<rest>\S.*)$", lines[i])
        r0 = _termination_row(m.group("rest")) if m else None
        if r0 is None:
            out.append(lines[i])
            i += 1
            continue
        indent = len(m.group("indent"))
        rows = [r0]
        j = i + 1
        while j < n:
            mm = re.match(r"^(?P<indent>\s*)- (?P<rest>\S.*)$", lines[j])
            r = _termination_row(mm.group("rest")) if mm else None
            if r is None or len(mm.group("indent")) != indent:
                break
            rows.append(r)
            j += 1
        if len(rows) >= 2:
            pad = " " * indent
            out.append("")
            out.append(pad + "| person | singular | plural |")
            out.append(pad + "|---|---|---|")
            for k, (sg, pl) in enumerate(rows):
                p = _VERB_PERSONS[k] if k < len(_VERB_PERSONS) else str(k + 1)
                out.append(pad + f"| {p} | {sg} | {pl} |")
            out.append("")
            i = j
        else:
            out.append(lines[i])
            i += 1
    return out


def _mono_declension(text: str) -> tuple[list[list[str]], str] | None:
    """Split a declension smashed into a single bullet into singular/plural
    rows: 'cittaṁ / cittā, cittāni (bho) citta, cittā / (bhavantāni) "
    cittaṁ / citte, cittāni...(as purisa)'. The transition between a plural
    cell and the next singular cell is an interjection parenthesis ('(bho)')
    or a repeated-cell quote (' "'). Returns (rows, trailing note)."""
    text = text.strip().rstrip(">")
    if text.count("/") != 3:
        return None
    if re.search(r"\b" + CASE_LABEL + r"\b", text, re.I):
        return None
    parts = [p.strip() for p in text.split("/")]

    def transition(seg: str) -> tuple[str, str] | None:
        qi = seg.find('"')
        pm = _INTERJ_RE.search(seg)
        if qi != -1 and (pm is None or qi < pm.start()):
            return seg[:qi + 1].strip(), seg[qi + 1:].strip()
        if pm:
            return seg[:pm.start()].strip(), seg[pm.start():].strip()
        return None

    t1 = transition(parts[1])
    t2 = transition(parts[2])
    if t1 is None or t2 is None:
        return None
    pl1, sg2 = t1
    pl2, sg3 = t2
    if not (parts[0] and pl1 and sg2 and pl2 and sg3):
        return None
    tail = parts[3]
    note = ""
    mn = re.search(r"((?:\.{2,}|\u2026)\s*)?(\([^()]*\))\s*$", tail)
    if mn and (mn.group(1) or " " in mn.group(2)):
        note = mn.group(2)
        tail = tail[:mn.start(2)].strip()
        if mn.group(1):
            tail = tail.rstrip(".\u2026 \t").strip()
    if not tail:
        return None
    return [[parts[0], pl1], [sg2, pl2], [sg3, tail]], note


def _prefix_table(lines: list[str]) -> list[str]:
    """Curated pages carry the four upasagga group bullets as literal lines;
    replace them with the headered single-column table (same as the
    generated pages get from fix_ch1_indeclinables)."""
    want = [r.rstrip(",").strip() for r in PREFIX_LISTS]
    pat = re.compile(r"^\s*- (?:pa, parā|saṁ, vi|pari, adhi|ati, api)")
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        if pat.match(lines[i]):
            j = i
            rows: list[str] = []
            while j < n and pat.match(lines[j]):
                rows.append(lines[j].strip().lstrip("- ").rstrip(", \t"))
                j += 1
            if rows == want:
                pad = " " * (len(lines[i]) - len(lines[i].lstrip()))
                out.append(pad + "| upasaggas |")
                out.append(pad + "|---|")
                out.extend(pad + "| " + r + " |" for r in rows)
                i = j
                continue
        out.append(lines[i])
        i += 1
    return out


def _join_wrapped_bullets(lines: list[str]) -> list[str]:
    """RemNote exports wrap long bullets over several physical lines ('- ī,
    i, / uṁ, iṁsu' / 'o, (i) / ttha' / ...). Rejoin any non-empty line that
    is neither a bullet, a table row, a heading nor a comment into its
    preceding bullet, so the declension/table parsers see one bullet."""
    out: list[str] = []
    for line in lines:
        if (out and line.strip()
                and not line.lstrip().startswith(("-", "|", "#", "<"))
                and out[-1].strip()):
            out[-1] = out[-1].rstrip() + " " + line.strip()
        else:
            out.append(line)
    return out


def _curated_tables(lines: list[str]) -> list[str]:
    """declension_tables for hand-curated pages: rejoins RemNote-wrapped
    bullets, runs the prefix-group replacement, text fixes (↓ arrows, the
    '*declension' glyph, 'rassa sara'), then the standard pipeline."""
    lines = _join_wrapped_bullets(lines)
    lines = _prefix_table(lines)
    lines = [strip_misc_text(l) if not l.lstrip().startswith(("|", "#", "<"))
             else l for l in lines]
    return _case_tables(_termination_tables(_verb_tables(_noun_tables(
        _person_purisa_tables(_alphabet_tables(lines))))))


def _is_quotable(t: str) -> bool:
    t = t.strip()
    return bool(t) and bool(re.fullmatch(r"[\u0022\u201c\u201d\u2013]+", t))


def _fix_quotes(cells: list[str]) -> None:
    """Normalize quote/dash marks standing for a repeated cell to a plain
    double-quote character."""
    for i, c in enumerate(cells):
        if _is_quotable(c):
            cells[i] = '"'


def _split_pairs(text: str) -> list[str]:
    """Split 'a / b c / d' into 'a / b' and 'c / d': a lone word between two
    slashes belongs with the following one ('ssati / ssanti ssasi / ssatha'
    gives 'ssati / ssanti' and 'ssasi / ssatha'). Used for noun rows whose
    cells are comma lists (spaces inside cells are kept)."""
    parts = [p.strip() for p in text.split("/")]
    out = [parts[0]] if parts and parts[0] else []
    k = 1
    while k < len(parts):
        tk = parts[k]
        if tk and " " not in tk and k + 1 < len(parts):
            out.append(tk + " / " + parts[k + 1].strip())
            k += 2
        elif tk:
            out.append(tk)
            k += 1
        else:
            k += 1
    return [p for p in (s.strip() for s in out) if p]


def _verb_cells(text: str) -> list[str] | None:
    """Split a slashed verb line into person-pair cells. Handles smashed
    lines ('ssati / ssanti ssasi / ssatha' -> 'ssati / ssanti', 'ssasi /
    ssatha') and comma-list cells ('i, i / um, imsu o, i / ttha im / mha,
    mha'): a part closes the open pair with its first word, or with the word
    after the first comma-ended word when the cell is a comma list."""
    parts = [p.strip() for p in text.split("/") if p.strip()]
    if not parts:
        return None
    cells: list[str] = []
    head = parts[0]
    k = 1
    while k < len(parts):
        words = parts[k].split(" ")
        ci = next((i for i, w in enumerate(words) if w.endswith(",")), None)
        cut = (ci + 2) if ci is not None else 1
        cut = min(cut, len(words))
        close = " ".join(words[:cut])
        rest = " ".join(words[cut:]).strip()
        cells.append(head + " / " + close)
        head = rest
        k += 1
    if head:
        cells.append(head)
    return cells or None


def _unlabeled_row(text: str) -> list[str] | None:
    """Parse 'a / b c / d' into the cells ['a / b', 'c / d']; a bullet with no
    slash is not a row."""
    text = text.strip()
    if not text or "/" not in text:
        return None
    cells = _split_pairs(text)
    if len(cells) > 2 or any(VERB_CELL_BAD.search(c) for c in cells):
        return None
    return cells


def _unlabeled_run(rows: list[list[str]]) -> list[str] | None:
    """Needs at least 2 rows sharing one shape (same cell count). Rows only
    reach here after passing _unlabeled_row, which requires a '/'. Returns
    table lines or None."""
    if len(rows) < 2 or not all(len(r) == len(rows[0]) for r in rows):
        return None
    r0 = rows[0]
    # unlabeled rows carry no case column: the cells themselves are the
    # singular / plural columns
    hdr = ["singular", "plural"][:len(r0)]
    return (["| " + " | ".join(hdr) + " |", "|" + "---|" * len(r0)]
            + ["| " + " | ".join(r) + " |" for r in rows])


def _unlabeled_bullet(text: str) -> bool:
    """A declension bullet: contains '/', no case labels, no 'Label:' notes."""
    t = text.strip()
    if not t or "/" not in t:
        return False
    if re.search(r"\b" + CASE_LABEL + r"\b", t, re.I):
        return False
    if re.match(r"^[A-Z][a-z\u00e0-\u00ff]+\s*:", t):  # 'mem aid:', 'note:' ...
        return False
    if re.search(r"\w>\w", t):  # sandhi/transformation rule (i>v/a), not forms
        return False
    return True


def _frag_run(lines: list[str], i: int, j: int, indent: int) -> bool:
    """A candidate table run is 'fragmentary' when a same-indent sibling
    bullet follows it that is neither a row nor a table/heading. Such lists
    are partial mem-aids (e.g. guṇavantu 'forms with va:'), not declensions
    - never tableize them. Two siblings mark a COMPLETE run instead:
    'forms with va:' (a per-case suffix recap of the rows above) and
    'mem aid:'/'memory aid:' (a mnemonic following the full declension,
    e.g. guṇavantu m.) - the rows above may become a table."""
    for k in range(j, min(j + 3, len(lines))):
        s = lines[k].strip()
        if not s:
            continue
        mm = re.match(r"^(\s*)- (.+)$", lines[k])
        if mm:
            if len(mm.group(1)) != indent:
                return False
            # label checks must see the text WITH the '- ' bullet stripped
            # (previously the dash defeated these patterns)
            text = mm.group(2)
            if re.match(r"^\*?\*?\s*forms with", text, re.I):
                return False
            if re.match(r"^\*?\*?\s*(?:mem|memory)\s+aid\b\s*:", text, re.I):
                return False
            return True
        if not s.startswith(("#", "<", "|")):
            return False
    return False


def _noun_tables(lines: list[str]) -> list[str]:
    """Unlabeled singular/plural bullet runs become tables (quote cells
    normalized)."""
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        m = re.match(r"^(?P<indent>\s*)- (?P<rest>.+)$", lines[i])
        # a whole declension smashed into one bullet ('cittaṁ / cittā, cittāni
        # (bho) citta, cittā / (bhavantāni) " cittaṁ / citte, cittāni...')
        # splits into proper sg/pl rows
        mono = _mono_declension(m.group("rest")) if m else None
        if mono is not None:
            rows, note = mono
            for r in rows:
                _fix_quotes(r)
            pad = " " * len(m.group("indent"))
            out.append("")
            out.extend(pad + t for t in _unlabeled_run(rows))
            if note:
                out.append(pad + "- " + note)
            out.append("")
            i += 1
            continue
        if not m or not _unlabeled_bullet(m.group("rest")):
            out.append(lines[i])
            i += 1
            continue
        indent = len(m.group("indent"))
        rows: list[list[str]] = []
        j = i
        while j < n:
            mm = re.match(r"^(?P<indent>\s*)- (?P<rest>.+)$", lines[j])
            if mm and len(mm.group("indent")) == indent:
                r = _unlabeled_row(mm.group("rest"))
                if r is None:
                    break
                _fix_quotes(r)
                rows.append(r)
                j += 1
                continue
            # blank line(s) inside a run are fine if a same-level row follows
            k = j
            while k < n and not lines[k].strip():
                k += 1
            if k > j:
                mm2 = re.match(r"^(?P<indent>\s*)- (?P<rest>.+)$", lines[k]) if k < n else None
                if (mm2 and len(mm2.group("indent")) == indent
                        and _unlabeled_row(mm2.group("rest")) is not None):
                    j = k
                    continue
            break
        if rows and _frag_run(lines, i, j, indent):
            tbl = None
        else:
            tbl = _unlabeled_run(rows)
        if tbl:
            pad = " " * indent
            out.append("")
            out.extend(pad + t for t in tbl)
            out.append("")
        elif j > i:
            out.extend(lines[i:j])
        else:
            out.append(lines[i])
        i = j if j > i else i + 1  # always advance (first row may fail the check)
    return out


def _verb_row(text: str) -> list[str] | None:
    """Parse one verb bullet into cells: slashed lines via _verb_cells
    (smash-unsmashed), or a bare comma pair ('eyya, eyyuṃ,') as 2 cells.
    Trailing commas are line-wrap artifacts and are stripped."""
    text = text.strip()
    if not text or VERB_CELL_BAD.search(text):
        return None
    if "/" in text:
        cells = _verb_cells(text)
        if cells is not None and len(cells) > 3:
            return None  # a line holds at most 3 person pairs
    else:
        # a bare comma pair ('eyya, eyyuṃ,'): exactly two comma parts, each a
        # single word — letter enumerations ('k, kh, g, gh, ṅ'), word lists
        # and multi-word glosses are not verb rows. The trailing comma is a
        # line-wrap artifact and is dropped before splitting.
        t = text.rstrip(",").strip()
        parts = [p.strip().rstrip(",").strip() for p in t.split(",")]
        bare = [p.replace("**", "").strip() for p in parts]  # RemNote bold
        if (len(parts) != 2 or not all(parts)
                or not all(len(p) > 1 and _VERB_WORD_RE.fullmatch(p)
                           for p in bare)):
            # a whole conjugation smashed into one comma/space-separated line
            # ('ssati, ssanti ssasi, ssatha ssāmi, ssāma') is 6 single words
            mm = re.fullmatch(
                r"(\S+),\s+(\S+)\s+(\S+),\s+(\S+)\s+(\S+),\s+(\S+)", text)
            if (mm and all(len(w) > 1 and _VERB_WORD_RE.fullmatch(w)
                           for w in mm.groups())):
                g = mm.groups()
                cells = [f"{g[k]}, {g[k + 1]}" for k in (0, 2, 4)]
            else:
                return None
        else:
            cells = parts
    return [re.sub(r"\s+([,;])", r"\1", c) for c in cells] if cells else None


def _verb_cells_per_row(cells: list[str]) -> int | None:
    """3 cells = 3 smashed person-pairs per line; 2 cells = 2 explicit pairs;
    1 cell = a single explicit pair; anything else is not part of a run."""
    if len(cells) == 3 and all("/" in c for c in cells):
        return 3
    if len(cells) == 3 and all("/" not in c
                               and VERB_COMMA_PAIR.fullmatch(c) for c in cells):
        return 3  # one whole conjugation smashed into a single line
    if len(cells) == 2 and all("/" in c for c in cells):
        return 2
    if len(cells) == 1 and "/" in cells[0]:
        return 1
    if len(cells) == 2 and all("/" not in c for c in cells):
        return 1  # comma pair like 'eyya, eyyuṃ,'
    return None


def _verb_tables(lines: list[str]) -> list[str]:
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        m = VERB_ROW_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        indent = len(m.group("indent"))
        # head: the first bullet must itself parse as a verb row — this
        # parser only claims runs of conjugation bullets, not arbitrary
        # lists (e.g. the consonant alphabet 'k, kh, g, gh, ṅ')
        r0 = _verb_row(m.group("rest"))
        if r0 is None or _verb_cells_per_row(r0) is None:
            out.append(lines[i])
            i += 1
            continue
        rows: list[list[str]] = []
        j = i
        while j < n:
            mm = VERB_ROW_RE.match(lines[j])
            if mm and len(mm.group("indent")) == indent:
                r = _verb_row(mm.group("rest"))
                if r is None or _verb_cells_per_row(r) is None:
                    break
                rows.append(r)
                j += 1
                continue
            # blank line(s) inside a run are fine if a same-level row follows
            k = j
            while k < n and not lines[k].strip():
                k += 1
            if k > j:
                mm2 = VERB_ROW_RE.match(lines[k]) if k < n else None
                if mm2 and len(mm2.group("indent")) == indent:
                    r2 = _verb_row(mm2.group("rest"))
                    if r2 is not None and _verb_cells_per_row(r2) is not None:
                        j = k
                        continue
            break
        # a single smashed 3-pair line ('ī, i, / uṁ, iṁsu o, (i) / ttha iṁ /
        # mhā, mha') is a complete 3-person conjugation on its own
        single = (len(rows) == 1 and len(rows[0]) == 3
                  and all("/" in c or "," in c for c in rows[0]))
        if rows and _frag_run(lines, i, j, indent):
            tbl = None
        elif len(rows) >= 2 or single:
            tbl = _verb_table(rows)
        else:
            tbl = None
        if tbl:
            pad = " " * indent
            out.append("")
            out.extend(pad + t for t in tbl)
            out.append("")
        elif j > i:
            out.extend(lines[i:j])
        else:
            out.append(lines[i])
        i = j if j > i else i + 1  # always advance (first row may fail the check)
    return out


def _verb_table(rows: list[list[str]]) -> list[str] | None:
    """Render verb conjugation rows as a | person | singular | plural | table.
    Every row is normalized to person-pairs: k slashed cells = k pairs, two
    comma cells = one pair, one slash cell = one pair. The person label is
    the pair's position within its source line (3rd, 2nd, 1st pp.), or the
    line's position when every line holds exactly one pair."""
    # comma-pair runs (no slashes) need >=3 rows: optative-style termination
    # lists ('eyya, eyyuṃ,' ...); shorter comma pairs are vocabulary pairs
    if (rows and all(len(r) == 2 and "/" not in r[0] and "/" not in r[1]
                     for r in rows) and len(rows) < 3):
        return None
    per_row: list[list[tuple[str, str]]] = []
    for r in rows:
        # trailing commas are line-wrap artifacts; ** pairs are RemNote bold
        r = [re.sub(r",\s*$", "", c.replace("**", "")).strip() for c in r]
        if r and all("/" in c for c in r):
            pr = []
            for c in r:
                a, b = c.split("/", 1)
                # a comma before the slash is a line-wrap artifact
                pr.append((a.strip().rstrip(",").strip(), b.strip()))
            per_row.append(pr)
        elif len(r) == 3 and all("/" not in c and "," in c for c in r):
            # a whole conjugation smashed into one line: the 3 cells are the
            # 3 person pairs ('ssati, ssanti' / 'ssasi, ssatha' / 'ssāmi, ssāma')
            per_row.append([(c.split(",", 1)[0].strip(),
                             c.split(",", 1)[1].strip()) for c in r])
        elif len(r) == 2:
            per_row.append([(r[0], r[1])])
        elif len(r) == 1:
            per_row.append([(r[0], "")])
        else:
            return None
    if not per_row:
        return None
    # prose guard: a cell holding >=3 ASCII-only words is a sentence or a
    # definition, not a conjugation form (Pali forms are short or diacritic)
    for pr in per_row:
        for sg, pl in pr:
            for cell in (sg, pl):
                toks = [t for t in re.split(r"\s+", cell) if t]
                if sum(1 for t in toks if _ASCII_WORD_RE.fullmatch(t)) >= 3:
                    return None
    one_per_line = all(len(pr) == 1 for pr in per_row)
    out = ["| person | singular | plural |", "|---|---|---|"]
    for i, pr in enumerate(per_row):
        for j, (sg, pl) in enumerate(pr):
            k = i if one_per_line else j
            p = _VERB_PERSONS[k] if k < len(_VERB_PERSONS) else str(k + 1)
            out.append("| " + p + " | " + sg + " | " + pl + " |")
    return out


def _case_tables(lines: list[str]) -> list[str]:
    """Runs of case-labeled bullets (nom./voc./acc./...) become tables."""
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        m = CASE_ROW_RE.match(lines[i])
        if m and len(CASE_MONO_SPLIT_RE.findall(m.group("rest"))) >= 2:
            rows = _mono_rows(m.group("label"), m.group("rest"))
            if len(rows) >= 3:
                out.append("")
                out.extend(_table(rows, labeled=True))
                out.append("")
                i += 1
                continue
        if not m:
            out.append(lines[i])
            i += 1
            continue
        # prose/formula guard: bullets like 'gen + nom + atthi / natthi:
        # structure ...' use a case word inside a structural formula, not as
        # a row label - never start a table from them
        if re.search(r"\b(?:atthi|natthi)\b", m.group("rest"), re.I):
            out.append(lines[i])
            i += 1
            continue
        indent = len(m.group("indent"))
        rows: list[tuple[str, str]] = []
        notes: list[str] = []
        j = i
        while j < n:
            mm = CASE_ROW_RE.match(lines[j])
            if mm and len(mm.group("indent")) >= indent:
                rows.append((mm.group("label"), mm.group("rest")))
                j += 1
                continue
            # absorb blank line(s) and one note line if a same-level row follows
            k = j
            while k < n and not lines[k].strip():
                k += 1
            note_end = k
            if (k < n and not lines[k].startswith(("#", "<", "|"))
                    and not CASE_ROW_RE.match(lines[k])
                    and not re.search(r"\bdeclension\b", lines[k], re.I)):
                note_end = k + 1  # one interleaved note line
                k2 = note_end
                while k2 < n and not lines[k2].strip():
                    k2 += 1
                mm2 = CASE_ROW_RE.match(lines[k2]) if k2 < n else None
                if mm2 and len(mm2.group("indent")) >= indent:
                    notes.extend(lines[j:note_end])
                    j = k2
                    continue
            mm3 = CASE_ROW_RE.match(lines[k]) if k < n else None
            if k > j and mm3 and len(mm3.group("indent")) >= indent:
                j = k  # blank line(s) inside the run
                continue
            break
        # an unlabeled sibling bullet directly above the first case row is a
        # nominative row RemNote left unlabelled: fold it into the table
        if rows:
            k = i - 1
            while k >= 0 and not lines[k].strip():
                k -= 1
            pm = re.match(r"^(?P<indent>\s*)- (?P<rest>.+)$", lines[k]) if k >= 0 else None
            if (pm and len(pm.group("indent")) == indent
                    and "/" in pm.group("rest")
                    and _unlabeled_bullet(pm.group("rest"))):
                # the bullet must be the very last thing emitted verbatim
                # (possibly followed by blanks) - otherwise leave it alone
                while out and not out[-1].strip():
                    out.pop()
                if out and out[-1] == lines[k]:
                    out.pop()
                    rows.insert(0, ("nom.", pm.group("rest").strip()))
        if len(rows) >= 2 or (len(rows) == 1 and "/" in rows[0][1]):
            # keep the table inside its list item: align with the case rows'
            # own indentation (= the parent bullet's content column)
            pad = " " * indent
            out.append("")
            out.extend(pad + t for t in _table(rows, labeled=True))
            out.append("")
            out.extend(notes)
        else:
            out.extend(lines[i:j])
        i = j
    return out


def split_at_lessons(lines: list[str]) -> tuple[list[str], list[str]]:
    """Split a chapter body in half: the first '## Lesson N' heading that is
    past the midpoint starts part 2."""
    heads = [i for i, l in enumerate(lines)
             if (m := H_RE.match(l)) and m.group(1) == "##"
             and re.match(r"lesson\s+\d+", m.group(2), re.I)]
    if len(heads) < 2:
        return lines, []
    # split into halves by lesson count: lessons 1-5 / 6-10, etc.
    mid_idx = (len(heads) + 1) // 2
    mid = heads[mid_idx]
    return lines[:mid], lines[mid:]


def split_at_heading(lines: list[str], prefix: str) -> tuple[list[str], list[str]]:
    """Split the stream at the first line starting with prefix (that line
    begins the second half)."""
    for i, l in enumerate(lines):
        if l.startswith(prefix):
            return lines[:i], lines[i:]
    return lines, []


def write_page(dst: Path, title: str, permalink: str, body_lines: list[str],
               drop_first_h1: bool = False) -> None:
    PALI.mkdir(parents=True, exist_ok=True)
    body = rebase_lists(body_lines)
    body = salvage_exercise_notes(body)
    body = declension_tables(body)
    if drop_first_h1:
        # the front-matter title already names the subject; drop a leading
        # duplicate '# ...' heading
        for k, l in enumerate(body):
            s = l.strip()
            if not s:
                continue
            if s.startswith("# ") and not s.startswith("## "):
                body = body[:k] + body[k + 1:]
            break
    body = capitalize_top_bullets(body)
    content = (FRONT.format(title=title, permalink=permalink) + "\n"
               + "\n".join(squeeze(body)) + "\n\n{% include toc.html %}\n")
    dst.write_text(content, encoding="utf-8", newline="\n")
    print(f"wrote {dst.relative_to(ROOT)} ({len(content.splitlines())} lines)")


def write_vocab_audit(audit_key: str, fname: str) -> None:
    d = AUDITED.get(audit_key, {})
    lines: list[str] = []
    for label, items in d.items():
        lines.append(f"## {label}")
        lines.extend("- " + it for it in items)
        lines.append("")
    (AUDIT / fname).write_text("\n".join(lines), encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- ch3 restructure

def write_ch3_reading_page(readings: list[dict]) -> None:
    """Dedicated page for the Chapter III reading (translation exercise)
    passages, with the lesson they came from and their vocabulary."""
    lines: list[str] = []
    for r in readings:
        lines.append(f"## {r['lesson']}")
        lines.append("")
        lines.extend(r["lines"])
        lines.append("")
    # drop the VOCAB extraction markers (site plumbing), keep the <details>
    # vocab boxes themselves so the vocabulary travels with its passage
    body = [l for l in lines if not VMARKER.match(l.strip())]
    write_page(PALI / "pps-ch3-reading.md",
               "Pāḷi Pāṭha Sikkhā — Chapter III, Readings & Translation",
               "pps-ch3-reading", body, drop_first_h1=True)


def fix_ch3_sannaa(lines: list[str]) -> list[str]:
    """The nine saññā definition bullets under 'saññā (f.) (grammar)' carry
    RemNote list numbers ('1.', '2.', ..., '9.') on an otherwise unnumbered
    list — strip them (user request). Sutta/vagga numbers elsewhere are kept."""
    out: list[str] = []
    inside = False
    for l in lines:
        if re.match(r"^\s*- saññā \(f\.\) \(grammar\)", l):
            inside = True
        elif inside and re.match(r"^\s*- 9 saññās under sandhi", l):
            inside = False
        if inside:
            l = re.sub(r"^(\s*- )\d{1,2}[.)]\s*", r"\1", l)
        out.append(l)
    return out


_SARA_TYPE_NUM = {
    "lopa": "1", "adesa": "2", "digha": "3", "agama": "4",
}


def fix_ch3_sara_sandhi(lines: list[str]) -> list[str]:
    """The 'Sara sandhi is further divided into following categories.'
    bullet (already promoted to a '###' heading by fix_ch3_topics, or still
    a raw bullet) becomes a plain '### Sara sandhi' section headed by a
    '4 types of sara sandhi' bullet, and its type bullets are renumbered
    1-4: the source listed 1) Lopa, 2) Ādesa, 4) Dīgha, 3) Āgama - a
    numbering slip with Dīgha and Āgama swapped; the lopa/ādesa/dīgha/āgama
    order follows the sandhi chart taught in semester 2. The examples under
    each type stay in place (ASCII-folded type names make the mapping
    diacritic-proof)."""
    out: list[str] = []
    inside = False
    for l in lines:
        head = re.match(r"^(?:###\s*|\s*- )Sara sandhi is further divided "
                        r"into following categories\.?\s*$", l, re.I)
        if head:
            out.append("### Sara sandhi")
            out.append("4 types of sara sandhi")
            inside = True
            continue
        if inside and l.startswith("#"):
            inside = False
        m = re.match(r"^(\s*- )(\d+)(\)?\.?\s*)(\S+)(.*)$", l) if inside else None
        if m:
            word = re.sub(r"[^\w\u00c0-\u024f]", "",
                          unicodedata.normalize("NFD", m.group(4))
                          .encode("ascii", "ignore").decode("ascii").lower())
            num = _SARA_TYPE_NUM.get(word)
            if num:
                l = m.group(1) + num + m.group(3) + m.group(4) + m.group(5).rstrip()
        out.append(l)
    return out


_GAṆA_NAMES = ("bhūvādigaṇa", "rudhādigaṇa", "divādigaṇa", "svādigaṇa",
              "kiyādigaṇa", "gahādigaṇa", "tanādigaṇa", "curādigaṇa")


def fix_ch3_dhatugana(lines: list[str]) -> list[str]:
    """Dhātugaṇa section (Chapter III, Lesson 3) clean-up, per user request:
    the 'Dhātugaṇa (root groups)' bullet sits one level too deep under a
    vocabulary tail ('Some masculine nouns of ratti-group ending in 'i'') -
    promote it to a '### Dhātugaṇa (root groups)' heading (only the first
    occurrence; the word is reused in Lesson 10); its children re-nest under
    the heading, with 'Curādi group' promoted to a '#### Curādi group'
    heading to give the group more weight. The hardcoded '1.'-'8.'
    list-number prefixes of the eight gaṇa bullets are dropped (RemNote list
    artifacts; the bullets render with their own numbering, as with the
    saññā definitions)."""
    gaṇa_num = re.compile(r"^(\s*- )\d{1,2}\. (?=(?:"
                          + "|".join(_GAṆA_NAMES) + r")\b)")
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if re.match(r"^\s*- Dhātugaṇa \(root groups\)\s*$", line):
            out.append("")
            out.append("### Dhātugaṇa (root groups)")
            i += 1
            # pull the block under the heading one level shallower; promote
            # the 'Curādi group' bullet; drop the gaṇa list numbers
            while i < n:
                b = BULLET_LINE.match(lines[i])
                if b and len(b.group(1)) > 2:
                    text = b.group(2)
                    if re.match(r"^Curādi\s+group\s*$", text, re.I):
                        out.append("")
                        out.append("#### Curādi group")
                    else:
                        text = gaṇa_num.sub(r"\1", "- " + text)
                        out.append(" " * (len(b.group(1)) - 2) + text)
                    i += 1
                    continue
                if not b and lines[i].strip() and not lines[i].lstrip().startswith(
                        ("|", "<!--", "!")):
                    break
                out.append(lines[i])
                i += 1
            continue
        out.append(line)
        i += 1
    return out


VOCAB_LABEL_BULLET = re.compile(
    r"^(?P<indent>\s*)- (?:vocab\b[^:]*|Vocabulary)\s*(?::|$)")


def fix_ch3_ratti_vocab(lines: list[str]) -> list[str]:
    """The two ratti-group word lists ('Some masculine nouns of ratti-group
    ending in 'i'' and 'Some more nouns ending in 'u' of the group ratti')
    are grammar content, not exercise vocabulary: they stay on the notes
    page, directly under their lead bullet (the page previously showed only
    the lead bullet - the list lived in an extracted vocab block). Their
    'vocab:' label child is dropped; the words keep their glosses.
    Word bullets are capitalized on output by capitalize_top_bullets."""
    out: list[str] = []
    inside = False
    moved = 0
    for l in lines:
        if re.match(r"^\s*- some masculine nouns of ratti-group ending", l, re.I):
            inside = True
        elif re.match(r"^\s*- some more nouns ending in ‘u’ of the group ratti\s*$", l, re.I):
            inside = True
        elif inside:
            s = l.strip()
            if not s:
                continue  # wrapper blanks
            if s == VOCAB_END:
                inside = False
                continue
            if s.startswith("<"):
                continue  # <details open>, <summary>, <!-- VOCAB: ... -->
            if s.startswith(("#", "|")):
                inside = False  # heading/table: end of the block, keep it
            elif not BULLET_LINE.match(l):
                inside = False  # plain text: end of the block, keep it
        if inside and VOCAB_LABEL_BULLET.match(l):
            continue  # drop the 'vocab:' label bullet
        if inside and l.strip():
            moved += 1
        out.append(l)
    if moved:
        print(f"fix_ch3_ratti_vocab: kept {moved} word bullets inline")
    return out


def fix_ch3_memaid_wraps(lines: list[str]) -> list[str]:
    """A 'mem aid:'/'memory aid:' bullet whose mnemonic sits on a single
    child bullet is rejoined ('mem aid: nom. bhikkhavo, voc. bhikkhave'):
    RemNote wrapped the mnemonic, but as a child bullet it used to be
    swallowed into the preceding declension table as a fake case row. Only
    single-child wraps are touched - genuine mnemonic lists ('mem aid:'
    followed by 2+ child bullets, e.g. daṇḍī) stay lists."""
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        m = re.match(r"^(?P<indent>\s*)- (?:mem|memory)\s+aid\s*:\s*$", lines[i])
        nxt = lines[i + 1] if i + 1 < n else ""
        cm = re.match(r"^(?P<i2>\s*)- (.+)$", nxt)
        after = lines[i + 2] if i + 2 < n else ""
        if (m and cm and len(cm.group("i2")) > len(m.group("indent"))
                and (not after.strip()
                     or len(after) - len(after.lstrip()) <= len(cm.group("i2")))):
            out.append(m.group("indent") + "- mem aid: " + cm.group(2).strip())
            i += 2
            continue
        out.append(lines[i])
        i += 1
    return out


def fix_ch3_sayambhu_heading(lines: list[str]) -> list[str]:
    """Standard for the notes pages: every declension table sits under a
    '### Declension of <word>' heading. The sayambhū table was still
    introduced by a plain text bullet - promote it to match bhikkhu,
    daṇḍī, aggi, ... Its children re-nest one level up."""
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        m = re.match(r"^(?P<indent>\s*)- Declension of sayambhū "
                     r"\(m\.\) \(rattādigaṇa\)\s*$", lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        indent = len(m.group("indent"))
        out.append("")
        out.append("### Declension of sayambhū (m.) (rattādigaṇa)")
        i += 1
        while i < n:
            b = BULLET_LINE.match(lines[i])
            if b and len(b.group(1)) > indent:
                out.append(" " * max(0, len(b.group(1)) - 2) + "- " + b.group(2))
                i += 1
                continue
            if (not lines[i].strip()
                    or lines[i].lstrip().startswith(("|", "<!--", "!"))):
                out.append(lines[i])
                i += 1
                continue
            break
    return out


def fix_ch3_kitaka(lines: list[str]) -> list[str]:
    """The word-formation definition bullet is two definitions smashed into
    one line and reads as plain body text: give it a '### Kitaka' heading
    (standard topic-heading style of these pages) and split the definitions
    into separate bullets."""
    out: list[str] = []
    for l in lines:
        m = re.match(r"^(?P<indent>\s*)- primary derivatives \(kitaka\) are "
                     r"the nouns formed by adding suffixes to roots/stems "
                     r"secondary derivatives \(taddhita\) are nouns formed by "
                     r"adding suffixes to nouns\s*$", l, re.I)
        if m:
            out.append("")
            out.append("### Kitaka")
            out.append("- Primary derivatives (kitaka) are the nouns formed "
                       "by adding suffixes to roots/stems")
            out.append("- Secondary derivatives (taddhita) are nouns formed "
                       "by adding suffixes to nouns")
            continue
        out.append(l)
    return out


def drop_heading_numbers(lines: list[str]) -> list[str]:
    """'## Lesson 7 - 3 grammatical persons...' -> '## Lesson 7 - Grammatical
    persons...' (RemNote numbered the sub-bullets; the heading is the only
    place the number is visible)."""
    out: list[str] = []
    for l in lines:
        m = re.match(r"^(## Lesson \d+ - )\d+\.\s+(.*)$", l)
        out.append(m.group(1) + m.group(2) if m else l)
    return out


def split_ch3_readings(lines: list[str]) -> tuple[list[str], list[dict]]:
    """Chapter III lessons pair a Pāḷi reading passage (translation exercise)
    with its grammar points. The readings move to a dedicated page; the
    grammar stays. A 'Grammar' bullet is promoted to a heading, and the first
    sub-bullet under it (e.g. 'declension of ta', 'sandhi') becomes a
    subtitle, per the user's example.

    Returns (remaining_lines, [{lesson, lines}]). The Reading bullet is
    replaced by a pointer to the reading page, so the source bullet stays
    represented in place (the verifier's sample check still matches)."""
    out: list[str] = []
    readings: list[dict] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        m = re.match(r"^(?P<indent>\s*)- (?P<num>\d+(?:\.\d+)?)\.? Reading\s*$",
                     line, re.I)
        if not m:
            out.append(line)
            i += 1
            continue
        indent = len(m.group("indent"))
        num = m.group("num").split(".")[0]
        # current lesson heading (search back for '## Lesson ...')
        lesson = ""
        for prev in reversed(out):
            hm = re.match(r"^## (Lesson \d+[^\n]*)$", prev)
            if hm:
                lesson = hm.group(1).strip()
                break
        j = i + 1
        body: list[str] = []
        while j < n:
            mm = re.match(r"^(?P<i2>\s*)- \d+(?:\.\d+)?\.? Grammar\s*$",
                          lines[j], re.I)
            if mm and len(mm.group("i2")) == indent:
                break
            if re.match(r"^## ", lines[j]):
                break
            body.append(lines[j])
            j += 1
        readings.append({"lesson": lesson, "num": num, "lines": body})
        out.append(f"{m.group('indent')}- {m.group('num')}. Reading: see the "
                   f"dedicated [reading & translation page](/summaries/pali/"
                   f"pps-ch3-reading).")
        i = j
    return out, readings


def promote_grammar_headings(lines: list[str]) -> list[str]:
    """'  - N.M Grammar' bullets become '### Grammar' headings so the main
    topics of each lesson (declension of 'ta', sandhi, ...) sit directly
    under a clear section. Sub-bullets of the old Grammar bullet are lifted
    one level up."""
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        m = re.match(r"^(?P<indent>\s*)- \d+(?:\.\d+)?\.? Grammar\s*$",
                     line, re.I)
        if not m:
            out.append(line)
            i += 1
            continue
        indent = len(m.group("indent"))
        out.append("")
        out.append("### Grammar")
        i += 1
        # lift the Grammar block's sub-bullets one level shallower, but only
        # while they are deeper than the Grammar bullet itself; table, image
        # and comment lines travel with their preceding bullet
        while i < n:
            b = BULLET_LINE.match(lines[i])
            if b and len(b.group(1)) > indent:
                out.append(" " * max(0, len(b.group(1)) - indent - 2)
                           + "- " + b.group(2))
                i += 1
                continue
            non_b = lines[i]
            if non_b.strip() and not non_b.lstrip().startswith(
                    ("|", "<!--", "!")):
                break
            out.append(non_b)
            i += 1
    return out


# ---------------------------------------------------------------- ch3 topics

_CH3_TOPIC_RES = [
    re.compile(r"^- Declension of \S", re.I),
    re.compile(r"^- Sandhi: euphonic combination$", re.I),
    re.compile(r"^- Saññā \(f\.\) \(grammar\)", re.I),
    re.compile(r"^- Sara sandhi is further divided", re.I),
    re.compile(r"^- Sarasandi$", re.I),
    re.compile(r"^- Manogaṇa$", re.I),
    re.compile(r"^- Niggahīta Sandhi$", re.I),
    re.compile(r"^- Dvebhāva sandhi$", re.I),
    re.compile(r"^- Cardinal numbers \(saṅkhyā nāma\)", re.I),
    re.compile(r"^- Causative actions and verbs", re.I),
    re.compile(r"^- Present tense conjugation of the root", re.I),
]


def fix_ch3_topics(lines: list[str]) -> list[str]:
    """Promote the main topics of each Chapter III lesson (declension of
    'ta', sandhi, saññā, ...) to '###' subtitles so they are clearly visible
    sections under the lesson heading. The promoted bullet is kept verbatim
    as the heading text (nothing is lost); its children re-nest under the
    heading. 'pumādigaṇa' sits misfiled one level deep under the mano-group
    list and is lifted out."""
    out: list[str] = []
    for l in lines:
        if re.match(r"^- Sandhi: euphonic combination$", l, re.I):
            # the label itself becomes the subtitle; the gloss stays as content
            out.append("")
            out.append("### Sandhi")
            out.append("- Euphonic combination")
            continue
        hit = next((rx for rx in _CH3_TOPIC_RES if rx.match(l)), None)
        if hit:
            text = re.sub(r"^-\s*", "", l)
            text = text[0].upper() + text[1:]
            out.append("")
            out.append("### " + text)
            continue
        if re.match(r"^\s*- pumādigaṇa$", l, re.I):
            out.append("")
            out.append("### Pumādigaṇa")
            continue
        out.append(l)
    # a bare '### Grammar' heading immediately followed by a topic subtitle
    # is redundant (the subtitle carries the structure)
    out2: list[str] = []
    for k, l in enumerate(out):
        if l.strip() == "### Grammar":
            nxt = next((x for x in out[k + 1:] if x.strip()), "")
            if nxt.startswith("###"):
                continue
        out2.append(l)
    return out2


# ---------------------------------------------------------------- source drivers

def pps() -> None:
    CUR_SOURCE[0] = "pali-patha-sikkha-ch1-3.html"
    LAST_HEADING[0] = ""
    ANCESTORS[:] = [""] * 12
    md = close_vocab_blocks(convert_source("pali-patha-sikkha-ch1-3.html").split("\n"))
    write_audits("pali-patha-sikkha-ch1-3.html", md)
    # one page per chapter, one page per part within a chapter:
    # part 1 = first half of the lessons, part 2 = the rest
    chapters: dict[str, list[str]] = {}
    key: str | None = None
    pre: list[str] = []
    for line in md.split("\n"):
        m = re.match(r"^# (Chapter \d+)\b", line)
        if m:
            key = m.group(1).lower().replace(" ", "-")
            chapters[key] = []
        elif key is None:
            pre.append(line)
        else:
            chapters[key].append(line)
    for key, ch_lines in chapters.items():
        n = key.split("-")[1]
        if n == "1":
            ch_lines = fix_ch1_lesson1(ch_lines)
            ch_lines = fix_ch1_lesson7(ch_lines)
            ch_lines = fix_ch1_lesson8(ch_lines)
            ch_lines = fix_ch1_indeclinables(ch_lines)
        ch_lines = salvage_exercise_notes(ch_lines)
        readings: list[dict] = []
        if n == "3":
            ch_lines = fix_ch3_sannaa(ch_lines)
            ch_lines, readings = split_ch3_readings(ch_lines)
            ch_lines = drop_heading_numbers(ch_lines)
            ch_lines = promote_grammar_headings(ch_lines)
            ch_lines = fix_ch3_topics(ch_lines)
            ch_lines = fix_ch3_dhatugana(ch_lines)
            ch_lines = fix_ch3_sara_sandhi(ch_lines)
            ch_lines = fix_ch3_ratti_vocab(ch_lines)
            ch_lines = fix_ch3_memaid_wraps(ch_lines)
            ch_lines = fix_ch3_sayambhu_heading(ch_lines)
            ch_lines = fix_ch3_kitaka(ch_lines)
        part1, part2 = split_at_lessons(ch_lines)
        for part, lines in ((1, part1), (2, part2)):
            if not lines:
                continue
            slug = f"pps-ch{n}-part{part}"
            title = f"Pāḷi Pāṭha Sikkhā — Chapter {n}, Part {part}"
            lines = process_vocab(lines, "s1", title,
                                  f"/summaries/pali/{slug}", "pps")
            write_page(PALI / f"{slug}.md", title, slug,
                       strip_anchors(lines))
        if readings:
            write_ch3_reading_page(readings)
    write_vocab_audit("pps", "vocab-moved-pps.txt")
    for old_name in ("pali-patha-sikkha-ch1-3-notes.md", "pps-ch1.md",
                     "pps-ch2.md", "pps-ch3.md"):
        old = PALI / old_name
        if old.exists():
            old.unlink()
            print(f"removed {old_name} (superseded by per-part chapter pages)")


def semester2() -> None:
    CUR_SOURCE[0] = "pali-semester-2.html"
    LAST_HEADING[0] = ""
    ANCESTORS[:] = [""] * 12
    md = close_vocab_blocks(convert_source("pali-semester-2.html").split("\n"))
    write_audits("pali-semester-2.html", md)
    lines = process_vocab(md.split("\n"), "s2",
                          "Pāḷi Pāṭha Sikkhā — Semester II",
                          "/summaries/pali/semester-2", "s2")
    write_vocab_audit("s2", "vocab-moved-s2.txt")
    parts = split_anchored("\n".join(lines))
    main = parts.get(None, [])
    ch3, ch4 = split_at_heading(main, "# Chapter IV")
    c3a, c3b = split_at_heading(ch3, "## Lesson 18")
    c4a, c4b = split_at_heading(ch4, "## Lesson 11 - taddhitanāma")
    write_page(PALI / "pps-ch3-part3.md",
               "Pāḷi Pāṭha Sikkhā — Chapter 3, Part 3",
               "pps-ch3-part3", strip_anchors(c3a), drop_first_h1=True)
    write_page(PALI / "pps-ch3-part4.md",
               "Pāḷi Pāṭha Sikkhā — Chapter 3, Part 4",
               "pps-ch3-part4", strip_anchors(c3b), drop_first_h1=True)
    write_page(PALI / "pps-ch4-part1.md",
               "Pāḷi Pāṭha Sikkhā — Chapter 4, Part 1",
               "pps-ch4-part1", strip_anchors(c4a), drop_first_h1=True)
    write_page(PALI / "pps-ch4-part2.md",
               "Pāḷi Pāṭha Sikkhā — Chapter 4, Part 2",
               "pps-ch4-part2", strip_anchors(c4b), drop_first_h1=True)
    # final-exam page retired: its unique practice sets were merged into
    # pps-ch3-part4 (Lesson 23) and pps-ch4-part2 (Lessons 15 & 17)
    for old_name in ("semester-2.md", "semester-2-part1.md",
                     "semester-2-part2.md", "pps-final-exam-1st-year.md"):
        old = PALI / old_name
        if old.exists():
            old.unlink()
            print(f"removed {old_name} (superseded by pps-ch3/ch4 part pages)")


def semester3() -> None:
    CUR_SOURCE[0] = "pali-semester-3.html"
    LAST_HEADING[0] = ""
    ANCESTORS[:] = [""] * 12
    md = close_vocab_blocks(convert_source("pali-semester-3.html").split("\n"))
    write_audits("pali-semester-3.html", md)
    lines = process_vocab(md.split("\n"), "s3",
                          "Pāḷi — Semester III",
                          "/summaries/pali/niruttidipani-part-1", "s3",
                          anchor_links={
                              "dhp-1": "/summaries/pali/dhammapada-atthakatha-1",
                              "iti-1": "/summaries/pali/itivuttaka-1",
                              "an-1": "/summaries/pali/anguttara-1",
                              "declensions": "/summaries/pali/nominal-declensions",
                              "misc-3": "/summaries/pali/semester-3-notes",
                          })
    write_vocab_audit("s3", "vocab-moved-s3.txt")
    parts = split_anchored("\n".join(lines))
    write_page(PALI / "niruttidipani-part-1.md",
               "Niruttidīpaṇī — Part I (saññārāsi, saṅketarāsi, sandhividhāna)",
               "niruttidipani-part-1", strip_anchors(parts.get("nirutti-1", [])),
               drop_first_h1=True)
    write_page(PALI / "dhammapada-atthakatha-1.md",
               "Dhammapadaṭṭhakathā — Part I (Cakkhupālattheravatthu)",
               "dhammapada-atthakatha-1", strip_anchors(parts.get("dhp-1", [])),
               drop_first_h1=True)
    write_page(PALI / "itivuttaka-1.md",
               "Itivuttaka — Part I (Ekakanipāta)",
               "itivuttaka-1", strip_anchors(parts.get("iti-1", [])),
               drop_first_h1=True)
    write_page(PALI / "anguttara-1.md",
               "Aṅguttara Nikāya — Part I",
               "anguttara-1", strip_anchors(parts.get("an-1", [])),
               drop_first_h1=True)
    write_page(PALI / "nominal-declensions.md",
               "Nominal Declensions — Charts & Words",
               "nominal-declensions", strip_anchors(parts.get("declensions", [])),
               drop_first_h1=True)
    write_page(PALI / "semester-3-notes.md",
               "Semester III — Class Notes & Exam Info",
               "semester-3-notes", strip_anchors(parts.get("misc-3", [])))


def semester4() -> None:
    CUR_SOURCE[0] = "pali-semester-4.html"
    LAST_HEADING[0] = ""
    ANCESTORS[:] = [""] * 12
    md = close_vocab_blocks(convert_source("pali-semester-4.html").split("\n"))
    write_audits("pali-semester-4.html", md)
    lines = process_vocab(md.split("\n"), "s3",
                          "Pāḷi — Semester IV",
                          "/summaries/pali/niruttidipani-part-2", "s4",
                          anchor_links={
                              "dhp-2": "/summaries/pali/dhammapada-atthakatha-2",
                          })
    write_vocab_audit("s4", "vocab-moved-s4.txt")
    parts = split_anchored("\n".join(lines))
    write_page(PALI / "niruttidipani-part-2.md",
               "Niruttidīpaṇī — Part II (Sandhi by type)",
               "niruttidipani-part-2", strip_anchors(parts.get("nirutti-2", [])),
               drop_first_h1=True)
    write_page(PALI / "dhammapada-atthakatha-2.md",
               "Dhammapadaṭṭhakathā — Part II (Cakkhupālattheravatthu, continued)",
               "dhammapada-atthakatha-2", strip_anchors(parts.get("dhp-2", [])),
               drop_first_h1=True)


def semester5() -> None:
    CUR_SOURCE[0] = "pali-semester-5.html"
    LAST_HEADING[0] = ""
    ANCESTORS[:] = [""] * 12
    md = close_vocab_blocks(convert_source("pali-semester-5.html").split("\n"))
    write_audits("pali-semester-5.html", md)
    lines = process_vocab(md.split("\n"), "s3",
                          "Pāḷi — Semester V",
                          "/summaries/pali/niruttidipani-namakanda-notes", "s5",
                          anchor_links={
                              "reading-1": "/summaries/pali/dhammapada-reading-1",
                              "translation-notes": "/summaries/pali/translation-notes",
                          })
    write_vocab_audit("s5", "vocab-moved-s5.txt")
    parts = split_anchored("\n".join(lines))
    write_page(PALI / "niruttidipani-namakanda-notes.md",
               "Niruttidīpaṇī — Nāmakaṇḍa (class notes)",
               "niruttidipani-namakanda-notes", strip_anchors(parts.get(None, [])),
               drop_first_h1=True)
    write_page(PALI / "dhammapada-reading-1.md",
               "Reading & Translation — Dhammapada Aṭṭhakathā (Cittavagga)",
               "dhammapada-reading-1", strip_anchors(parts.get("reading-1", [])),
               drop_first_h1=True)
    write_page(PALI / "translation-notes.md",
               "Notes on Translation Approach (bhante Vijitānanda)",
               "translation-notes", strip_anchors(parts.get("translation-notes", [])),
               drop_first_h1=True)


def semester6() -> None:
    CUR_SOURCE[0] = "pali-semester-6.html"
    LAST_HEADING[0] = ""
    ANCESTORS[:] = [""] * 12
    md = convert_source("pali-semester-6.html")
    write_audits("pali-semester-6.html", md)
    parts = split_anchored(md)
    write_page(PALI / "semester-6-grammar.md",
               "Nāmagaṇa — Gacchantādi, Satthādi, Rattādi (Semester VI)",
               "semester-6-grammar", strip_anchors(parts.get(None, [])))
    write_page(PALI / "semester-6-reading.md",
               "Reading & Translation — Cittavagga (Parts III–IV)",
               "semester-6-reading", strip_anchors(parts.get("s6-reading", [])),
               drop_first_h1=True)


def roots() -> None:
    CUR_SOURCE[0] = "common-roots-in-pali.html"
    LAST_HEADING[0] = ""
    ANCESTORS[:] = [""] * 12
    md = convert_source("common-roots-in-pali.html")
    write_audits("common-roots-in-pali.html", md)
    write_page(PALI / "common-roots.md",
               "Common Roots in Pāḷi",
               "common-roots", strip_anchors(md.split("\n")))


# ---------------------------------------------------------------- vocabulary page

VOCAB_GROUPS = {
    "s1": "Pāḷi Pāṭha Sikkhā — Semester I (Chapters 1–3)",
    "s2": "Pāḷi Pāṭha Sikkhā — Semester II (Chapters III–IV)",
    "s3": "Semesters III–V",
}


def build_vocab_page() -> None:
    if not VOCAB_BLOCKS:
        print("no vocab blocks recorded — run the source conversions first")
        return
    lines: list[str] = [
        "Vocabulary lists collected from the Pāḷi notes, grouped by semester.",
        "In the notes pages, the */*-prefixed bullets mark the vocabulary needed",
        "for each exercise; those stay next to the exercises.",
        "",
    ]
    for vk in ("s2", "s3"):
        blocks = [b for b in VOCAB_BLOCKS if b["vkey"] == vk]
        if not blocks:
            continue
        lines.append(f"## {VOCAB_GROUPS[vk]}")
        lines.append("")
        for b in blocks:
            label = esc(b["label"]).replace('"', "&quot;")
            lines.append("<details>")
            lines.append(f"<summary>{label} — <a href=\"{b['source_link']}\">↩ source</a></summary>")
            lines.append("")
            lines.extend(b["lines"])
            lines.append("")
            lines.append("</details>")
            lines.append("")
    write_page(VOCAB_MD, "Pāḷi Vocabulary", "vocabulary", lines)
    # Semester I (PPS) vocab is not shown on the vocabulary page, but keep it
    # on an unlinked archive page so no content is lost.
    s1 = [b for b in VOCAB_BLOCKS if b["vkey"] == "s1"]
    if s1:
        arch: list[str] = ["Vocabulary groups extracted from the Semester I "
                           "(Chapters 1–3) notes; kept for reference only.", ""]
        for b in s1:
            label = esc(b["label"]).replace('"', "&quot;")
            arch.append("<details>")
            arch.append(f"<summary>{label}</summary>")
            arch.append("")
            arch.extend(b["lines"])
            arch.append("")
            arch.append("</details>")
            arch.append("")
        write_page(PALI / "pps-vocab-archive.md",
                   "Pāḷi Pāṭha Sikkhā (Semester I) — Vocabulary Archive",
                   "pps-vocab-archive", arch)


# ---------------------------------------------------------------- summaries.md

NEW_SUMMARIES_BLOCK = """#### Notes on "Pāḷi Pāṭha Sikkhā" by Ven. Vijitānanda
- [Chapter III — readings & translation](/summaries/pali/pps-ch3-reading)

#### Niruttidīpaṇī — class notes
- [Part I: saññārāsi, saṅketarāsi, sandhividhāna (Semester III)](/summaries/pali/niruttidipani-part-1)
- [Part II: sandhi by type (Semester IV)](/summaries/pali/niruttidipani-part-2)
- [Nāmakaṇḍa (Semester V notes)](/summaries/pali/niruttidipani-namakanda-notes)

#### Reading & translation
- [Dhammapadaṭṭhakathā I — Cakkhupālattheravatthu (Semester III)](/summaries/pali/dhammapada-atthakatha-1)
- [Dhammapadaṭṭhakathā II — Cakkhupālattheravatthu continued (Semester IV)](/summaries/pali/dhammapada-atthakatha-2)
- [Cittavagga — Meghiya & related stories (Semester V)](/summaries/pali/dhammapada-reading-1)
- [Cittavagga, parts III–IV (Semester VI)](/summaries/pali/semester-6-reading)
- [Itivuttaka I (Semester III)](/summaries/pali/itivuttaka-1)
- [Aṅguttara Nikāya I (Semester III)](/summaries/pali/anguttara-1)
- [Notes on translation approach](/summaries/pali/translation-notes)
- [Semester III — class notes & exam info](/summaries/pali/semester-3-notes)

#### Reference
- [Nominal declensions — charts & words](/summaries/pali/nominal-declensions)
- [Nāmagaṇa: gacchantādi, satthādi, rattādi (Semester VI)](/summaries/pali/semester-6-grammar)
- [Common Roots in Pāḷi](/summaries/pali/common-roots)

#### Vocabulary
- [Pāḷi Vocabulary — all semesters, grouped](/summaries/pali/vocabulary)

#### Elaborated study pages (from the notes above)
- [Saññarāsi](/summaries/pali/niruttidipani-sannarasi)
- [Saṅketarāsi](/summaries/pali/niruttidipani-sanketarasi)
- [Sandhividhāna](/summaries/pali/niruttidipani-sandhividhana)
- [Nāmakaṇḍa](/summaries/pali/namakanda)
- Kārakakaṇḍa
  - [Introduction](/summaries/pali/karakakanda-intro)
  - [Meanings of Paṭhamāvibhatti](/summaries/pali/karakakanda-pathama)
  - [Meanings of Dutiyāvibhatti](/summaries/pali/karakakanda-dutiya)
  - [Meanings of Tatiyāvibhatti](/summaries/pali/karakakanda-tatiya)
  - [Meanings of Catutthīvibhatti](/summaries/pali/karakakanda-catutthi)
  - [Meanings of Pañcamīvibhatti](/summaries/pali/karakakanda-pancami)
  - [Meanings of Chaṭṭhīvibhatti](/summaries/pali/karakakanda-chatthi)
  - [Meanings of Sattamīvibhatti](/summaries/pali/karakakanda-sattami)
  - [Appendix](/summaries/pali/karakakanda-appendix)
- Samāsakaṇḍa
  - [Introduction](/summaries/pali/samasakanda-intro)
  - [Abyayībhāvasamāsa](/summaries/pali/samasakanda-abyayibhava)
"""


def pps_summary_lines() -> str:
    """One collapsible block per part: the link is the <summary>, the lesson
    topics collapse beneath it (details/summary, closed on load)."""
    out: list[str] = []
    for n in (1, 2, 3, 4):
        for part in (1, 2, 3, 4):
            fp = PALI / f"pps-ch{n}-part{part}.md"
            if not fp.exists():
                continue
            text = fp.read_text(encoding="utf-8").splitlines()
            lessons = [re.match(r"^## (Lesson .*)$", l).group(1).strip()
                       for l in text if re.match(r"^## Lesson ", l)]
            lo = re.search(r"Lesson (\d+)", lessons[0]).group(1) if lessons else "?"
            hi = re.search(r"Lesson (\d+)", lessons[-1]).group(1) if lessons else "?"
            rng = f" (Lessons {lo}–{hi})" if lessons else ""
            out.append('<details markdown="1">')
            out.append(f'<summary><a href="/summaries/pali/pps-ch{n}-part{part}">'
                       f"Chapter {n}, Part {part}{rng}</a></summary>")
            out.append("")
            out.extend(f"- {l}" for l in lessons)
            out.append("</details>")
            out.append("")
    return "\n".join(out)


def update_summaries() -> None:
    text = SUMMARIES_MD.read_text(encoding="utf-8")
    m = re.search(r"^#### .*(Vijitānanda|Pāḷi Pāṭha Sikkhā).*$", text, re.M)
    assert m, "PPS block header not found in summaries.md"
    start = m.start()
    end = text.index("<hr style=")
    old_block = text[start:end]
    assert "Kārakakaṇḍa" in old_block and "Samāsakaṇḍa" in old_block
    block = NEW_SUMMARIES_BLOCK.format(pps_links=pps_summary_lines())
    text = text[:start] + block + "\n" + text[end:]
    SUMMARIES_MD.write_text(text, encoding="utf-8", newline="\n")
    print(f"updated {SUMMARIES_MD.relative_to(ROOT)}")


# ---------------------------------------------------------------- driver

def run_curated(path: str) -> None:
    """Apply the byte-safe transform pass (arrows, exercise salvage, declension
    tables) to a hand-curated page, preserving its line endings."""
    p = (ROOT / path).resolve()
    raw = p.read_bytes().decode("utf-8")
    crlf = "\r\n" in raw
    lines = raw.split("\r\n" if crlf else "\n")
    lines = _curated_tables(lines)
    lines = salvage_exercise_notes(lines)
    lines = [arrows_to_colon(l) for l in lines]
    out = ("\r\n" if crlf else "\n").join(lines)
    p.write_bytes(out.encode("utf-8"))
    print(f"curated pass: {p.name} ({'CRLF' if crlf else 'LF'}, "
          f"{sum(1 for l in lines if l.lstrip().startswith('| '))} table lines)")


def main() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) >= 3 and sys.argv[1] == "--curated":
        for path in sys.argv[2:]:
            run_curated(path)
        return
    only = set(sys.argv[1:])
    do_all = not only
    if do_all or "pps" in only:
        pps()
    if do_all or "s2" in only:
        semester2()
    if do_all or "s3" in only:
        semester3()
    if do_all or "s4" in only:
        semester4()
    if do_all or "s5" in only:
        semester5()
    if do_all or "s6" in only:
        semester6()
    if do_all or "roots" in only:
        roots()
    if do_all or "vocab" in only:
        build_vocab_page()
    if do_all or "summaries" in only:
        update_summaries()


if __name__ == "__main__":
    main()
