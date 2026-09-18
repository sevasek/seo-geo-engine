# TRUST-001 — The site has a substantive About/Team page introducing real people, not a stub.

**Finding:** No About/Team page, or the page that exists looks like a stub (<=1 image or <150 words).

**Fix:** Address the finding above so a re-crawl flips TRUST-001 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** CMS-ACCESS

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
