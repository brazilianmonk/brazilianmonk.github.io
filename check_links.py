#!/usr/bin/env python3
"""
check_links.py -- Link checker for brazilianmonk.github.io.

Validates links in the generated HTML under _site/:
  * Internal links (same-origin: /foo, /foo/, #frag, ./bar, etc.)
      - resolved against the page URL
      - page must exist in _site (as .html or directory index)
      - a #fragment must exist on the target page (id/name attributes)
  * Asset links (images, css, js, pdf, ...) must exist as files in _site/
  * External links (http/https) are probed with HTTP HEAD, falling back to GET.
    Only 4xx client errors (except 429) are reported as broken.

Run from the repo root:
  bundle exec jekyll build      # regenerate _site first
  python check_links.py [--external]
"""

import argparse
import html
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_site")
OWN_NETLOCS = {"brazilianmonk.github.io", "www.brazilianmonk.github.io"}
SKIP_EXT = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".mp3", ".mp4", ".zip", ".woff", ".woff2", ".ttf", ".eot",
}

# -- helpers -------------------------------------------------------------------

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def fs_path_for(url_path):
    """Filesystem path inside _site for a URL path like '/foo/bar'."""
    parts = [p for p in url_path.lstrip("/").split("/") if p]
    return os.path.join(SITE_DIR, *parts) if parts else SITE_DIR


def page_file_candidates(url_path):
    """Possible generated files for a page URL path (fragment stripped)."""
    p = url_path
    cands = []
    if p in ("", "/"):
        cands.append("index.html")
    else:
        stripped = p.strip("/")
        cands.extend([
            stripped + ".html",
            os.path.join(stripped, "index.html"),
            stripped,  # file already carrying .html
            stripped + "/index.html",
        ])
    return cands


def page_exists(url_path):
    return any(os.path.isfile(fs_path_for(c)) for c in page_file_candidates(url_path))


def load_page_text(url_path):
    for c in page_file_candidates(url_path):
        fp = fs_path_for(c)
        if os.path.isfile(fp):
            with open(fp, encoding="utf-8", errors="replace") as f:
                return f.read()
    return None


def collect_ids(page_html):
    id_re = re.compile(r'(?:\bid|name)\s*=\s*["\']([^"\']+)["\']', re.I)
    return set(id_re.findall(page_html or ""))


def is_internal(value):
    """Classify a URL. Returns None for external/scheme links."""
    if value.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return None
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme in ("http", "https"):
        return parsed.netloc.lower() in OWN_NETLOCS
    if parsed.scheme:
        return None
    return True  # relative, absolute-path, fragment-only


def resolve(page_rel, value):
    """Resolve a link value to a site-absolute path (no fragment)."""
    if value.startswith("/"):
        return value.partition("#")[0] or "/"
    frag_stripped = value.partition("#")[0]
    if frag_stripped == "":
        return None  # fragment-only: checked against current page
    base_dir = os.path.dirname("/" + page_rel)
    combined = urllib.parse.urljoin(base_dir + "/", frag_stripped)
    return combined


def is_ignored(url_path, ignore_list):
    """True when url_path equals or is under one of the ignore prefixes."""
    p = "/" + url_path.lstrip("/")
    for ig in ignore_list:
        ig = "/" + ig.strip("/")
        if p == ig or p.startswith(ig + "/"):
            return True
    return False


def check_external(url):
    """Return (ok, note). HEAD then GET; only 4xx (except 429) counts as broken."""
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0 Safari/537.36 link-checker"),
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    }

    def fetch(u, method):
        req = urllib.request.Request(u, headers=headers, method=method)
        return urllib.request.urlopen(req, timeout=20)

    try:
        r = fetch(url, "HEAD")
        return True, f"HEAD {r.status}"
    except urllib.error.HTTPError as e:
        if e.code == 405 or 500 <= e.code < 600 or e.code == 429:
            try:
                r = fetch(url, "GET")
                return True, f"GET {r.status}"
            except urllib.error.HTTPError as e2:
                if 400 <= e2.code < 500 and e2.code != 429:
                    return False, f"HTTP {e2.code}"
                return True, f"GET {e2.code} (not counted)"
            except Exception as e2:
                return True, f"GET network-error ({type(e2).__name__}), skipped"
        if 400 <= e.code < 500:
            return False, f"HTTP {e.code}"
        return True, f"HEAD {e.code} (not counted)"
    except Exception as e:
        return None, f"network-error: {type(e).__name__}"


