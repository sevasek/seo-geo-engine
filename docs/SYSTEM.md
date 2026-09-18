# System map (for agents)

This is the orientation document for anyone — human or agent — landing
in **this repo**. It answers three questions the other docs assume:

1. **What is the goal, and what counts as an objective toward it?**
2. **What infrastructures exist or still need erecting?**
3. **How do those pieces relate** (data, ownership, sequencing)?

Read this before adding a feature, migrating a site, or inventing a
new surface (MCP, a UI, a multi-site runner). Sequencing of remaining
work is [PLAN.md](PLAN.md). Trade-offs for a single piece are under
[design/](design/). Working rules for *this* tree are
[`CLAUDE.md`](../CLAUDE.md).

A **profile** (a per-site directory or repo) is a different job. That
agent follows the scaffolded Skill, not this file. This file is how
the engine itself is supposed to be understood and extended.

---

## 1. What this project is

`seo-geo-engine` is a **shared kernel** for SEO/GEO audit-and-remediation.
It is not a website, not a CMS, not a hosted dashboard, and not one
client's audit.

The unit of attachment is a **profile**: a thin directory (`site.yaml`
plus optional extensions) that names one business. The engine scores
that profile's crawl against a weighted standard, ranks what to fix,
drafts what is mechanically draftable, and — after a new crawl —
checks whether a verdict actually flipped.

Two real audits already proved this pattern by forking it
(`auto-ps-seo-audit`, `sevasek-com-seo-audit`). This package exists so
the next site is a profile, not a third fork.

---

## 2. Goals, objectives, non-goals

### Goal (the product)

A website-agnostic **loop** you attach to any number of your own site
repos:

**crawl → score → work the ranked queue → re-crawl until the
verdict flips → repeat next quarter as the standard evolves.**

A new client site is a `site.yaml` and maybe a handful of extension
rows. An agent following only the scaffolded Skill (plus engine docs)
can take a non-passing item to a **verified pass** without being told
extra procedure in chat.

That loop is the definition of done for "up and running." MCP,
unblocking every GEO row, and migrating both legacy audits are
**means** to the loop, not substitutes for it.

### Objectives (measurable; status is honest)

| # | Objective | Status |
|---|---|---|
| O1 | Synthetic profile scores, queue ranks, HTML dashboard renders, Layer 1 fixtures exist for every open default check, Layer 2 crawler + local-serve proven, scaffolded profile passes its generated test. | **Met** (Phase 0). |
| O2 | A brand-new profile can be crawled, scored, queued, and worked with **no copy of engine code** in the profile. Engine-owned remediations, plan-sync, `--id` artifacts, `update-status` CLI, crawl schema, CI. | **Met** (Phase 1). |
| O3 | PERF-002 / PERF-003 / CRAWL-008 return pass/fail (not runtime-blocked) when credentials exist. Enricher is a post-crawl merge; crawler stays auth-free. | **Met on fixtures** (Phase 2). Live Google is not in the fast suite. |
| O4 | Compatibility policy a pinned profile can depend on (semver + CHANGELOG of IDs / crawl-contract). Then **one** real fork migrated onto this package. | **Not met.** Designed in [design/versioning.md](design/versioning.md) and [design/profile-migration.md](design/profile-migration.md). Versioning has a sibling PR; the migration is a different repo. |
| O5 | Engine operator path is one gather command + a verify command; Skill sequences them. | **Engine half met** (Phase 4 commands). |
| O6 | On a **migrated** profile, an agent following only the Skill takes at least one script item and one manual item to a verified pass (re-crawl, not a Status cell). | **Not met.** Blocked on O4. |
| O7 | Second legacy audit migrated the same way. Generic rules discovered during migration move into engine defaults with fixtures; business facts stay in that profile. Default standard does not grow a new blocked stub in the process. | **Not met** (Phase 5). |
| O8 | MCP server, only if O6 happened: thin wrapper over the same functions the CLI already exposes. | **Deferred** (Phase 6). Skip indefinitely if O6 never happens. |

Objectives are not calendar. An objective is done when its exit
criterion is true, including tests. Do not start O8 to make the
package look complete. Do not migrate both forks in parallel (O4 then
O7): the first migration is how we learn whether the split holds.

