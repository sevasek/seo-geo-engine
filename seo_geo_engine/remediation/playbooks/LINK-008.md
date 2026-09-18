# LINK-008 — Internal link authority flows to newly published pages.

**Rule:** Internal link authority flows to newly published pages.

**Evidence the check emits:** None from a crawl. The check is a blocked stub.

**Kind of change that flips it:** Not assessable from a single crawl snapshot without a defined set of 'new' pages and a linking policy.

**Depends on:** `NEW-PAGE-POLICY`

Unblock needs a new-page list (or a publish-date rule) and a policy for how they get in-content links. A crawl cannot know what 'new' means on its own.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
