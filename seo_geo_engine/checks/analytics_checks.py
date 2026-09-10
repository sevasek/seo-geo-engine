from seo_geo_engine.checks.framework import check, passed, failed
from seo_geo_engine.checks.helpers import pages


@check("ANALYTICS-001")
def check_analytics_present(site: dict):
    """Reads `hasAnalytics` — set by the crawl step scanning each page's raw
    HTML for a GA4/GTM/gtag.js script signature."""
    offenders = [p["url"] for p in pages(site) if not p.get("hasAnalytics")]
    total = len(pages(site))
    if not offenders:
        return passed("ANALYTICS-001", f"All {total} pages load a web-analytics script.")
    return failed(
        "ANALYTICS-001",
        f"{len(offenders)}/{total} pages have no detectable analytics script.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )
