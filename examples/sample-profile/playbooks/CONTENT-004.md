# CONTENT-004 — Page content matches its documented target search intent.

**Finding:** Needs a documented target search-intent (informational/commercial/navigational) per page to compare against.

**Fix:** Address the finding above so a re-crawl flips CONTENT-004 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** SEARCH-INTENT-MAP

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
