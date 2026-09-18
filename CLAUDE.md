# Working instructions for this project

This repo is the **engine**, not any one site's audit. Its own shipped
`seo_geo_engine/standard/default/*.md` must stay genuinely site-agnostic —
no URL, business name, address/phone pattern, or entity/cluster map ever
belongs here. That content lives in a profile (see README.md's "How a
profile works").

## Decision procedure: does something belong in the engine or a profile?

1. **Does it require a fact about one specific business** (a URL, an entity
   map, a contact pattern, a CMS-specific remediation playbook)? → profile,
   never the engine.
2. **Is it a generically-applicable SEO/GEO rule any site could be judged
   against** (title length, heading structure, schema presence, HTTPS,
   sitemap coverage, ...)? → an engine default, with a real `@check(id)` if
   assessable from crawl data alone, or a one-line `blocked(id)` stub if it
   fundamentally isn't (see `standard/default/`'s existing blocked rows for
   the pattern — the reason must be genuine ("no reliable automated signal
   exists"), never "this specific site hasn't given us access yet," which
   is a profile-level blocker, not an engine one).
3. **Unsure?** Ask, rather than picking silently — see the two real
   per-site repos this engine was generalized from for examples of this
   judgment call going both ways. Broader sequencing lives in
   [`docs/PLAN.md`](docs/PLAN.md).

## Engineering discipline carried over from the repos this generalizes

- Every check function is a pure `(site: dict) -> CheckResult` — profile
  data reaches it via `site["profile"]`, never a second parameter, never an
  imported module-level constant.
- `python3 -m pytest` must be green before every commit — the traceability
  suite (standard row ↔ `@check` ↔ engine-owned remediation) is what keeps
  the standard/code/remediation triangle from silently drifting apart.
- Test text-matching heuristics against real (or realistic synthetic) data
  before trusting them — a regex that looks plausible is not the same as
  one that's been checked against actual crawl output.
- When two numbers are supposed to agree (a total and the sum of its
  parts), compute them from one shared function — see `_points_earned()` in
  `report.py`.
- Never hand-edit a generated report — regenerate it from the standard/check
  code instead.
