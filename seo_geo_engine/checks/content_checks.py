from seo_geo_engine.checks.framework import check, passed, failed, blocked
from seo_geo_engine.checks.helpers import pages, service_pages


@check("CONTENT-001")
def check_word_count(site: dict):
    targets = service_pages(site)
    if not targets:
        return passed("CONTENT-001", "No service pages found for this profile — nothing to check.")
    offenders = [f"{p['url']} — {p.get('wordCount', 0)} words" for p in targets if p.get("wordCount", 0) < 500]
    if not offenders:
        return passed("CONTENT-001", f"All {len(targets)} service pages have 500+ words.")
    return failed(
        "CONTENT-001",
        f"{len(offenders)}/{len(targets)} service pages fall short of 500 words.",
        offenders,
        fraction=(len(targets) - len(offenders)) / len(targets),
    )


# At least this fraction of a page's visible text should sit inside real
# <p> elements for a content extractor to recognize the page as substantive
# prose rather than mostly-chrome. Permissive on purpose — headings, list
# items, and captions are legitimately outside <p> even on a well-marked-up
# page, so this isn't looking for 100%.
_P_TAG_RATIO_THRESHOLD = 0.5


@check("CONTENT-002")
def check_paragraph_markup(site: dict):
    assessable = [p for p in pages(site) if p.get("wordCount", 0) > 0]
    offenders = []
    for p in assessable:
        ratio = p.get("pTagWordCount", 0) / p["wordCount"]
        if ratio < _P_TAG_RATIO_THRESHOLD:
            offenders.append(f"{p['url']} — {round(ratio * 100)}% of visible text is inside <p> tags")
    total = len(assessable)
    if total == 0:
        return passed("CONTENT-002", "No pages with visible text to check.")
    if not offenders:
        return passed(
            "CONTENT-002",
            f"All {total} page(s) with visible text carry most of it in real <p> tags.",
        )
    return failed(
        "CONTENT-002",
        f"{len(offenders)}/{total} page(s) have less than {int(_P_TAG_RATIO_THRESHOLD * 100)}% of "
        f"their visible text inside <p> tags — a content extractor may not recognize the rest as prose.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


@check("CONTENT-003")
def check_freshness_signal(site: dict):
    """Checks presence of a dateModified property only — whether it's
    actually kept up to date as content changes is a process question a
    crawl can't verify, same as CONTENT-004 through CONTENT-008 below."""
    offenders = [p["url"] for p in pages(site) if not p.get("dateModified")]
    total = len(pages(site))
    if not offenders:
        return passed("CONTENT-003", f"All {total} pages carry a dateModified signal in structured data.")
    return failed(
        "CONTENT-003",
        f"{len(offenders)}/{total} pages have no dateModified (or equivalent freshness) property in their JSON-LD.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


@check("CONTENT-004")
def check_matches_documented_search_intent(site: dict):
    return blocked("CONTENT-004")


@check("CONTENT-005")
def check_no_keyword_stuffing(site: dict):
    return blocked("CONTENT-005")


@check("CONTENT-006")
def check_formatted_for_skimming(site: dict):
    return blocked("CONTENT-006")


@check("CONTENT-007")
def check_information_gain(site: dict):
    return blocked("CONTENT-007")


@check("CONTENT-008")
def check_claims_backed_by_sources(site: dict):
    return blocked("CONTENT-008")
