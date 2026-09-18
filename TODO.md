# TODO

Status legend: `[ ]` open · `[x]` done. Each open item is scoped to be one
standalone session for whoever picks it up — self-contained context, one
test to prove it worked.

## The picture of finished

Today: `auto-ps-seo-audit` and `sevasek-com-seo-audit` are each a full
~30-file copy of the standard/check/remediation machinery, one forked from
the other. This engine exists standalone but nothing depends on it yet.

**Finished** looks like: both real repos shrink to ~6 files each
(`site.yaml`, `checks_ext.py`, `handlers.py`, `standard/extensions.md`,
`remediation-plan.md`, `playbooks/`) and declare `seo-geo-engine` as a
pinned dependency. Running `python3 -m seo_geo_engine.report <crawl.json>
--profile site.yaml` against Price & Speed's real 2026-08-31 crawl produces
the *exact same score* their team already trusts — proving the migration
moved code, not behavior. Adding a third client site is an afternoon of
writing a `site.yaml` + a couple of extension rows, not forking a repo. An
MCP-enabled agent session can run the whole crawl → score → work-queue →
re-verify loop through 5 tool calls. A `git tag` exists for every version a
profile might pin to, and a one-page policy says what changes require a
major bump.

## 0. Cut the first release (blocks everything below)

- [ ] **0.1 Tag and push `v0.1.0`.** `git tag v0.1.0 && git push origin v0.1.0`.
      **Test:** in a scratch dir, `pip install git+https://github.com/sevasek/seo-geo-engine.git@v0.1.0`
      into a fresh venv, then `python3 -c "import seo_geo_engine; print('ok')"`.

## A. Migrate `auto-ps-seo-audit` onto the engine

Do these in order — each is independently testable, so a bad step is caught
before the next one compounds it.

- [ ] **A1. Add the profile skeleton.** Depend on `seo-geo-engine @ v0.1.0`
      (pip line in `requirements-dev.txt`). Write `site.yaml` from the real
      facts already hardcoded in `seo_checks/helpers.py`
      (`service_page_pattern: "/services/"`, `service_index_url`),
      `seo_checks/linking_checks.py` (`CLUSTERS` → `entity_clusters`),
      `remediation/handlers.py` (AU phone regex →
      `contact.phone_pattern: AU_MOBILE_LANDLINE`, the depot-1 address
      pattern → `contact.address_patterns`), and `README.md` (base_url, org
      name). Shape: see `seo-geo-engine`'s `examples/sample-profile/site.yaml`.
      **Test:** `python3 -c "from seo_geo_engine.profile import load_profile; p=load_profile('site.yaml'); print(p.base_url, p.entity_clusters)"`
      prints the real values, no exception.

- [ ] **A2. Split the standard.** Diff `standard/seo-standard.md`'s row IDs
      against `seo_geo_engine.paths.default_standard_paths()`'s IDs. Every
      ID NOT in the engine defaults (expect: LOCAL-\*, TRUST-\*, VOICE-\*,
      SNIPPET-\*, RANK-\*, CITE-\*, LINK-001/002/003, META-005, HEAD-005,
      CONTENT-004) moves verbatim (same weight/status/unblock-text) into
      `standard/extensions.md`.
      **Test:** a script that loads both the OLD `standard/seo-standard.md`
      and the NEW `default_standard_paths() + [Path("standard/extensions.md")]`,
      and asserts the two ID sets are identical.

