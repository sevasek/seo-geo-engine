# HEAD-003 — Each page has at least one `<h2>`.

**Rule:** Each page has at least one `<h2>`.

**Evidence the check emits:** Pages whose `h2Count` is 0.

**Kind of change that flips it:** Add at least one H2 that sections the page. An H1 alone is not enough.

**Depends on:** `CMS-ACCESS`

Short landing pages and thin templates fail this. Add real subsections, not a dummy H2 for the check.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
