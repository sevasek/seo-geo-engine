# CRAWL-003 — No internal link is broken (4xx/5xx or unreachable).

**Rule:** No internal link is broken (4xx/5xx or unreachable).

**Evidence the check emits:** `linkResolutions` (and discovered pages) whose `status` is 4xx/5xx or `null` (request failed).

**Kind of change that flips it:** Fix the href or restore the target. `status: null` is a failed request, not 'unknown'.

**Depends on:** `CMS-ACCESS`

Don't recrawl around it. If the target moved, update every internal href (see also LINK-004).

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
