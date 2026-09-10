import re

from seo_geo_engine.checks.framework import check, passed, failed
from seo_geo_engine.checks.helpers import pages

NUMERAL_ONLY = re.compile(r"^\d+$")


@check("HEAD-001")
def check_single_h1(site: dict):
    offenders = []
    for p in pages(site):
        n = p.get("h1Count", 0)
        if n != 1:
            offenders.append(f"{p['url']} — {n} <h1> elements")
    total = len(pages(site))
    if not offenders:
        return passed("HEAD-001", f"All {total} pages have exactly one <h1>.")
    return failed(
        "HEAD-001",
        f"{len(offenders)}/{total} pages have zero or multiple <h1> elements.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


@check("HEAD-002")
def check_no_numeral_only_headings(site: dict):
    offenders = []
    for p in pages(site):
        numerals = [h for h in (p.get("h1s") or []) if NUMERAL_ONLY.match(h.strip())]
        if numerals:
            offenders.append(f"{p['url']} — numeral heading(s) {numerals}")
    total = len(pages(site))
    if not offenders:
        return passed("HEAD-002", f"No bare-numeral headings on any of {total} pages.")
    return failed(
        "HEAD-002",
        f"{len(offenders)}/{total} pages mark up a step-counter numeral as a heading.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


@check("HEAD-003")
def check_has_h2(site: dict):
    offenders = []
    for p in pages(site):
        if p.get("h2Count", 0) < 1:
            offenders.append(f"{p['url']} — 0 <h2> elements")
    total = len(pages(site))
    if not offenders:
        return passed("HEAD-003", f"All {total} pages have at least one <h2>.")
    return failed(
        "HEAD-003",
        f"{len(offenders)}/{total} pages have zero <h2> elements.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


@check("HEAD-004")
def check_no_skipped_heading_levels(site: dict):
    """Reads `headingSequence` — heading levels in DOM order, e.g. ["h1","h2","h3"].
    A level is a "skip" if it's more than one deeper than the deepest level
    already seen on the page (h1 -> h3 with no h2 in between)."""
    offenders = []
    for p in pages(site):
        seq = p.get("headingSequence") or []
        seen_max = 0
        skips = []
        for tag in seq:
            level = int(tag[1])
            if level > seen_max + 1:
                skips.append(tag)
            seen_max = max(seen_max, level)
        if skips:
            offenders.append(f"{p['url']} — skipped level(s): {skips}")
    total = len(pages(site))
    if not offenders:
        return passed("HEAD-004", f"No skipped heading levels on any of {total} pages.")
    return failed(
        "HEAD-004",
        f"{len(offenders)}/{total} pages skip a heading level (e.g. an <h3> before any <h2>).",
        offenders,
        fraction=(total - len(offenders)) / total,
    )
