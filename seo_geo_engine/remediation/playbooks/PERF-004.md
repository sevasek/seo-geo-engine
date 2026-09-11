# PERF-004 — Interaction to Next Paint (INP) meets Google's "Good" threshold.

**Rule:** Interaction to Next Paint (INP) meets Google's "Good" threshold.

**Evidence the check emits:** None. The check is a blocked stub — no lab-data substitute exists for INP.

**Kind of change that flips it:** Not assessable until real-user field/CrUX data is available for the URL.

**Depends on:** `CRUX-DATA`

PageSpeed lab data is not INP. A low-traffic site may never accumulate CrUX. Leave this blocked until a field-data source exists. INP is not on the `pageSpeed` object yet on purpose.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
