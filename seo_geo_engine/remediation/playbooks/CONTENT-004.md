# CONTENT-004 — Page content matches its documented target search intent.

**Rule:** Page content matches its documented target search intent.

**Evidence the check emits:** None from a crawl. The check is a blocked stub.

**Kind of change that flips it:** Not assessable until a per-page target-intent map exists.

**Depends on:** `SEARCH-INTENT-MAP`

This is **not assessable from crawl data**. Unblock is a documented informational/commercial/navigational intent per URL, supplied by the profile, plus a method that compares page copy to that intent. Do not 'unblock' this with a keyword-density heuristic.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
