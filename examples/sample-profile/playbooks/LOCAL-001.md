# LOCAL-001 — Every embedded map links to the business's Google Business Profile listing, not a plain address/name text search.

**Finding:** 1/1 map embed(s) search by address/name text instead of linking to a GBP listing.

**Fix:** Address the finding above so a re-crawl flips LOCAL-001 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** CMS-ACCESS

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