- [ ] **A3. Move the checks.** For every ID now in `extensions.md`, cut its
      `@check` function out of `seo_checks/*.py` into `checks_ext.py`,
      rewriting any hardcoded URL/`CLUSTERS` read to
      `site["profile"]["pages"][...]` / `site["profile"]["entity_clusters"]`
      (see `seo-geo-engine`'s `examples/sample-profile/checks_ext.py` for
      the exact pattern — it's the same LINK-001 rule, already done once).
      Delete the ~11 modules that are now pure engine defaults
      (`metadata_checks.py`, `heading_checks.py`, etc. — keep only files
      with a moved or extension-only check in them).
      **Test:** run `python3 -m seo_geo_engine.report audits/data/site-crawl-2026-08-31.json --profile site.yaml`
      and diff its JSON output against the last real generated
      `audits/data/standard-report-2026-08-31.json` — every ID present in
      both must have an identical `verdict` and `fraction` (a real behavior
      change found here is a bug in the port, not an intentional fix — stop
      and ask).

- [ ] **A4. Move the remediation handlers.** Same cut-and-rewire for
      `remediation/handlers.py`'s business-specific script handlers and the
      ~24 `manual(...)` registrations, into the profile's own `handlers.py`,
      reading `site["profile"]["contact"]["phone_regex"]` etc. instead of
      module constants. Copy `playbooks/*.md` as-is (no rewiring needed,
      they're prose).
      **Test:** `python3 -m seo_geo_engine.remediation.plan audits/data/site-crawl-2026-08-31.json --profile site.yaml`
      produces the same ranked ID order and `points_lost` values as the
      last real `remediation-queue-2026-08-31.md`.

- [ ] **A5. Replace the test suite.** Delete
      `tests/test_traceability.py`/`test_remediation_traceability.py`'s
      duplicated logic; replace with a few lines importing
      `seo_geo_engine.testing.traceability.assert_standard_has_full_check_coverage`
      pointed at this profile's paths (see `seo-geo-engine`'s
      `scaffold/init_profile.py`'s generated `test_traceability.py` for the
      exact shape to copy).
      **Test:** `python3 -m pytest` green.

- [ ] **A6. Delete the dead engine copy.** Remove
      `seo_checks/framework.py`, `standard_loader.py`, `report.py`,
      `helpers.py`, and `remediation/remediation_framework.py`/
      `remediation_loader.py`/`plan.py` — everything now comes from the
      installed `seo_geo_engine` package.
      **Test:** `python3 -m pytest` still green after deletion (proves
      nothing orphaned still imports a deleted module) +
      `grep -r "from seo_checks" .` and `grep -r "from remediation\." .`
      (excluding `.venv`) both return nothing outside
      `checks_ext.py`/`handlers.py`'s new `seo_geo_engine.*` imports.

- [ ] **A7. Update the docs.**
      `README.md`/`CLAUDE.md`/`.claude/skills/seo-geo-audit/SKILL.md` now
      describe a thin profile, not a standalone engine — base the SKILL.md
      rewrite on `seo-geo-engine`'s
      `seo_geo_engine/skills/seo-geo-audit-template/SKILL.md`.
      **Test:** `grep -r "seo_checks\|remediation\.plan\b" README.md CLAUDE.md .claude/`
      returns nothing (no stale references to deleted modules).

## B. Same migration for `sevasek-com-seo-audit`

Repeat A1-A7 against this repo. It forked from an earlier snapshot of
`auto-ps-seo-audit`, so its business-specific row set may differ — **don't
assume it matches Milestone A's list**; B2's diff-against-engine-defaults
step is what actually discovers it. Same 7 sub-tasks, same tests, swap in
sevasek.com's own facts (`README.md`/`TODO.md` there have the real base
URL/org name).

- [ ] B1. Profile skeleton (see A1)
- [ ] B2. Split the standard (see A2)
- [ ] B3. Move the checks (see A3)
- [ ] B4. Move the remediation handlers (see A4)
- [ ] B5. Replace the test suite (see A5)
- [ ] B6. Delete the dead engine copy (see A6)
- [ ] B7. Update the docs (see A7)

## C. MCP server (net-new code, not a migration)

- [ ] **C1. Confirm the `mcp` PyPI package name/API** the
      `pyproject.toml` `mcp>=1.0` extra assumes is still correct — read
      that package's own README/examples before writing server code; this
      doesn't pin exact API calls because that surface may have moved.
- [ ] **C2. Implement `seo_geo_engine/mcp_server/server.py`** — 5 tools,
      each a thin wrapper around an existing function, no new business
      logic: `run_site_audit` → crawl (live/local) + `report.run_report`;
      `get_audit_issues` → `report.top_issues`; `get_remediation_queue` →
      `remediation.plan.build_queue`; `set_remediation_status` →
      `remediation.remediation_loader.update_status`; `regenerate_report`
      → `render_markdown`/`render_json`/`render_html_report`.
      **Test:** a script that starts the server in-process and calls each
      of the 5 tools once against `examples/sample-profile/`, asserting
      each returns without raising and `run_site_audit`'s result contains
      a `score` key.
- [ ] **C3. Document it** — one "Agent interface (MCP)" section in
      README, `pip install seo-geo-engine[mcp]` + how to point Claude/Cursor
      at it.

## D. Versioning policy (pure docs, smallest task here)

- [x] **D1. Write the compatibility policy.** Lives at
      [`docs/design/versioning.md`](docs/design/versioning.md) (not a
      second root `VERSIONING.md`, which would drift). SemVer — MAJOR =
      breaking change to the `site` dict shape, a check's return
      contract, or a CLI flag; MINOR = new engine-default
      checks/standard rows; PATCH = bugfixes with no contract change.
      0.x is treated like 1.x. Every release's `CHANGELOG.md` names
      what a pinned profile must change. Profiles pin
      `seo-geo-engine>=0.1,<0.2`.
      **Test:** `tests/test_versioning.py` — CHANGELOG matches
      `pyproject.toml` version; policy file mentions MAJOR/MINOR/PATCH
      and "profile".

## Definition of done for the whole backlog

- [ ] `v0.1.0` tag pushed, installs cleanly from git in a scratch venv
- [ ] `auto-ps-seo-audit`: `pytest` green, report output for the real
      2026-08-31 crawl unchanged for every shared ID, repo down to ~6
      profile-specific files
- [ ] `sevasek-com-seo-audit`: same, with its own crawl fixture
- [ ] MCP smoke-test script exercises all 5 tools against the sample
      profile without error
- [x] Compatibility policy exists at `docs/design/versioning.md` and
      reads like it's meant for a pinned dependent, with `CHANGELOG.md`
      as the release record
