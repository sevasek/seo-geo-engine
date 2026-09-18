# Design: migrating the two source audits onto this engine

**Status:** proposed (Phase 3 for the first, Phase 5 for the second).
The README lists both as unchecked.

**Why this needs a design doc.** `auto-ps-seo-audit` and
`sevasek-com-seo-audit` are the repos this package was extracted
from. They still contain forked copies of `framework.py`,
`standard_loader.py`, `report.py`, crawler, HTML renderer, etc.
A sloppy migration either (a) leaves a fork in place under a pip
dependency, or (b) drops site-specific rules on the floor because they
"look generic." The engine-vs-profile decision procedure in
`CLAUDE.md` is the whole game, and it has to be applied row by row
with the real files in front of us — not from memory of this
synthetic sample.

This document is the procedure and the judgment calls. It is not
the migration itself.

## Decision

Keep each existing audit **repo** as that site's profile repo.
Do not create a third repo per site, and do not move those profiles
into `examples/` here (this engine must stay site-agnostic; real
business data does not belong in this tree).

Migrate **one site first** (Phase 3), run the loop for real (Phase
4), then migrate the second (Phase 5). Which one goes first is
whichever, at migration time, has the smaller `checks_ext.py` +
fewer CMS-specific playbooks — inspect both; don't guess from this
doc. If they're similar, prefer the one whose live site is easier to
crawl without extra auth.

Pin the engine per [versioning.md](versioning.md). During the
migration PR, an editable install is fine; the merge should pin a
tag.

## What stays in the profile repo

Anything that fails CLAUDE.md question 1 ("does it require a fact
about one specific business?"):

- `site.yaml` (created from whatever currently hardcodes base URL,
  clusters, phone patterns, local-dev command).
- `standard/extensions.md` — rows that need those facts, plus any
  row the site disagrees with the engine about (override-by-ID).
- `checks_ext.py` / `handlers.py` for those IDs.
- `playbooks/` that name CMS fields, templates, or vendor logins.
- `remediation-plan.md` (living).
- Historical `audits/` if they want them (regenerate rather than
  hand-edit going forward).
- The Skill / routine, scaffolded then edited only if the generic
  template is wrong for that team.
- Profile tests that import `seo_geo_engine.testing.traceability`.

## What is deleted from the profile repo

Any file that now lives in this package:

- `framework.py`, `standard_loader.py`, `report.py`,
  `render_html_report.py`, `report_template.html`
- Built-in check modules that match engine defaults
- Packaged crawler copies (`crawl.js` and friends)
- Duplicate pytest assertions that
  `seo_geo_engine.testing.traceability` already provides
- Duplicate Skill text that restates engine procedure

If a "duplicate" check in the fork has **diverged** from the engine
default (different threshold, extra special case), that is a
decision, not a delete:

1. Was the divergence a site fact? → profile override (new ID, or
   disable + replacement ID — not check-registry overwrite; see
   [engine-owned-remediation.md](engine-owned-remediation.md)).
2. Was the divergence a better generic rule? → port it into the
   engine *in this engine repo* with a Layer 1 fixture, then the
   profile uses the default. Don't "migrate" by leaving the better
   rule stranded in the profile.

## Row-by-row procedure

For each standard ID in the fork:

| Question | Action |
|---|---|
| Engine already has this ID with the same meaning? | Drop the fork's row and check. If weights differ, either accept the engine weight or override-by-ID in extensions.md with a comment in the profile README *why*. |
| Engine has this ID with different meaning? | Don't reuse the ID. Disable the engine ID if it's wrong for the site; add a fresh ID for the site's meaning. File an engine issue if the engine's meaning is just wrong. |
| Engine doesn't have it, and it's generic (no business fact)? | Port to engine defaults (this repo, fixture pair, this migration's prerequisite PR). Then the profile doesn't carry it. |
| Engine doesn't have it, needs a business fact? | `extensions.md` + `checks_ext.py`. |
| Blocked in the fork because "we don't have GSC access yet"? | That's a profile-level `disabled_ids` or a missing enricher, **not** an engine `blocked` stub. Engine CRAWL-008 stays `open`. |

Do this as a spreadsheet or a markdown table in the profile's
migration PR, not as a memory. The first migration's table is how
we find engine bugs.

## Code mechanics

1. In the profile repo: add `seo-geo-engine` dependency, create
   `site.yaml` pointing at existing extension files (adjust paths).
2. Change check imports from local `framework` to
   `seo_geo_engine.checks.framework`. Same for remediation.
3. Delete the forked engine modules. Run pytest. The first red is
   the real work.
4. Point CLI invocations in the Skill / README at
   `python3 -m seo_geo_engine.*` (or the `seo-geo-*` entry points).
5. First live crawl through the *engine* crawler, not a saved JSON
   from the fork (the shape should match; if it doesn't, that's a
   data-contract bug to fix here, not a transform to keep in the
   profile).
6. `plan-sync` (once Phase 1 has it) to rebuild the plan from the new
   non-passing set. Diff against the old plan; leftover IDs are
   either renamed or still failing.
7. Remove any CI that linted the deleted modules; add pytest + the
   engine pin.

Do not try to keep both the forked `report.py` and the package
"for a while." Dual scoring is how the triangle drifts.

## Sample profile's job during migration

The sample is not a third site to migrate. It stays synthetic. If
the first real migration discovers a missing `site.yaml` key, add
the key to `SiteProfile` here and to the sample as a commented
example, not as a fake Acme fact unless the sample's own checks need
it.

## Risk: leaking a business into the engine

The person doing the migration will see a useful regex that contains
a city name, or a cluster map that "lots of sites might want." That
still belongs in the profile. The test is CLAUDE.md question 1, not
"is this clever."

The inverse risk: leaving a generic heading check in the profile
because "we might want to tweak it." If it's generic, it goes to
the engine with a fixture. Tweaks later are MINOR/MAJOR per
[versioning.md](versioning.md).

## Alternatives considered

**Rewrite both profiles in this repo's `examples/`.** Rejected.
Real URLs and addresses would land in the engine history. Also
makes this repo's CI need those sites' credentials.

**New empty profile + copy/paste selected files.** That's how
business facts get dropped. Start from the living repo and subtract
the engine.

**Migrate both in one week, in parallel.** Rejected. The first
migration is the design review of *this engine*. Doing two at once
doubles the chance we "resolve" a split both ways.

## Implementation notes

- This engine repo should not submodule the site repos.
- After the first migration, update README Status checkboxes and
  PLAN.md's "What's already built."
- If the first migration needs an engine change (it will), that
  change lands *here* first, tagged, then the profile pin bumps.
  Don't patch the engine via the profile's `sys.path`.
