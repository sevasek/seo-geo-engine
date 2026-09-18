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

This Skill is the **runbook for auditing {{ORG_NAME}}**. How the engine
itself is built — goals, infrastructures (crawler, contract, scoring
triangle, remediations, verify, versioning), and what still needs
erecting — lives in that repo's `docs/SYSTEM.md`. Do not add engine
kernel code to this profile; if a change needs a business fact it
belongs here, otherwise it belongs in the engine.

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

One command gathers a dated snapshot and scores it. Do not reconstruct the
individual crawl/report/plan-sync/queue/HTML flags unless you are debugging
a single step.

Live URL (needs Playwright Chromium in the engine's `crawler/` directory —
`npm install` and `npx playwright install chromium`; `pip install` is not
enough for that step):

```bash
seo-geo-run --profile site.yaml --date <YYYY-MM-DD>
```

A website repo, before it's deployed (needs `local_dev` configured in
`site.yaml`):

```bash
seo-geo-run --profile site.yaml --local --date <YYYY-MM-DD>
```

Already have a crawl JSON (no live fetch):

```bash
seo-geo-run --profile site.yaml --from-crawl audits/data/site-crawl-<date>.json --date <YYYY-MM-DD>
```

Optional PageSpeed Insights / Search Console merge, after crawl, same
invocation — either token may be omitted; without it PERF-002, PERF-003,
and CRAWL-008 stay runtime-blocked. See `docs/design/enrichment.md`.

```bash
seo-geo-run --profile site.yaml --enrich pagespeed,gsc --date <YYYY-MM-DD>
```

`--pagespeed` needs `PAGESPEED_API_KEY` (or the env var named by
`profile.enrichment.pagespeed_api_key_env`) and is refused for localhost /
`.test` / private IPs. `--gsc` needs `pip install seo-geo-engine[enrich]`
plus ADC or `GSC_CREDENTIALS_JSON`, and `profile.enrichment.gsc_property`.

The crawl writes a site dict whose shape is the engine's data contract
(`seo_geo_engine/crawler/site-dict.schema.json`, documented in
`docs/design/data-contract.md`). Checks never fetch; if a field is missing
they skip, fail, or return `blocked`.

## 3. The report + remediation queue

`seo-geo-run` already wrote, under `--out-dir` (default `audits/`):

- `data/site-crawl-<date>.json`
- `standard-report-<date>.md` and `data/standard-report-<date>.json`
- `remediation-queue-<date>.md`
- `standard-report-<date>.html`

and synced `remediation-plan.md` (add currently non-passing IDs, delete
rows whose verdict is now `pass`). Do not hand-edit the generated report,
queue, or HTML dashboard — regenerate with another `seo-geo-run`. Do not
add or delete plan rows by hand; use `seo-geo-update-status` for
Status/Notes.

The HTML dashboard is a plain, deterministic static file — never
AI-authored, never published through a hosted "Artifact" system.

## 4. Working the remediation queue

Every non-passing item has exactly one row in `remediation-plan.md` and one
registered handler — usually an engine default (generic playbook, or a
script for SCHEMA-001 / OG-002). `handlers.py` in this profile is only for
extension IDs and CMS-specific overrides.

Crawls are slow. Batch a few `applied` items, then one re-run, then verify
the batch — do not re-crawl after every single ID.

Per ready item (no `depends_on`):

1. `seo-geo-update-status <ID> in-progress --plan remediation-plan.md`
2. If `script`:

   ```bash
   seo-geo-remediate audits/data/site-crawl-<date>.json <date> \
       --profile site.yaml --id <ID> --out-dir audits
   ```

   That writes `audits/artifacts/<date>/<ID>.txt`. It does not publish, and
   it does not change the plan row. Apply the artifact in the **website**
   repo or CMS (out of this profile). Committing it here instead of the
   site is a common miss — `seo-geo-verify` will then correctly show no
   flip, because the crawl is unchanged.
3. If `manual`: follow the playbook (engine default under
   `seo_geo_engine/remediation/playbooks/`, or a profile override in
   `playbooks/`).
4. `seo-geo-update-status <ID> applied --plan remediation-plan.md` only
   when the change is actually published or committed to the site, not
   when the artifact file is written. Use status `verified` only as the
   in-between "waiting on deploy/re-crawl" marker — the engine never sets
   it as a side-effect of drafting.
5. After a batch: `seo-geo-run` again with a **new** date (same date
   overwrites the snapshot).
6. Confirm the flip against the previous JSON report:

   ```bash
   seo-geo-verify \
       --before audits/data/standard-report-<old-date>.json \
       --after  audits/data/standard-report-<new-date>.json \
       --id <ID> \
       --require-not-worse
   ```

   `--id` exits 0 only if that ID is now `pass` or its earned fraction
   strictly increased. `--require-not-worse` exits 1 if any ID moved
   pass→fail or lost fraction. An unchanged crawl fails both, which is
   the correct failure.

An item only stays in `remediation-plan.md` while it's non-passing — once
a re-crawl flips its verdict to `pass`, `seo-geo-plan-sync` (inside
`seo-geo-run`) deletes the row. That is a stronger close than a Status
cell. `pytest` enforces plan rows ↔ current non-passing set.