### Non-goals (do not erect)

- A hosted Artifact / SaaS dashboard. The static HTML file is the
  product.
- Engine write-access to a website CMS or website repo. Script
  remediations **draft**; apply is out of band.
- Engine default rows that name a business, URL, or CMS.
- Heuristic "unblocks" of Kind A stubs (CONTENT-005/006/008, PERF-004,
  …) without a method tested on real crawl output. See
  [design/blocked-rules.md](design/blocked-rules.md).
- Filling the LINK-001..003 ID gap in engine defaults. Those IDs are
  already used in the sample (and likely the forks). New linking
  rules start at LINK-009.
- Multi-profile-in-one-process until registries are isolated. v1 is
  one `--profile` per process.
- Hand-edited generated reports or HTML.

---

## 3. Repo constellation (the estates)

Three kinds of repo. Agents confuse them; verify then fails.

```
┌──────────────────────────┐     pip pin / editable install
│  seo-geo-engine          │◄────────────────────────────────┐
│  (THIS repo)             │                                 │
│  shared kernel           │                                 │
│  no business facts       │                                 │
└────────────┬─────────────┘                                 │
             │ scaffolds / is depended on                    │
             ▼                                               │
┌──────────────────────────┐     "apply artifact here"       │
│  <site>-seo-audit        │─────────────────────────────────┘
│  PROFILE repo            │
│  site.yaml, extensions,  │        ┌──────────────────────┐
│  plan, Skill, audits/    │        │  <website> repo/CMS  │
│  NOT the public site     │───────►│  where humans publish│
└──────────────────────────┘  out   │  titles, schema, copy│
                              of    └──────────────────────┘
                              band
```

| Estate | What lives there | Engine may write? |
|---|---|---|
| **Engine** (`sevasek/seo-geo-engine`) | Standard defaults, `@check`s, crawler, enricher, remediations, CLIs, Skill *template*, tests, this map. | Yes — this is the working tree. |
| **Profile** (today: `examples/sample-profile/` in-tree, synthetic; later: `auto-ps-seo-audit`, `sevasek-com-seo-audit` as dependents) | `site.yaml`, `standard/extensions.md`, `checks_ext.py`, `handlers.py`, `remediation-plan.md`, optional `playbooks/` overrides, dated `audits/`. | Yes, inside that profile: plan-sync, reports, artifacts. |
| **Website** (the CMS or front-end repo the public origin serves) | The actual titles, JSON-LD, copy, templates. | **Never.** Artifacts are files under `audits/artifacts/`. A human or a profile-owned apply step publishes them. |

The sample profile is a **canary**, not a client. Real business data
does not belong in this tree. Migrating a fork means thinning *that*
repo until it depends on this package — not copying the business into
`examples/`.

---

## 4. The loop as one picture

```
                    profile (site.yaml + extensions + plan)
                                │
                                ▼
   ┌──────── gather ────────┐   ┌──────── score ─────────┐
   │ crawl.js (Playwright)  │   │ standard ⊕ extensions  │
   │ optional local-serve   │──►│ @check(id) per row     │
   │ optional seo-geo-enrich│   │ weighted points_earned │
   └──────────┬─────────────┘   └──────────┬─────────────┘
              │ site-crawl JSON            │ standard-report JSON
              ▼                            ▼
   site dict (schema)              markdown + HTML dashboard
              │                            │
              │            ┌──────── work ─┴────────┐
              │            │ plan-sync (add/prune)  │
              │            │ remediation-plan.md    │
              │            │ queue ranked pts-lost  │
              │            │ --id → artifact.txt    │
              │            │ update-status CLI      │
              │            └───────────┬────────────┘
              │                        │ apply out of band (website)
              │                        ▼
              └──────────── seo-geo-run (new date) ──► seo-geo-verify
                            (before JSON vs after JSON)
                            pass or higher fraction ⇒ plan-sync drops the row
```

`seo-geo-run` is the gather-and-score half in one process. The
work-the-queue half stays step-by-step: editorial judgment and CMS
access live there. There is no `--fix-all`.

---

