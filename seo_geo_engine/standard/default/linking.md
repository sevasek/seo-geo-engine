# Linking — default rules

## Linking

| ID | Rule | Source | Weight | Status | Unblock requirement |
|---|---|---|---|---|---|
| LINK-004 | Internal links point directly at the canonical destination, not through a redirect. | SEO fundamentals | 1 | open | — |
| LINK-005 | Every page has at least one inbound internal link from another page. | SEO fundamentals | 3 | open | — |
| LINK-006 | External links only point to responsible/authoritative sources. | SEO fundamentals | 1 | blocked | Needs a policy defining what counts as a "responsible" external link (relevance/authority criteria) to assess against. |
| LINK-007 | Outbound links carry appropriate `rel` attributes (`nofollow`/`sponsored`/`ugc`) where warranted. | SEO fundamentals | 1 | blocked | Needs a policy on when outbound links should carry which `rel` attribute — not assessable without one. |
| LINK-008 | Internal link authority flows to newly published pages. | SEO fundamentals | 2 | blocked | Needs a defined set of "new" pages and an internal linking policy for surfacing them — not derivable from a single crawl snapshot. |
