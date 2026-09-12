#!/usr/bin/env python3
"""
convert_semester.py — bring a semester's RemNote exports into the site.

Usage:
    python convert_semester.py <season-key>     e.g. python convert_semester.py semester5
    python convert_semester.py --list           show configured seasons

Pipeline (same as semesters II/III/IV, now reusable):
  1. Convert each subject file: RemNote cloze spans {{id::text}} ->
     <mark class="cloze">text</mark> (nested handled; text preserved exactly),
     prepend Jekyll front matter, keep .Portal / mark.cloze styles.
  2. Files that hold several site pages (e.g. Vinaya = vibhanga + khandhaka)
     are split at their top-level <li> items; the file's <h1> is kept at the
     head of the first part; the last part is trimmed of the file's closing
     parent </ul>.
  3. Verify BEFORE writing anything:
       - every subfile in the semester folder must be contained in one of the
         converted sources (catches handouts / subfile trees like semester II)
       - split slices must be tag-balanced and recombine to exactly the source
       - pairwise containment probe across sources (info: duplicate content)
       - written pages must contain no residual cloze/liquid syntax
  4. Only after ALL checks pass, move originals to assets/<semester>/.
"""
import importlib
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


def top_level_items(body):
    lines = body.split("\n")
    items, off = [], 0
    for ln in lines:
        s = ln.strip()
        if s.startswith("<li>") and (len(ln) - len(ln.lstrip())) <= 10:
            items.append((off, " ".join(re.sub(r"<[^>]+>", "", s).split()).lower()))
        off += len(ln) + 1
    return items


def balance(sl):
    return (len(re.findall(r"<li[ >]", sl)), sl.count("</li>"),
            len(re.findall(r"<ul[ >]", sl)), sl.count("</ul>"))


