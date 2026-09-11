# CONTENT-003 — Every page carries a `dateModified` (or equivalent freshness) signal in structured data.

**Rule:** Every page carries a `dateModified` (or equivalent freshness) signal in structured data.

**Evidence the check emits:** Pages whose `dateModified` is missing (first JSON-LD `dateModified` the crawler found).

**Kind of change that flips it:** Emit `dateModified` in JSON-LD and keep it honest when the page actually changes.

**Depends on:** `CMS-ACCESS`

A hardcoded date that never updates is worse than missing. Wire it to the CMS's real modified timestamp.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
