#!/usr/bin/env python3
"""
convert_semester2.py — bring the semester II RemNote exports into the site.

Plan (mirrors what was done for semester I):
  1. The 6 subject files inside pages/semester II .../ are converted:
     - RemNote cloze spans {{id::text}} -> <mark class="cloze">text</mark>
       (nested clozes handled by repeated passes; text preserved exactly)
     - Jekyll front matter (layout: page, title, permalink) prepended
     - .Portal / mark.cloze styles kept so portal boxes look right
  2. The Vinaya subject file is split by its top-level sections:
       entrance to khandhaka vinaya (part II)          -> pages/kha/
       entrance to vibhanga vinaya (part I - cont.)    -> pages/v/vibhanga/
       entrance to vibhanga vinaya (part II) - NP      -> pages/v/vibhanga/
       trailing "notes:" (final exam, khandhaka content) -> appended to khandhaka page
  3. Everything is verified: the flattened (tags stripped, clozes unwrapped)
     text of every source must appear, unchanged, in the outputs. Additionally
     every one of the 46 subfiles must be contained in its subject file, and
     every subject file must be contained in the whole-semester file.
  4. Only after ALL checks pass, the originals are moved to
     assets/semester II (05_06_2023 - 31_10_2023)/  (move, not delete).
"""
import os
import re
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "pages/semester II (05_06_2023 - 31_10_2023)"
ASSETS = "assets/semester II (05_06_2023 - 31_10_2023)"
TOP_FILE = "pages/semester II (05_06_2023 - 31_10_2023).html"

PORTAL_STYLE = (
    "<style>\n"
    ".Portal { border-color: lightblue; border-style: solid; }\n"
    'mark.cloze { background-color: rgba(255, 235, 59, 0.45); color: inherit; '
    "padding: 0 1px; border-radius: 2px; }\n"
    "</style>"
)

CLOZE = re.compile(r"\{\{[^{}]*?::(.*?)\}\}", re.S)


def fix_clozes(text):
    """Convert cloze spans to <mark class="cloze">, innermost first (handles nesting)."""
    prev = None
    while prev != text:
        prev = text
        text = CLOZE.sub(lambda m: '<mark class="cloze">%s</mark>' % m.group(1), text)
    return text


def body_of(text):
    m = re.search(r"<body[^>]*>(.*)</body>", text, re.S)
    return m.group(1).strip("\r\n") if m else text


def flatten(text):
    """Tags stripped + clozes unwrapped -> plain text (for content-equality checks)."""
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


def top_level_items(body):
    """Offsets + flattened text of the top-level <li> items of a RemNote export body."""
    lines = body.split("\n")
    items, off = [], 0
    for ln in lines:
        s = ln.strip()
        if s.startswith("<li>") and (len(ln) - len(ln.lstrip())) <= 10:
            items.append((off, " ".join(re.sub(r"<[^>]+>", "", s).split())[:120]))
        off += len(ln) + 1
    return items


def balance_report(slice_text):
    li_o = len(re.findall(r"<li[ >]", slice_text))
    li_c = slice_text.count("</li>")
    ul_o = len(re.findall(r"<ul[ >]", slice_text))
    ul_c = slice_text.count("</ul>")
    return li_o, li_c, ul_o, ul_c


# ---------------------------------------------------------------- load sources
def load(rel):
    with open(os.path.join(BASE, rel), encoding="utf-8") as f:
        return f.read()


src_fund = load("Fundamentals of Theravāda - Bhante Maggavihāri.html")
src_su = load("Dhammānuloma - Bhante Devānanda.html")
src_khu = load("Khuddaka Nikāya - Āvuso (Laos) Sumana.html")
src_p = load("Pāḷi - Bhante Vijitānanda.html")
src_kha = load("Vinaya – Bhante Maggavihāri/entrance to khandhaka vinaya (part II).html")
src_vin = load("Vinaya – Bhante Maggavihāri.html")
src_top = open(TOP_FILE, encoding="utf-8").read()

# ------------------------------------------------------- split the vinaya file
vin_body = body_of(src_vin)
items = top_level_items(vin_body)
print("Vinaya top-level items:")
for off, txt in items:
    print(f"  @{off}: {txt[:80]}")


def find_item(prefix):
    for off, txt in items:
        if txt.lower().startswith(prefix):
            return off
    raise SystemExit(f"!! could not find top-level item starting with: {prefix}")


