# PERF-001 — Raw HTML payload is under 250KB per page.

**Rule:** Raw HTML payload is under 250KB per page.

**Evidence the check emits:** Pages whose `bytes` is over 250000.

**Kind of change that flips it:** Cut HTML weight: stop inlining huge CSS/JS, split the page, don't dump a JSON blob into the document.

**Depends on:** `CMS-ACCESS`

`bytes` is the plain-fetch HTML size, not the fully loaded page. Images are not in this number; this is document bloat.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
