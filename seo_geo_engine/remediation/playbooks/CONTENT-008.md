# CONTENT-008 — Factual claims are backed by a citable source.

**Rule:** Factual claims are backed by a citable source.

**Evidence the check emits:** None from a crawl. The check is a blocked stub.

**Kind of change that flips it:** Not assessable without a claims/sources map or a method that tells unsupported claims from sourced ones.

**Depends on:** `CLAIMS-SOURCES-MAP`

Do not treat the presence of any `<a href>` as a citation. Unblock is either a profile-supplied claims map or a method that actually distinguishes a source from a nav link.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
