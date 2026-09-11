# LINK-007 — Outbound links carry appropriate `rel` attributes (`nofollow`/`sponsored`/`ugc`) where warranted.

**Rule:** Outbound links carry appropriate `rel` attributes (`nofollow`/`sponsored`/`ugc`) where warranted.

**Evidence the check emits:** None from a crawl. The check is a blocked stub.

**Kind of change that flips it:** Not assessable without a policy on when which `rel` applies.

**Depends on:** `REL-POLICY`

Unblock is a written policy (affiliate → sponsored, user comments → ugc, etc.) plus a check. Nofollowing every outbound link is not a pass.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
