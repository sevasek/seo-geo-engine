# Engine docs

This directory is about **how the engine itself should evolve**, not how
to audit any one site. Site-specific facts (URLs, entity maps, CMS
playbooks) stay in a profile — see the repo README's "How a profile
works" and `CLAUDE.md`'s engine-vs-profile decision procedure.

**Start here:** [SYSTEM.md](SYSTEM.md) — goals and objectives, the
infrastructures that stand or still need erecting, and how they relate
(data flow, ownership, join key, CLI surface, construction queue).

Then:

| Doc | What it's for |
|---|---|
| [SYSTEM.md](SYSTEM.md) | **Map.** Goal vs objectives vs non-goals; infrastructures I1–I12; relationships. Read this before adding a surface. |
| [PLAN.md](PLAN.md) | **Schedule.** Phases 0–6, exit criteria, what not to do. Construction order for the map. |
| [design/data-contract.md](design/data-contract.md) | The crawl JSON every check reads, and how enrichment merges in. |
| [design/engine-owned-remediation.md](design/engine-owned-remediation.md) | Default playbooks/handlers in the engine, first-audit plan bootstrap. |
| [design/enrichment.md](design/enrichment.md) | PageSpeed Insights and Search Console as a post-crawl merge. |
| [design/agent-loop.md](design/agent-loop.md) | Crawl → score → work the queue → re-crawl and confirm the verdict flipped. |
| [design/versioning.md](design/versioning.md) | Accepted compatibility policy (0.x treated like 1.x; pin `>=0.1,<0.2` on 0.1.x; CHANGELOG lists standard-ID and crawl-contract deltas). |
| [design/profile-migration.md](design/profile-migration.md) | Moving `auto-ps-seo-audit` and `sevasek-com-seo-audit` onto this package. |
| [design/blocked-rules.md](design/blocked-rules.md) | When a blocked row may become a real check, and when it must stay a stub. |
| [design/mcp.md](design/mcp.md) | MCP server — deferred until the Skill-only path has been used for real. |

The design docs exist because those features have real trade-offs; they
are not a backlog of tickets. SYSTEM.md names the infrastructure; the
matching design doc (if any) is the decision record for that piece.
PLAN.md says when to erect it.
