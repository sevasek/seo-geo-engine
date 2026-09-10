from seo_geo_engine.checks.framework import check, passed, failed
from seo_geo_engine.checks.helpers import pages


@check("OG-001")
def check_no_duplicate_og_core_tags(site: dict):
    watched = {"og:title", "og:url", "og:type"}
    offenders = []
    for p in pages(site):
        dup = watched & set(p.get("dupOgTags") or [])
        if dup:
            offenders.append(f"{p['url']} — duplicated {sorted(dup)}")
    total = len(pages(site))
    if not offenders:
        return passed("OG-001", f"No duplicate og:title/og:url/og:type on any of {total} pages.")
    return failed(
        "OG-001",
        f"{len(offenders)}/{total} pages have at least one duplicated core OG tag.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


@check("OG-002")
def check_og_description_present(site: dict):
    offenders = []
    for p in pages(site):
        desc = p.get("ogDescription")
        if not desc or not desc.strip():
            offenders.append(f"{p['url']} — og:description missing or empty")
    total = len(pages(site))
    if not offenders:
        return passed("OG-002", f"All {total} pages have a non-empty og:description.")
    return failed(
        "OG-002",
        f"{len(offenders)}/{total} pages have a missing or empty og:description.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )
