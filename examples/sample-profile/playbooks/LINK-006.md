# LINK-006 — External links only point to responsible/authoritative sources.

**Finding:** Needs a policy defining what counts as a "responsible" external link (relevance/authority criteria) to assess against.

**Fix:** Address the finding above so a re-crawl flips LINK-006 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** —

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
