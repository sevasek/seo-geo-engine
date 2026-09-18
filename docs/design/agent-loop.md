# Design: the agent loop

**Status:** proposed (Phase 4 to close; Phase 1–2 build the commands
it needs). The Skill template already describes the happy path in
prose. The engine does not yet enforce it.

**Why this needs a design doc.** The README's loop is the product:
crawl → score → work the queue → re-crawl until the verdict flips.
Several pieces of that are social conventions (don't hand-edit the
report, don't mark verified without a re-crawl, don't invent copy).
If those stay Skill-only, an agent will skip them under time
pressure, and we will not notice because generated reports don't
say so.

This doc specifies the **operator path** the Skill should invoke, and
the few engine-side guards worth building. It is not a workflow
engine, an orchestrator SaaS, or a CMS writer.

## Decision

One profile, one working directory, dated snapshots on disk. The
engine offers commands; the agent (or a human) sequences them. A
thin orchestrator CLI glues the *gather-and-score* half. The
*work-the-queue* half stays step-by-step — that's where editorial
judgment and CMS access live, and hiding it behind `--fix-all` would
produce unverified edits.

```
seo-geo-run --profile site.yaml [--local] [--enrich pagespeed,gsc] --date YYYY-MM-DD
        │
        ├─ crawl  → audits/data/site-crawl-<date>.json
        ├─ enrich (optional)
        ├─ report → audits/standard-report-<date>.md
        │           audits/data/standard-report-<date>.json
        ├─ plan-sync → remediation-plan.md  (add fails, drop passes)
        ├─ queue  → audits/remediation-queue-<date>.md
        └─ html   → audits/standard-report-<date>.html
```

Then, per queue item, the agent:

1. Picks the top ready (no `depends_on`) item.
2. Sets status `in-progress` via CLI.
3. If `script`: `seo-geo-remediate --id ID` and applies the artifact
   in the **website** repo or CMS (out of engine). If `manual`:
   follows the playbook (engine default or profile override).
4. Sets status `applied` when the change is actually published or
   committed to the site, not when the artifact is written.
5. Re-runs `seo-geo-run` (new date, or same date only if they accept
   overwriting the snapshot — default is new date).
6. `seo-geo-verify --before <old.json> --after <new.json> --id ID`
   must show that ID's verdict is now `pass` (or a strictly higher
   fraction, for partials they're iterating). Only then is the row
   gone (plan-sync deletes it) and the work real.

The engine never sets `verified` itself. After plan-sync, a flipped
item has no row, which is a stronger statement than a status cell.

## Snapshot layout

```
<profile>/
  site.yaml
  remediation-plan.md          # living work order, git-tracked
  playbooks/                   # profile overrides only
  audits/
    data/site-crawl-<date>.json
    data/standard-report-<date>.json
    standard-report-<date>.md
    standard-report-<date>.html
    remediation-queue-<date>.md
    artifacts/<date>/<ID>.txt
```

`audits/` may be gitignored in a profile (crawls are large) or
tracked for the HTML dashboard — profile choice. The engine does not
care. `remediation-plan.md` **is** tracked: it's how status survives
across agent sessions.

## `seo-geo-verify`

Input: two `standard-report-*.json` files (the JSON, not the
markdown). Output:

- Score delta.
- Per-ID verdict transitions (`fail→pass`, `blocked→fail`, …).
- `--id` to assert a specific ID became `pass`; exit 1 if not.
- `--require-not-worse` to fail if any ID moved pass→fail (a
  regression guard after a batch of fixes).

This is the only place two dates are compared. Do not add a database.

`update_status(..., "verified")` remains a legal status for the
in-between moment ("I applied this; waiting on deploy/re-crawl").
The Skill should prefer that over claiming victory. plan-sync on
the after-crawl is what closes the item.

## What the engine refuses to do

- Write to the website's CMS or repo. Script artifacts are files under
  `audits/artifacts/`.
- Mark a plan row `verified` as a side-effect of writing an artifact.
- Re-crawl in a tight loop inside a check. Verification is a new
  gather, not a hope that the in-memory site dict changed.
- Interpret playbooks. They're markdown for the agent/human.

## Skill rewrite (when Phase 4 lands)

The template's four sections stay, but every "optional" that is now
a command becomes a command:

- Gathering: `seo-geo-run` (or crawl + enrich).
- Report: produced by the same invocation; don't tell the agent to
  reconstruct flags.
- Queue work: `update_status` CLI, `seo-geo-remediate --id`, apply
  out of band, re-run, `seo-geo-verify`.
- Evolving the standard: unchanged (engine vs profile decision
  procedure, then pytest, then regenerate).

Delete the sentence that points at missing enrichment docs; point at
`docs/design/enrichment.md`.

The PR-review routine stays a separate scheduled path. It does not
work the queue; it reviews PRs that came out of working the queue.

## Parallelism and multiple sites

v1 is one profile per process. The global check/remediation
`REGISTRY` is not safe for two profiles at once (a profile's
`@check("LINK-001")` would collide with another profile's). That's
acceptable: the CLI loads one `--profile`. A future multi-site runner
would need registry isolation; it is not this phase and not a reason
to redesign the decorator now.

## Failure modes worth designing for

**The agent "applies" a script artifact by committing it to the
profile repo instead of the website repo.** Verify will fail (crawl
unchanged). That's the correct failure. Mention it in the Skill.

**The agent edits `standard-report-*.md` to look greener.** Already
forbidden by culture; CI on a profile should regenerate and diff.
The migrated profiles' tests should include "report is generated,
not hand-kept" if they don't already.

**Blocked items sit at the top of the queue by points-lost.**
`build_queue` already splits ready vs depends-on. Keep that split.
Blocked-*verdict* items (true stubs) should still appear, in the
blocked section, so the score hole is visible. Do not hide them.

**Partial credit loops.** META-001 at 16/19 pages is `fail` with
fraction 3/19, not `partial`, in current checks — many checks use
`failed(..., fraction=...)`. `partial` as a verdict is rare. Verify
should treat "fraction increased and verdict is pass" as the success
criteria for `--id`; don't require a `partial→pass` state machine.

## Alternatives considered

**A daemon / MCP tool that performs the whole loop including CMS
writes.** Rejected. CMS write is site-specific and dangerous.
[mcp.md](mcp.md) wraps the same commands, it doesn't add apply.

**Store status in JSON next to the crawl, not in markdown.**
Rejected for now. `remediation-plan.md` is grepable, reviewable in
PRs, and already has `update_status`. Don't migrate the store in the
same phase as inventing the loop.

**Automatic re-crawl after every item.** Rejected as a default.
Crawls are slow (real browser, sequential). Batch a few `applied`
items, then one re-crawl, then verify `--require-not-worse` plus
per-ID checks. The Skill should say so.

## Implementation notes

- Phase 1 can ship `plan-sync`, `update_status` CLI, and
  `seo-geo-remediate --id` without `seo-geo-run` or `seo-geo-verify`.
  The Skill can still list the long form.
- Phase 4 adds `seo-geo-run` and `seo-geo-verify` once a real profile
  exists to try them on.
- `seo-geo-run` is a Python function that calls the existing `main()`s
  with argv, not a rewrite of crawl/report.
