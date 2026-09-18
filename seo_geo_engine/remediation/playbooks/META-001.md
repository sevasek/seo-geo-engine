# META-001 — Every page has a unique, descriptive `<title>` between 30–60 characters.

**Rule:** Every page has a unique, descriptive `<title>` between 30–60 characters.

**Evidence the check emits:** Failing page URLs plus whether the title is missing, too short, or too long (`title` / `titleLen`).

**Kind of change that flips it:** Write a unique title per page in that length band. Do not invent a shared house title and stamp it on every URL.

**Depends on:** `CMS-ACCESS`

Edit each offending page's title field (or the template that generates it). Count characters as the crawler does — the rendered `<title>` text, not the CMS field before a suffix is appended. If a sitewide suffix pushes titles over 60, shorten the unique portion or the suffix, don't fight the check.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
