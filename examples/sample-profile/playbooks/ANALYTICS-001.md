# ANALYTICS-001 — Every page loads a web-analytics script.

**Finding:** 1/7 pages have no detectable analytics script.

**Fix:** Address the finding above so a re-crawl flips ANALYTICS-001 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** CMS-ACCESS

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
