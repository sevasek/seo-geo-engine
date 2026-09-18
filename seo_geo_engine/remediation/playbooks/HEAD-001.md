# HEAD-001 — Each page has exactly one `<h1>`.

**Rule:** Each page has exactly one `<h1>`.

**Evidence the check emits:** Pages whose `h1Count` is 0 or greater than 1, with the `h1s` text.

**Kind of change that flips it:** One H1 that names the page. Extra H1s become H2s (or get dropped if they're chrome).

**Depends on:** `CMS-ACCESS`

A missing H1 is usually the template not emitting one; multiple H1s are usually a builder block and the template both using H1. Do not style a div to look like a heading instead of using a real H1 — the check reads the tag.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
