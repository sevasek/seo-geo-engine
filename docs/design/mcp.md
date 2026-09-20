# Design: MCP server

**Status:** implemented. `pip install seo-geo-engine[mcp]` (pinned
`mcp>=1.0,<3`) and `seo-geo-mcp --profile site.yaml`. The CLI and the
Skill remain the testable, scriptable surface; this is a host adapter.

C1 confirmed the PyPI name is still `mcp`. mcp 2.x renamed `FastMCP` to
`MCPServer` (`from mcp.server.mcpserver import MCPServer`). mcp 1.x
still exports `FastMCP`; the server module tries 2.x then 1.x.

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

## Tools

Expose the operator path, not a chat-oriented paraphrase of the
standard. TODO C2 also names five gather/queue tools that wrap the
same functions; both names are registered.

| Tool | Wraps |
|---|---|
| `run_site_audit` | `seo_geo_engine.run.run` (crawl live/local/`from_crawl` + report + plan-sync + queue + HTML) |
| `get_audit_issues` | `report.top_issues` |
| `get_remediation_queue` / `queue` | `build_queue` |
| `set_remediation_status` / `update_status` | `update_status()` |
| `regenerate_report` / `score` | `run_report` + write markdown/JSON/HTML |
| `crawl` | `seo_geo_engine.crawl.run` (`local: bool`) |
| `enrich` | Phase 2 enricher, flags for psi/gsc |
| `plan_sync` | Phase 1 plan-sync |
| `remediate_script` | run one `--id` script handler, return artifact text + path |
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

**Build MCP now so the engine looks complete.** Originally rejected
by the README until a Skill-only path had been used for real. The
TODO C items + operator request shipped the wrapper anyway; a
real-site verified flip (O6) is still a different objective.

**MCP as the primary API, CLI as a client.** Rejected. CLI is the
testable, scriptable surface; CI calls it. MCP sits on top.

**Multi-site tool that takes a list of profiles.** Not until
registries are isolated. Out of scope for v1.

## Implementation

- Module `seo_geo_engine.mcp.server` (TODO C2 path
  `seo_geo_engine.mcp_server.server` re-exports), console script
  `seo-geo-mcp`.
- Fast tests (`tests/test_mcp_server.py`) with the sample-profile
  crawl fixture; no live MCP host in CI.
- Skill: if the host has MCP, call these tools; otherwise the CLI
  is equivalent.
