# CONTENT-008 — Factual claims are backed by a citable source.

**Finding:** Needs a way to distinguish an unsupported claim from a sourced one — requires content-level judgment or a claims/sources map.

**Fix:** Address the finding above so a re-crawl flips CONTENT-008 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** CLAIMS-SOURCES-MAP

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
