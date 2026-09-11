---
name: seo-geo-audit
description: Audit {{ORG_NAME}}'s site for SEO and GEO (generative-engine/AI-answer) health, and produce a prioritized, actionable remediation report. Use when asked to audit, assess, review, or improve the site's SEO/GEO, add a new SEO/GEO rule or "angle" to the standard, or check AI-answer/citation readiness.
---

# {{ORG_NAME}} — SEO/GEO audit

This profile's standard is the engine's shipped defaults
(`seo_geo_engine/standard/default/*.md`) plus this profile's own
`standard/extensions.md` — see `seo-geo-engine`'s own `CLAUDE.md` for the
decision procedure on which one a new rule belongs in. This file assumes
that repo is installed (`pip install seo-geo-engine`, or an editable local
checkout during co-development).

## 1. Evolving the standard

When a new SEO/GEO angle comes up (a tweet, a competitor page, a piece of
Google guidance):

1. Does an existing row already claim this ground? If a check has a bug
   letting a real case through, fix the check — don't add a row.
2. Is it a sub-angle of a broader existing rule? Split only if it can
   genuinely diverge from the parent (pass while the parent fails, or vice
   versa).
3. Otherwise: add a row to `standard/extensions.md` with a fresh
   `CATEGORY-NNN` ID, a plain-English rule, a source, a weight (1-5), and a
   status (`open` if assessable today, `blocked` with a real unblock
   requirement if not) — then a matching `@check(...)` in `checks_ext.py`
   and a `@remediate` / `manual(...)` in `handlers.py`.
4. Run `pytest`. Regenerate the report.

If in doubt whether something is an engine-default candidate (genuinely
site-agnostic) vs. this profile's own extension (needs a fact specific to
{{ORG_NAME}}), it's almost always the latter — see `seo-geo-engine`'s
`CLAUDE.md`.

## 2. Gathering data

Live URL:

```bash
python3 -m seo_geo_engine.crawl.run --profile site.yaml --out audits/data/site-crawl-<date>.json
```

A website repo, before it's deployed (needs `local_dev` configured in
`site.yaml`):

```bash
python3 -m seo_geo_engine.crawl.run --profile site.yaml --local --out audits/data/site-crawl-<date>.json
```

The crawl writes a site dict whose shape is the engine's data contract
(`seo_geo_engine/crawler/site-dict.schema.json`, documented in
`docs/design/data-contract.md`). Checks never fetch; if a field is missing
they skip, fail, or return `blocked`.

A real crawl needs Playwright Chromium in the engine's `crawler/` directory
(`npm install` and `npx playwright install chromium`). `pip install` is not
enough for that step.

Optional enrichment (PageSpeed Insights, Search Console) is a separate,
profile-invoked step that merges keys into the same JSON — see
`docs/design/enrichment.md`. Until that runs, PERF-002, PERF-003, and
CRAWL-008 return `blocked` on a crawl-only dataset; that is expected.

## 3. Regenerate the report + remediation queue

```bash
python3 -m seo_geo_engine.report audits/data/site-crawl-<date>.json <date> "{{ORG_NAME}}" \
    --profile site.yaml --out-dir audits

seo-geo-plan-sync audits/data/site-crawl-<date>.json --profile site.yaml

python3 -m seo_geo_engine.remediation.plan audits/data/site-crawl-<date>.json <date> \
    --profile site.yaml --out-dir audits
```

`seo-geo-plan-sync` appends rows for currently non-passing IDs and deletes
rows whose verdict is now `pass`. That is the mechanical form of "re-crawl,
confirm the flip, drop the row." Do not add or delete plan rows by hand.

Optional static HTML dashboard (plain, deterministic, never AI-authored,
never published through a hosted "Artifact" system — open it directly or
serve it with any static host):

```bash
python3 -m seo_geo_engine.render_html_report \
    audits/data/standard-report-<date>.json audits/standard-report-<date>.html \
    --eyebrow "SEO / GEO Standard  ·  {{ORG_NAME}}" --title "SEO Scorecard"
```

## 4. Working the remediation queue

Every non-passing item has exactly one row in `remediation-plan.md` and one
registered handler — usually an engine default (generic playbook, or a
script for SCHEMA-001 / OG-002). `handlers.py` in this profile is only for
extension IDs and CMS-specific overrides.

To draft a script artifact:

```bash
seo-geo-remediate audits/data/site-crawl-<date>.json <date> \
    --profile site.yaml --id SCHEMA-001 --out-dir audits
```

That writes `audits/artifacts/<date>/<ID>.txt`. It does not publish, and it
does not change the plan row. After you paste or commit the draft, mark
status via the CLI — never hand-edit the Status/Notes cells:

```bash
seo-geo-update-status SCHEMA-001 in-progress --plan remediation-plan.md \
    --notes "Drafted, awaiting CMS access."
```

An item only stays in `remediation-plan.md` while it's non-passing — once a
re-crawl flips its verdict to `pass`, `seo-geo-plan-sync` deletes the row.
`pytest` enforces plan rows ↔ current non-passing set.
