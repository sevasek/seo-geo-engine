# CONTENT-007 — Page content offers real information gain over top competing results.

**Rule:** Page content offers real information gain over top competing results.

**Evidence the check emits:** None from a crawl. The check is a blocked stub.

**Kind of change that flips it:** Not assessable without a competitor/SERP content corpus.

**Depends on:** `COMPETITOR-CONTENT-CORPUS`

A single-site crawl cannot answer this. Unblock is a corpus of competing pages plus a comparison method that has been tested on real output — not 'the page is long'.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
