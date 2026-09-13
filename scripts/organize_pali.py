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
    return t.replace("\u00a0", " ").replace("<", "&lt;")


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
    return arrows_to_colon(t).strip()


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
        return [f"![image](https://remnote-user-data.s3.amazonaws.com/{src})"] if src else []
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
            txt = " ".join("".join(parts).split()).replace("|", "\\|")
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


def arrows_to_colon(t: str) -> str:
    return ARROW_RE.sub(": ", t)
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
                    link = f"{source_link}-{PART_TAG[0]}"
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
    true nesting intact."""
    out: list[str] = []
    stack: list[int] = []  # columns of currently open list levels
    for line in lines:
        m = BULLET_LINE.match(line)
        if m:
            c = len(m.group(1))
            while stack and c <= stack[-1]:
                stack.pop()
            if not stack:
                c = 0
                stack.append(0)
            elif c == stack[-1] + 2:
                stack.append(c)
            else:
                c = stack[-1] + 2
                stack.append(c)
            out.append(" " * c + "- " + m.group(2))
            continue
        stripped = line.strip()
        if not stripped:
            out.append(line)  # blank lines don't close a list
            continue
        if line.startswith(("#", "<", "<!", "|", "    ")):
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
VERB_CELL_BAD = re.compile(r"[.\-:|]| - |–|—")
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
    singular/plural bullet runs (gunavantu, yagu, taruni, ...) and verbal
    conjugation runs (ajjatani/bhavissanti/sattami ...) into tables."""
    return _case_tables(_verb_tables(_noun_tables(lines)))


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
    return True


def _noun_tables(lines: list[str]) -> list[str]:
    """Unlabeled singular/plural bullet runs become tables (quote cells
    normalized)."""
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        m = re.match(r"^(?P<indent>\s*)- (?P<rest>.+)$", lines[i])
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
    else:
        t = text.rstrip(",").strip()
        if "," not in t:
            return None
        a, b = t.split(",", 1)
        cells = [a.strip(), b.strip().rstrip(",").strip()]
    return [re.sub(r"\s+([,;])", r"\1", c) for c in cells] if cells else None


def _verb_cells_per_row(cells: list[str]) -> int | None:
    """3 cells = 3 smashed person-pairs per line; 2 cells = 2 explicit pairs;
    1 cell = a single explicit pair; anything else is not part of a run."""
    if len(cells) == 3 and all("/" in c for c in cells):
        return 3
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
        tbl = _verb_table(rows) if len(rows) >= 2 else None
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
    per_row: list[list[tuple[str, str]]] = []
    for r in rows:
        if r and all("/" in c for c in r):
            pr = []
            for c in r:
                a, b = c.split("/", 1)
                pr.append((a.strip(), b.strip()))
            per_row.append(pr)
        elif len(r) == 2:
            per_row.append([(r[0], r[1])])
        elif len(r) == 1:
            per_row.append([(r[0], "")])
        else:
            return None
    if not per_row:
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


def split_sem2(lines: list[str]) -> tuple[list[str], list[str]]:
    """Split the semester-2 stream at the '# Chapter IV' heading."""
    for i, l in enumerate(lines):
        if l.startswith("# Chapter IV"):
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
        ch_lines = salvage_exercise_notes(ch_lines)
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
    part1, part2 = split_sem2(main)
    write_page(PALI / "semester-2-part1.md",
               "Pāḷi Pāṭha Sikkhā — Semester II, Part 1 (Chapter III, Lessons 11–17)",
               "semester-2-part1", strip_anchors(part1), drop_first_h1=True)
    write_page(PALI / "semester-2-part2.md",
               "Pāḷi Pāṭha Sikkhā — Semester II, Part 2 (Lessons 18–25, Chapter IV)",
               "semester-2-part2", strip_anchors(part2), drop_first_h1=True)
    if "final" in parts:
        write_page(PALI / "pps-final-exam-1st-year.md",
                   "Pāḷi Pāṭha Sikkhā — Final Exam (1st Year)",
                   "pps-final-exam-1st-year", strip_anchors(parts["final"]),
                   drop_first_h1=True)
    for old_name in ("semester-2.md",):
        old = PALI / old_name
        if old.exists():
            old.unlink()
            print(f"removed {old_name} (superseded by semester-2-part1/2)")


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
{pps_links}- [Semester II, Part 1 — Chapter III (Lessons 11–17)](/summaries/pali/semester-2-part1)
- [Semester II, Part 2 — Chapters III & IV (Lessons 18–25, IV 1–19)](/summaries/pali/semester-2-part2)
- [Final exam, 1st year](/summaries/pali/pps-final-exam-1st-year)

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
    """One link per part, with the lesson topics of that part beneath."""
    out: list[str] = []
    for n in (1, 2, 3):
        for part in (1, 2):
            fp = PALI / f"pps-ch{n}-part{part}.md"
            if not fp.exists():
                continue
            text = fp.read_text(encoding="utf-8").splitlines()
            lessons = [re.match(r"^## (Lesson .*)$", l).group(1).strip()
                       for l in text if re.match(r"^## Lesson ", l)]
            lo = re.search(r"Lesson (\d+)", lessons[0]).group(1) if lessons else "?"
            hi = re.search(r"Lesson (\d+)", lessons[-1]).group(1) if lessons else "?"
            rng = f" (Lessons {lo}–{hi})" if lessons else ""
            out.append(f"- [Chapter {n}, Part {part}{rng}](/summaries/pali/pps-ch{n}-part{part})")
            out.extend(f"  - {l}" for l in lessons)
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

def main() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
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
