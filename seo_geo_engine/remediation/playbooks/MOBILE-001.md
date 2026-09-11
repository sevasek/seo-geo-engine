# MOBILE-001 — Every page declares a responsive viewport meta tag.

**Rule:** Every page declares a responsive viewport meta tag.

**Evidence the check emits:** Pages whose `viewport` is missing or doesn't include `width=device-width`.

**Kind of change that flips it:** Add `<meta name="viewport" content="width=device-width, initial-scale=1">` in the template `<head>`.

**Depends on:** `CMS-ACCESS`

One template fix usually clears every page. Don't set a fixed width.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
