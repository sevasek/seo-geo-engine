# CRAWL-004 — Every page URL and internal link uses HTTPS.

**Rule:** Every page URL and internal link uses HTTPS.

**Evidence the check emits:** Page `url`s and internal hrefs that start with `http://`.

**Kind of change that flips it:** Serve the site on HTTPS and make internal links HTTPS (or scheme-relative).

**Depends on:** `CMS-ACCESS`

A mixed-content leftover `http://` in a hardcoded nav link fails this even when the page itself is HTTPS.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
