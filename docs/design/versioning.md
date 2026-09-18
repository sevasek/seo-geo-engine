# Design: engine versioning and profile compatibility

**Status:** proposed (Phase 3, before any live migration). The README
names this as undecided. Package version is currently `0.1.0`.

**Why this needs a design doc.** A profile is supposed to *depend on*
this package, not fork it. The moment `auto-ps-seo-audit` pins
`seo-geo-engine==0.1.0`, a change to META-001's meaning or a removed
standard ID becomes a silent score change — or a broken
`@check` import — on the next `pip install -U`. The two source repos
avoided this by being forks: they moved when they chose. A shared
engine needs a policy those profiles can pin to.

## Decision

Follow **semver** on the Python package, with an explicit mapping from
*standard/check/crawl-contract* changes to major/minor/patch.
During 0.x, `MINOR` may still break (semver's 0.x rule); we will
**not** use that as a license to break profiles casually. Treat 0.x
like 1.x for compatibility, and ship `1.0.0` at the end of Phase 3
once one real profile is on the engine and the contract has been
wrong once in production.

Profiles pin:

```
seo-geo-engine>=0.2,<0.3    # while we are on 0.x, after this policy lands
seo-geo-engine>=1.0,<2.0    # after 1.0
```

Co-development (engine and profile in adjacent checkouts) uses
`pip install -e /path/to/seo-geo-engine`. That's a development
convenience, not a pin story.

## What counts as which bump

The **crawl JSON + check ID semantics + `@check`/`@remediate`
function signatures** are the public API, not just the Python
modules.

| Change | Bump | Notes |
|---|---|---|
| Bugfix in a check that does not change a previously-correct pass to fail on the sample/Layer-1 good fixture | PATCH | If the good fixture would flip, it's not a bugfix. |
| New default standard ID + check + (after Phase 1) remediation | MINOR | Profiles gain a row on upgrade. plan-sync will add a plan row if it fails. |
| Reweight or reword a default row without changing the check's verdict function | MINOR | Score numbers move; IDs don't. Mention in CHANGELOG. |
| New optional crawl/enrichment field (`additionalProperties`) | MINOR | Old crawlers still validate. |
| New CLI command, new optional `site.yaml` key with a default | MINOR | |
| Check verdict semantics change (same ID, different notion of pass) | MAJOR | The ID is the API. If the rule's *meaning* changed, that's a new ID or a major. |
| Remove or rename a default ID | MAJOR | Profiles' `disabled_ids`, plan rows, and playbook overrides would dangle. Prefer disable-in-place (status blocked, weight kept) over deletion until the next major. |
| Required crawl field added or meaning of an existing field changes | MAJOR | See [data-contract.md](data-contract.md). |
| `@check` / `@remediate` signature change | MAJOR | |
| `SiteProfile.to_dict()` key rename | MAJOR | |

Python-only refactors with no scoring change are PATCH.

## Standard IDs are forever (within a major)

Do not recycle META-001 to mean something else. Do not fill the
LINK-001..003 gap in the engine with new default rules: those IDs
are already used in the sample profile (and likely in the real
forks). New linking rules continue from LINK-009, or use a new
prefix if the category is genuinely different.

If a default rule is wrong, options in order:

1. Fix the check (PATCH/MINOR per table).
2. Reword/reweight the row (MINOR).
3. Profile disables it (`disabled_ids` + reason) if it's wrong
   *for that site*.
4. Next major: remove it.

## CHANGELOG

`CHANGELOG.md` at the repo root, Keep a Changelog format. Every
release lists:

- Standard IDs **added**.
- Standard IDs **removed** (major only).
- Standard IDs **reweighted** (old → new).
- Crawl-contract field changes.
- Migration notes for profiles (e.g. "plan-sync once after
  upgrade").

The sample profile is the **canary**: `pytest` in this repo runs it.
A change that turns the sample red without a fixture update is
either a real break or an incomplete commit.

We will not run the migrated real profiles in *this* repo's CI
(they are other repos, with other secrets). Their CI pins a version
and runs their tests. That's the feedback loop; it is not this
package's job to vendor them.

## How a breaking standard change reaches a pinned profile

It doesn't, until they bump the pin. That's the point.

When we need a behavior change that would be MAJOR:

1. Ship it on `main` / a major tag.
2. CHANGELOG spells out the ID-level delta.
3. The profile's upgrade PR: bump pin, run pytest, run a crawl,
   `plan-sync`, read the report diff. The PR-review routine already
   says to regenerate the report and diff it against the PR's
   claims — that applies to engine upgrades too.

For a MINOR that adds IDs, the profile may do nothing: new rows
appear, some fail, plan-sync adds them next audit. That's desired.

## `disabled_ids` is not a version pin

Disabling META-001 because you disagree with titles-must-be-30-60
is a site policy. Disabling META-001 because the engine "broke it
in 0.4" is a pin that should have happened. Don't document
`disabled_ids` as a compatibility tool.

## Alternatives considered

**CalVer (`2026.09.10`).** Makes "when" obvious, makes "safe to bump"
opaque. Profiles need a contract, not a date.

**Separate version for the standard vs the Python package.** Two
numbers for one wheel. The standard *is* the package's data.
One version.

**Engine always additive; never change a check.** Too timid. META-001
will have bugs. The good-fixture rule distinguishes "bugfix" from
"we decided 30–60 is now 20–70."

**Vendoring a copy of `standard/default/` in each profile.** That's a
fork with extra steps. Override-by-ID already covers the case where
a site disagrees with a default.

## Implementation notes

- Add CHANGELOG.md in the same PR that adopts this policy (Phase 3
  start), even if the only entry is "0.1.0: initial extract."
- README Status's "not decided yet" line becomes a pointer here.
- Tag releases (`v0.2.0`). Don't publish to PyPI until at least one
  real profile wants a non-editable install; editable + git tag is
  enough for the first migration.
- 1.0.0 is a Phase 3 *exit* decision, not a Phase 1 task.
