# HEAD-004 — No page skips a heading level (e.g. an `<h3>` before any `<h2>`).

**Rule:** No page skips a heading level (e.g. an `<h3>` before any `<h2>`).

**Evidence the check emits:** Pages whose `headingSequence` jumps a level.

**Kind of change that flips it:** Use headings in order: H1, then H2, then H3. Don't skip because a style looks better.

**Depends on:** `CMS-ACCESS`

The check walks `headingSequence` in DOM order. Restyle with CSS; don't pick H3 because it's smaller.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
