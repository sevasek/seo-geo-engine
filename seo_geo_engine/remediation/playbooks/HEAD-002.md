# HEAD-002 — No page uses a bare numeral (e.g. a step-counter "1", "2", "3") as a heading.

**Rule:** No page uses a bare numeral (e.g. a step-counter "1", "2", "3") as a heading.

**Evidence the check emits:** Page URL plus the numeral-only heading text.

**Kind of change that flips it:** Replace the numeral with a real heading that says what the step is ('Book a visit', not '1').

**Depends on:** `CMS-ACCESS`

Stepper / process widgets that put the step number in an H2/H3 are the usual cause. Keep the number in the body copy if you want it; the heading has to be words.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
