# CRAWL-007 — Page URLs are clean (lowercase, hyphen-separated, no query-string cruft).

**Rule:** Page URLs are clean (lowercase, hyphen-separated, no query-string cruft).

**Evidence the check emits:** Page URLs with uppercase path segments, underscores, or query strings.

**Kind of change that flips it:** Pick a clean slug and 301 the old URL. Don't leave both live.

**Depends on:** `CMS-ACCESS`

Tracking query strings on canonical page URLs fail this. Keep campaigns on the href, not the canonical URL.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
