# Design: MCP server

**Status:** deferred (Phase 6). `pyproject.toml` already declares
`mcp = ["mcp>=1.0"]`. There is no server module. The README is
explicit: not required for the loop to work, and not started until
the Skill-only path has been used for real.

**Why this needs a design doc anyway.** Optional extras that never
gain a module become folklore. If and when Phase 4's exit criterion
is true (an agent following only the scaffolded Skill flipped a
real item to pass), this is the shape to build — so Phase 6 doesn't
invent a parallel scoring path.

## Decision

The MCP server is a **thin wrapper over existing Python functions**,
not a second engine.

- Same `load_profile` / `run_report` / `build_queue` /
  `update_status` / plan-sync / enrich / verify.
- No scoring logic in the server.
- No CMS writes.
- One profile per session (the global `REGISTRY` is not
  multi-profile-safe; see [agent-loop.md](agent-loop.md)).
- Install: `pip install seo-geo-engine[mcp]`.

If Phase 4 never happens, do not build this.

## Tools (when built)

Expose the operator path, not a chat-oriented paraphrase of the
standard:

| Tool | Wraps |
|---|---|
| `crawl` | `seo_geo_engine.crawl.run` (`local: bool`) |
| `enrich` | Phase 2 enricher, flags for psi/gsc |
| `score` | `run_report` + write markdown/JSON/HTML |
| `plan_sync` | Phase 1 plan-sync |
| `queue` | `build_queue` |
| `remediate_script` | run one `--id` script handler, return artifact text + path |
| `update_status` | `update_status()` |
| `verify` | Phase 4 report diff |

Do not add `explain_rule` that rewrites standard markdown through an
LLM. The agent can read the standard file. Do not add `suggest_fix`
that generates copy. That's the manual playbook's job, or a script
handler that already refused to invent copy.

Resources (optional): `standard://default/<category>` as the raw
markdown, `report://<date>` as the JSON. Nice to have; tools are
enough for v1.

## What MCP is for

A host that prefers tools to shell. That's it. It does not replace
the Skill: the Skill still contains the engine-vs-profile
decision procedure, the "don't hand-edit reports" rule, and when
to stop and ask a human. MCP without that Skill is a bag of
commands an agent will call in the wrong order.

## Alternatives considered

**Build MCP now so the engine looks complete.** Rejected by the
README. A server wrapping an incomplete loop (no plan-sync, no
engine playbooks, no enricher) would teach agents a broken
procedure.

**MCP as the primary API, CLI as a client.** Rejected. CLI is the
testable, scriptable surface; CI calls it. MCP, if it exists, sits
on top.

**Multi-site tool that takes a list of profiles.** Not until
registries are isolated. Out of scope even for Phase 6 v1.

## Implementation notes (only in Phase 6)

- New module `seo_geo_engine.mcp.server`, console script
  `seo-geo-mcp`.
- Fast tests with in-memory crawl fixtures; no live MCP host in CI.
- Update the Skill with "if your host has MCP, call these tools;
  otherwise the CLI is equivalent."
- Do not block any earlier phase on this document.