m_h1 = re.search(r"<h1[^>]*>(.*?)</h1>", vin_body, re.S)
vin_h1 = m_h1.group(0) if m_h1 else ""
vin_h1_flat = " ".join(re.sub(r"<[^>]+>", " ", vin_h1 or "").split())
off_k = find_item("entrance to khandhaka vinaya (part ii)")
off_v1 = find_item("entrance to vibhaṅga vinaya (part i")
off_v2 = find_item("entrance to vibhaṅga vinaya (part ii")
off_notes = find_item("notes:")

# slice ranges: item k -> item v1, v1 -> v2, v2 -> notes, notes -> last </ul>
last_ul = vin_body.rfind("</ul>", off_notes)
assert last_ul != -1, "closing </ul> after notes item not found"
slice_kha = vin_body[off_k:off_v1].strip("\r\n")
slice_v1 = vin_body[off_v1:off_v2].strip("\r\n")
slice_v2 = vin_body[off_v2:off_notes].strip("\r\n")
slice_notes = vin_body[off_notes:last_ul].strip("\r\n")

for name, sl in [("khandhaka", slice_kha), ("vib-part1cont", slice_v1),
                 ("vib-part2np", slice_v2), ("notes", slice_notes)]:
    lo, lc, uo, uc = balance_report(sl)
    flag = "" if (lo == lc and uo == uc) else "   <-- UNBALANCED"
    print(f"  slice {name:14} li {lo}/{lc}  ul {uo}/{uc}  ({len(sl)} bytes){flag}")

# --------------------------------------------------------------- build outputs
OUT = []

OUT.append(("pages/a/fundamentals-of-theravada-2.html",
            "Fundamentals of Theravāda (Semester II) – bhante Maggavihāri",
            "/summaries/abhidhamma/fundamentals-2",
            body_of(src_fund), flatten(body_of(src_fund)), [src_fund]))

OUT.append(("pages/su/dhammanuloma-2.html",
            "Dhammānuloma (Semester II) – bhante Devānanda",
            "/summaries/suttanta/dhammanuloma-2",
            body_of(src_su), flatten(body_of(src_su)), [src_su]))

OUT.append(("pages/khu/khuddaka-nikaya-2.html",
            "Khuddaka Nikāya (Semester II) – āvuso Sumana",
            "/summaries/khuddaka/semester-2",
            body_of(src_khu), flatten(body_of(src_khu)), [src_khu]))

OUT.append(("pages/p/pali-semester-2.html",
            "Pāḷi (Semester II) – bhante Vijitānanda",
            "/summaries/pali/semester-2",
            body_of(src_p), flatten(body_of(src_p)), [src_p]))

# khandhaka page = part II body + the final-exam notes section appended
kha_body = body_of(src_kha)
notes_html = (
    '<hr/>\r\n<h2>Notes (final exam – khandhaka vinaya)</h2>\r\n\r\n<ul>\r\n'
    + slice_notes + "\r\n</ul>"
)
OUT.append(("pages/kha/entrance-to-khandhaka-vinaya-part-ii.html",
            "Entrance to Khandhaka Vinaya (Part II) – bhante Maggavihāri",
            "/summaries/vinaya/khandhaka/entrance-notes-2",
            kha_body + "\r\n\r\n" + notes_html,
            flatten(kha_body) + " " + flatten("<ul>" + slice_notes + "</ul>"),
            [src_kha]))

OUT.append(("pages/v/vibhanga/entrance-to-vibhanga-vinaya-part-1-cont.html",
            "Entrance to Vibhaṅga Vinaya (Part I, continued) – bhante Maggavihāri",
            "/summaries/vinaya/vibhanga/entrance-notes-1-cont",
            vin_h1 + "\r\n<br/>\r\n<ul>\r\n" + slice_v1 + "\r\n</ul>",
            vin_h1_flat + " " + flatten("<ul>" + slice_v1 + "</ul>"), [src_vin]))

OUT.append(("pages/v/vibhanga/entrance-to-vibhanga-vinaya-part-2-np.html",
            "Entrance to Vibhaṅga Vinaya (Part II) – Nissaggiya Pācittiya – bhante Maggavihāri",
            "/summaries/vinaya/vibhanga/entrance-notes-2",
            "<ul>\r\n" + slice_v2 + "\r\n</ul>",
            flatten("<ul>" + slice_v2 + "</ul>"), [src_vin]))

# --------------------------------------------------- containment sanity checks
print("\n--- containment checks ---")


