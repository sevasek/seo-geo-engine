# SCHEMA-002 — Every service page with visible FAQ content carries matching `FAQPage` JSON-LD.

**Finding:** 3/3 service pages carry no FAQPage schema.

**Fix:** Address the finding above so a re-crawl flips SCHEMA-002 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** CMS-ACCESS

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
