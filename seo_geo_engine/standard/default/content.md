# Content — default rules

## Content

| ID | Rule | Source | Weight | Status | Unblock requirement |
|---|---|---|---|---|---|
| CONTENT-001 | Every service page has at least 500 words of visible content. | SEO fundamentals | 3 | open | — |
| CONTENT-002 | At least half of a page's visible text sits inside real `<p>` elements, so a content extractor recognizes it as prose. | SEO/GEO fundamentals | 2 | open | — |
| CONTENT-003 | Every page carries a `dateModified` (or equivalent freshness) signal in structured data. | SEO/GEO fundamentals | 2 | open | — |
| CONTENT-004 | Page content matches its documented target search intent. | SEO fundamentals | 3 | blocked | Needs a documented target search-intent (informational/commercial/navigational) per page to compare against. |
| CONTENT-005 | No page shows signs of keyword stuffing. | SEO fundamentals | 2 | blocked | Needs a defined keyword-stuffing detection method beyond naive frequency counting — no reliable automated signal exists yet. |
| CONTENT-006 | Content is formatted for skimming (subheadings, lists, short paragraphs). | SEO/GEO fundamentals | 2 | blocked | Needs a defined "skimmability" rubric to assess against. |
| CONTENT-007 | Page content offers real information gain over top competing results. | GEO fundamentals | 3 | blocked | Needs a competitor/SERP content corpus to compare against — not derivable from a single-site crawl. |
| CONTENT-008 | Factual claims are backed by a citable source. | GEO / E-E-A-T fundamentals | 3 | blocked | Needs a way to distinguish an unsupported claim from a sourced one — requires content-level judgment or a claims/sources map. |
