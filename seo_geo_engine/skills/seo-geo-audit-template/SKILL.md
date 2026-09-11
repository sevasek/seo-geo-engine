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
   requirement if not) — then a matching `@check(...)` in `checks_ext.py`.
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

Optional enrichment is a separate, profile-invoked step after crawl
(PageSpeed Insights, Search Console). Either flag may be omitted —
without it, PERF-002, PERF-003, and CRAWL-008 stay runtime-blocked:

```bash
seo-geo-enrich audits/data/site-crawl-<date>.json \
    --profile site.yaml \
    --pagespeed \
    --gsc
```

`--pagespeed` needs `PAGESPEED_API_KEY` (or the env var named by
`profile.enrichment.pagespeed_api_key_env`) and is refused for
localhost / `.test` / private IPs. `--gsc` needs
`pip install seo-geo-engine[enrich]` plus ADC or `GSC_CREDENTIALS_JSON`,
and `profile.enrichment.gsc_property`. Default `--out` overwrites the
crawl JSON in place. See `docs/design/enrichment.md`.

## 3. Regenerate the report + remediation queue

```bash
python3 -m seo_geo_engine.report audits/data/site-crawl-<date>.json <date> "{{ORG_NAME}}" \
    --profile site.yaml --out-dir audits

python3 -m seo_geo_engine.remediation.plan audits/data/site-crawl-<date>.json <date> \
    --profile site.yaml --out-dir audits
```

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
registered handler in `handlers.py` (a `script` that drafts real fix
content from crawl data, or `manual` pointing at a `playbooks/<ID>.md`
procedure). Update a row's status as you work it — never hand-edit the
Status/Notes cells directly:

```python
from seo_geo_engine.remediation.remediation_loader import update_status
update_status("SCHEMA-001", "in-progress", "remediation-plan.md", notes="Drafted, awaiting CMS access.")
```

An item only stays in `remediation-plan.md` while it's non-passing — once a
re-crawl flips its verdict to `pass`, delete the row and its handler/playbook.
`pytest` enforces both directions.
