# CONTENT-002 — At least half of a page's visible text sits inside real `<p>` elements, so a content extractor recognizes it as prose.

**Rule:** At least half of a page's visible text sits inside real `<p>` elements, so a content extractor recognizes it as prose.

**Evidence the check emits:** Pages where `pTagWordCount` is less than half of `wordCount`.

**Kind of change that flips it:** Put body copy in `<p>` tags, not a pile of styled `<div>`s.

**Depends on:** `CMS-ACCESS`

Page builders that emit everything as divs fail this even when a human sees paragraphs. Switch the block type to a paragraph / rich-text block, or fix the template.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
