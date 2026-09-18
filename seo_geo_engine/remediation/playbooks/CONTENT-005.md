# CONTENT-005 — No page shows signs of keyword stuffing.

**Rule:** No page shows signs of keyword stuffing.

**Evidence the check emits:** None from a crawl. The check is a blocked stub.

**Kind of change that flips it:** Not assessable until a stuffing-detection method exists that is better than naive frequency counting.

**Depends on:** `STUFFING-METHOD`

No reliable automated signal exists yet. A regex or term-frequency cutoff is not a method. Leave this blocked. Editorial judgment during copy review is the current control; it is not this check.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