def load(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def convert_season(cfg):
    src_dir, assets_dir = cfg["src"], cfg["assets"]
    print(f"=== converting {src_dir} -> pages, originals -> {assets_dir} ===")

    # ---------------- gather sources (whole files + split files + split parts)
    sources = {}   # relpath -> raw text
    for rel in cfg.get("pages", []):
        sources[rel] = load(os.path.join(src_dir, rel))
    for split in cfg.get("splits", []):
        rel = split["source"]
        if rel not in sources:
            sources[rel] = load(os.path.join(src_dir, rel))

    # ------------------------------------------------------------ plan splits
    plans = []  # dicts: source, h1, slices, parts
    for split in cfg.get("splits", []):
        rel = split["source"]
        body = body_of(sources[rel])
        items = top_level_items(body)
        print(f"\nsplit {rel} — top-level items:")
        for off, txt in items:
            print(f"  @{off}: {txt[:80]}")

        m_h1 = re.search(r"<h1[^>]*>.*?</h1>", body, re.S)
        h1 = m_h1.group(0) if m_h1 else ""
        h1_flat = " ".join(re.sub(r"<[^>]+>", " ", h1 or "").split())

        # locate part boundaries by prefix; parts may pull from other sources
        offsets = []
        for part in split["parts"]:
            pref = part["match"].lower()
            hit = next((off for off, txt in items
                        if txt.startswith(pref) and off not in offsets), None)
            if hit is None:
                raise SystemExit(f"!! {rel}: no top-level item starts with {pref!r}")
            offsets.append(hit)

        # each slice runs from its offset to the next PART offset within the
        # same source (or EOF for the last slice of this source)
        same_src = [(o, p) for o, p in zip(offsets, split["parts"])
                    if p.get("source", rel) == rel]
        slices = []
        for i, (off, part) in enumerate(same_src):
            nxt = same_src[i + 1][0] if i + 1 < len(same_src) else len(body)
            slices.append((off, nxt, part))

        processed = []
        for i, (a, b, part) in enumerate(slices):
            sl = body[a:b].strip("\r\n")
            last = i == len(slices) - 1
            lo, lc, uo, uc = balance(sl)
            if last and uc > uo:
                idx = sl.rfind("</ul>")
                sl = sl[:idx] + sl[idx + 5:]
                lo, lc, uo, uc = balance(sl)
            flag = "" if (lo == lc and uo == uc) else "   <-- UNBALANCED"
            print(f"  slice {part['match'][:24]:24} li {lo}/{lc}  ul {uo}/{uc}  "
                  f"({len(sl)} bytes){flag}")
            processed.append((sl, part))

        plans.append(dict(source=rel, body=body, h1=h1, h1_flat=h1_flat,
                          parts=processed, srcs_one=bool(
                              all(p.get("source", rel) == rel
                                  for _sl, p in processed))))

    # ------------------------------------------------------------ plan pages
    OUT = []  # (dest, title, permalink, body_html, src_flat)
    for rel in cfg.get("pages", []):
        body = body_of(sources[rel])
        OUT.append((None, None, None, body, flatten(body)))  # filled below

    for i, rel in enumerate(cfg.get("pages", [])):
        p = cfg["pages"][rel]
        _d, _t, _pl, body, flat = OUT[i]
        OUT[i] = (p["dest"], p["title"], p["permalink"], body, flat)

    for plan in plans:
        for j, (sl, part) in enumerate(plan["parts"]):
            if j == 0 and plan["h1"]:
                body_html = (plan["h1"] + "\r\n<br/>\r\n<ul>\r\n" + sl + "\r\n</ul>")
                src_flat = plan["h1_flat"] + " " + flatten(sl)
            else:
                body_html = "<ul>\r\n" + sl + "\r\n</ul>"
                src_flat = flatten(sl)
            OUT.append((part["dest"], part["title"], part["permalink"],
                        body_html, src_flat))

    # ----------------------------------------------------- verification gates
    print("\n--- verification ---")
    ok = True

    # 1. every subfile in the semester folder is contained in a converted source
    src_flats = {rel: flatten(body_of(t)) for rel, t in sources.items()}
    uncovered = []
    for root, _d, fns in os.walk(src_dir):
        for fn in fns:
            if not fn.endswith(".html"):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, src_dir)
            f = flatten(body_of(load(p)))
            if f and not any(f in sf for sf in src_flats.values()):
                uncovered.append(rel)
    if uncovered:
        ok = False
        print("!! FAIL subfiles NOT contained in any converted source:")
        for u in uncovered:
            print("   ", u)
    else:
        print("OK  every subfile is contained in a converted source")

    # 2. split recombination: h1 + slices == source (single-source splits only)
    for plan in plans:
        if not plan["srcs_one"]:
            continue
        recom = " ".join([plan["h1_flat"]] +
                         [flatten(sl) for sl, _p in plan["parts"]])
        same = recom == flatten(plan["body"])
        ok &= same
        print(f"{'OK ' if same else '!! FAIL'} recombination of {plan['source']}")
        if not same:
            for i, (a, b) in enumerate(zip(recom, flatten(plan["body"]))):
                if a != b:
                    print(f"   diverge at {i}: ...{recom[max(0, i-60):i+60]!r} "
                          f"VS ...{flatten(plan['body'])[max(0, i-60):i+60]!r}")
                    break

    # 3. pairwise containment probe across sources (info only)
    print("info: pairwise containment across sources:")
    found = False
    for a in src_flats:
        for b in src_flats:
            if a != b and src_flats[a] and src_flats[a] in src_flats[b]:
                print(f"   NOTE: {a} is fully contained in {b}")
                found = True
    if not found:
        print("   none")

    if not ok:
        print("\n!! VERIFICATION FAILED — nothing written, originals not moved.")
        sys.exit(1)

    # ---------------------------------------------------------- write pages
    print("\n--- writing pages ---")
    for dest, title, plink, body, _flat in OUT:
        fixed = fix_clozes(body)
        page = make_page(title, plink, fixed)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="") as f:
            f.write(page)
        n_cloze = len(re.findall(r'<mark class="cloze">', fixed))
        n_portal = len(re.findall(r'class="Portal"', fixed))
        residual = len(re.findall(r"\{\{", fixed)) + len(re.findall(r"\{%", fixed))
        status = "OK " if residual == 0 else "!! RESIDUAL LIQUID"
        print(f"  {status} wrote {dest}  ({len(page)} bytes, {n_cloze} clozes, "
              f"{n_portal} portals)")
        if residual:
            sys.exit(1)

    # ------------------------------------------------- move originals to assets
    os.makedirs(assets_dir, exist_ok=True)
    for fn in os.listdir(src_dir):
        s = os.path.join(src_dir, fn)
        d = os.path.join(assets_dir, fn)
        if os.path.isdir(s):
            shutil.move(s, d)
        else:
            shutil.move(s, d)
    os.rmdir(src_dir)
    print(f"\nmoved originals -> {assets_dir}/")
    print("Done. All checks passed.")


def main():
    from convert_semester import SEASONS  # config lives at the bottom

    if "--list" in sys.argv:
        for k in SEASONS:
            print(k, "->", SEASONS[k]["src"])
        return
    key = next((a for a in sys.argv[1:] if not a.startswith("-")), None)
    if key not in SEASONS:
        raise SystemExit(f"unknown season {key!r}; use one of: {', '.join(SEASONS)}")
    convert_season(SEASONS[key])


