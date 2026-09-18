# SCHEMA-001 — Every service page carries `Service` JSON-LD structured data.

**Rule:** Every service page carries `Service` JSON-LD structured data.

**Evidence the check emits:** Service-page URLs whose `jsonLdTypes` does not include `Service`.

**Kind of change that flips it:** Add a Service JSON-LD block built from the page title, URL, and org name already in the crawl.

**Depends on:** `—`

This ID has a **script** handler: `seo-geo-remediate <crawl.json> --profile site.yaml --id SCHEMA-001`. It drafts JSON-LD from crawl fields and does not invent a service description. Paste the artifact into the page; the engine will not publish it.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
