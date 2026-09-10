"""
Acme Example Co's own checks — the worked example of a profile adding rules
the engine's shipped defaults can't cover generically (an entity/cluster
map, a map-embed convention, an About-page convention). Imported by
seo_geo_engine.profile.import_profile_code() via the `checks_module` name in
site.yaml, same mechanism the engine's own built-in checks use.
"""
from seo_geo_engine.checks.framework import check, passed, failed, blocked
from seo_geo_engine.checks.helpers import pages


@check("LOCAL-001")
def check_map_links_to_gbp(site: dict):
    assessed = 0
    offenders = []
    for p in pages(site):
        for iframe_src in (p.get("iframes") or []):
            if "google.com/maps" not in iframe_src:
                continue
            assessed += 1
            if "place_id=" not in iframe_src and "cid=" not in iframe_src:
                offenders.append(f"{p['url']} — map embed searches address/name text, not a GBP listing")
    if assessed == 0:
        return passed("LOCAL-001", "No Google Maps embeds found to check.")
    if not offenders:
        return passed("LOCAL-001", f"All {assessed} map embed(s) link to a Google Business Profile listing.")
    return failed(
        "LOCAL-001",
        f"{len(offenders)}/{assessed} map embed(s) search by address/name text instead of linking to a GBP listing.",
        offenders,
        fraction=(assessed - len(offenders)) / assessed,
    )


@check("TRUST-001")
def check_about_page_has_real_people(site: dict):
    about_pages = [p for p in pages(site) if "/about" in p["url"]]
    if not about_pages:
        return failed("TRUST-001", "No About/Team page found.", [], fraction=0.0)
    p = about_pages[0]
    if p.get("imageCount", 0) <= 1 or p.get("wordCount", 0) < 150:
        return failed(
            "TRUST-001",
            f"{p['url']} exists but looks like a stub (<=1 image or <150 words) — not a real About/Team page.",
            [p["url"]],
            fraction=0.0,
        )
    return passed("TRUST-001", f"{p['url']} is a substantive About/Team page.")


@check("LINK-001")
def check_contextual_linking_within_clusters(site: dict):
    """Reads the profile's own entity_clusters — a profile-added check can
    read site["profile"] exactly like a built-in one, no special-casing."""
    clusters = (site.get("profile") or {}).get("entity_clusters") or {}
    if not clusters:
        return blocked("LINK-001")
    by_url = {p["url"].rstrip("/"): p for p in pages(site)}
    offenders = []
    assessed = 0
    for cluster_name, urls in clusters.items():
        norm_urls = {u.rstrip("/") for u in urls}
        for url in norm_urls:
            page = by_url.get(url)
            if page is None:
                continue
            assessed += 1
            contextual = {h.rstrip("/") for h in (page.get("contentInternalHrefs") or [])}
            other_members = norm_urls - {url}
            if not (contextual & other_members):
                offenders.append(f"{url} — no in-content link to a {cluster_name} cluster-mate")
    if assessed == 0:
        return passed("LINK-001", "No clustered pages from entity_clusters were found in this crawl.")
    if not offenders:
        return passed("LINK-001", "Every clustered page links in-content to at least one cluster-mate.")
    return failed(
        "LINK-001",
        f"{len(offenders)}/{assessed} clustered pages have no in-content link to a related page.",
        offenders,
        fraction=(assessed - len(offenders)) / assessed,
    )


@check("LINK-002")
def check_money_page_anchor_text_match(site: dict):
    return blocked("LINK-002")
