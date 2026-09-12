---
name: semester-notes-import
description: >
  Import new Dhamma study notes (RemNote HTML exports, semester folders, or
  loose files) into the brazilianmonk Jekyll site: convert them to site pages,
  fix RemNote cloze syntax, verify nothing is lost, move originals to assets/,
  and add links to pages/summaries.md. Use whenever the user says a new
  semester folder or note file appeared in pages/ and should be added to the
  Dhamma summaries.
metadata:
  category: content-pipeline
---

# Semester Notes Import (RemNote → Jekyll)

Imports Dhamma study notes into the site without losing content. Three tools
already exist at the repo root:

| Script | Purpose |
|---|---|
| `convert_semester.py` | Whole-semester folder → site pages (config-driven) |
| `scan_remnote.py` | Find RemNote artifacts (clozes, portals, tags, Liquid breakers) |
| `convert_loose_notes.py` | One-off template for loose single files |

## Knowledge

### Destination map (never change this structure)

| Subject in the note | Page folder | Permalink prefix |
|---|---|---|
| Abhidhamma / Fundamentals of Theravāda | `pages/a/` | `/summaries/abhidhamma/` |
| Vibhaṅga Vinaya | `pages/v/vibhanga/` | `/summaries/vinaya/vibhanga/` |
| Khandhaka Vinaya | `pages/kha/` | `/summaries/vinaya/khandhaka/` |
| Khuddaka Nikāya | `pages/khu/` | `/summaries/khuddaka/` |
| Pāḷi | `pages/p/` | `/summaries/pali/` |
| Suttanta / Dhammānuloma (always call it "Suttanta") | `pages/su/` | `/summaries/suttanta/` |
| Samatha | `pages/sa/` | `/summaries/samatha/` |

Naming: `fundamentals-of-theravada-N.html`, `<subject>-semester-N.html`,
`khuddaka-nikaya-N.html`. N = semester number.

### What conversion does (and must only do)

1. Strip the `<html>/<head>/<style>/<body>` wrapper.
2. Convert RemNote clozes `{{id::text}}` → `<mark class="cloze">text</mark>`
   (text preserved exactly; only the internal RemNote id is dropped).
3. Prepend Jekyll front matter (`layout: page`, `title`, `permalink`) plus the
   `.Portal` / `mark.cloze` style block.
4. Nothing else. Portals stay (cosmetic), tags stay, org anchors in `.md`
   files stay. NEVER rewrite, summarize, or reorder note content.

Markdown files (org-mode exports): prepend front matter only; leave every byte
of content untouched (verify with a prefix check, not equality).

## Instructions

### Adding a new semester (typical case)

1. **Probe first.** List the folder (`ls pages/semester*`), then check each
   file: which subjects it holds, whether the Vinaya file needs splitting into
   vibhaṅga + khandhaka sections, whether subfiles are contained in parent
   files (use a containment probe before deciding what to convert), and cloze
   counts (`python scan_remnote.py pages/<semester folder>`).
2. **Add a config block** to `SEASONS` at the bottom of `convert_semester.py`
   (copy the `semester6` block; it's the leanest example). Each entry:
   - `pages`: one source file → one site page (`dest`, `title`, `permalink`).
   - `splits`: one source file → several pages, cut at top-level `<li>` items
     whose flattened text starts with `match` (case-insensitive). The first
     part keeps the file's `<h1>`; the last slice auto-trims the file's closing
     parent `</ul>`.
   - Titles follow the existing pattern, e.g.
     `Suttanta (Semester VII) – Bhante Devānanda`. Only include a teacher name
     if one actually appears in the file.
3. **Run it:** `python convert_semester.py <season-key>`. The script refuses to
   write anything unless ALL gates pass: subfile containment, split slices
   tag-balanced, slices recombine exactly to the source, zero residual
   `{{`/`{%` in outputs. If a gate fails, fix the config — never disable a
   check.
4. **Scan the outputs:** `python scan_remnote.py --all pages/a/<new> ...`
   Expect 0 clozes and 0 liquid issues; portals and `#[[...]]` tags are
   cosmetic and stay. If clozes remain, the converter missed them — fix and
   re-run.
5. **Link them in `pages/summaries.md`.** Add each link under its section:
   `## Pāḷi Language`, `## Abhidhamma` (### Abhidhamma Notes),
   `## Vinaya` (#### Vibhaṅga Vinaya / #### Khandhaka Vinaya), `## Suttanta`,
   `## Khuddaka Nikāya`, `## Samatha`. Keep each section's list in semester
   order (I, II, III, …). Format: `- [Title – Teacher](/permalink)`.
6. **Build & verify:** `bundle exec jekyll build -d _site_check`, confirm every
   new page renders under its permalink and the search index picked it up
   (`_site_check/search.json` entry count grows). Then
   `rm -rf _site_check` (retry patiently — a file-sync process sometimes holds
   it on Windows).
7. **Originals** are moved to `assets/<semester folder name>/` by the script.
   Confirm the folder is gone from `pages/` and present under `assets/`.

### Loose files (not a semester folder)

For one or two files outside a semester folder, adapt `convert_loose_notes.py`
(its `JOBS` list: source, dest, title, permalink, kind `html`|`md`) instead of
adding a season. Same verification discipline: equality for HTML, prefix check
for markdown.

### Troubleshooting

- Windows console Unicode errors printing Pāḷi diacritics → scripts already
  reconfigure stdout to UTF-8 with errors="replace"; keep that line when
  writing new scripts.
- `scan_remnote.py` skips files that already have front matter; pass `--all`
  to scan processed pages too.
- If a semester folder has subfiles (handouts) whose content is NOT contained
  in a parent file, they are real separate notes: convert them individually
  rather than relying on containment.
- The `_site_check` cleanup can fail because an external sync process holds
  files (e.g. Terabox); wait and retry, it always clears.

## Verify

After any import: build passes, every new permalink serves the page with the
site layout, `summaries.md` shows the links in the right sections and order,
`scan_remnote.py` reports 0 clozes/liquid on the new pages, and originals
exist under `assets/`.
