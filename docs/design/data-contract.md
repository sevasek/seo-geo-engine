# Design: crawl data contract

**Status:** proposed (Phase 1). Checks and `crawl.js` already implement
most of this by convention; this doc makes the convention the
interface.

**Why this needs a design doc.** Every `@check` is
`(site: dict) -> CheckResult`. The crawler, the Layer 1 fixtures, the
sample profile's hand-written JSON, and the not-yet-built enricher
all have to produce the same shape. There is no schema file today.
Enrichment and profile authors currently reverse-engineer
`tests/fixtures/checks/` and `examples/sample-profile/fixtures/`.

## Decision

The site dict is the **one** interface between gather and score.

- The crawler writes it.
- Enrichment merges extra keys into the same object (never a parallel
  file format).
- `report.run_report()` then attaches `site["profile"]` from
  `SiteProfile.to_dict()` before any check runs.
- Checks never fetch. If a field is missing they either skip that
  page, return `blocked`, or fail with the gap named in `detail` —
  whichever that check already does. They do not invent a second
  source.

A JSON Schema (draft 2020-12) should live at
`seo_geo_engine/crawler/site-dict.schema.json` and be loaded by a test
that validates: the crawler's output against a Layer 2 crawl, every
Layer 1 fixture, and the sample fixture. The schema is allowed to be
`additionalProperties: true` at the page level so a profile-specific
check can read extra keys without a schema change. Required keys are
the ones built-in checks already read.

Until that file exists, this document is the contract.

## Top-level keys

| Key | Written by | Required for a crawl-only score |
|---|---|---|
| `sitemapUrls` | crawler | yes (empty list if `--pages-file`) |
| `robotsTxt` | crawler | yes (empty string if fetch failed) |
| `pages` | crawler | yes |
| `discoveredNonSitemapPages` | crawler | yes (may be `[]`) |
| `linkResolutions` | crawler | yes (may be `[]`) |
| `externalPresence` | enricher / profile | no — crawler writes `null` |
| `searchConsole` | enricher | no — crawler omits or writes `null` |
| `profile` | `run_report()`, not the crawler | attached at score time |

Do not add a second top-level "enrichment" object. Keys merge at the
level the check already looks (`site["searchConsole"]`,
`page["pageSpeed"]`).

## Page object (each entry of `pages`)

Built-in checks currently read:

| Field | Used by (examples) | Notes |
|---|---|---|
| `url` | almost everything | Absolute. |
| `status` | crawler records it; few checks use it on `pages` itself | Resolutions use `status` more. |
| `title`, `titleLen` | META-001, META-003 | |
| `metaDesc`, `metaDescLen` | META-002 | |
| `canonical` | META-004 | |
| `dupOgTags` | OG-001 | List of duplicated `og:*` property names. |
| `ogDescription` | OG-002 | |
| `jsonLdTypes` | SCHEMA-*, CONTENT-003 | Deduplicated `@type` strings. |
| `organizationNode` | captured, not yet a default check | Reserved. |
| `dateModified` | CONTENT-003 | First JSON-LD `dateModified` found. |
| `h1Count`, `h1s`, `h2Count`, `h3Count`, `headingSequence` | HEAD-* | |
| `imageCount`, `imagesMissingAlt` | IMG-* | |
| `wordCount`, `pTagWordCount`, `bodyText` | CONTENT-*, CRAWL-006 | `bodyText` is after stripping script/style/noscript/template. |
| `viewport` | MOBILE-001 | |
| `generator` | captured, not yet a default check | Reserved. |
| `hasAnalytics` | ANALYTICS-001 | Google-family signatures only. |
| `bytes` | PERF-001 | Raw HTML byte length from a plain fetch. |
| `noJsWordCount` | CRAWL-006 | Plain-fetch word count, no JS. |
| `internalHrefs` | LINK-*, CRAWL-001, CRAWL-004 | Deduplicated, origin-filtered. |
| `contentInternalHrefs` | profile LINK-001 | Excludes ancestors `nav, header, footer`. |
| `anchorTexts` | captured; profile LINK-002 would use | |
| `iframes` | profile LOCAL-001 | Includes lazy-load attribute fallbacks. |
| `extractError` | crawler, on failure | Page still appears; checks must tolerate missing fields. |
| `pageSpeed` | PERF-002, PERF-003 | Enrichment. Shape below. |