## 5. Infrastructures

Each block below is a **system with a job**, not a file. Status is
standing / partial / not erected. "Relates to" is the important
column — that is how an agent knows what else moves when they touch
one piece.

### I1 — Profile (the attachment point)

**Job.** Name one business so the kernel stays site-agnostic.

**Standing.** `SiteProfile` loads `site.yaml`. Merge rule: engine
default standard + `standard/extensions.md` (same ID replaces; new ID
adds). `disabled_ids` requires a non-empty reason. `import_profile_code`
loads `checks_module` / `handlers_module`. `seo-geo-init-profile`
scaffolds a profile that passes its own traceability test.

**Not erected.** A real (non-synthetic) profile depending on this
package. That is O4, in another repo.

**Relates to.** Every other infrastructure reads `site["profile"]` or
paths from the profile root. The profile **owns** `remediation-plan.md`
and `audits/`. The engine **owns** default rows, default playbooks,
and the CLIs.

**Must not.** Contain a copy of `framework.py` / `report.py` /
`crawl.js`. That is a fork, which is the failure mode this repo exists
to end.

### I2 — Crawl data contract

**Job.** One interface between gather and score. Every `@check` is
`(site: dict) -> CheckResult`.

**Standing.** Narrative + JSON Schema at
`seo_geo_engine/crawler/site-dict.schema.json`. Validated against
Layer 1 fixtures, the sample crawl, and Layer 2 live crawl.
`additionalProperties` is allowed on pages so a profile check can
read extra keys without a schema bump.

**Not erected.** Nothing structural. New required fields are a **MAJOR**
compat change (I10).

**Relates to.** I3 writes it. I4 merges extra keys into the **same
object** (never a parallel file). I5 `run_report()` attaches
`site["profile"]` at score time — the crawler does not write `profile`.
Checks never fetch.

See [design/data-contract.md](design/data-contract.md).

### I3 — Gather: crawler + local-serve

**Job.** Produce a site dict from a live origin or from the website
repo booted locally (`local_dev.start_command`). Same `crawl.js`
either way.

**Standing.** Packaged Playwright crawler; Python `seo-geo-crawl`;
local-serve with port teardown tests. Needs `npm install` and
`npx playwright install chromium` in `seo_geo_engine/crawler/` —
pip is not enough for a real crawl.

**Not erected.** Auth-gated crawl (sites behind login). Out of scope
until a profile proves it needs it; do not put credentials in the
crawler to "get ready."

**Relates to.** I2 (output shape). I4 (explicitly does **not** call
PageSpeed or GSC). I8 (`seo-geo-run` calls this, or `--from-crawl`
copies an existing JSON into the dated snapshot).

### I4 — Gather: enrichment

**Job.** Fill keys the crawler will not: `page.pageSpeed.{lcpMs,cls}`
(PERF-002/003) and `site.searchConsole` (CRAWL-008).

**Standing.** `seo-geo-enrich` / `seo-geo-run --enrich pagespeed,gsc`.
PSI via urllib; GSC via optional `[enrich]` extra. Credentials in the
environment (`PAGESPEED_API_KEY`, ADC / `GSC_CREDENTIALS_JSON`).
`site.yaml` may name the env var and the GSC property URL — never the
secret. Localhost / `.test` / private IPs refuse `--pagespeed`. INP is
never written (PERF-004 is Kind A).

**Not erected.** A producer for `externalPresence` (crawler writes
`null`; no default check reads it). CrUX-as-primary for field INP
(PERF-004) — not v1.

**Relates to.** I2 (merge-in-place). I3 (must stay auth-free; that is
why this is a separate infrastructure). I5 (those three checks are
`status: open` but **runtime-block** without these blobs — different
from Kind A stubs). I8 (`--enrich` is optional on `seo-geo-run`).

See [design/enrichment.md](design/enrichment.md) and
[design/blocked-rules.md](design/blocked-rules.md).

### I5 — Scoring triangle (standard ↔ check ↔ report)

**Job.** One ID, one rule, one function, one report row. Weighted
partial-credit score. Deterministic markdown / JSON / HTML.

