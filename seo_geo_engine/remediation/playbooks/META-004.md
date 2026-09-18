# META-004 — Every page has a self-referencing canonical tag.

**Rule:** Every page has a self-referencing canonical tag.

**Evidence the check emits:** Pages whose `canonical` is missing, empty, or points at a different URL than `url`.

**Kind of change that flips it:** Emit `<link rel="canonical" href="{this page's URL}">` on every page.

**Depends on:** `CMS-ACCESS`

Fix the canonical in the page template. A canonical that points at a different URL is a signal to drop this URL — only keep that if the page is a genuine duplicate you want deindexed.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
