# CONTENT-006 — Content is formatted for skimming (subheadings, lists, short paragraphs).

**Rule:** Content is formatted for skimming (subheadings, lists, short paragraphs).

**Evidence the check emits:** None from a crawl. The check is a blocked stub.

**Kind of change that flips it:** Not assessable until a skimmability rubric exists.

**Depends on:** `SKIMMABILITY-RUBRIC`

Heading counts and list presence are not a rubric. Don't ship a check that rewards `<ul>` spam. Unblock requires a defined rubric tested against real crawl output.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
