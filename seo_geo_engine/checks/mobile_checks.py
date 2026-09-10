from seo_geo_engine.checks.framework import check, passed, failed
from seo_geo_engine.checks.helpers import pages


@check("MOBILE-001")
def check_responsive_viewport(site: dict):
    offenders = []
    for p in pages(site):
        viewport = p.get("viewport") or ""
        if "width=device-width" not in viewport:
            offenders.append(f"{p['url']} — viewport: {viewport!r}")
    total = len(pages(site))
    if not offenders:
        return passed("MOBILE-001", f"All {total} pages declare a responsive viewport meta tag.")
    return failed(
        "MOBILE-001",
        f"{len(offenders)}/{total} pages are missing a responsive viewport meta tag.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )
