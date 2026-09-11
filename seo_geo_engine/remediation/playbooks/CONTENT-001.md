# CONTENT-001 — Every service page has at least 500 words of visible content.

**Rule:** Every service page has at least 500 words of visible content.

**Evidence the check emits:** Service pages whose `wordCount` is under 500 (chrome stripped).

**Kind of change that flips it:** Write real page copy until the visible word count clears 500. Do not hide text in `display:none` or JS-only injection to game the count.

**Depends on:** `CMS-ACCESS`

The crawler counts `bodyText` after stripping script/style/noscript/template. Nav and footer words count; that is not a license to stuff chrome. Write the page.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
