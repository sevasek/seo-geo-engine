# HEAD-002 — No page uses a bare numeral (e.g. a step-counter "1", "2", "3") as a heading.

**Finding:** 1/7 pages mark up a step-counter numeral as a heading.

**Fix:** Address the finding above so a re-crawl flips HEAD-002 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** CMS-ACCESS

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
