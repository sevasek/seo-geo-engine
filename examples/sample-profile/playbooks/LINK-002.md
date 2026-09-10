# LINK-002 — The anchor text used to link to a money page matches its target keyword.

**Finding:** Needs a documented page → target-keyword map to compare anchor text against.

**Fix:** Address the finding above so a re-crawl flips LINK-002 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** KEYWORD-MAP

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
