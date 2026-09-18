# PERF-002 — Largest Contentful Paint (LCP) meets Google's "Good" threshold (<=2.5s).

**Rule:** Largest Contentful Paint (LCP) meets Google's "Good" threshold (<=2.5s).

**Evidence the check emits:** Requires `page.pageSpeed.lcpMs`. Absent → the check returns blocked.

**Kind of change that flips it:** Once enriched, get LCP to ≤2500ms (optimize the LCP element, server response, fonts).

**Depends on:** `PSI-ACCESS`

A crawl-only run will show this as blocked. Unblock is PageSpeed Insights (or equivalent) merged onto each page — see docs/design/enrichment.md. Do not treat a missing `pageSpeed` key as a fail, and do not stub LCP from HTML size.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
