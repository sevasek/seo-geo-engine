# LINK-004 — Internal links point directly at the canonical destination, not through a redirect.

**Rule:** Internal links point directly at the canonical destination, not through a redirect.

**Evidence the check emits:** `linkResolutions` entries that are internal links with `redirected: true`.

**Kind of change that flips it:** Update the href to the final URL so the link is a 200, not a 301.

**Depends on:** `CMS-ACCESS`

Typical cause: an old slug left in nav or body copy after a rename. Change the link, don't add another redirect.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
