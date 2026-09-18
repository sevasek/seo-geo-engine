# PERF-003 — Cumulative Layout Shift (CLS) meets Google's "Good" threshold (<=0.1).

**Rule:** Cumulative Layout Shift (CLS) meets Google's "Good" threshold (<=0.1).

**Evidence the check emits:** Requires `page.pageSpeed.cls`. Absent → the check returns blocked.

**Kind of change that flips it:** Once enriched, reserve image/ad/font space so CLS stays ≤0.1.

**Depends on:** `PSI-ACCESS`

Same enrichment dependency as PERF-002. Width/height on images and font-display are the usual CMS-side fixes after you have a number.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
