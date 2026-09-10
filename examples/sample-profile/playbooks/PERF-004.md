# PERF-004 — Interaction to Next Paint (INP) meets Google's "Good" threshold.

**Finding:** Needs real-user field/CrUX data — no lab-data substitute exists for INP, and a lower-traffic site may not accumulate enough CrUX data for Google to report it at all.

**Fix:** Address the finding above so a re-crawl flips PERF-004 to pass — this is a synthetic worked example, so the fix here is illustrative (a real profile's playbook would name the exact CMS field/template to edit).

**Depends on:** —

**Next step once unblocked:** Apply the fix, re-crawl, re-run `python3 -m seo_geo_engine.report` and confirm the verdict is now `pass`, then delete this row and playbook.
