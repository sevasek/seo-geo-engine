# CRAWL-006 — Substantive page content is present without executing JavaScript.

**Rule:** Substantive page content is present without executing JavaScript.

**Evidence the check emits:** Pages whose `noJsWordCount` is far below JS-rendered `wordCount` (or near zero).

**Kind of change that flips it:** Render the main copy in the initial HTML. Don't ship an empty shell that hydrates in JS.

**Depends on:** `CMS-ACCESS`

`noJsWordCount` comes from a plain fetch, not Playwright. If it is empty, crawlers that don't run JS see nothing. SSR or prerender the body copy.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
