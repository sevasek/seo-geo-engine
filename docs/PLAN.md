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
compose. As of the README's last count: 103 tests green (85 fast + 2
slow Python, 16 JS).

**Versioning.** Semver on the package; 0.x is treated like 1.x for
compatibility. `CHANGELOG.md` records standard-ID and crawl-contract
deltas. Profiles pin `seo-geo-engine>=0.1,<0.2`. The sample profile is
the 0.1.x compatibility canary (`pytest` in this repo). See
[design/versioning.md](design/versioning.md). Not on PyPI; `1.0.0`
waits until a real profile has migrated.

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
read them — the scripts that fill them do not exist yet. See
[design/enrichment.md](design/enrichment.md) and
[design/data-contract.md](design/data-contract.md).

### Remediation (half-built)

The *tracking* layer is real: `@remediate` / `manual` registry,
`remediation-plan.md` loader, `update_status()` so an agent doesn't
hand-edit table cells, a points-lost queue (`seo-geo-remediate` today
only *renders* that queue). The sample profile has two script handlers
(SCHEMA-001, OG-002) and a playbook per remaining non-passing ID.

What is **not** in the engine:

- No default playbooks or handlers for the 41 shipped rules. A
  brand-new `seo-geo-init-profile` scaffold gets an empty
  `remediation-plan.md` and empty `handlers.py`. The first real audit
  produces fails with nothing to work.
- No command that *runs* a script handler and writes its artifact.
- No command that bootstraps or prunes `remediation-plan.md` from the
  current non-passing set. The sample plan was authored to match its
  fixture by hand.
- Profile-level traceability (every non-passing ID has a row and a
  handler) exists for the sample; CLAUDE.md's "standard ↔ check ↔
  remediation" triangle for engine defaults is still waiting on
  engine-owned remediations.

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
Enrichment contracts now live in `docs/design/enrichment.md`; the
scripts themselves do not exist yet.

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

There is no GitHub Actions (or other CI) config in this repo yet.
Default `pytest` excludes `slow`. Playwright Chromium is a separate
`npx playwright install` — `pip install -e ".[dev]"` is not enough to
run a real crawl.

### Explicitly not built (from the README)

- MCP server (`[project.optional-dependencies] mcp` is declared;
  there is no server module). Deferred on purpose — see
  [design/mcp.md](design/mcp.md).
- Migration of `auto-ps-seo-audit` and `sevasek-com-seo-audit` — they
  still run forked copies. See
  [design/profile-migration.md](design/profile-migration.md).

### Honest gaps that the README doesn't spell out

These are the reasons you cannot yet point this at a third site and
walk away:

| Gap | Why it blocks the loop |
|---|---|
| Engine-owned remediations missing | A new profile has a score and a list of fails, not a workable queue. |
| No plan bootstrap | `remediation-plan.md` must be hand-kept in sync with whatever the latest crawl failed. |
| Enrichment scripts missing | PERF-002, PERF-003, CRAWL-008 are `status: open` but return `blocked` on an un-enriched crawl. The sample fixture cheats by embedding `pageSpeed` by hand. |
| No verify-the-flip tool | Status can be set to `verified` without a re-crawl. The Skill says not to; the engine doesn't enforce it. |
| No crawl JSON schema | Checks, fixtures, and the crawler agree by convention. Enrichment and profile authors currently reverse-engineer fixtures. |
| Global `REGISTRY` | Importing two profiles in one process would collide on ID. Fine for CLI-per-profile; a future MCP/multi-site runner would not be. |
| 9 blocked default rows | They occupy weight in the score with no path to earn it. A new site starts with a structural hole (CONTENT-004–008, LINK-006–008, PERF-004). |
| LINK ID gap | Engine linking starts at LINK-004. LINK-001/002 live in the sample profile. LINK-003 does not exist. Leave it; don't backfill. |
| No CI | The 103-test claim is a local fact, not a gate. |
| Scaffold README github URL is a stub | `seo-geo-init-profile` writes `https://github.com/` as the engine link. |

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

### Phase 1 — make a new profile operable

This is "getting it up and running" for a *new* site that is willing
to live with blocked enrichment-backed rules.

**Build:**

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
4. **Run a script handler** — `seo-geo-remediate` (or a sibling)
   actually invokes `@remediate` and writes the artifact to a dated
   audits directory. Today it only prints the queue.
5. **CLI for `update_status`** — the function exists; agents currently
   have to write a Python snippet.
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

**Exit criterion:** `seo-geo-init-profile`, fill in `site.yaml`, crawl
a real URL (no PSI/GSC keys), generate the report + plan + queue, run
one script handler, mark a status via CLI, regenerate the HTML
dashboard — all without copying engine code into the profile. Fast
tests stay green in CI.

A blocked PERF-002 on that first crawl is expected and acceptable.
Un-blocking it is Phase 2.

### Phase 2 — enrichment so "open" rules can actually pass

PERF-002, PERF-003, and CRAWL-008 are labeled `open` because a
reliable automated signal *exists* — it just isn't the crawler. Until
something writes `pageSpeed` / `searchConsole` onto the site dict, they
runtime-block and occupy score weight as a hole.

**Build:** the post-crawl enricher specified in
[design/enrichment.md](design/enrichment.md). Credentials stay in the
profile or the environment, never in the engine. The crawler stays
auth-free.

Also in this phase, not later: document the three kinds of "blocked"
(no signal / missing enrichment / needs a profile map) so a future
contributor doesn't "unblock" CONTENT-005 with a naive keyword
counter. That's [design/blocked-rules.md](design/blocked-rules.md),
which this phase should treat as accepted.

**Exit criterion:** the sample profile's hand-written `pageSpeed`
blocks can be reproduced by the enricher against a fixture (mocked
API). A live crawl + enrich of the sample's local-site (PSI will
fail against localhost — that's fine) still scores the crawl-only
rules. PERF-002 on a public URL, given a key, returns pass/fail
rather than blocked.

### Phase 3 — versioning, then one real migration

**Versioning policy (implemented).** Do not migrate a living audit onto
this package without a pin story.
[design/versioning.md](design/versioning.md) is accepted:

- 0.x semver rules are declared in the README / CHANGELOG; 0.x is
  treated like 1.x for compatibility. Profiles pin
  `seo-geo-engine>=0.1,<0.2`.
- `CHANGELOG.md` records standard IDs added, removed, or reweighted,
  crawl-contract field changes, and profile migration notes.
- Sample profile is the compatibility canary: `pytest` in this repo
  runs it against 0.1.0.

Tags and GitHub releases are cut as we ship versions; the package is
not on PyPI yet. `1.0.0` remains a Phase 3 *exit* after a real
migration.

**Still not done:** migrate **one** of the two forked repos — whichever
is smaller or more typical; the design doc's recommendation is
`auto-ps-seo-audit` first only if its extra surface area is smaller in
practice, otherwise pick the one whose `checks_ext.py` is the cleaner
split. The procedure is
[design/profile-migration.md](design/profile-migration.md). Do not
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
