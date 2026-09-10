# LINK-007 — Outbound links carry appropriate `rel` attributes (`nofollow`/`sponsored`/`ugc`) where warranted.

**Finding:** Needs a policy on when outbound links should carry which `rel` attribute — not assessable without one.

**Fix:** Address the finding above so a re-crawl flips LINK-007 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** —

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
