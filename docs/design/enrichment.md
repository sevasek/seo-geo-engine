# Design: enrichment (PageSpeed Insights, Search Console)

**Status:** accepted / implemented (Phase 2). `seo-geo-enrich` is the
producer; checks already consumed the keys.

**Why this needs a design doc.** Three default rows are `status:
open` with real logic, but they return `blocked` unless extra blobs
are merged into the crawl JSON:

- PERF-002 / PERF-003 read `page.pageSpeed.{lcpMs,cls}`.
- CRAWL-008 reads `site.searchConsole`.

Those signals need API keys, quota, and (for GSC) OAuth. Putting
them in `crawl.js` would make the default crawl path require Google
credentials and would mix a 30-second page fetch with a multi-second
PSI lab run per URL. They also don't apply to `--local` crawls of
localhost.

## Decision

Enrichment is a **post-crawl merge**, invoked explicitly:

```
seo-geo-enrich audits/data/site-crawl-<date>.json \
    --profile site.yaml \
    --pagespeed \
    --gsc \
    --out audits/data/site-crawl-<date>.json
```

- Default `--out` may overwrite in place (the crawl JSON is a
  snapshot; the enriched form is what scoring should read). Recommend
  writing in place so `seo-geo-run` has one file to thread through.
- Either flag may be omitted. Omitted → those keys stay absent/null →
  the corresponding checks stay runtime-blocked. That is correct,
  not a failure of the enricher.
- `--local` crawls: `--pagespeed` against `localhost` is refused
  (PSI cannot see it). `--gsc` is allowed (GSC is about the live
  property, independent of this crawl's origin) but the operator
  should know they're mixing a local HTML snapshot with live search
  data. Warn, don't refuse.

The crawler remains credential-free. `crawl.js` keeps writing
`externalPresence: null` and omitting `searchConsole` / `pageSpeed`.

## Credentials

Never in the engine repo, never in `site.yaml` committed to git.

| Source | Env var | Also allowed |
|---|---|---|
| PageSpeed Insights | `PAGESPEED_API_KEY` | `profile.enrichment.pagespeed_api_key_env` naming a different env var |
| Search Console | Application Default Credentials, or `GSC_CREDENTIALS_JSON` path | `profile.enrichment.gsc_property` (the *property URL*, not a secret) |

`site.yaml` may grow an `enrichment:` block:

```yaml
enrichment:
  pagespeed_api_key_env: PAGESPEED_API_KEY   # default if omitted
  gsc_property: "https://www.example.com/"    # Search Console site URL
```

The property URL is a site fact (like `base_url`), so it belongs in
the profile. The key does not.

No credentials → that enricher no-ops with a clear stderr line and
exit code 0 if the other enricher ran, or exit 2 if the user passed
`--pagespeed` and we cannot call it. Don't silently skip a requested
enricher.

## PageSpeed Insights

- API: Google PageSpeed Insights v5, strategy `mobile` (mobile-first
  indexing; matches MOBILE-001's worldview).
- One request per crawled page URL, sequentially, with a small delay.
  PSI quota is the reason this is not inside the crawl loop.
- Cache by `(url, date, strategy)` under `audits/cache/pagespeed/` so
  a re-score the same day doesn't spend quota. Cache is optional to
  skip via `--no-cache`.
- Map the response into the page object:

```
page["pageSpeed"] = {
    "lcpMs": audits.metrics["largest-contentful-paint"].numericValue,
    "cls": audits.metrics["cumulative-layout-shift"].numericValue,
    "hasFieldData": bool(loadingExperience.metrics),
}
```

Exact JSON paths should be pinned by a fixture of a recorded PSI
response (redacted), not by hitting live Google in CI.

- Missing metric → leave that key off; the check already treats
  "no `lcpMs`" as unassessable for that page and blocks the whole rule
  if *no* page is assessable.
- INP: do **not** write it even if the API returns field data.
  PERF-004's stub exists because lab INP doesn't exist and field INP
  is often absent for low-traffic sites. Writing a number we then
  ignore is how a later contributor "unblocks" PERF-004 by accident.
  When PERF-004 grows a real check, it will declare the key it wants.

Localhost / `.test` / private IPs: refuse `--pagespeed`.

## Search Console

- Scope: the sitemap list for `gsc_property`, plus error/warning
  counts on the submitted sitemap(s).
- Map:

```
site["searchConsole"] = {
    "sitemapSubmitted": bool,
    "sitemapErrors": int,
    "sitemapWarnings": int,
}
```

- If the property is not in this credential's site list: fail the
  enricher (exit 2), do not write a fake `sitemapSubmitted: false`.
  False-failing CRAWL-008 because of an auth mistake is worse than
  leaving it blocked.
- Multiple sitemaps: `sitemapSubmitted` is true if any sitemap URL
  matches the profile's `crawl.sitemap_url` (or `${base_url}/sitemap.xml`).
  Errors/warnings are summed for matching sitemap(s) only.

GSC client libraries are an optional extra (`pip install
seo-geo-engine[enrich]`), not part of the base package. Same pattern
as the declared-but-empty `[mcp]` extra. Base `pip install` must keep
working without Google libs.

## Orchestration with the crawl

`seo-geo-run` (Phase 4, see [agent-loop.md](agent-loop.md)) will call
enrich between crawl and report when flags or profile config ask.
Until then, the Skill's "Gathering data" section should show two
commands (crawl, then enrich) rather than pretending enrich is
automatic.

Do not enrich inside `crawl/run.py`. Local-serve, Playwright, and
Google auth failing in one process is an un-debuggable blob.

## Standard-row status vs runtime blocked

This is the part that's easy to "clean up" wrongly.

| ID | Standard status | Without enrichment | With enrichment |
|---|---|---|---|
| PERF-002 | open | runtime `blocked` | pass/fail/partial |
| PERF-003 | open | runtime `blocked` | pass/fail/partial |
| PERF-004 | blocked | stub `blocked` | still stub |
| CRAWL-008 | open | runtime `blocked` | pass/fail |

`status: open` means "a reliable automated signal exists." It does
**not** mean "this crawl JSON contains it." Leave CRAWL-008 and
PERF-002/003 as `open`. The completeness gate already requires fixtures
for them (and those fixtures include the enrichment blobs). That is
the right test: the check's logic is real; the gather step is
optional.

Do not add a third standard status like `needs-enrichment`. It would
split the table without changing scoring. The runtime `blocked`
verdict plus the standard's unblock-requirement column (for true
stubs) is enough. Optionally, PERF-002's blocked *detail* when
`pageSpeed` is missing could be a hardcoded sentence in the check
("Needs PageSpeed Insights enrichment — see docs/design/enrichment.md")
instead of the standard's unblock column (which is `—` for open
rows). That's a small check change in Phase 2.

