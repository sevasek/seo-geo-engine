# CONTENT-002 — At least half of a page's visible text sits inside real `<p>` elements, so a content extractor recognizes it as prose.

**Finding:** 1/7 page(s) have less than 50% of their visible text inside <p> tags — a content extractor may not recognize the rest as prose.

**Fix:** Address the finding above so a re-crawl flips CONTENT-002 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** CMS-ACCESS

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
