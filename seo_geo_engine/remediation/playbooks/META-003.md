# META-003 — No two pages share the same `<title>`.

**Rule:** No two pages share the same `<title>`.

**Evidence the check emits:** The colliding title string and the URLs that share it.

**Kind of change that flips it:** Make each colliding title unique. Length still has to satisfy META-001.

**Depends on:** `CMS-ACCESS`

Usually a template is emitting the same default title on several URLs. Give each page its own title; do not append a random suffix to 'make it unique'.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