# -- main ----------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--external", action="store_true",
                    help="probe external links with HTTP requests (slower)")
    ap.add_argument("--ignore", action="append", default=[],
                    help="skip links whose target path matches this prefix "
                         "(repeatable, e.g. --ignore monktype)")
    args = ap.parse_args()

    if not os.path.isdir(SITE_DIR):
        print("ERROR: _site/ not found. Run 'bundle exec jekyll build' first.")
        sys.exit(2)

    html_files = []
    for root, dirs, files in os.walk(SITE_DIR):
        for fn in files:
            if fn.endswith(".html"):
                html_files.append(os.path.join(root, fn))
    print(f"Scanning {len(html_files)} HTML files under _site/\n")

    link_re = re.compile(
        r'\b(?:href|src|srcset|poster|data-(?:src|href|url|background|poster))'
        r'\s*=\s*"([^"]*)"', re.I)

    internal_errors = []
    external_results = []
    checked_pairs = set()
    external_seen = set()

    for fp in sorted(html_files):
        rel = os.path.relpath(fp, SITE_DIR).replace("\\", "/")
        if rel.endswith("index.html"):
            rel = rel[: -len("index.html")]
        page_url = "/" + rel
        with open(fp, encoding="utf-8", errors="replace") as f:
            page_html = f.read()
        # drop script/style bodies and comments so JS template literals and
        # commented-out links are not mistaken for live links
        page_html = re.sub(r'(?is)<script\b.*?</script>', "", page_html)
        page_html = re.sub(r'(?is)<style\b.*?</style>', "", page_html)
        page_html = re.sub(r'(?is)<!--.*?-->', "", page_html)
        page_ids = collect_ids(page_html)

        for m in link_re.finditer(page_html):
            value = html.unescape(m.group(1).strip())
            if not value or value.startswith(("mailto:", "tel:", "javascript:",
                                              "data:")):
                continue
            parsed = urllib.parse.urlparse(value)
            if parsed.scheme in ("http", "https") and \
                    parsed.netloc.lower() in OWN_NETLOCS:
                # own-domain absolute URL: reduce to its path
                value = parsed.path or "/"
            if not is_internal(value):
                if args.external and value.startswith("http") and \
                        value not in external_seen:
                    external_seen.add(value)
                    external_results.append((page_url, value, *check_external(value)))
                continue

            if value.startswith("#"):
                # fragment on the current page
                if value[1:] and value[1:] not in page_ids:
                    key = (page_url, value)
                    if key not in checked_pairs:
                        checked_pairs.add(key)
                        internal_errors.append(
                            (page_url, value, f"missing fragment #{value[1:]} "
                                              f"on {page_url}"))
                continue

            target = resolve(rel, value)
            if target is None:
                continue
            target_path, _, frag = target.partition("#")
            key = (page_url, target_path, frag)
            if key in checked_pairs:
                continue
            checked_pairs.add(key)

            ext = os.path.splitext(target_path)[1].lower()
            if ext in SKIP_EXT or ext in (".xml", ".txt", ".json", ".webmanifest"):
                if not is_ignored(target_path, args.ignore) and \
                        not os.path.isfile(fs_path_for(target_path)):
                    internal_errors.append(
                        (page_url, value, f"missing file: {target_path}"))
                continue

            if not is_ignored(target_path, args.ignore) and \
                    not page_exists(target_path):
                internal_errors.append(
                    (page_url, value, f"page not found: {target_path}"))
                continue
            if frag:
                target_html = load_page_text(target_path)
                ids = collect_ids(target_html)
                if frag not in ids:
                    internal_errors.append(
                        (page_url, value,
                         f"missing fragment #{frag} on {target_path}"))

    print("=" * 64)
    print("  Internal links")
    print("=" * 64)
    if not internal_errors:
        print("  \u2705 all internal links resolve")
    else:
        for page_url, value, why in internal_errors:
            print(f"  \u274c {page_url}")
            print(f"     {value}")
            print(f"     -> {why}")

    external_broken = []
    if args.external:
        print()
        print("=" * 64)
        print("  External links (HTTP probe)")
        print("=" * 64)
        net_errors, ok_count = [], 0
        for page_url, value, ok, note in external_results:
            if ok is True:
                ok_count += 1
            elif ok is False:
                external_broken.append((page_url, value, note))
            else:
                net_errors.append((page_url, value, note))
        for page_url, value, note in external_broken:
            print(f"  \u274c {page_url}")
            print(f"     {value}")
            print(f"     -> {note}")
        if net_errors:
            print(f"\n  \u26a0\ufe0f  {len(net_errors)} external link(s) unreachable "
                  f"from this machine (not counted as broken):")
            for page_url, value, note in net_errors[:20]:
                print(f"     {value}  (on {page_url})  -- {note}")
        print(f"\n  External: {ok_count} ok, {len(external_broken)} broken, "
              f"{len(net_errors)} unreachable")

    print()
    print("=" * 64)
    msg = f"  Result: {len(internal_errors)} internal error(s)"
    if args.external:
        msg += f", {len(external_broken)} broken external link(s)"
    print(msg)
    print("=" * 64)
    sys.exit(1 if internal_errors or external_broken else 0)


if __name__ == "__main__":
    main()
