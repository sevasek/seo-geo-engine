# Design: engine-owned remediations

**Status:** proposed (Phase 1). The registries and the sample
profile's handlers exist; the engine ships no remediations of its
own.

**Why this needs a design doc.** The README loop says an agent "drafts
what's mechanically draftable from crawl data" and "works down
manual playbooks." Today both of those live only in a profile. A
scaffold produces empty `handlers.py` and an empty plan table. The
first audit of a real site therefore yields a score without a queue
that can be worked — unless someone copies the sample profile's
playbooks and rewrites them. That copying is the fork this engine
exists to eliminate.

## Decision

The engine ships a **default remediation** for every default standard
ID that can have one:

- `manual` + a generic playbook for rules whose fix is editorial,
  CMS-shaped, or access-gated, but whose *procedure* is
  site-agnostic ("give every page a unique 30–60 character title").
- `script` for rules whose artifact is computable from the crawl +
  `site["profile"]` with no invented copy. The two that already
  qualify, proven in the sample profile, are SCHEMA-001 and OG-002.

A profile **overrides by ID**, same cascade as the standard: later
registration wins if we load engine remediations first, then
`import_profile_code`. A profile that needs a WordPress-specific
playbook for META-001 registers its own `manual("META-001",
playbook="playbooks/META-001.md")` and ships that file. The engine
playbook stays the fallback for everyone else.

The engine does **not** ship a `remediation-plan.md`. That file is a
per-audit work order (which IDs are currently non-passing, their
status, their dependencies). It is generated into the profile by a
bootstrap command, not copied from the engine.

## Why remediations aren't just "the check, backwards"

A check answers "is this true of the crawl." A remediation answers
"what do we do about it, and can a script draft the bytes." Those
diverge:

- SCHEMA-001's check is "service pages have Service JSON-LD." The
  script can draft a block from `title` + `url` + `org_name`. It
  still cannot publish it.
- META-001's check is mechanical; the fix is copywriting. Manual
  playbook.
- CONTENT-007's check is blocked; the playbook's job is to say so
  and name the unblock (`COMPETITOR-CONTENT-CORPUS`), not to pretend
  a fix exists.

So the engine ships remediations even for blocked stubs: the playbook
is "this is not assessable yet; here is the genuine unblock." That
keeps the queue honest instead of silently dropping blocked weight.

## Registry load order

Today `REGISTRY` in `remediation_framework.py` is a process-global
dict, filled by decorator side-effect, matching checks. Keep that
(changing it is a large break). Define the load order explicitly:

1. `import seo_geo_engine.remediation.defaults`  (new package, same
   pattern as `seo_geo_engine.checks`).
2. `import_profile_code(profile)` which imports `handlers_module`.

A profile re-registering an ID must be allowed to replace the engine
entry. That means the "duplicate ID is a hard error" rule needs a
narrow exception: **a profile module may overwrite**, an engine module
may not. Implementation sketch: `remediate()` / `manual()` gain an
optional `override: bool = False`, and `import_profile_code` sets a
context flag, *or* profile-side decorators always overwrite.

Recommended: **overwrite allowed only when the existing entry was
tagged `origin="engine"` and the new one is `origin="profile"`.**
Two profile handlers for the same ID remain a hard error. Two engine
handlers remain a hard error.

Checks do not need this yet (a profile adding a check for a *new* ID
is the common case; overriding META-001's check is rare and already
impossible without deleting the engine check from the registry). If
a profile needs to replace a check, it disables the engine ID and
adds a new ID. Don't add check-override in this phase.

## Playbook contract

Engine playbooks live at
`seo_geo_engine/remediation/playbooks/<ID>.md` and are packaged as
package data.

They are site-agnostic:

- No URL, business name, or CMS product.
- State the rule, what evidence the check emits, the kind of change
  that flips it, and the typical `Depends on` value (`CMS-ACCESS`,
  `GSC-ACCESS`, `—`).
- End with: apply the change in the site's own repo or CMS, re-crawl,
  confirm the verdict flipped, then let plan-bootstrap delete the
  row.

The sample profile's current playbooks ("this is a synthetic worked
example…") are **not** this contract. After this phase, the sample
should either:

- drop its copies of engine-default playbooks and rely on the engine
  ones, keeping only playbooks for LOCAL-001 / TRUST-001 / LINK-001 /
  LINK-002, or
- keep copies that *override* with Acme-specific CMS notes, as a
  demonstration of the override path.

Recommended: the sample **overrides none** of the engine defaults, so
it proves the fallback. Its `handlers.py` only registers extension-ID
handlers plus any script override it wants to demonstrate. SCHEMA-001
and OG-002 move into the engine; the sample deletes its copies.

## Script handler contract

Unchanged from `remediation_framework.py`:

- `(site: dict) -> RemediationResult`
- `kind="script"`
- `artifact` is ready-to-paste text. Never publish. Never call a CMS.
- Evidence is the URLs touched.

Engine script handlers go in
`seo_geo_engine/remediation/handlers/*.py` and are imported from
`seo_geo_engine.remediation.defaults`.

OG-002's sample implementation (reuse `metaDesc` as `og:description`,
refuse to invent copy) is the template. SCHEMA-001's (build JSON-LD
from title/url/org_name) likewise. Neither needs a business fact
beyond `profile.site.org_name`, which every profile has.