## Scoring impact

Blocked-because-unenriched still earns zero and keeps its weight in
the denominator. A first crawl without keys therefore looks worse than
the crawl-only rules warrant. That is visible and correct: the
score is "of the whole standard," not "of the subset we bothered to
gather."

A profile that cannot obtain a PSI key may `disabled_ids` PERF-002/003
with a reason. That's an honest subset, not a fake pass. Do not
auto-disable them.

## Alternatives considered

**Call PSI from `crawl.js` with an `--psi-key` flag.** Rejected.
Node/Playwright crawl plus Google quota in one loop makes timeouts
and partial crawls the default. Auth belongs in Python next to the
profile loader.

**Lab metrics from Playwright (LCP/CLS in-session) instead of PSI.**
Tempting for `--local`. Rejected as a *replacement*: Playwright lab
numbers are not PSI lab numbers and must not be written to
`pageSpeed` or PERF-002 will compare them to Google's "Good"
thresholds as if they were. A future `pageLab` blob with different
checks could exist; it is not PERF-002.

**CrUX History API as the primary source.** Better long-term for
field data, and the eventual PERF-004 path. Not v1: more auth
surface, and many sites this engine will be pointed at won't have
CrUX. PSI lab is the available proxy; the check's caveat string
already says so.

**Engine-hosted keys.** Never. This is not a SaaS.

## Implementation notes

- Optional extra (pinned): `enrich = ["google-api-python-client>=2.160.0,<3",
  "google-auth>=2.35.0,<3", "google-auth-httplib2>=0.2.0,<1"]`. Keep
  `[mcp]` as-is. Base `pip install` does not pull Google libs.
- Tests: recorded API payloads under `tests/fixtures/enrichment/`,
  merge function unit-tested, urllib mocked, no live network in fast
  tests. Sample scores stay on the enriched crawl fixture; the
  unenriched variant is
  `tests/fixtures/enrichment/site-crawl-unenriched.json`.
- Rate limits: a 50-page site is ~50 PSI calls, sequential, with a
  1s delay. Don't parallelize in v1.
