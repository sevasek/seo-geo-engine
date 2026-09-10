# LINK-001 — Pages within the same topical/entity cluster link to each other in-content, not just via shared nav.

**Finding:** 1/3 clustered pages have no in-content link to a related page.

**Fix:** Address the finding above so a re-crawl flips LINK-001 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** CMS-ACCESS

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
