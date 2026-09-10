# PERF-001 — Raw HTML payload is under 250KB per page.

**Finding:** 1/7 pages exceed 250,000 bytes of raw HTML.

**Fix:** Address the finding above so a re-crawl flips PERF-001 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** CMS-ACCESS

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
