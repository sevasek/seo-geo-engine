# SCHEMA-002 — Every service page with visible FAQ content carries matching `FAQPage` JSON-LD.

**Rule:** Every service page with visible FAQ content carries matching `FAQPage` JSON-LD.

**Evidence the check emits:** Service-page URLs. The shipped check currently requires FAQPage on every service page (it does not detect visible FAQ copy).

**Kind of change that flips it:** Add FAQPage JSON-LD that matches the on-page FAQ, or add both the FAQ copy and the JSON-LD together.

**Depends on:** `CMS-ACCESS`

Do not invent FAQ answers in the JSON-LD that are not on the page — that is the failure mode this rule exists to catch. If a service page has no FAQ, either add a real FAQ or accept that the current check still wants the type present; a profile that disagrees should override this playbook, not weaken the check in the engine.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
