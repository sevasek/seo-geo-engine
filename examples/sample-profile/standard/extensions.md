# Acme Example Co — standard extensions

Worked example of a profile adding rules the engine's defaults don't (and
can't, generically) cover — business facts like an entity/cluster map or a
map-embed convention live here, not in the engine.

## Local SEO

| ID | Rule | Source | Weight | Status | Unblock requirement |
|---|---|---|---|---|---|
| LOCAL-001 | Every embedded map links to the business's Google Business Profile listing, not a plain address/name text search. | Local SEO fundamentals | 3 | open | — |

## Trust & Entity Verification

| ID | Rule | Source | Weight | Status | Unblock requirement |
|---|---|---|---|---|---|
| TRUST-001 | The site has a substantive About/Team page introducing real people, not a stub. | E-E-A-T fundamentals | 3 | open | — |

## Linking

| ID | Rule | Source | Weight | Status | Unblock requirement |
|---|---|---|---|---|---|
| LINK-001 | Pages within the same topical/entity cluster link to each other in-content, not just via shared nav. | GEO topical-authority fundamentals | 3 | open | — |
| LINK-002 | The anchor text used to link to a money page matches its target keyword. | On-page SEO fundamentals | 2 | blocked | Needs a documented page → target-keyword map to compare anchor text against. |
