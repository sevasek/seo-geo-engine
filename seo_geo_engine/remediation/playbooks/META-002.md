# META-002 — Every page has a unique, descriptive meta description between 120–160 characters.

**Rule:** Every page has a unique, descriptive meta description between 120–160 characters.

**Evidence the check emits:** Failing page URLs plus missing / too-short / too-long (`metaDesc` / `metaDescLen`).

**Kind of change that flips it:** Write a unique meta description per page in that length band. Do not reuse one description across URLs.

**Depends on:** `CMS-ACCESS`

Edit the meta description field or the template that emits `<meta name="description">`. This is copywriting, not a script: if the crawl has no usable sentence, write one.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