Do not add a script handler that invents titles, meta descriptions, or
FAQ copy. If the crawl doesn't already contain the string, it's
manual.

## Plan bootstrap

New CLI, recommended name `seo-geo-plan-sync` (distinct from today's
`seo-geo-remediate` which renders the queue):

```
seo-geo-plan-sync <site-crawl.json> --profile site.yaml [--plan remediation-plan.md]
```

Behaviour:

1. Run the report (same `run_report` as everything else).
2. Non-passing IDs that have no plan row: append one.
   - `Approach` from the registered handler's kind (`script`/`manual`).
   - `Depends on` from a handler-supplied default if we add one, else
     `—` for script and `CMS-ACCESS` for manual unless the playbook
     declares otherwise. Keep this data on the registered remediation
     (e.g. `manual(..., depends_on="CMS-ACCESS")`) so it isn't
     inferred by ID regex.
   - `Status` = `not-started`.
   - `Notes` = `See {playbook}` or `Drafted by {fn.__name__}`.
3. Passing IDs that still have a plan row: **delete the row.** This
   is the mechanical form of "once a re-crawl flips its verdict to
   pass, delete the row." Do not require a `verified` status first —
   the new crawl *is* the verification. (Status `verified` remains
   available as an in-progress marker *between* apply and re-crawl;
   see [agent-loop.md](agent-loop.md).)
4. Never change `Status` or `Notes` on a row that still exists and is
   still non-passing, except to fix `Approach` if it disagrees with
   the handler (that's a bug if it happens; loud warning, don't
   silently overwrite status).
5. Refuse to run if a non-passing ID has no registered handler at
   all. After engine defaults ship, that should only happen for a
   profile extension the author forgot to handle.

Empty plan files (scaffold) are currently a format error in
`load_remediation_plan` ("No remediation rows found"). Bootstrap must
be allowed to start from that header-only table. Relax the loader:
zero rows is legal; it's a fresh profile.

## Running a script handler

Today `python3 -m seo_geo_engine.remediation.plan` only writes
`remediation-queue-<date>.md`. Add:

```
seo-geo-remediate <site-crawl.json> --profile site.yaml --id SCHEMA-001 --out-dir audits
```

- Looks up the handler, requires `kind="script"`.
- Writes `audits/artifacts/<date>/<ID>.txt` (or `.json` if the
  artifact is JSON-LD — don't be clever; `.txt` is enough).
- Prints the path. Does not call `update_status`. The agent marks
  `in-progress` / `applied` itself after it has actually pasted /
  committed the artifact.

`--id` required in v1. No `--all`: running every script blindly
produces a pile of artifacts with no apply step, which looks like
progress and isn't.

## Traceability

After this lands, CLAUDE.md's "once Phase 2 lands" sentence is this
design, and should be rewritten to present tense.

Engine tests:

- Every default standard ID has a registered remediation (engine
  defaults module imported). This is stricter than the profile rule
  ("every *non-passing* item has a row") because the engine can't
  know which IDs a given site will fail. The engine ships the *ability*
  to remediate every default ID; the plan file selects the current
  subset.
- Every engine `manual` playbook file exists.
- Every engine `script` handler returns a `RemediationResult` with
  `artifact` when pointed at the sample's *failing* fixture for that
  ID (or a dedicated fixture). Don't run SCHEMA-001's handler against
  a site that already passes it and treat empty artifact as failure —
  the sample handler already returns a "nothing to draft" detail
  with empty artifact. Tests should use a known-failing site dict.

Profile tests stay as they are: plan rows ↔ current non-passing set,
plan rows ↔ handlers, playbooks exist, approach matches kind.
`assert_standard_has_full_check_coverage` stays check-only; add a
sibling `assert_engine_defaults_have_remediations` in
`seo_geo_engine.testing.traceability`.

## Alternatives considered

**Keep remediations profile-only; ship playbooks as a template the
scaffold copies.** Rejected. Copied playbooks drift from the standard
the moment a default rule's wording changes. Override-by-ID is the
same cascade the standard already uses.

**Engine ships playbooks but not script handlers.** Rejected. SCHEMA-001
and OG-002 are the demonstration that "mechanically draftable" is
real. If the engine doesn't ship them, every profile reimplements the
same JSON-LD snippet.

**Auto-apply script artifacts to a git checkout of the site.**
Rejected for this phase and likely forever at the engine layer. The
engine must not assume it can see the website repo, let alone write
to it. A profile *may* grow an apply helper; that's profile code.

**Generate playbooks from the standard row with no extra file.**
Tempting (one less artifact). Rejected because a playbook has
procedure a rule sentence doesn't ("reuse the meta description; don't
invent one"). The extra file is the point.

## Implementation notes

- Package the playbooks in `pyproject.toml` `[tool.setuptools.package-data]`.
- Scaffold stops writing empty playbook directories as the only
  remediation story; it can still create `playbooks/` for overrides.
- Sample profile shrinks. That's a feature. Update its tests so they
  import engine remediations before `handlers.py`.
- `update_status` gets a CLI wrapper in the same module, not a new
  package.
