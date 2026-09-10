# LINK-004 — Internal links point directly at the canonical destination, not through a redirect.

**Finding:** 1 unique redirecting URL(s) are linked to directly instead of their final destination.

**Fix:** Address the finding above so a re-crawl flips LINK-004 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** CMS-ACCESS

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