A page the crawler failed to extract still appears with `url`,
`status: null`, `bytes: null`, `noJsWordCount: null`, and
`extractError`. Checks that assume `wordCount` must already treat a
missing key as zero or skip — they do, via `.get`.

## Resolution objects

`discoveredNonSitemapPages` and `linkResolutions` share a shape:

```
{
  "url": "...",
  "status": 200 | 404 | null,
  "redirected": false,
  "finalUrl": "...",
  "noindex": false,
  "redirectStatus": 301 | null,
  "redirectHops": 0
}
```

`status: null` means the request failed outright (DNS, connection
refused), not "unknown." CRAWL-003 treats that as broken. Do not change
that meaning.

## Enrichment blobs

### `page.pageSpeed`

```
{
  "lcpMs": 1500,
  "cls": 0.02,
  "hasFieldData": false
}
```

All three keys optional individually; PERF-002 requires `lcpMs`,
PERF-003 requires `cls`. `hasFieldData` only changes the caveat string,
not the verdict. INP is **not** on this object yet — PERF-004 stays
a blocked stub until a field-data source exists. See
[enrichment.md](enrichment.md).

### `site.searchConsole`

```
{
  "sitemapSubmitted": true,
  "sitemapErrors": 0,
  "sitemapWarnings": 0
}
```

Absence of the whole object → CRAWL-008 returns `blocked` (and the
standard row stays `status: open`, because a signal exists). That
split is load-bearing; do not flip the standard row to `blocked` just
because a given crawl wasn't enriched.

### `site.externalPresence`

Currently always `null`. No default check reads it. Leave the key as
a reserved slot; do not invent a check that consumes it until a
gather method exists (WebSearch is profile-invoked, not the crawler).

## Profile attachment

`SiteProfile.to_dict()` is the shape of `site["profile"]`:

```
site, pages, entity_clusters, contact, crawl, local_dev
```

Checks read it. They must not import `load_profile` themselves. A
fixture that needs service-page targeting includes a `profile` key
directly; `run_report(profile=...)` overwrites it when a real profile
is in play.

## What is not in the contract

- HTML. Checks do not see the page source except via the fields
  above. If a new check needs a new field, add it to `extractPage` in
  `crawl.js`, add it here, add it to a Layer 1 fixture pair, then
  write the check. That order is mandatory so we don't grow
  check-side BeautifulSoup as a back door.
- Per-site page lists. The crawler gets URLs from the sitemap or
  `--pages-file`. A profile that needs a subset filters in a check or
  passes a pages file through `local_dev.pages_file`.
- Historical crawls. Each JSON is a snapshot. Trend/verify compares
  two snapshots; it does not require a new key.

## Alternatives considered

**A typed dataclass / pydantic model instead of a dict.** Rejected
for now. The check signature is already `(site: dict)` across two
real source repos; changing it is a breaking change for every
`checks_ext.py`. A schema file plus a test is enough discipline.
Revisit after 1.0 if extra keys become a mess.

**Checks fetch their own enrichment.** Rejected. Quota, auth, and
runtime would leak into a function that must stay pure enough to run
against fixtures in <100ms.

**Two files (crawl.json + enrichment.json) merged at CLI only.**
Worse for fixtures and for `run_report`. Merge once, write one JSON,
score that.

## Implementation notes (Phase 1)

- Add the schema file and a `tests/test_site_dict_schema.py` that
  parametrizes over Layer 1 fixtures + sample crawl.
- Layer 2's live crawl output should validate too (slow test).
- Document the contract in the Skill under "Gathering data" as a
  pointer here, not a duplicate table.
- Changing a required field's meaning is a MAJOR version bump — see
  [versioning.md](versioning.md).
