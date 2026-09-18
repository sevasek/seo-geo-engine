# Engine docs

This directory is about **how the engine itself should evolve**, not how
to audit any one site. Site-specific facts (URLs, entity maps, CMS
playbooks) stay in a profile — see the repo README's "How a profile
works" and `CLAUDE.md`'s engine-vs-profile decision procedure.

| Doc | What it's for |
|---|---|
| [PLAN.md](PLAN.md) | Goal, what's already built, and the phased plan to make the loop runnable on a real site. |
| [design/data-contract.md](design/data-contract.md) | The crawl JSON every check reads, and how enrichment merges in. |
| [design/engine-owned-remediation.md](design/engine-owned-remediation.md) | Default playbooks/handlers in the engine, first-audit plan bootstrap. |
| [design/enrichment.md](design/enrichment.md) | PageSpeed Insights and Search Console as a post-crawl merge. |
| [design/agent-loop.md](design/agent-loop.md) | Crawl → score → work the queue → re-crawl and confirm the verdict flipped. |
| [design/versioning.md](design/versioning.md) | Semver, how a standard-schema change reaches a pinned profile. |
| [design/profile-migration.md](design/profile-migration.md) | Moving `auto-ps-seo-audit` and `sevasek-com-seo-audit` onto this package. |
| [design/blocked-rules.md](design/blocked-rules.md) | When a blocked row may become a real check, and when it must stay a stub. |
| [design/mcp.md](design/mcp.md) | MCP server — deferred until the Skill-only path has been used for real. |

Read PLAN.md first. The design docs exist because those features have
real trade-offs; they are not a backlog of tickets.
