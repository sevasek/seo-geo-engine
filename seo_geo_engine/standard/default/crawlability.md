# Crawlability — default rules

## Crawlability

| ID | Rule | Source | Weight | Status | Unblock requirement |
|---|---|---|---|---|---|
| CRAWL-001 | Every indexable, canonical page is listed in the sitemap. | SEO fundamentals | 4 | open | — |
| CRAWL-002 | robots.txt doesn't fully disallow known AI-answer-engine crawlers. | GEO fundamentals | 3 | open | — |
| CRAWL-003 | No internal link is broken (4xx/5xx or unreachable). | SEO fundamentals | 4 | open | — |
| CRAWL-004 | Every page URL and internal link uses HTTPS. | SEO fundamentals | 3 | open | — |
| CRAWL-005 | Internal redirects are clean, single-hop 301s. | SEO fundamentals | 1 | open | — |
| CRAWL-006 | Substantive page content is present without executing JavaScript. | SEO/GEO fundamentals | 3 | open | — |
| CRAWL-007 | Page URLs are clean (lowercase, hyphen-separated, no query-string cruft). | SEO fundamentals | 1 | open | — |
| CRAWL-008 | The sitemap is submitted to Google Search Console with no errors. | SEO fundamentals | 2 | open | — |
