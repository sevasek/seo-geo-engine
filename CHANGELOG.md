# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

During 0.x we treat compatibility like 1.x: do not casually break
profiles. The public API is the crawl JSON, check ID semantics, and
`@check` / `@remediate` function signatures. See
[docs/design/versioning.md](docs/design/versioning.md).

## How future releases must be listed

Every release entry **must** record:

- Standard IDs **added**
- Standard IDs **removed** (major only)
- Standard IDs **reweighted** (old → new)
- Crawl-contract field changes
- Migration notes for profiles (e.g. "run `seo-geo-plan-sync` once after
  upgrade")

Use the headings below as the template. "None" is a valid value; omitting
the heading is not.

## [Unreleased]

Work landed after the `v0.1.0` tag (still package version 0.1.0).

### Added

- Engine-owned remediations for every default standard ID, `seo-geo-plan-sync`,
  `seo-geo-remediate --id`, `seo-geo-update-status`, crawl site-dict JSON
  Schema, and GitHub Actions CI.
- `seo-geo-enrich` post-crawl merge of PageSpeed Insights (mobile lab LCP/CLS)
  and Search Console sitemap status. Optional extra: `[enrich]`.
- Compatibility policy: `docs/design/versioning.md` (accepted). 0.x treated
  like 1.x; profiles pin `seo-geo-engine>=0.1,<0.2`.
- `seo-geo-run` (crawl → optional enrich → report → plan-sync → queue → HTML)
  and `seo-geo-verify` (diff two report JSONs; `--id`, `--require-not-worse`).

### Standard IDs added

None.

### Standard IDs removed

None.

### Standard IDs reweighted

None.

### Crawl-contract field changes

None in the crawler. `pageSpeed` and `searchConsole` are now produced by
`seo-geo-enrich` (keys were already reserved in 0.1.0).

### Migration notes for profiles

- After upgrade, run `seo-geo-plan-sync` so engine-owned remediations
  populate `remediation-plan.md`.
- Optional: `pip install seo-geo-engine[enrich]` and `seo-geo-enrich` if
  PERF-002 / PERF-003 / CRAWL-008 should leave runtime-blocked.

## [0.1.0] - 2026-09-11

Initial extract of the engine (standard IDs as of current defaults,
crawl contract as of `seo_geo_engine/crawler/crawl.js`). No prior
packaged release.

### Added

- Python package `seo-geo-engine` 0.1.0: weighted rule standard, `@check`
  registry, remediation-tracking layer, markdown/JSON report and
  deterministic HTML dashboard, packaged Playwright crawler, per-site
  profile merge, `seo-geo-init-profile` scaffold.

### Standard IDs added

Engine defaults (41 rows across 11 categories). These IDs are the public
check-ID API as of 0.1.0:

- Metadata: `META-001`, `META-002`, `META-003`, `META-004`
- Headings: `HEAD-001`, `HEAD-002`, `HEAD-003`, `HEAD-004`
- Structured data: `SCHEMA-001`, `SCHEMA-002`
- Open Graph: `OG-001`, `OG-002`
- Images: `IMG-001`, `IMG-002`
- Content: `CONTENT-001`, `CONTENT-002`, `CONTENT-003`, `CONTENT-004`,
  `CONTENT-005`, `CONTENT-006`, `CONTENT-007`, `CONTENT-008`
- Linking: `LINK-004`, `LINK-005`, `LINK-006`, `LINK-007`, `LINK-008`
- Crawlability: `CRAWL-001`, `CRAWL-002`, `CRAWL-003`, `CRAWL-004`,
  `CRAWL-005`, `CRAWL-006`, `CRAWL-007`, `CRAWL-008`
- Performance: `PERF-001`, `PERF-002`, `PERF-003`, `PERF-004`
- Mobile: `MOBILE-001`
- Analytics: `ANALYTICS-001`

`LINK-001` and `LINK-002` live in the sample profile's extensions, not
in engine defaults. `LINK-003` does not exist. Do not recycle
`LINK-001`/`LINK-002`/`LINK-003` into engine defaults; new linking rules
continue from `LINK-009`.

### Standard IDs removed

None.

### Standard IDs reweighted

None.

### Crawl-contract field changes

Initial contract (no prior version to diff against). The crawler writes:

- Top-level: `sitemapUrls`, `robotsTxt`, `pages`,
  `discoveredNonSitemapPages`, `linkResolutions`, `externalPresence`
  (always `null` from the crawler).
- Each `pages[]` entry: `url`, `status`, `bytes`, `noJsWordCount`, and
  on extract failure `extractError`; otherwise `title`, `titleLen`,
  `metaDesc`, `metaDescLen`, `canonical`, `dupOgTags`, `ogDescription`,
  `jsonLdTypes`, `organizationNode`, `dateModified`, `h1Count`, `h1s`,
  `h2Count`, `h3Count`, `headingSequence`, `imageCount`,
  `imagesMissingAlt`, `wordCount`, `pTagWordCount`, `bodyText`,
  `viewport`, `generator`, `hasAnalytics`, `internalHrefs`,
  `contentInternalHrefs`, `anchorTexts`, `iframes`.
- Resolution objects (`discoveredNonSitemapPages`, `linkResolutions`):
  `url`, `status`, `redirected`, `finalUrl`, `noindex`,
  `redirectStatus`, `redirectHops`.

The crawler does not write `pageSpeed` or `searchConsole`. Those keys
are reserved for a later enricher; built-in checks already read them
when present.

### Migration notes for profiles

- Pin `seo-geo-engine>=0.1,<0.2`.
- Co-development (adjacent checkouts): `pip install -e /path/to/seo-geo-engine`.
- Not published to PyPI; editable install or a git tag is the install
  path until a real profile wants a non-editable pin.
- `examples/sample-profile/` is the 0.1.x compatibility canary:
  `pytest` in this repo scores it. A change that turns the sample red
  without a fixture update is either a real break or an incomplete
  commit.

[Unreleased]: https://github.com/sevasek/seo-geo-engine/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sevasek/seo-geo-engine/releases/tag/v0.1.0
