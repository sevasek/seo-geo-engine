# CRAWL-006 — Substantive page content is present without executing JavaScript.

**Finding:** 1/7 page(s) rely on JavaScript for most of their content.

**Fix:** Address the finding above so a re-crawl flips CRAWL-006 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** CMS-ACCESS

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
