"""Post-crawl enrichment: PageSpeed Insights and Search Console.

Invoked explicitly via `seo-geo-enrich`. The crawler stays credential-free;
this package merges `page.pageSpeed` and `site.searchConsole` into an
existing site-dict JSON. See docs/design/enrichment.md.
"""

from seo_geo_engine.enrichment.errors import EnrichmentError
from seo_geo_engine.enrichment.pagespeed import map_psi_response
from seo_geo_engine.enrichment.search_console import map_sitemaps
from seo_geo_engine.enrichment.urls import is_psi_unreachable_url

__all__ = [
    "EnrichmentError",
    "is_psi_unreachable_url",
    "map_psi_response",
    "map_sitemaps",
]
