from collections import Counter

from seo_geo_engine.checks.framework import check, passed, failed
from seo_geo_engine.checks.helpers import pages


@check("META-001")
def check_title_length(site: dict):
    offenders = []
    for p in pages(site):
        title = p.get("title")
        if not title:
            offenders.append(f"{p['url']} — no <title> at all")
        elif not (30 <= p.get("titleLen", 0) <= 60):
            offenders.append(f"{p['url']} — {p['titleLen']} chars: {title!r}")
    total = len(pages(site))
    if not offenders:
        return passed("META-001", f"All {total} pages have a 30–60 char title.")
    return failed(
        "META-001",
        f"{len(offenders)}/{total} pages fail (missing or wrong length).",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


@check("META-002")
def check_meta_description_length(site: dict):
    offenders = []
    for p in pages(site):
        desc = p.get("metaDesc")
        if not desc:
            offenders.append(f"{p['url']} — no meta description")
        elif not (120 <= p.get("metaDescLen", 0) <= 160):
            offenders.append(f"{p['url']} — {p['metaDescLen']} chars")
    total = len(pages(site))
    if not offenders:
        return passed("META-002", f"All {total} pages have a 120–160 char meta description.")
    return failed(
        "META-002",
        f"{len(offenders)}/{total} pages fail (missing or wrong length).",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


@check("META-003")
def check_title_uniqueness(site: dict):
    all_pages = pages(site)
    counts = Counter(p["title"] for p in all_pages if p.get("title"))
    offenders = [
        f"{p['url']} — {p['title']!r} (shared by {counts[p['title']]} pages)"
        for p in all_pages
        if p.get("title") and counts[p["title"]] > 1
    ]
    total = len(all_pages)
    if not offenders:
        return passed("META-003", f"All {total} pages have a unique <title>.")
    return failed(
        "META-003",
        f"{len(offenders)}/{total} pages share a <title> with at least one other page.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


@check("META-004")
def check_self_referencing_canonical(site: dict):
    offenders = []
    for p in pages(site):
        canonical = (p.get("canonical") or "").rstrip("/")
        url = p["url"].rstrip("/")
        if not canonical:
            offenders.append(f"{p['url']} — no canonical tag")
        elif canonical != url:
            offenders.append(f"{p['url']} — canonical points to {canonical}")
    total = len(pages(site))
    if not offenders:
        return passed("META-004", f"All {total} pages have a self-referencing canonical tag.")
    return failed(
        "META-004",
        f"{len(offenders)}/{total} pages are missing a canonical tag or point somewhere else.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )
