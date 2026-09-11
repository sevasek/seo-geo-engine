# seo-geo-engine

A website-agnostic SEO/GEO audit-and-remediation engine: a weighted rule
standard, a check registry, a remediation-tracking layer, and a plain
static-file report/dashboard generator — all driven by a per-site
**profile** instead of being forked per site.

## The end state this is building toward

The goal isn't a nicer audit report — it's a tool you point at *any number*
of your own website repos, each as a thin profile, and have an agent take
each one from wherever it starts to a genuinely strong, verified SEO/GEO
score, without you re-explaining the standard or forking a copy of the
engine per site.

The loop, once a profile exists for a site: **crawl** (live URL, or the
site's own repo booted locally and crawled before it's even deployed) →
**score** against the effective standard (engine defaults + that profile's
own rules) → **work the ranked remediation queue** — an agent drafts what's
mechanically draftable from crawl data, works down manual playbooks for
what needs editorial or access-gated judgment, and marks each item's status
as it goes → **re-crawl and confirm the verdict actually flipped**, not
just that a fix was applied. Repeat until the score reflects reality, then
repeat again next quarter as the standard itself evolves. A profile is
cheap enough to add that a new client site is a `site.yaml` and maybe a
handful of rows, not a new repo to maintain in lockstep with the last one.

This build is the engine and one worked example (`examples/sample-profile/`,
entirely synthetic). The two real site-specific repos this generalizes —
`auto-ps-seo-audit` and `sevasek-com-seo-audit` — still run their own
forked copy of the pattern and haven't been migrated onto this engine yet;
see "Status" below for exactly what that migration involves.

Underneath the loop above, the engine generalizes a pattern already proven
across those two real, site-specific audit repos: a testable `standard.md`
of weighted rules, one `@check(id)` function per rule, a
bidirectionally-enforced test suite (no rule without a check, no check
without a rule), a remediation-tracking layer mapping every non-passing
rule to a tracked fix, and a deterministic report/HTML dashboard generator.
Everything specific to one business — base URL, entity/topical clusters,
contact-info patterns, extra standard rows — lives in a **profile** (a
`site.yaml` + a small Python module), not in the engine.

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

- [x] Core: `@check` registry, multi-file standard merge (engine defaults +
      profile extensions, override-by-ID semantics), weighted
      partial-credit scoring, profile-aware report generation, a plain
      deterministic static HTML dashboard.
- [x] Remediation: `@remediate`/`manual` registry, points-lost-ranked
      queue, `update_status()` for agent-driven queue work instead of
      hand-editing `remediation-plan.md`.
- [x] Fixture-based test harness: 32 built-in checks each with a
      known-good/known-bad JSON fixture + a completeness gate (Layer 1),
      plus a real deliberately-broken static site crawled end-to-end by
      the real packaged crawler and a real headless browser (Layer 2).
- [x] Local-serve-and-crawl: boot a profile's own dev/build command and
      crawl `localhost` through the identical pipeline a live-URL audit
      uses — verified same output shape, confirmed port teardown.
- [x] Skill template + `seo-geo-init-profile` scaffold command — a
      brand-new profile passes its own generated test with zero
      hand-written logic beyond `site.yaml`. 103/103 tests green
      (85 fast + 2 slow Python, 16 JS) as of 2026-09-11.
- [x] Enrichment: `seo-geo-enrich` post-crawl merge of PageSpeed Insights
      (mobile lab LCP/CLS) and Search Console sitemap status. GSC client
      libs are `pip install seo-geo-engine[enrich]`; credentials stay in
      the environment. See
      [docs/design/enrichment.md](docs/design/enrichment.md).
- [ ] MCP server (`pip install seo-geo-engine[mcp]`) — deferred until the
      Skill-only path has been used for real; not required for the loop
      above to work today.
- [ ] Migrate `auto-ps-seo-audit` into a real profile depending on this
      engine (drop its own copy of `framework.py`/`standard_loader.py`/
      `report.py`/etc., keep only `site.yaml` + its business-specific
      `checks_ext.py`/`handlers.py`/`standard/extensions.md`/
      `remediation-plan.md`/`playbooks/`).
- [ ] Same migration for `sevasek-com-seo-audit`.
- [ ] An engine versioning/compatibility policy for those two migrations
      (semver, how a breaking rule-schema change reaches a profile pinned
      to an older tag) — not decided yet.