def flat_of(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return flatten(body_of(f.read()))


subfiles = []
for root, _dirs, files in os.walk(BASE):
    for fn in files:
        if fn.endswith(".html"):
            subfiles.append(os.path.join(root, fn))
print(f"subfiles found: {len(subfiles)}")

subjects = {
    "Fundamentals of Theravāda - Bhante Maggavihāri.html": src_fund,
    "Dhammānuloma - Bhante Devānanda.html": src_su,
    "Khuddaka Nikāya - Āvuso (Laos) Sumana.html": src_khu,
    "Pāḷi - Bhante Vijitānanda.html": src_p,
    os.path.join("Vinaya – Bhante Maggavihāri", "entrance to khandhaka vinaya (part II).html"): src_kha,
    "Vinaya – Bhante Maggavihāri.html": src_vin,
}
subj_flats = {k: flatten(body_of(v)) for k, v in subjects.items()}
subj_keys = list(subj_flats)

uncovered = []
for sf in subfiles:
    rel = os.path.relpath(sf, BASE)
    flat = flat_of(sf)
    if not flat:
        continue
    if not any(flat in subj_flats[k] for k in subj_keys):
        uncovered.append(rel)
if uncovered:
    print("!! subfiles NOT contained in any subject file:")
    for u in uncovered:
        print("   ", u)
else:
    print("OK: every subfile's content is contained in a subject file")

top_flat = flatten(body_of(src_top))
missing_in_top = [k for k in subj_keys if subj_flats[k] not in top_flat]
if missing_in_top:
    print("!! subject files NOT fully contained in the whole-semester file:")
    for m in missing_in_top:
        print("   ", m)
else:
    print("OK: every subject file is fully contained in the whole-semester file")

# ------------------------------------------------- content-equality of outputs
print("\n--- output content equality (source -> page) ---")
ok = True
for path, _title, _plink, body, out_flat, _srcs in OUT:
    src_flat = None
    if path.endswith("entrance-to-khandhaka-vinaya-part-ii.html"):
        src_flat = flatten(kha_body) + " " + flatten(slice_notes)
    elif path.endswith("entrance-to-vibhanga-vinaya-part-1-cont.html"):
        src_flat = vin_h1_flat + " " + flatten(slice_v1)
    elif path.endswith("entrance-to-vibhanga-vinaya-part-2-np.html"):
        src_flat = flatten(slice_v2)
    if src_flat is None:
        continue
    same = src_flat == out_flat
    ok &= same
    print(f"  {'PASS' if same else 'FAIL'} {path}")
# vinaya parent == sum of the three slices
vin_flat = flatten(vin_body)
recombined = " ".join([vin_h1_flat, flatten(slice_kha), flatten(slice_v1),
                       flatten(slice_v2), flatten(slice_notes)])
same = recombined == vin_flat
ok &= same
print(f"  {'PASS' if same else 'FAIL'} vinaya parent == khandhaka + vib1cont + vib2np + notes")
if not same:
    # show where they diverge
    for i, (a, b) in enumerate(zip(recombined, vin_flat)):
        if a != b:
            print(f"    diverge at {i}: ...{recombined[max(0,i-60):i+60]!r} VS ...{vin_flat[max(0,i-60):i+60]!r}")
            break
    print(f"    lens: recom={len(recombined)} orig={len(vin_flat)}")

if not (ok and not uncovered and not missing_in_top):
    print("\n!! VERIFICATION FAILED — nothing written, originals not moved.")
    sys.exit(1)

# ------------------------------------------------------------------ write pages
print("\n--- writing pages ---")
for path, title, plink, body, _flat, _srcs in OUT:
    fixed = fix_clozes(body)
    page = make_page(title, plink, fixed)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(page)
    n_cloze = len(re.findall(r'<mark class="cloze">', fixed))
    n_portal = len(re.findall(r'class="Portal"', fixed))
    print(f"  wrote {path}  ({len(page)} bytes, {n_cloze} clozes, {n_portal} portals)")

# ------------------------------------------------- move originals into assets
print("\n--- moving originals to assets ---")
os.makedirs(ASSETS, exist_ok=True)
shutil.move(BASE, os.path.join(ASSETS, os.path.basename(BASE)))
shutil.move(TOP_FILE, os.path.join(ASSETS, os.path.basename(TOP_FILE)))
print(f"  moved folder -> {ASSETS}/{os.path.basename(BASE)}")
print(f"  moved file   -> {ASSETS}/{os.path.basename(TOP_FILE)}")

print("\nDone. All checks passed.")
