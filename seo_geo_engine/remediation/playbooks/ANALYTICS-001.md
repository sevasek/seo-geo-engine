# ANALYTICS-001 — Every page loads a web-analytics script.

**Rule:** Every page loads a web-analytics script.

**Evidence the check emits:** Pages whose `hasAnalytics` is false. The crawler looks for Google-family signatures (GTM, gtag, analytics.js) only.

**Kind of change that flips it:** Load analytics on every template, including thin / legal pages you assumed were exempt.

**Depends on:** `CMS-ACCESS`

A non-Google analytics stack will look like a fail. Either add a Google-family tag or disable this ID in site.yaml with a reason and add a profile check for the actual vendor. Don't fake a gtag snippet to silence the check.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