**Standing.** 41 default rows in 11 markdown files; 32 open `@check`s;
9 blocked stubs. Profile extensions merge afterwards. `_points_earned`
is the single function for "points" anywhere (report total, top
issues, queue rank). HTML is string substitution into
`report_template.html` — not model-authored, not hosted.

**Not erected.** Growing the default standard with new **site-agnostic
open** rows. That is O7, and only after a real migration has shown
which fork-only rules were actually generic. Do not add blocked stubs
to "look more GEO."

**Relates to.** I2 (input). I1 (effective standard). I6 (same IDs; a
fail without a handler is a hole in the queue). I9 (Layer 1 fixture
pair per open default check; traceability test). I10 (ID semantics
are the public API).

```
standard/default/*.md  --(ID)-->  @check(id)  --(verdict)-->  report
                                      |
                                      v
                              I6 remediation (same ID)
```

### I6 — Remediation (work order + handlers)

**Job.** For every currently non-passing ID: a plan row, a handler
(`script` or `manual`), a points-lost rank, a status the agent can
set without editing table cells.

**Standing.** Engine default playbook per shipped ID; SCHEMA-001 and
OG-002 script handlers; profile may overwrite by ID (`origin=profile`).
`seo-geo-plan-sync` adds fails, drops passes, preserves Status/Notes.
`seo-geo-remediate --id` writes `audits/artifacts/<date>/<ID>.txt`.
`seo-geo-update-status` wraps `update_status()`. Empty plans are legal.

**Not erected.** CMS apply. Will not be erected **in the engine**.
A profile may grow its own apply step; that is I1, not I6.

**Relates to.** I5 (same points-lost). I1 (plan file lives in the
profile). I8 (run calls plan-sync + queue; verify does **not** set
`verified` — plan-sync deleting a now-passing row is the close).
I7 (Skill forbids hand-editing the plan table).

See [design/engine-owned-remediation.md](design/engine-owned-remediation.md).

### I7 — Operator surface (Skill + scaffold + routine)

**Job.** Tell an agent which commands to run, in which order, and
which decisions are engine-vs-profile. Copy into a profile at
scaffold time.

**Standing.** Skill template with org-name substitution; PR-review
routine template; `seo-geo-init-profile`. Skill describes `seo-geo-run`,
`--enrich`, `seo-geo-remediate --id`, `update-status`, `seo-geo-verify`.

**Not erected.** A Skill that has been **used for real** on a migrated
profile (O6). Until then, playbooks that say "this is illustrative"
are the wrong teacher for editorial work — which is why O6 waits on
O4 even though the commands exist.

**Relates to.** I8 (the commands it names). I11 (MCP, if built, does
not replace the Skill: the Skill still has the decision procedure and
the "don't invent copy" rule). I1 (scaffolded into the profile, not
run from this repo against a live client).

### I8 — Operator path (CLI orchestrator + verify)

**Job.** Glue gather-and-score. Compare two dated **JSON** reports so
"verified" is a flipped verdict, not a status cell.

**Standing.** `seo-geo-run` (crawl or `--from-crawl` → optional enrich
→ report → plan-sync → queue → HTML). `seo-geo-verify` (`--id`,
`--require-not-worse`). Both call existing `main()`s; they are not a
second scoring engine.

**Not erected.** Automatic re-crawl after every item (rejected: crawls
are slow; Skill says batch then one re-run). A database of runs
(rejected: dated files on disk).

**Relates to.** I3–I6 (the steps it sequences). I2 (snapshot layout
under `audits/`). I7 (Skill). I11 (MCP wraps these same functions).

See [design/agent-loop.md](design/agent-loop.md).

### I9 — Trust (fixtures, traceability, CI)

**Job.** Make "the triangle hasn't drifted" a failing test, not a
hope. Make "the crawler still emits the contract" a failing test.

**Standing.**

- Layer 1: known-good / known-bad JSON per open default check;
  completeness gate.
- Layer 2 (slow): real Playwright against a broken static site; pilot
  IDs only.
- Schema tests; plan-sync / remediate / enrich / run / verify tests;
  sample-profile remediation coverage.
- GitHub Actions: fast pytest + crawler unit tests on PRs; `pytest -m
  slow` on pushes to main.

