# CRAWL-001 — Every indexable, canonical page is listed in the sitemap.

**Rule:** Every indexable, canonical page is listed in the sitemap.

**Evidence the check emits:** Indexable pages found via internal links (`discoveredNonSitemapPages`) that are not in `sitemapUrls`.

**Kind of change that flips it:** Add the missing URLs to the sitemap, or noindex/canonical them if they should not be indexed.

**Depends on:** `CMS-ACCESS`

If the page should be indexed, put it in the sitemap. If it shouldn't, don't just omit it — give it noindex or a canonical to the URL you do want indexed, otherwise CRAWL-001 will keep flagging it.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
