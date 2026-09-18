# LINK-005 — Every page has at least one inbound internal link from another page.

**Rule:** Every page has at least one inbound internal link from another page.

**Evidence the check emits:** Page URLs that never appear in any other page's `internalHrefs`.

**Kind of change that flips it:** Link to the orphan from a related page (in content, not only a sitemap).

**Depends on:** `CMS-ACCESS`

The check uses crawl-time internal hrefs. A page linked only from an uncrawlable location still looks orphaned.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
