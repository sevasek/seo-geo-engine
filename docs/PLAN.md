# Phased plan

The README already states the end state. This document is the
engineering path from "the engine works on a synthetic profile" to
"point this at a real site repo and an agent can take the score from
wherever it starts to a verified result."

## Goal (what "up and running" means)

The product is not a nicer audit report. It is a **website-agnostic
loop** you attach to any number of your own site repos, each as a thin
profile:

1. **Crawl** — live URL, or the site's own repo booted locally.
2. **Score** against the effective standard (engine defaults + that
   profile's extensions).
3. **Work the ranked remediation queue** — draft what's mechanically
   draftable from crawl data; follow playbooks for editorial or
   access-gated work; mark status as you go.
4. **Re-crawl and confirm the verdict actually flipped**, not just that
   a fix was applied.
5. Repeat until the score reflects reality, then again next quarter as
   the standard evolves.

A new client site should be a `site.yaml` and maybe a handful of
extension rows — not a new fork of this repo.

That loop is the definition of done for "up and running." Shipping an
MCP server, unblocking every GEO row, or migrating both legacy audits
are means to that loop, not substitutes for it.

## What's already built

The engine is a Python package (`seo-geo-engine` 0.1.0) plus a
packaged Playwright crawler. A synthetic profile
(`examples/sample-profile/`, "Acme Example Co") proves the pieces
compose. Fast tests run in GitHub Actions on every PR; slow crawler
tests run on pushes to main.

### The scoring triangle

```
standard/default/*.md  --(ID)-->  @check(id)  --(verdict)-->  report
                                      |
                                      v
                              remediation-plan.md
                              @remediate / manual
```

- **Standard.** Markdown tables under `seo_geo_engine/standard/default/`.
  41 default rows across 11 categories. A profile's
  `standard/extensions.md` merges in afterwards; same ID replaces the
  engine row (reweight / reword / restatus); a fresh ID adds a rule.
  `disabled_ids` in `site.yaml` drops a row only with a non-empty
  reason.
- **Checks.** Every function is `@check("ID")` and
  `(site: dict) -> CheckResult`. Profile facts arrive as
  `site["profile"]`, never as a second parameter or a module-level
  constant. 32 rows are `status: open` with a real implementation; 9
  are `status: blocked` stubs whose unblock requirement lives in the
  standard row, not in the check.
- **Scoring.** Weighted, partial-credit. Points earned come from one
  function (`_points_earned`). Blocked items count their full weight in
  the denominator and earn zero. Top issues and the remediation queue
  rank by the same points-lost number.
- **Reports.** Markdown + JSON from `seo_geo_engine.report`; a
  deterministic static HTML dashboard from `render_html_report`.
  Nothing in that pipeline is AI-authored.

### Crawl

`seo_geo_engine/crawler/crawl.js` is a real-browser crawl. It takes a
sitemap (or a pages file), strips chrome before `bodyText`, captures
internal hrefs including in-content vs nav, resolves redirects, and
computes a no-JS word count. Python `crawl/run.py` shells out to it
against `base_url`, or boots `local_dev.start_command` and crawls
localhost through the identical pipeline.

The crawler does **not** fetch PageSpeed Insights, Search Console, or
external-presence data. Those keys exist on the site dict
(`pageSpeed`, `searchConsole`, `externalPresence`) and checks already
read them. `seo-geo-enrich` is the post-crawl merge that writes
`pageSpeed` / `searchConsole`; `externalPresence` stays unused. See
[design/enrichment.md](design/enrichment.md) and
[design/data-contract.md](design/data-contract.md).

### Remediation

The tracking layer, engine-owned remediations, and the commands that
make a new profile operable are shipped:

- `@remediate` / `manual` registry with `origin` (`engine` then
  `profile` may overwrite).
- Default playbook per shipped standard ID under
  `seo_geo_engine/remediation/playbooks/`, plus SCHEMA-001 and OG-002
  script handlers. A profile's `handlers.py` only registers extension
  IDs (and optional CMS-specific overrides).
- `seo-geo-plan-sync` bootstraps and prunes `remediation-plan.md` from
  the current non-passing set (empty plans are legal).
- `seo-geo-remediate --id` runs a script handler and writes
  `audits/artifacts/<date>/<ID>.txt`. It does not publish and does not
  call `update_status`.
- `seo-geo-update-status` is the CLI for `update_status()`.

See [design/engine-owned-remediation.md](design/engine-owned-remediation.md).

### Agent-facing surface

- A Skill template (`skills/seo-geo-audit-template/SKILL.md`)
  scaffolded into `.claude/skills/seo-geo-audit/SKILL.md`.
- A PR-review routine template, likewise copied in.
- `seo-geo-init-profile` produces a profile that passes its own
  generated traceability test with zero hand-written logic beyond
  `site.yaml`.

The Skill tells an agent which commands to run. It does not close the
loop: there is no verify-the-flip command and no single orchestrator.
Enrichment is a separate command (`seo-geo-enrich`) after crawl; see
[design/enrichment.md](design/enrichment.md).

### Tests

- Layer 1: every open default check has known-good / known-bad JSON
  fixtures (`tests/fixtures/checks/<ID>/`). Completeness gate fails CI
  if an open check ships without them.
- Layer 2 (slow): a deliberately-broken static site crawled by the real
  Playwright crawler. Pilot subset only (META-002, HEAD-002,
  SCHEMA-001, LINK-005, CRAWL-001).
- Local-serve: boot a command, crawl localhost, confirm teardown.
- Profile merge, scoring arithmetic, sample-profile remediation
  traceability, crawler unit tests (pure helpers, no browser).
- Site-dict JSON Schema (`seo_geo_engine/crawler/site-dict.schema.json`)
  against Layer 1 fixtures, the sample crawl, and the Layer 2 live crawl.
- Engine-default remediations (every shipped ID has a handler; every
  engine manual has a playbook file).
- `seo-geo-plan-sync`, `seo-geo-remediate --id`, `seo-geo-update-status`,
  and the scaffold's engine repo URL.
- `seo-geo-enrich` against recorded PSI/GSC fixtures (no live Google).

GitHub Actions runs fast `pytest` plus crawler unit tests on every PR;
`pytest -m slow` (Playwright Chromium) on pushes to main. Default
`pytest` still excludes `slow`. Playwright Chromium is a separate
`npx playwright install` — `pip install -e ".[dev]"` is not enough to
run a real crawl.

### Explicitly not built (from the README)

- MCP server (`[project.optional-dependencies] mcp` is declared;
  there is no server module). Deferred on purpose — see
  [design/mcp.md](design/mcp.md).
- Migration of `auto-ps-seo-audit` and `sevasek-com-seo-audit` — they
  still run forked copies. See
  [design/profile-migration.md](design/profile-migration.md).
- An engine versioning / compatibility policy. Not decided until this
  doc set. See [design/versioning.md](design/versioning.md).

### Honest gaps that the README doesn't spell out

These are the reasons you cannot yet point this at a third site and
walk away (Phase 1 closed the operable-queue gaps; Phase 2 closed the
enrichment producer):

| Gap | Why it still blocks the loop |
|---|---|
| Enrichment needs credentials | PERF-002, PERF-003, CRAWL-008 still runtime-block on a crawl-only JSON. `seo-geo-enrich` writes the blobs when keys are present. |
| No verify-the-flip tool | Status can be set to `verified` without a re-crawl. The Skill says not to; the engine doesn't enforce it. Phase 4. |
| Global `REGISTRY` | Importing two profiles in one process would collide on ID. Fine for CLI-per-profile; a future MCP/multi-site runner would not be. |
| 9 blocked default rows | They occupy weight in the score with no path to earn it. A new site starts with a structural hole (CONTENT-004–008, LINK-006–008, PERF-004). |
| LINK ID gap | Engine linking starts at LINK-004. LINK-001/002 live in the sample profile. LINK-003 does not exist. Leave it; don't backfill. |

None of these are reasons to redo the architecture. The split
(engine package + per-site profile, one `@check` per row, one
remediation per non-passing ID, deterministic reports) is the right
shape. The work is to make the loop operable, then run it on a real
site before adding surface area (MCP, more GEO heuristics).

## Phased plan

Phases are sequential where a later phase consumes a decision from an
earlier one. They are not calendar estimates. A phase is done when its
exit criterion is true, including tests.

### Phase 0 — already done (this repo today)

**Exit criterion:** the synthetic profile scores, the queue ranks, the
HTML dashboard renders, Layer 1 fixtures exist for every open default
check, Layer 2 crawler integration and local-serve are proven, a
brand-new scaffolded profile passes its generated test.

Shipped. Do not reopen by adding features here that belong in later
phases.

### Phase 1 — make a new profile operable (shipped)

This is "getting it up and running" for a *new* site that is willing
to live with blocked enrichment-backed rules.

**Shipped:** crawl data contract + schema; engine-owned remediations
for every default ID; `seo-geo-plan-sync`; `seo-geo-remediate --id`;
`seo-geo-update-status`; GitHub Actions CI; scaffold engine URL +
Skill pointers at `docs/design/`; engine-default remediation
traceability. See the **Build** list below as the decision record.

**Exit criterion (met):** `seo-geo-init-profile`, fill in `site.yaml`,
score a crawl (no PSI/GSC keys), generate the report + plan + queue,
run one script handler, mark a status via CLI, regenerate the HTML
dashboard — all without copying engine code into the profile. Fast
tests stay green in CI.

A blocked PERF-002 on that first crawl is expected and acceptable.
Un-blocking it is Phase 2.

**Build (what landed):**

1. **Crawl data contract** — write down the site-dict shape the
   crawler emits and checks already depend on. Treat it as the
   interface. See [design/data-contract.md](design/data-contract.md).
2. **Engine-owned remediations** for default IDs: generic playbooks
   (CMS-field-agnostic: "what to change," not "which WordPress
   metabox") plus the two script handlers that are already generic
   (SCHEMA-001, OG-002). Profiles override by ID the same way they
   override standard rows. See
   [design/engine-owned-remediation.md](design/engine-owned-remediation.md).
3. **Plan bootstrap / prune** — a command that, given a crawl +
   profile, writes `remediation-plan.md` rows for currently
   non-passing IDs (preserving existing status/notes) and removes
   rows whose verdict is now `pass`. This is what makes
   "re-crawl, confirm flip, delete the row" mechanical instead of a
   Skill instruction.
4. **Run a script handler** — `seo-geo-remediate --id` invokes
   `@remediate` and writes `audits/artifacts/<date>/<ID>.txt`.
5. **CLI for `update_status`** — `seo-geo-update-status`.
6. **CI** — GitHub Actions: `pytest` (fast) on every PR; `pytest -m
   slow` plus `node --test` on main or a nightly. Document Playwright
   install as a required crawl prerequisite, not a silent extra.
7. **Fix the scaffold** — real engine repo URL in the generated
   README; copy or reference engine playbooks so the empty-plan
   problem doesn't recur; Skill no longer points at missing
   enrichment docs (point here instead).
8. **Traceability triangle for engine defaults** — once engine
   remediations exist, an engine test that every *open, currently
   non-passing-on-the-sample-or-badseo* default ID has a handler. Do
   not require a remediation row for a rule that is passing on every
   fixture; remediations track *current* fails, not every ID in the
   abstract.

### Phase 2 — enrichment so "open" rules can actually pass (shipped)

PERF-002, PERF-003, and CRAWL-008 are labeled `open` because a
reliable automated signal *exists* — it just isn't the crawler. Until
something writes `pageSpeed` / `searchConsole` onto the site dict, they
runtime-block and occupy score weight as a hole.

**Build (what landed):** the post-crawl enricher specified in
[design/enrichment.md](design/enrichment.md) — `seo-geo-enrich`
`--pagespeed` / `--gsc`, optional `[enrich]` extra for GSC client
libs. Credentials stay in the environment (or an env-var *name* in
the profile), never in the engine. The crawler stays auth-free.

Also in this phase: the three kinds of "blocked" (no signal / missing
enrichment / needs a profile map) in
[design/blocked-rules.md](design/blocked-rules.md), treated as
accepted.

**Exit criterion (met):** the sample profile's hand-written
`pageSpeed` blocks are reproduced by the enricher against a recorded
PSI fixture (mocked API, no live Google). `--pagespeed` against
localhost / `.test` is refused. PERF-002 on a public URL, given a
key (tests mock HTTP), returns pass/fail rather than blocked.

### Phase 3 — versioning, then one real migration

Do not migrate a living audit onto this package without a pin story.
[design/versioning.md](design/versioning.md) is the decision; this
phase implements it:

- Declare 0.x semver rules in the README / CHANGELOG.
- CHANGELOG records standard IDs added, removed, or reweighted.
- Sample profile is the compatibility canary: it must stay green
  against the engine version it claims.

Then migrate **one** of the two forked repos — whichever is smaller
or more typical; the design doc's recommendation is `auto-ps-seo-audit`
first only if its extra surface area is smaller in practice, otherwise
pick the one whose `checks_ext.py` is the cleaner split. The procedure
is [design/profile-migration.md](design/profile-migration.md). Do not
migrate both in parallel: the first migration is how we find out
whether the engine/profile split actually holds.

**Exit criterion:** one real site is a profile depending on this
package (editable pin during co-development, version pin after). Its
own tests are green. A live crawl + report + queue run has been
regenerated from the engine, not from leftover forked `report.py`. The
old forked copies of `framework.py` / `standard_loader.py` /
`report.py` are gone from that repo.

### Phase 4 — close the agent loop on that real site

Only after Phase 3, because a Skill working a synthetic queue teaches
the wrong lessons (playbooks that say "this is illustrative").

**Build:** the operator path in [design/agent-loop.md](design/agent-loop.md):

- One orchestrator CLI (`seo-geo-run` or equivalent): crawl → optional
  enrich → report → bootstrap/prune plan → queue → HTML.
- `seo-geo-verify` (or a mode of report): diff two dated JSON reports,
  list IDs whose verdict changed, refuse to treat `update_status(...,
  "verified")` as meaningful unless the after-report says `pass`.
- Skill rewrite against those commands, using the migrated profile as
  the worked example (the Skill itself stays templated / org-name
  substituted — the *procedure* is what gets real).
- Optionally wire the PR-review routine to that profile's CI.

Work the queue for real: at least one script artifact applied and
verified by re-crawl, and at least one manual playbook followed to a
flipped verdict. That is the proof the engine was generalized *from*
those two repos rather than merely extracted.

**Exit criterion:** on the migrated profile, an agent following only
the scaffolded Skill (plus engine docs) can take a non-passing item
to a verified pass without being told extra procedure in chat.

### Phase 5 — second migration + standard evolution

Migrate `sevasek-com-seo-audit` the same way. Anything that turned out
to be generic during Phase 3/4 (a check that didn't need a business
fact) moves into engine defaults with a fixture pair; anything that
needed a URL or cluster map stays in that profile's extensions.

Then, and only then, consider growing the default standard — new
site-agnostic rows with real `@check` implementations and Layer 1
fixtures. Do not add rows to "look more GEO" if they would be blocked
stubs. See [design/blocked-rules.md](design/blocked-rules.md) for
which currently-blocked rows may grow a real check (profile-supplied
maps) versus which must wait for a method that does not exist.

**Exit criterion:** both legacy audits are profiles on this engine.
The engine's default standard has not grown a new blocked stub in the
process.

### Phase 6 — MCP, if the Skill path was actually used

Build the server in [design/mcp.md](design/mcp.md) only after Phase 4's
exit criterion is true. It is a thin wrapper over the same functions
the CLI already exposes. If Phase 4 never happened, skip this phase
indefinitely — that is an explicit README position, not a backlog
item rotting.

## What not to do

- Don't add engine default rows that name a business, URL, or CMS.
- Don't unblock CONTENT-005/006/007/008 with a regex that hasn't been
  tested on real crawl output. A plausible heuristic is not a method.
- Don't hand-edit generated reports or the HTML dashboard.
- Don't build a hosted artifact/dashboard product. The static file is
  the product.
- Don't give the engine CMS write access. Script remediations draft;
  humans (or a profile-owned, out-of-engine apply step) publish.
- Don't fork this repo per site. If a change needs a business fact, it
  belongs in that site's profile.
- Don't ship MCP, a web UI, or a multi-site runner before one real
  profile has completed the loop.

## How to use this document

When a new idea shows up, put it in a phase or reject it against "What
not to do." If it needs a design decision, add or amend a file under
`docs/design/` *before* writing the code — the files in this directory
are the decisions, not a promise that the code already matches them.
After a phase lands, update the README Status checklist and this
plan's "What's already built" so the three can't drift.
