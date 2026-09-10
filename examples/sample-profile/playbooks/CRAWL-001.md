# CRAWL-001 — Every indexable, canonical page is listed in the sitemap.

**Finding:** 3 page-like URL(s) are linked from the site but not accounted for in the 6-URL sitemap (asset files like PDFs/images are excluded from this count; confirmed redirects to already-sitemapped pages are also excluded).

**Fix:** Address the finding above so a re-crawl flips CRAWL-001 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** CMS-ACCESS

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
