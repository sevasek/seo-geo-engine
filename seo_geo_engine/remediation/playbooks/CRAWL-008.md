# CRAWL-008 — The sitemap is submitted to Google Search Console with no errors.

**Rule:** The sitemap is submitted to Google Search Console with no errors.

**Evidence the check emits:** Requires `site.searchConsole` (`sitemapSubmitted`, `sitemapErrors`, `sitemapWarnings`). Absent → the check returns blocked.

**Kind of change that flips it:** Submit the sitemap in GSC and clear errors. Enrichment (Phase 2) is what writes `searchConsole` onto the site dict.

**Depends on:** `GSC-ACCESS`

A crawl-only run will show this as blocked, not fail. That is expected until the profile runs the Search Console enricher. Do not flip the standard row to `blocked` just because this crawl wasn't enriched.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
