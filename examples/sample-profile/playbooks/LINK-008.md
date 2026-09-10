# LINK-008 — Internal link authority flows to newly published pages.

**Finding:** Needs a defined set of "new" pages and an internal linking policy for surfacing them — not derivable from a single crawl snapshot.

**Fix:** Address the finding above so a re-crawl flips LINK-008 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** —

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
