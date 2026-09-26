#!/usr/bin/env python3
"""
send_newsletter.py — email new blog posts to Kit (ConvertKit) subscribers.

Reads _site/rss-feed.xml, finds posts that haven't been announced yet,
and creates+schedules a Kit broadcast for each via the Kit V4 API
(POST https://api.kit.com/v4/broadcasts). Scheduled with send_at so Kit
delivers them; runs on GitHub Actions after each site deploy, or locally
for testing.

V4 API keys are available on ALL Kit plans (free included):
https://help.kit.com/en/articles/9902901-kit-api-overview

Usage:
  python scripts/send_newsletter.py --dry-run        # show what would send
  python scripts/send_newsletter.py --init-state     # mark all current posts as sent
  python scripts/send_newsletter.py                  # announce new posts via Kit
  python scripts/send_newsletter.py --limit 1        # cap how many go out per run

Environment (required for real sends):
  KIT_API_KEY          Kit V4 API key (Developer settings > V4 keys)
  KIT_EMAIL_TEMPLATE_ID  numeric id of the email template to use

State: scripts/newsletter_state.json tracks announced post URLs.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree

# Pāḷi titles contain characters some consoles can't encode (e.g. cp1252)
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
FEED = ROOT / "_site" / "rss-feed.xml"
STATE = Path(__file__).resolve().parent / "newsletter_state.json"
API_URL = "https://api.kit.com/v4/broadcasts"

NS = {
    "rss": "",  # RSS 2.0 core has no namespace
    "atom": "http://www.w3.org/2005/Atom",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def parse_feed(limit=10):
    """Return newest posts from the built RSS feed."""
    if not FEED.exists():
        sys.exit(f"Feed not found at {FEED}. Run 'bundle exec jekyll build' first.")
    tree = ElementTree.parse(FEED)
    channel = tree.getroot().find("channel")
    posts = []
    for item in channel.findall("item"):
        def txt(tag, ns=None):
            el = item.find(tag, ns) if ns else item.find(tag)
            return (el.text or "").strip() if el is not None else ""

        link = txt("link")
        title = txt("title")
        pub = txt("pubDate")
        if not link or not title:
            continue
        try:
            date = parsedate_to_datetime(pub) if pub else None
        except (TypeError, ValueError):
            date = None
        posts.append({"title": title, "url": link, "date": date})
        if len(posts) >= limit:
            break
    return posts


def load_state():
    if STATE.exists():
        return set(json.loads(STATE.read_text(encoding="utf-8")))
    return set()


def save_state(sent):
    STATE.write_text(json.dumps(sorted(sent), indent=2), encoding="utf-8")


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_broadcast(post, template_id, send_at):
    """Kit V4 broadcast payload announcing one post."""
    read_more = (
        f'<p><a href="{post["url"]}">Read the full post on the website &rarr;</a></p>'
    )
    return {
        "email_template_id": template_id,
        "content": (
            f"<p>A new post was published on the website:</p>"
            f"<h2>{post['title']}</h2>"
            f"<p>{read_more}</p>"
            "<p>You are receiving this because you subscribed to updates from "
            "the website. You can unsubscribe at any time using the link in "
            "any email.</p>"
        ),
        "description": f"Auto: {post['title']}",
        "subject": f"New post: {post['title']}",
        "preview_text": f"New on the blog: {post['title']}",
        "public": True,
        "published_at": iso(datetime.now(timezone.utc)),
        "send_at": iso(send_at),
    }


def send_broadcast(payload, api_key):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Kit-Api-Key": api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        return e.code, detail[:500]
    except urllib.error.URLError as e:
        return None, str(e)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="print planned broadcasts, send nothing")
    ap.add_argument("--init-state", action="store_true",
                    help="mark all posts currently in the feed as announced")
    ap.add_argument("--limit", type=int, default=3,
                    help="max posts to announce in one run (default 3)")
    ap.add_argument("--delay-minutes", type=int, default=2,
                    help="schedule each broadcast N minutes ahead (default 2)")
    args = ap.parse_args()

    posts = parse_feed()
    state = load_state()

    if args.init_state:
        for p in posts:
            state.add(p["url"])
        save_state(state)
        print(f"Initialized: {len(posts)} posts marked as announced.")
        return

    new_posts = [p for p in posts if p["url"] not in state][: args.limit]
    if not new_posts:
        print("No new posts to announce.")
        return

    print(f"{len(new_posts)} new post(s) to announce:")
    for p in new_posts:
        print(f"  - {p['title']}  ({p['url']})")

    if args.dry_run:
        print("Dry run: nothing sent.")
        return

    api_key = os.environ.get("KIT_API_KEY")
    template_id = os.environ.get("KIT_EMAIL_TEMPLATE_ID")
    missing = [n for n, v in
               (("KIT_API_KEY", api_key), ("KIT_EMAIL_TEMPLATE_ID", template_id))
               if not v]
    if missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")

    try:
        template_id = int(template_id)
    except ValueError:
        sys.exit("KIT_EMAIL_TEMPLATE_ID must be a numeric template id.")

    newly_sent = []
    for p in new_posts:
        send_at = datetime.now(timezone.utc) + timedelta(minutes=args.delay_minutes)
        payload = make_broadcast(p, template_id, send_at)
        status, body = send_broadcast(payload, api_key)
        if status and 200 <= status < 300:
            print(f"  scheduled: {p['title']} (HTTP {status})")
            newly_sent.append(p)
        else:
            print(f"  FAILED ({status}): {body}", file=sys.stderr)
            # stop on auth/validation errors; keep state consistent
            break

    if newly_sent:
        for p in newly_sent:
            state.add(p["url"])
        save_state(state)
        print(f"Announced {len(newly_sent)} post(s); state saved.")


if __name__ == "__main__":
    main()
