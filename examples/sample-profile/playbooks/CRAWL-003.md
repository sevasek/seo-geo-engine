# CRAWL-003 — No internal link is broken (4xx/5xx or unreachable).

**Finding:** 1/9 internal link(s) are broken or unreachable.

**Fix:** Address the finding above so a re-crawl flips CRAWL-003 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** CMS-ACCESS

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