**Not erected.** Profile-side "report is generated, not hand-kept" CI
on a **real** migrated repo (called out in agent-loop.md; belongs in
that profile's tests, not here).

**Relates to.** I5/I6 (traceability). I2 (schema). I10 (a check that
flips a Layer-1 **good** fixture is not a PATCH). Global `REGISTRY`
means test order can import a profile's checks into the engine-only
traceability test; engine orphan detection is scoped to
`seo_geo_engine.checks` modules for that reason.

### I10 — Compatibility (versioning + pin story)

**Job.** A profile can depend on this package instead of forking it.
The public API is **crawl JSON + check ID semantics + `@check` /
`@remediate` signatures**, not merely Python module names.

**Standing.** Decision record: [design/versioning.md](design/versioning.md).
Package version is `0.1.0`. Treat 0.x like 1.x for compatibility
(do not casual-break). Sample profile is the intended canary.

**Not erected.** `CHANGELOG.md` in the Keep a Changelog shape this
policy requires; README pin language (`>=0.1,<0.2`); 1.0.0 after one
real profile has been on the engine. Sibling work exists; this branch
does not land it. **Do not migrate a living audit (O4) without this.**

**Relates to.** I2 (required-field changes are MAJOR). I5 (new default
ID is MINOR; same ID with new *meaning* is MAJOR or a new ID). I1
(profiles pin a range; co-dev uses editable install).

### I11 — MCP (optional host adapter)

**Job.** Same operator path for hosts that prefer tools to a shell.

**Standing.** `pyproject.toml` extra `mcp = ["mcp>=1.0"]`. **No
server module.**

**Not erected.** Entirely. Only after O6. Thin wrapper; no scoring
logic; no CMS writes; one profile per session.

**Relates to.** I8 (what it wraps). I7 (does not replace the Skill).
I1 (global `REGISTRY` is why multi-site MCP is not v1).

See [design/mcp.md](design/mcp.md).

### I12 — Legacy forks (the proof, and the debt)

**Job.** Eventually become I1 dependents. Until then they are the
evidence the pattern works and the reason this engine must not drift
into a rewrite.

**Standing.** Separate repos, still containing copies of
`framework.py`, `standard_loader.py`, `report.py`, crawler, renderer.

**Not erected.** The migration itself ([design/profile-migration.md](design/profile-migration.md)).
Row-by-row engine-vs-profile judgment with the real files open — not
from memory of the sample.

**Relates to.** I10 (pin before migrate). I5 (a "duplicate" check that
**diverged** is either a site fact → profile override, or a better
generic rule → port into the engine *here* with a Layer 1 fixture).
I6 (CMS-named playbooks stay in the profile). O6 cannot run on the
sample without teaching the wrong editorial lessons.

---

## 6. How the infrastructures relate

### 6.1 The join key is the standard ID

`META-001`, `SCHEMA-001`, … is the same string in:

- a row in `standard/default/*.md` or `standard/extensions.md`
- `@check("…")` and `@remediate("…")` / `manual("…")`
- a report JSON `items[].id`
- a `remediation-plan.md` row
- an artifact filename
- `seo-geo-verify --id`
- `disabled_ids`

If you need a new *meaning*, you need a new ID (or a MAJOR). Do not
recycle LINK-001.

### 6.2 Data flow (what produces what)

| Artifact | Written by | Read by |
|---|---|---|
| `audits/data/site-crawl-<date>.json` | I3, optionally I4; or `--from-crawl` copy | I5, I6, I8 |
| `audits/data/standard-report-<date>.json` | I5 (`seo-geo-report` / `seo-geo-run`) | HTML renderer, `seo-geo-verify`, humans |
| `audits/standard-report-<date>.md` | I5 | humans (do not edit) |
| `audits/standard-report-<date>.html` | I5 renderer | humans / static host |
| `audits/remediation-queue-<date>.md` | I6 | humans (do not edit; regenerate) |
| `remediation-plan.md` | I6 plan-sync (structure); `update-status` (Status/Notes) | I6 queue, agents, git |
| `audits/artifacts/<date>/<ID>.txt` | I6 `--id` | humans / website apply step |
| `site.yaml` | humans (scaffold stub) | I1, I3, I4 |

Two dates are compared **only** in `seo-geo-verify`, and only as JSON.
There is no run database.

### 6.3 Ownership of writes

```
Engine code     → this git tree (PRs)
Profile facts   → profile git tree (site.yaml, extensions, plan notes)
Generated audit → profile `audits/` (gitignored or not: profile choice)
Plan status     → profile `remediation-plan.md` (tracked)
Website bytes   → website repo / CMS   ← engine NEVER
Secrets         → environment          ← never site.yaml, never this repo
```

### 6.4 Load order (process-global registries)

Checks and remediations register by decorator into a **process-global**
`REGISTRY`. v1 is one profile per process. Load order:

1. `import seo_geo_engine.checks` (engine `@check`s).
2. `import seo_geo_engine.remediation` (engine `@remediate` / `manual`).
3. `import_profile_code(profile)` — profile checks, then profile
   handlers with `origin=profile` (may overwrite an engine remediation
   ID; two profile handlers for one ID remain a hard error).

A future multi-site runner or naive MCP session that loads two
profiles will collide (e.g. two `LINK-001`s). That is I11's constraint
and **not** a reason to redesign the decorator in this phase.

### 6.5 CLI surface (the operator API)

These are the functions I7 names and I11 would wrap. Prefer them to
re-implementing scoring.

| Command | Infrastructure | Role |
|---|---|---|
| `seo-geo-init-profile` | I1, I7 | Erect an empty profile. |
| `seo-geo-crawl` | I3 | Gather only. |
| `seo-geo-enrich` | I4 | Merge PSI/GSC into a crawl JSON. |
| `seo-geo-report` | I5 | Score a crawl JSON. |
| `seo-geo-plan-sync` | I6 | Add fails, drop passes. |
| `seo-geo-remediate` | I6 | Queue markdown, or `--id` artifact. |
| `seo-geo-update-status` | I6 | Status/Notes only. |
| `seo-geo-run` | I8 → I3–I6 | Gather-and-score orchestrator. |
| `seo-geo-verify` | I8 | Diff two report JSONs. |

`python3 -m seo_geo_engine.render_html_report` is the dashboard step;
`seo-geo-run` already invokes it.

### 6.6 Dependency graph (what you must not skip)

```
I2 contract
 ├─ I3 crawler
 │   └─ I4 enricher (optional keys on the same dict)
 │       └─ I5 scoring
 │           ├─ I6 remediation (needs verdicts)
 │           │   └─ I8 run/verify (needs plan-sync + report JSON)
 │           │       ├─ I7 Skill (names I8)
 │           │       └─ I11 MCP (wraps I8; only after O6)
 │           └─ I9 trust (fixtures per open check)
 └─ I10 versioning (API = contract + ID semantics)
         └─ I12 migration (must pin I10)
             └─ O6 real verified flip
```

Skipping I10 and migrating I12 anyway produces a profile that cannot
safely `pip install -U`. Skipping I12 and declaring O6 done on the
sample teaches playbooks that are illustrative, not operational.
Building I11 before O6 teaches agents a procedure that has never
closed a real item.

### 6.7 Phases are how we erect these, not a second architecture

| Phase | Erects / completes | Depends on |
|---|---|---|
| 0 | I5 core, I3, I9 Layer 1+2, sample as I1 canary | — |
| 1 | I2 schema, I6 engine remediations + plan-sync, I9 CI | 0 |
| 2 | I4 enricher; blocked-rules policy accepted | I2, I5 |
| 3 | I10 then first I12 → real I1 | I2, I5, I6, I10 |
| 4 | I8 commands (engine half shipped); O6 on real I1 | I8 standing; O6 needs Phase 3 |
| 5 | Second I12; maybe I5 growth (open rows only) | O6 lessons |
| 6 | I11 | O6 true |

[PLAN.md](PLAN.md) is the construction schedule. This file is the
site plan. When a new idea shows up, name the infrastructure it
belongs to (or reject it as a non-goal), then put it in a phase.

---

## 7. What still needs erecting (construction queue)

In dependency order. Do not start a later item to look busy.

1. **I10 in this repo** — CHANGELOG + pin language matching
   [design/versioning.md](design/versioning.md). (Sibling PR; rebase /
   land relative to this branch as needed.)
2. **I12 first migration** — in `auto-ps-seo-audit` *or* the smaller
   fork; editable pin during the PR, version pin at merge. Procedure:
   [design/profile-migration.md](design/profile-migration.md).
3. **O6** — on that profile: one script artifact **published to the
   website**, re-`seo-geo-run`, `seo-geo-verify --id` green; one
   manual playbook to a flipped verdict. Skill-only procedure.
4. **Second I12** — `sevasek-com-seo-audit`. Promote genuinely generic
   checks into I5 here (with fixtures); leave business facts in I1.
5. **I5 growth** — only open rows with a real method; never a new
   Kind A stub. [design/blocked-rules.md](design/blocked-rules.md).
6. **I11 MCP** — only if step 3 happened. [design/mcp.md](design/mcp.md).

Out of queue on purpose: registry isolation, `externalPresence`
producer, CrUX INP, CMS apply in the engine, hosted dashboard.

---

## 8. How an agent should navigate

### You are changing the engine (this repo)

1. Read this file's relevant infrastructure + [CLAUDE.md](../CLAUDE.md)
   decision procedure (engine vs profile).
2. If the change has a trade-off, read or amend `docs/design/<topic>.md`
   **before** writing code.
3. Put the work in a [PLAN.md](PLAN.md) phase or reject it against
   non-goals. Do not silently add a default row that needs a URL.
4. Keep the triangle aligned: standard row, `@check`, Layer 1
   fixtures, engine remediation. `python3 -m pytest` green.
5. After a phase lands, update README Status, PLAN "already built",
   and this file's status cells so the three cannot drift.

### You are operating a profile (audit a site)

Do not use this file as the runbook. Use the profile's
`.claude/skills/seo-geo-audit/SKILL.md`. Commands: `seo-geo-run` →
work the queue → apply on the **website** → `seo-geo-run` (new date)
→ `seo-geo-verify`. Committing an artifact only in the profile repo
is the designed miss (`verify --id` stays red).

### You are migrating a fork

Read [design/profile-migration.md](design/profile-migration.md) and
I10. Do not copy business facts into this engine. Do not keep a
shadow `report.py`. One site first.

### You are tempted to add a surface

| Temptation | Where it actually belongs |
|---|---|
| "MCP so agents can call us" | I11, after O6 |
| "Just implement CONTENT-005 with a keyword %" | Forbidden Kind A |
| "Put PSI in crawl.js" | Forbidden; that is I4's reason to exist |
| "Engine writes to WordPress" | Forbidden; I6 drafts only |
| "Dashboard app" | Forbidden; static HTML is I5 |
| "Support two profiles in one process" | Registry isolation; not a phase yet |
| "New GEO row so we look complete" | I5 growth, Phase 5, open + fixtures or don't |

---

## 9. Where the other docs sit on this map

| Doc | Role on the map |
|---|---|
| This file | Goals, infrastructures, relationships. |
| [PLAN.md](PLAN.md) | Construction schedule (phases, exit criteria). |
| [README.md](../README.md) | Human/quickstart + status checklist (must match this file). |
| [CLAUDE.md](../CLAUDE.md) | Engine-vs-profile rule + engineering discipline for this tree. |
| [design/data-contract.md](design/data-contract.md) | I2. |
| [design/enrichment.md](design/enrichment.md) | I4. |
| [design/blocked-rules.md](design/blocked-rules.md) | I5 stubs vs I4 runtime-block vs profile maps. |
| [design/engine-owned-remediation.md](design/engine-owned-remediation.md) | I6. |
| [design/agent-loop.md](design/agent-loop.md) | I8 + I7 rewrite. |
| [design/versioning.md](design/versioning.md) | I10. |
| [design/profile-migration.md](design/profile-migration.md) | I12 procedure. |
| [design/mcp.md](design/mcp.md) | I11, deferred. |
| Profile Skill template | I7 — how to **run** the loop, not how to **build** the engine. |
