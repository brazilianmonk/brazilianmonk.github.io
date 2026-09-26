# Newsletter setup guide — Kit (ConvertKit) + GitHub Action

This site's footer signup form is powered by **Kit** (formerly ConvertKit).
The free plan covers **10,000 subscribers** with unlimited email sends and
includes double opt-in.

**The form is live** (UID `e5b2f356e4`, form 9964785) — new subscribers
already land in Kit.

**Automatic post-emails** are provided by a GitHub Action in this repo
(`.github/workflows/newsletter.yml`) rather than Kit's paid RSS feature:

- Kit's built-in RSS automation requires the paid Creator plan.
- But Kit's V4 **Broadcast API is available on every plan** — including free
  (Kit's own docs: "V3 and V4 API keys are not restricted... creators on any
  plan").
- So after each push, the Action builds the site, checks `rss-feed.xml` for
  posts that haven't been announced, and schedules a Kit broadcast for each
  via `POST https://api.kit.com/v4/broadcasts`. Subscribers get an email
  with the post title and a link. Fully automatic, no paid plan.

---

## 1. One-time Kit configuration (~5 minutes)

1. **Create an email template** (Send > Email Templates > New). Keep it
   minimal — the broadcast content (title + link) is inserted into it.
   Note its **numeric ID** (visible in the template URL or API).
2. **Create a V4 API key**: avatar > **Developer settings** > V4 Keys >
   "Add a new key". Copy it immediately — it's shown once.
3. **Add two GitHub secrets** (repo > Settings > Secrets and variables >
   Actions > New repository secret):
   - `KIT_API_KEY` — the V4 key
   - `KIT_EMAIL_TEMPLATE_ID` — the numeric template id
4. **Commit and push everything.** On the next push, the Action runs:
   check the Actions tab for a green "Newsletter" run.

The Action stores which posts were announced in
`scripts/newsletter_state.json` and commits it back, so nothing is ever
emailed twice. It announces at most 3 posts per run and schedules each
~5 minutes ahead. Want a safety net instead of auto-send? Change the
script's `make_broadcast` to set `"send_at": null` — broadcasts then sit
as drafts you approve in Kit.

## 2. Testing without spamming anyone

```bash
bundle exec jekyll build
python scripts/send_newsletter.py --dry-run     # what would be announced
python scripts/send_newsletter.py --init-state  # mark current posts as announced
```

Then publish a test post, push, and watch the Action. Your own
subscription should receive: "New post: <title>".

## 3. Migrating existing EmailOctopus subscribers

1. EmailOctopus > your list > **Export** as CSV.
2. Kit > Grow > Subscribers > **Import** the CSV.
3. Imported contacts skip double opt-in — fine, they already confirmed
   with EmailOctopus.
4. After a week of smooth running, delete or archive the EmailOctopus
   list so the two don't diverge.

## 4. If you'd rather have provider-native RSS (alternatives)

The Action is free and keeps you on Kit's 10k-subscriber free plan. If
you ever prefer the provider to handle it natively instead:

| Provider | Free tier | RSS-to-email on free |
| --- | --- | --- |
| **Kit** (current) | 10,000 subscribers | ❌ paid (Creator) — but **API path works free** (this repo's Action) |
| **Sender** | 2,500 subs / 15,000 emails/mo | ✅ included |
| **Brevo** | 300 emails/day | ✅ included (cap makes it impractical past ~300 subscribers) |
| **Zoho Campaigns** | 2,000 contacts / 6,000 emails/mo | ✅ included |
| **EmailOctopus** | 2,500 subs / 10,000 emails/mo | ❌ none; API can't send campaigns either |

Switching later means pasting that provider's embed snippet into
`custom_html` in `_data/settings.yml` — one line, no code changes.

## 5. Files involved

| File | Role |
| --- | --- |
| `_data/settings.yml` | `newsletter:` block — provider embed + wording |
| `_includes/newsletter.html` | Renders the right form for the configured provider |
| `_includes/footer.html` | Shows the form on every page |
| `_sass/_newsletter.scss` | Styling (Kit's own styles apply inside its embed) |
| `.github/workflows/newsletter.yml` | Runs the auto-sender after every push |
| `scripts/send_newsletter.py` | Detects new feed posts, schedules Kit broadcasts |
| `scripts/newsletter_state.json` | Which posts were already announced (auto-committed) |
| `pages/privacy.md` | Data-processing disclosure (updated to Kit) |
