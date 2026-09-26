# Newsletter setup guide — Kit (ConvertKit)

This site's footer signup form is powered by **Kit** (formerly ConvertKit).
The free plan covers **10,000 subscribers** with unlimited email sends,
includes double opt-in, and its RSS automation can email subscribers
automatically every time you publish a post.

The footer form is **live and pointing at your Kit form** (UID
`e5b2f356e4`, form 9964785) — new subscribers already land in Kit.
What remains is the RSS automation (section 4) and migrating any
existing EmailOctopus subscribers (section 5).

---

## 1. Create the account and list

1. Sign up free at <https://kit.com> (no card needed).
2. Grow > Subscribers — your list lives here. Nothing to configure.

## 2. Create the signup form

1. Grow > Landing Pages & Forms > **Create** > choose **Form**.
2. Pick any simple template (or start blank).
3. Keep it to a single **Email** field. Optionally add first name.
4. Turn on **Incentive email > double opt-in** if offered — subscribers
   must click a confirmation link before joining (matches the privacy page).
5. **Publish** the form.

## 3. Wire the form into this site

1. Open the published form > **Embed** (top right) > **JavaScript**.
2. Copy the whole snippet. It looks like:

   ```html
   <script async data-uid="XXXXXXXXXX" src="https://f.convertkit.com/ckjs/ck.ck.js"></script>
   ```

3. Preferred: paste the **entire snippet** into `_data/settings.yml`:

   ```yaml
   newsletter:
     custom_html: "<script async data-uid=\"XXXXXXXXXX\" src=\"https://f.convertkit.com/ckjs/ck.ck.js\"></script>"
   ```

   (Alternative: copy just the `data-uid` value into `kit_form_id: "XXXXXXXXXX"`.
   If the form doesn't render that way, use `custom_html`.)

4. Commit, push, and the footer form is Kit-powered on every page.

## 4. Turn on automatic post-emails (the goal!)

1. In Kit: **Grow > RSS** (under Automations).
2. **+ Add feed** > Feed URL: `https://www.brazilianmonk.org/rss-feed.xml`
3. Choose:
   - **Single** — one email per new post (recommended), or
   - **Digest** — a weekly/monthly roundup of new posts.
4. Enable **Send automatically** — otherwise emails sit as drafts.
5. Pick the sending address and recipients, then choose a template.
   Make sure the template contains the **Post content** block — Kit
   refuses to enable the connection without it.
6. Use `{{ title }}` in the subject line so it reads as the post title.
7. **Save / enable.** Kit checks the feed periodically; when a new post
   appears, an email goes out on its own (~30 min after drafting).
8. Tip: enable **Skip old items** so your 4 existing feed items aren't
   blasted to subscribers the moment you connect the feed.

## 5. Migrate existing EmailOctopus subscribers

1. EmailOctopus > your list > **Export** as CSV.
2. Kit > Grow > Subscribers > **Import** the CSV.
3. Important: imported contacts skip double opt-in, and that's fine —
   they already confirmed with EmailOctopus. Ask Kit support to confirm
   import compliance if you want belt-and-braces.
4. After a week of smooth running, delete the old EmailOctopus list (or
   keep it dormant) so both lists don't diverge.

## 6. Cleanup (after migration works)

In `_data/settings.yml`, empty out the legacy keys:

```yaml
newsletter:
  custom_html: "<script ... ></script>"   # keep — the live form
  kit_form_id: ""
  embed_url: ""                            # clear — EmailOctopus gone
  emailoctopus_list_key: ""                # clear
```

Then close your EmailOctopus account if you're not using it elsewhere.

---

## Current site files involved

| File | Role |
| --- | --- |
| `_data/settings.yml` | `newsletter:` block — provider keys and wording |
| `_includes/newsletter.html` | Renders the right form for the configured provider |
| `_includes/footer.html` | Shows the form on every page |
| `_sass/_newsletter.scss` | Styling (Kit's own styles override inside its embed) |
| `pages/privacy.md` | Data-processing disclosure (already updated to Kit) |

## Notes

- Kit's free plan has no RSS-to-email limit — sends are unlimited; only
  the subscriber count (10,000) matters.
- Unsubscribes and bounces are handled by Kit automatically.
- If you ever switch providers again, `custom_html` accepts any embed
  snippet — no code changes needed beyond that one line.
