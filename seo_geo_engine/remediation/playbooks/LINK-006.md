# LINK-006 — External links only point to responsible/authoritative sources.

**Rule:** External links only point to responsible/authoritative sources.

**Evidence the check emits:** None from a crawl. The check is a blocked stub.

**Kind of change that flips it:** Not assessable without a policy defining 'responsible'.

**Depends on:** `LINK-POLICY`

Unblock is a profile-supplied policy (relevance/authority criteria) and a check that applies it. A blocklist of spam domains is not that policy.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
