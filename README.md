# seo-geo-engine

A website-agnostic SEO/GEO audit-and-remediation engine: a weighted rule
standard, a check registry, a remediation-tracking layer, and a plain
static-file report/dashboard generator — all driven by a per-site
**profile** instead of being forked per site.

This engine generalizes a pattern proven across two real, site-specific
audit repos (one per business): a testable `standard.md` of weighted rules,
one `@check(id)` function per rule, a bidirectionally-enforced test suite
(no rule without a check, no check without a rule), a remediation-tracking
layer mapping every non-passing rule to a tracked fix, and a deterministic
report/HTML dashboard generator. Everything specific to one business — base
URL, entity/topical clusters, contact-info patterns, extra standard rows —
lives in a **profile** (a `site.yaml` + a small Python module), not in the
engine.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                                    # engine's own test suite

# Score the synthetic "Acme Example Co" sample profile against the engine
python3 -m seo_geo_engine.report \
    examples/sample-profile/fixtures/site-crawl-sample.json \
    2026-09-10 "Acme Example Co (synthetic)" \
    --profile examples/sample-profile/site.yaml \
    --out-dir /tmp/acme-audit

python3 -m seo_geo_engine.render_html_report \
    /tmp/acme-audit/data/standard-report-2026-09-10.json \
    /tmp/acme-audit/standard-report-2026-09-10.html \
    --eyebrow "SEO / GEO Standard  ·  Acme Example Co" --title "SEO Scorecard"
```

The HTML dashboard is a plain, deterministic static file — open it directly,
serve it with `python3 -m http.server`, or push it to any static host.
Nothing in the scoring/report/dashboard pipeline is AI-authored or
AI-interpreted, and it's never published through a hosted "Artifact"
system — that's a deliberate design choice, not an oversight.

## How a profile works

A profile is a directory with:
- `site.yaml` — base URL, entity/topical clusters, contact-info patterns,
  crawl settings, local-dev boot instructions, and paths to any standard
  extension files.
- `standard/extensions.md` (optional) — extra standard rows in the same
  table format the engine's own defaults use. A row with the same ID as an
  engine default overrides it (reweight/reword/disable); a fresh ID adds a
  genuinely new rule.
- `checks_ext.py` (optional, importable as `checks_module` from
  `site.yaml`) — one `@check(id)` per extension row, importing the same
  `seo_geo_engine.checks.framework` decorator the built-in checks use.

See [`examples/sample-profile/`](examples/sample-profile/) for a complete,
synthetic worked example ("Acme Example Co" — not a real business).

## What's in this repo

```
seo_geo_engine/            — the installable package
  checks/                  — @check registry + built-in, non-business-specific checks
  profile.py                — SiteProfile: loads site.yaml, merges standard + site dict
  report.py                  — scoring, top-issues ranking, markdown/JSON report, CLI
  render_html_report.py      — deterministic static HTML dashboard generator
  remediation/                — remediation-tracking layer (mirrors checks/)
  crawl/                      — crawler CLI + local-serve-and-crawl mode
  crawler/                    — the packaged Playwright crawler (crawl.js)
  testing/                    — reusable pytest assertions a profile can import
  standard/default/           — the engine's shipped, non-business-specific rule set
  skills/, routines/           — Skill/governance-routine templates a profile scaffolds
  scaffold/                    — `seo-geo-init-profile` — scaffold a new profile
tests/                        — the engine's own test suite (fixtures + traceability)
examples/sample-profile/       — synthetic worked example, not a real dependent
```

## Status

Built in phases — see the project's own issue/PR history for what's live.
