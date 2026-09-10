from seo_geo_engine.checks.framework import check, passed, failed, blocked
from seo_geo_engine.checks.helpers import pages


@check("LINK-004")
def check_internal_links_skip_redirects(site: dict):
    """
    Needs `linkResolutions` (crawl step fetches every unique internal href
    with redirects followed and records {url, status, redirected, finalUrl})
    — without it we can't tell a direct link from a redirected one, only
    that a link exists. Hrefs with no resolution entry are reported
    separately rather than silently assumed fine, same pattern as CRAWL-001.
    """
    resolutions = {r["url"]: r for r in (site.get("linkResolutions") or [])}

    all_hrefs = set()
    redirecting_hrefs = set()
    redirecting_evidence = []
    unresolved = set()
    for page in pages(site):
        for href in page.get("internalHrefs") or []:
            all_hrefs.add(href)
            res = resolutions.get(href)
            if res is None:
                unresolved.add(href)
                continue
            if res.get("redirected"):
                redirecting_hrefs.add(href)
                redirecting_evidence.append(f"{page['url']} links to {href} -> {res.get('finalUrl')} (redirect hop)")

    total = len(all_hrefs) or 1
    clean_fraction = (total - len(redirecting_hrefs) - len(unresolved)) / total

    if redirecting_hrefs:
        return failed(
            "LINK-004",
            f"{len(redirecting_hrefs)} unique redirecting URL(s) are linked to directly instead "
            f"of their final destination.",
            redirecting_evidence,
            fraction=clean_fraction,
        )
    if unresolved:
        return failed(
            "LINK-004",
            f"{len(unresolved)} linked URL(s) have no redirect-resolution data from the crawl "
            f"step, so this can't be fully assessed yet.",
            sorted(unresolved),
            fraction=clean_fraction,
        )
    return passed("LINK-004", "No internal link points through a redirect.")


@check("LINK-005")
def check_no_orphan_pages(site: dict):
    """A page counts as linked-to if ANY other page's internalHrefs
    references it — including nav links, since "is this page discoverable
    at all" is a different claim from "is it linked in body content
    specifically" (see a profile's own contextual/in-content linking checks
    for that distinction)."""
    all_pages = pages(site)
    inbound = set()
    for p in all_pages:
        self_url = p["url"].rstrip("/")
        for href in p.get("internalHrefs") or []:
            h = href.split("#", 1)[0].rstrip("/")
            if h and h != self_url:
                inbound.add(h)
    offenders = [p["url"] for p in all_pages if p["url"].rstrip("/") not in inbound]
    total = len(all_pages)
    if not offenders:
        return passed("LINK-005", f"All {total} pages have at least one inbound internal link.")
    return failed(
        "LINK-005",
        f"{len(offenders)}/{total} pages have no internal link pointing to them from any other page.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


@check("LINK-006")
def check_responsible_external_linking(site: dict):
    return blocked("LINK-006")


@check("LINK-007")
def check_outbound_rel_attributes(site: dict):
    return blocked("LINK-007")


@check("LINK-008")
def check_authority_flows_to_new_pages(site: dict):
    return blocked("LINK-008")