# ------------------------------------------------------------------ season map
# To add a future semester: copy a block, adjust src/assets, file names, titles,
# permalinks. "pages" = one source file -> one site page. "splits" = one source
# file -> several site pages, cut at top-level <li> items whose flattened text
# starts with part["match"] (case-insensitive); part["source"] may override the
# file a part is cut from. The first part of a single-source split keeps the
# file's <h1>.
SEASONS = {
    "semester6": {
        "src": "pages/semester VI (09_06_2025 ‒ 31_10_2025)",
        "assets": "assets/semester VI (09_06_2025 ‒ 31_10_2025)",
        "pages": {
            "Khuddaka Nikāya - Āvuso Sumana.html": dict(
                dest="pages/khu/khuddaka-nikaya-6.html",
                title="Khuddaka Nikāya (Semester VI) – Āvuso Sumana",
                permalink="/summaries/khuddaka/semester-6",
            ),
            "Pāḷi - Bhante Vijitānanda.html": dict(
                dest="pages/p/pali-semester-6.html",
                title="Pāḷi (Semester VI) – Bhante Vijitānanda",
                permalink="/summaries/pali/semester-6",
            ),
            "Suttanta - Bhante Devānanda.html": dict(
                dest="pages/su/suttanta-semester-6.html",
                title="Suttanta (Semester VI) – Bhante Devānanda",
                permalink="/summaries/suttanta/semester-6",
            ),
        },
        "splits": [
            dict(
                source="Vinaya.html",
                parts=[
                    dict(match="vibhaṅga",
                         dest="pages/v/vibhanga/vibhanga-semester-6.html",
                         title="Vibhaṅga Vinaya (Semester VI)",
                         permalink="/summaries/vinaya/vibhanga/semester-6"),
                    dict(match="khandhaka",
                         dest="pages/kha/khandhaka-semester-6.html",
                         title="Khandhaka Vinaya (Semester VI)",
                         permalink="/summaries/vinaya/khandhaka/semester-6"),
                ],
            ),
        ],
    },
    "semester5": {
        "src": "pages/semester V (04_12_2024 ‒ 27_05_2025)",
        "assets": "assets/semester V (04_12_2024 ‒ 27_05_2025)",
        "pages": {
            "Fundamentals of Theravāda - Bhante Maggavihāri.html": dict(
                dest="pages/a/fundamentals-of-theravada-5.html",
                title="Fundamentals of Theravāda (Semester V) – Bhante Maggavihāri",
                permalink="/summaries/abhidhamma/fundamentals-5",
            ),
            "Khuddaka Nikāya - Āvuso Sumana.html": dict(
                dest="pages/khu/khuddaka-nikaya-5.html",
                title="Khuddaka Nikāya (Semester V) – Āvuso Sumana",
                permalink="/summaries/khuddaka/semester-5",
            ),
            "Pāḷi - Bhante Vijitānanda.html": dict(
                dest="pages/p/pali-semester-5.html",
                title="Pāḷi (Semester V) – Bhante Vijitānanda",
                permalink="/summaries/pali/semester-5",
            ),
            "Samatha - Bhante Siddhatthālaṅkāra.html": dict(
                dest="pages/sa/samatha-semester-5.html",
                title="Samatha (Semester V) – Bhante Siddhatthālaṅkāra",
                permalink="/summaries/samatha/semester-5",
            ),
            "Suttanta - Bhante Devānanda.html": dict(
                dest="pages/su/suttanta-semester-5.html",
                title="Suttanta (Semester V) – Bhante Devānanda",
                permalink="/summaries/suttanta/semester-5",
            ),
        },
        "splits": [
            dict(
                source="Vinaya.html",
                parts=[
                    dict(match="vibhaṅgavinaya",
                         dest="pages/v/vibhanga/vibhanga-semester-5.html",
                         title="Vibhaṅga Vinaya (Semester V) – Bhante Maggavihāri",
                         permalink="/summaries/vinaya/vibhanga/semester-5"),
                    dict(match="khandhakavinaya",
                         dest="pages/kha/khandhaka-semester-5.html",
                         title="Khandhaka Vinaya (Semester V) – Bhante Siddhatthālaṅkāra",
                         permalink="/summaries/vinaya/khandhaka/semester-5"),
                ],
            ),
        ],
    },
}


if __name__ == "__main__":
    main()
