# CRAWL-005 — Internal redirects are clean, single-hop 301s.

**Rule:** Internal redirects are clean, single-hop 301s.

**Evidence the check emits:** `linkResolutions` with `redirected` where `redirectStatus` isn't 301 or `redirectHops` > 1.

**Kind of change that flips it:** Replace chains and 302s with a single 301 to the final URL, and update the source href (LINK-004) so the redirect isn't needed.

**Depends on:** `CMS-ACCESS`

Temporary 302s left in place after a migration are the usual cause. Make them 301, then point links at the destination.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
