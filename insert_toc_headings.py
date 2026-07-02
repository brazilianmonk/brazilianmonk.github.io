#!/usr/bin/env python3
"""
insert_toc_headings.py

Adds real <h2>/<h3> tags into RemNote-style exported .md files (Jekyll posts
that embed raw <html><body>...</body></html>) so that the toc.html include
(which scans for h2/h3) can build a table of contents.

How it decides what's a heading:
  - The file has ONE top-level <ul> right after the <h1>.
  - Each *direct* <li> child of that top-level <ul> becomes an <h2> section.
  - Each *direct* <li> child of THAT li's nested <ul> becomes an <h3> subsection.
  - Deeper nesting is left untouched (still normal bullet content).

How it avoids changing the page's look:
  - It doesn't add new visible text. It wraps the existing leading content
    of the <li> (everything before its first nested <ul>/<ol>) in an
    <h2>/<h3> tag with inline CSS that resets all heading styling
    (display:inline, inherited font-size/weight/margin/etc).
  - toc.html only reads heading.textContent and heading.id, so the wrapper
    is invisible on the page but fully discoverable by the TOC script.

Usage:
    python3 insert_toc_headings.py path/to/file.md
    # writes path/to/file.md in place, and backs up the original to
    # path/to/file.md.bak

    python3 insert_toc_headings.py path/to/file.md -o path/to/out.md
    # writes to a different file instead of overwriting

    python3 insert_toc_headings.py
    # no path given: pops up a file picker so you can choose one or more
    # .md files (falls back to a numbered console list if a GUI isn't
    # available). Each selected file is processed and overwritten in
    # place, with a .bak backup.

Run it once per file. It refuses to run twice on an already-processed file
(detects existing injected h2/h3 tags) unless --force is passed.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup, NavigableString

RESET_STYLE = (
    "display:inline; font-size:inherit; font-weight:inherit; "
    "font-style:inherit; font-family:inherit; color:inherit; "
    "margin:0; padding:0; line-height:inherit;"
)
MARKER_ATTR = "data-toc-injected"

FRONTMATTER_RE = re.compile(r"\A(---\s*\n.*?\n---\s*\n)", re.DOTALL)


def split_frontmatter(text: str):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def wrap_leading_content(soup: BeautifulSoup, li, level: int):
    """Wrap the content of `li` that precedes its first nested <ul>/<ol>
    inside a new h2/h3 tag (in place)."""
    # Find the first nested list, if any; only its preceding siblings
    # (within this li) get wrapped.
    boundary = None
    for child in li.contents:
        if getattr(child, "name", None) in ("ul", "ol"):
            boundary = child
            break

    heading = soup.new_tag(f"h{level}", style=RESET_STYLE)
    heading[MARKER_ATTR] = "true"

    # Move everything before the boundary into the heading tag.
    to_move = []
    for child in li.contents:
        if child is boundary:
            break
        to_move.append(child)

    if not to_move:
        return  # nothing to wrap (shouldn't normally happen)

    # Strip pure-whitespace-only trailing/leading text nodes so the heading
    # doesn't pick up stray newlines/indentation from the source markup.
    while to_move and isinstance(to_move[0], NavigableString) and not to_move[0].strip():
        to_move.pop(0)
    while to_move and isinstance(to_move[-1], NavigableString) and not to_move[-1].strip():
        to_move.pop()

    if not to_move:
        return

    # Insert heading right before the first item we're about to move,
    # then move each item into it, in order.
    to_move[0].insert_before(heading)
    for node in to_move:
        heading.append(node.extract())


def process(html_fragment: str, force: bool) -> str:
    soup = BeautifulSoup(html_fragment, "html.parser")
    body = soup.find("body") or soup

    if not force and soup.find(attrs={MARKER_ATTR: "true"}):
        raise SystemExit(
            "This file already has injected TOC headings "
            f"(found an element with {MARKER_ATTR}). "
            "Pass --force to redo it anyway."
        )

    top_ul = body.find("ul")
    if top_ul is None:
        raise SystemExit("Could not find a top-level <ul> in <body>. Nothing to do.")

    top_lis = top_ul.find_all("li", recursive=False)
    if not top_lis:
        raise SystemExit("Top-level <ul> has no direct <li> children. Nothing to do.")

    h2_count = 0
    h3_count = 0
    for li in top_lis:
        wrap_leading_content(soup, li, level=2)
        h2_count += 1
        nested_ul = li.find("ul", recursive=False)
        if nested_ul:
            for sub_li in nested_ul.find_all("li", recursive=False):
                wrap_leading_content(soup, sub_li, level=3)
                h3_count += 1

    print(f"Injected {h2_count} <h2> and {h3_count} <h3> headings.", file=sys.stderr)
    return str(soup)


def pick_files_gui():
    """Try to show a native file-picker dialog. Returns a list of Path
    objects, or None if a GUI isn't available (e.g. no display, no tkinter)."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return None

    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        paths = filedialog.askopenfilenames(
            title="Choose .md file(s) to add a TOC to",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
        )
        root.destroy()
    except tk.TclError:
        # No display available (e.g. headless/SSH session)
        return None

    if not paths:
        return []  # user cancelled the dialog
    return [Path(p) for p in paths]


def pick_files_console():
    """Fallback: ask the user to type a path, or list .md files in the
    current directory (recursively) and let them pick by number."""
    typed = input(
        "Enter the path to a .md file (or press Enter to browse the "
        "current folder): "
    ).strip().strip('"')
    if typed:
        return [Path(typed)]

    candidates = sorted(Path(".").rglob("*.md"))
    if not candidates:
        print("No .md files found under the current directory.", file=sys.stderr)
        return []

    print("\nFound these .md files:")
    for i, c in enumerate(candidates, 1):
        print(f"  {i}. {c}")
    choice = input(
        "\nEnter the number of the file to process "
        "(or comma-separated numbers for several): "
    ).strip()
    if not choice:
        return []
    indices = [int(x.strip()) for x in choice.split(",") if x.strip().isdigit()]
    return [candidates[i - 1] for i in indices if 1 <= i <= len(candidates)]


def process_one_file(input_path: Path, output_path: Optional[Path], force: bool):
    text = input_path.read_text(encoding="utf-8")
    frontmatter, body_html = split_frontmatter(text)
    new_body_html = process(body_html, force=force)
    new_text = frontmatter + new_body_html

    out_path = output_path or input_path
    if out_path == input_path:
        backup = input_path.with_suffix(input_path.suffix + ".bak")
        backup.write_text(text, encoding="utf-8")
        print(f"Backed up original to {backup}", file=sys.stderr)

    out_path.write_text(new_text, encoding="utf-8")
    print(f"Wrote {out_path}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path, nargs="?", default=None,
                     help="Path to the .md file to process. Omit this to pick file(s) interactively.")
    ap.add_argument("-o", "--output", type=Path, default=None,
                     help="Output path (default: overwrite input, with a .bak backup). "
                          "Only valid when a single input path is given on the command line.")
    ap.add_argument("--force", action="store_true",
                     help="Re-process a file even if it looks already-processed")
    args = ap.parse_args()

    if args.input is not None:
        targets = [args.input]
    else:
        targets = pick_files_gui()
        if targets is None:
            targets = pick_files_console()
        if not targets:
            print("No file selected. Nothing to do.", file=sys.stderr)
            return

    for path in targets:
        if not path.exists():
            print(f"Skipping {path}: file not found.", file=sys.stderr)
            continue
        print(f"\nProcessing {path} ...", file=sys.stderr)
        try:
            process_one_file(path, args.output if len(targets) == 1 else None, args.force)
        except SystemExit as e:
            print(f"Skipped {path}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
