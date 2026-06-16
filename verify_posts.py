#!/usr/bin/env python3
"""
verify_posts.py -- Format checker for brazilianmonk.github.io Jekyll posts.

Checks performed:
  1.  File naming: must match YYYY-MM-DD-slug.md (no backup/temp files)
  2.  Front matter: must open and close with ---
  3.  Required fields: layout, title, author, categories, tags, image
  4.  layout value: must be "post"
  5.  Title safety: if title contains ": " it must be quoted (to avoid YAML parse failure)
  6.  Image field: must not be empty
  7.  Image file: referenced image must exist in assets/img/
  8.  TOC include: post must contain {% include toc.html %}
  9.  Backup/temp files: warn about .md~ and similar files in _posts/
  10. Language sections: should contain all three flag headings (🇬🇧 🇪🇸 🇧🇷)
  11. No old inline TOC script: warn if <script> block with "table-of-contents" found

Run from the repo root:
  python verify_posts.py
"""

import io
import os
import re
import sys

# Force UTF-8 output so emoji print correctly on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# -- Configuration -------------------------------------------------------------

REPO_ROOT  = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR  = os.path.join(REPO_ROOT, "_posts")
ASSETS_IMG = os.path.join(REPO_ROOT, "assets", "img")

REQUIRED_FIELDS = ["layout", "title", "author", "categories", "tags", "image"]
LANGUAGE_FLAGS  = ["\U0001f1ec\U0001f1e7", "\U0001f1ea\U0001f1f8", "\U0001f1e7\U0001f1f7"]  # 🇬🇧 🇪🇸 🇧🇷

# -- Helpers -------------------------------------------------------------------

class Checker:
    def __init__(self):
        self.errors   = []
        self.warnings = []

    def error(self, msg): self.errors.append(msg)
    def warn(self,  msg): self.warnings.append(msg)


def extract_front_matter(text):
    """Return (fm_block_str, body) or (None, text) if no valid front matter."""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    fm_block = text[3:end].strip()
    body = text[end + 4:].strip()
    return fm_block, body


def parse_fm_fields(fm_block):
    """Lightweight field parser -- returns {key: raw_value_string}."""
    fields = {}
    for line in fm_block.splitlines():
        m = re.match(r'^(\w+)\s*:\s*(.*)', line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields


def title_needs_quoting(raw_title):
    """
    True when title contains ': ' but is NOT wrapped in quotes.
    An unquoted colon-space sequence breaks YAML front matter parsing.
    """
    if not raw_title:
        return False
    quoted = (
        (raw_title.startswith('"') and raw_title.endswith('"')) or
        (raw_title.startswith("'") and raw_title.endswith("'"))
    )
    inner = raw_title.strip('"\'')
    return (": " in inner) and not quoted


# -- Per-file checks -----------------------------------------------------------

def check_file(filepath, checker):
    filename = os.path.basename(filepath)

    # 1. Backup / temp files ---------------------------------------------------
    is_backup = (
        filename.endswith(".md~") or
        filename.startswith(".#") or
        filename.startswith("YYYY-MM-DD")
    )
    if is_backup:
        checker.warn(f"Temp/backup file in _posts/ -- consider removing: {filename}")
        return  # no further analysis

    # 2. Naming convention -----------------------------------------------------
    name_ok = re.match(r'^\d{4}-\d{2}-\d{2}-.+\.md$', filename)
    if not name_ok:
        checker.error(f"Filename does not match YYYY-MM-DD-slug.md pattern.")

    # Read file ----------------------------------------------------------------
    try:
        with open(filepath, encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        checker.error("Could not read file as UTF-8. Check encoding.")
        return

    # 3. Front matter delimiters -----------------------------------------------
    fm_block, body = extract_front_matter(text)
    if fm_block is None:
        checker.error("Missing or malformed front matter (must start and end with ---).")
        return

    # 4. Required fields -------------------------------------------------------
    fields = parse_fm_fields(fm_block)
    for field in REQUIRED_FIELDS:
        if field not in fields:
            checker.error(f"Missing required field: '{field}'.")
        elif not fields[field]:
            checker.error(f"Field '{field}' is empty.")

    # 5. layout value ----------------------------------------------------------
    layout_val = fields.get("layout", "")
    if layout_val and layout_val != "post":
        checker.warn(f"'layout' is '{layout_val}' (expected 'post').")

    # 6. Title quoting ---------------------------------------------------------
    raw_title = fields.get("title", "")
    if title_needs_quoting(raw_title):
        checker.error(
            f"Title contains ': ' but is not quoted -- this breaks YAML parsing.\n"
            f"         Fix: title: \"{raw_title.strip()}\""
        )

    # 7. Image file exists -----------------------------------------------------
    img_value = fields.get("image", "").strip("'\"")
    if img_value:
        img_path = os.path.join(ASSETS_IMG, img_value)
        if not os.path.isfile(img_path):
            checker.error(f"Image not found: assets/img/{img_value}")
    
    # 8. TOC include -----------------------------------------------------------
    if "{% include toc.html %}" not in text:
        checker.warn("Missing {%% include toc.html %%} -- TOC will not be generated.")

    # 9. Old inline TOC script -------------------------------------------------
    if "table-of-contents" in text and "<script>" in text:
        checker.error(
            "Old inline TOC <script> block still present. "
            "Replace it with {%% include toc.html %%}."
        )

    # 10. Language sections ----------------------------------------------------
    for flag in LANGUAGE_FLAGS:
        if flag not in text:
            checker.warn(f"Missing language section for {flag}.")


# -- Main ----------------------------------------------------------------------

def main():
    if not os.path.isdir(POSTS_DIR):
        print(f"ERROR: _posts/ directory not found at: {POSTS_DIR}")
        sys.exit(1)

    all_entries = sorted(os.listdir(POSTS_DIR))
    # Include md, md~, temp/backup files
    candidates = [
        f for f in all_entries
        if f.endswith(".md") or f.endswith(".md~")
        or f.startswith(".#") or f.startswith("YYYY-MM-DD")
    ]

    print("=" * 64)
    print("  Brazilian Monk -- Post Format Verifier")
    print("=" * 64)

    if not candidates:
        print("  No markdown files found in _posts/.")
        sys.exit(0)

    print(f"  Scanning {len(candidates)} file(s) in _posts/\n")

    results = {}
    for filename in candidates:
        c = Checker()
        check_file(os.path.join(POSTS_DIR, filename), c)
        results[filename] = c

    total_errors   = 0
    total_warnings = 0

    for filename, c in results.items():
        if not c.errors and not c.warnings:
            continue
        print(f"\U0001f4c4  {filename}")
        for e in c.errors:
            print(f"   \u274c  ERROR:   {e}")
            total_errors += 1
        for w in c.warnings:
            print(f"   \u26a0\ufe0f  WARN:    {w}")
            total_warnings += 1
        print()

    clean = [f for f, c in results.items() if not c.errors and not c.warnings]
    if clean:
        print("\u2705  Clean (no issues):")
        for f in clean:
            print(f"     {f}")
        print()

    print("=" * 64)
    print(f"  Result: {total_errors} error(s), {total_warnings} warning(s)")
    print("=" * 64)

    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
