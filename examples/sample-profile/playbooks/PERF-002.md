# PERF-002 — Largest Contentful Paint (LCP) meets Google's "Good" threshold (<=2.5s).

**Finding:** 1/7 page(s) miss Google's 'Good' LCP threshold (lab data (single PageSpeed Insights run) — no real-user field/CrUX data available for this site yet).

**Fix:** Address the finding above so a re-crawl flips PERF-002 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** CMS-ACCESS

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
