from seo_geo_engine.checks.framework import check, passed, failed, blocked
from seo_geo_engine.checks.helpers import pages

MAX_BYTES = 250_000


@check("PERF-001")
def check_html_payload_size(site: dict):
    total = len(pages(site))
    offenders = [f"{p['url']} — {p['bytes']:,} bytes" for p in pages(site) if p.get("bytes", 0) > MAX_BYTES]
    if not offenders:
        return passed("PERF-001", f"All {total} pages are under {MAX_BYTES:,} bytes of HTML.")
    return failed(
        "PERF-001",
        f"{len(offenders)}/{total} pages exceed {MAX_BYTES:,} bytes of raw HTML.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


# Google's "Good" thresholds — see web.dev/vitals. LCP/CLS/INP are tracked
# independently — a page can pass one and fail the other, which a single
# blended fraction would hide instead of surface.
_LCP_GOOD_MS = 2500
_CLS_GOOD = 0.1


def _field_data_caveat(assessable: list[dict]) -> str:
    """PERF-002 and PERF-003 both read the same PageSpeed Insights lab data
    (a separate enrichment step — own API key/quota, not part of the main
    crawl) and share this same caveat: "Good" thresholds are formally a
    field-data (CrUX) concept, and lab data is the closest available proxy,
    not the same claim — worded so it updates itself once the site actually
    has field data, rather than staying wrong forever after that happens."""
    has_field_data = any(p["pageSpeed"].get("hasFieldData") for p in assessable)
    if has_field_data:
        return (
            "lab data (single PageSpeed Insights run) — real-user field/CrUX data now "
            "exists for at least one page, but this check doesn't read it yet"
        )
    return "lab data (single PageSpeed Insights run) — no real-user field/CrUX data available for this site yet"


@check("PERF-002")
def check_lcp(site: dict):
    """Largest Contentful Paint, from PageSpeed Insights lab data."""
    assessable = [p for p in pages(site) if p.get("pageSpeed") and p["pageSpeed"].get("lcpMs") is not None]
    if not assessable:
        return blocked("PERF-002")
    caveat = _field_data_caveat(assessable)
    offenders = [
        f"{p['url']} — LCP {p['pageSpeed']['lcpMs'] / 1000:.2f}s (Good is <=2.5s)"
        for p in assessable
        if p["pageSpeed"]["lcpMs"] > _LCP_GOOD_MS
    ]
    total = len(assessable)
    if not offenders:
        return passed("PERF-002", f"LCP passes Google's 'Good' threshold on all {total} page(s) ({caveat}).")
    return failed(
        "PERF-002",
        f"{len(offenders)}/{total} page(s) miss Google's 'Good' LCP threshold ({caveat}).",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


@check("PERF-003")
def check_cls(site: dict):
    """Cumulative Layout Shift, from PageSpeed Insights lab data."""
    assessable = [p for p in pages(site) if p.get("pageSpeed") and p["pageSpeed"].get("cls") is not None]
    if not assessable:
        return blocked("PERF-003")
    caveat = _field_data_caveat(assessable)
    offenders = [
        f"{p['url']} — CLS {p['pageSpeed']['cls']} (Good is <=0.1)"
        for p in assessable
        if p["pageSpeed"]["cls"] > _CLS_GOOD
    ]
    total = len(assessable)
    if not offenders:
        return passed("PERF-003", f"CLS passes Google's 'Good' threshold on all {total} page(s) ({caveat}).")
    return failed(
        "PERF-003",
        f"{len(offenders)}/{total} page(s) miss Google's 'Good' CLS threshold ({caveat}).",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


@check("PERF-004")
def check_inp(site: dict):
    """Interaction to Next Paint — no lab-data substitute exists; PageSpeed
    Insights only reports it from real-user field/CrUX data, which a
    lower-traffic site won't have enough of for Google's Chrome UX Report
    yet (see _field_data_caveat)."""
    return blocked("PERF-004")
