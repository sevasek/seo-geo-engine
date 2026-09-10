import re
from urllib.parse import urlparse

from seo_geo_engine.checks.framework import check, passed, failed, blocked

# Known AI crawler user-agents worth checking robots.txt against — see the
# GEO framework's "make the site accessible to AI crawlers" idea.
AI_CRAWLER_AGENTS = [
    "GPTBot", "ChatGPT-User", "ClaudeBot", "Claude-Web", "anthropic-ai",
    "PerplexityBot", "Google-Extended", "Amazonbot", "Bytespider", "CCBot",
]

_ASSET_EXTENSIONS = (
    ".pdf", ".xlsx", ".xls", ".doc", ".docx", ".jpg", ".jpeg", ".png",
    ".gif", ".svg", ".zip", ".csv",
)


def _looks_like_a_page(url: str) -> bool:
    path = url.split("?")[0].rstrip("/")
    last_segment = path.rsplit("/", 1)[-1]
    if "@" in last_segment:  # malformed mailto: hrefs resolved as relative paths
        return False
    return not last_segment.lower().endswith(_ASSET_EXTENSIONS)


@check("CRAWL-001")
def check_sitemap_coverage(site: dict):
    """
    "Missing from the sitemap" only means something for URLs that are
    themselves indexable. Three cases are cleared, not counted as a gap:
    a legacy URL that 301s to an already-sitemapped page is doing exactly
    what it should (redirect, don't duplicate); a URL carrying
    `<meta name="robots" content="noindex">` is correctly absent from the
    sitemap, since the rule itself only covers "indexable" URLs; and a
    same-page URL fragment (`#section`) is never a distinct URL, so it's
    stripped before comparison rather than false-flagged as a page of its
    own. `discoveredNonSitemapPages` (populated by the crawl step by
    fetching each initially-missing URL with redirects followed and
    recording its `noindex` status) is what lets us tell a genuine gap
    apart from the redirect/noindex cases; without it we can't safely clear
    a URL, so it stays flagged with that uncertainty stated explicitly
    rather than silently assumed either way.
    """
    sitemap = {u.rstrip("/") + "/" for u in site["sitemapUrls"]}
    discovered = set()
    for p in site["pages"]:
        for href in p.get("internalHrefs") or []:
            href = href.split("#", 1)[0]  # same-page anchor, not a distinct URL
            if not href:
                continue
            discovered.add(href.rstrip("/") + "/")

    candidates = sorted(
        url for url in (discovered - sitemap)
        if _looks_like_a_page(url)
    )

    resolutions = {
        r["url"].rstrip("/") + "/": r
        for r in (site.get("discoveredNonSitemapPages") or [])
    }

    genuinely_missing = []
    resolved_as_redirects = []
    resolved_as_noindex = []
    unresolved = []
    for url in candidates:
        res = resolutions.get(url)
        if res is None:
            unresolved.append(url)
            continue
        final = (res.get("finalUrl") or "").rstrip("/") + "/"
        if res.get("noindex"):
            resolved_as_noindex.append(f"{url} — noindex, correctly excluded from the sitemap")
        elif res.get("redirected") and final in sitemap:
            resolved_as_redirects.append(f"{url} -> {final} (301, already sitemapped, not a gap)")
        else:
            genuinely_missing.append(f"{url} — resolves to {final or 'unknown'}, status {res.get('status')}")

    problems = genuinely_missing + [f"{u} — redirect status not checked at crawl time" for u in unresolved]

    if not problems:
        detail = (
            f"Every page-like URL discovered across the crawl ({len(discovered)} total) "
            f"is either in the {len(sitemap)}-URL sitemap, a confirmed redirect to a "
            f"sitemapped page, or correctly excluded as noindex."
        )
        cleared = resolved_as_redirects + resolved_as_noindex
        if cleared:
            detail += f" ({len(cleared)} cleared: {', '.join(cleared)})"
        return passed("CRAWL-001", detail)

    return failed(
        "CRAWL-001",
        f"{len(problems)} page-like URL(s) are linked from the site but not accounted for in the "
        f"{len(sitemap)}-URL sitemap (asset files like PDFs/images are excluded from this count; "
        f"confirmed redirects to already-sitemapped pages are also excluded).",
        problems,
        fraction=(len(candidates) - len(problems)) / len(candidates) if candidates else 1.0,
    )


def _parse_robots(robots_txt: str) -> dict:
    """Map user-agent (lowercased) -> list of Disallow paths."""
    groups: dict[str, list[str]] = {}
    current_agents: list[str] = []
    for line in robots_txt.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            current_agents = []
            continue
        m = re.match(r"(?i)user-agent:\s*(.+)", line)
        if m:
            agent = m.group(1).strip().lower()
            current_agents.append(agent)
            groups.setdefault(agent, [])
            continue
        m = re.match(r"(?i)disallow:\s*(.*)", line)
        if m and current_agents:
            path = m.group(1).strip()
            if path:
                for agent in current_agents:
                    groups.setdefault(agent, []).append(path)
    return groups


@check("CRAWL-002")
def check_ai_crawlers_not_blocked(site: dict):
    groups = _parse_robots(site["robotsTxt"])
    wildcard_disallows = groups.get("*", [])
    blocked_agents = []

    for agent in AI_CRAWLER_AGENTS:
        rules = groups.get(agent.lower(), wildcard_disallows)
        if "/" in rules:
            blocked_agents.append(agent)

    if not blocked_agents:
        return passed(
            "CRAWL-002",
            f"robots.txt doesn't fully disallow any of {len(AI_CRAWLER_AGENTS)} known AI crawlers.",
        )
    return failed(
        "CRAWL-002",
        f"{len(blocked_agents)} AI crawler(s) are fully disallowed in robots.txt.",
        blocked_agents,
        fraction=(len(AI_CRAWLER_AGENTS) - len(blocked_agents)) / len(AI_CRAWLER_AGENTS),
    )


def _combined_resolutions(site: dict) -> dict:
    """discoveredNonSitemapPages and linkResolutions can overlap (a URL not
    in the sitemap that's also a resolved internal href) — linkResolutions
    is the fuller set, so it wins on overlap."""
    combined: dict[str, dict] = {}
    for r in site.get("discoveredNonSitemapPages") or []:
        combined[r["url"]] = r
    for r in site.get("linkResolutions") or []:
        combined[r["url"]] = r
    return combined


@check("CRAWL-003")
def check_no_broken_internal_links(site: dict):
    """A resolution with status None means the request failed outright
    (DNS failure, connection refused) rather than the server returning a
    4xx/5xx. That's worse than a 404, not exempt from it: flagged the same
    way, not silently excluded by an isinstance(int) filter that only
    caught real HTTP status codes.

    Excludes malformed `mailto:` hrefs resolved as relative paths, same
    `_looks_like_a_page()` filter CRAWL-001 already applies to its own
    candidate set."""
    combined = _combined_resolutions(site)
    if not combined:
        return blocked("CRAWL-003")
    assessable = [r for r in combined.values() if _looks_like_a_page(r["url"])]
    broken = [
        r for r in assessable
        if r.get("status") is None or (isinstance(r.get("status"), int) and r["status"] >= 400)
    ]
    total = len(assessable)
    if not broken:
        return passed("CRAWL-003", f"No broken (4xx/5xx, or unreachable) internal link found across {total} resolved URL(s).")
    return failed(
        "CRAWL-003",
        f"{len(broken)}/{total} internal link(s) are broken or unreachable.",
        [f"{r['url']} — status {r['status'] if r.get('status') is not None else 'no response (connection failed)'}" for r in broken],
        fraction=(total - len(broken)) / total,
    )


@check("CRAWL-004")
def check_https_everywhere(site: dict):
    """Checks both a page's own URL and every internal href found on it.
    Scores by PAGE, not by pooling the page-URL count together with the
    per-page href count into one flat denominator: a page's own URL and its
    N internal hrefs aren't the same kind of unit, so counting them into one
    total lets a single bad page URL get diluted away by however many
    (good) links happen to sit on that page."""
    offenders = []
    failing_pages = 0
    for p in site["pages"]:
        page_ok = True
        if not p["url"].startswith("https://"):
            offenders.append(f"{p['url']} — page URL itself is not HTTPS")
            page_ok = False
        for href in p.get("internalHrefs") or []:
            if href.startswith("http://"):
                offenders.append(f"{p['url']} links to {href} — plain HTTP internal link")
                page_ok = False
        if not page_ok:
            failing_pages += 1
    total_pages = len(site["pages"])
    if not offenders:
        return passed("CRAWL-004", f"All {total_pages} page URLs and internal links use HTTPS.")
    return failed(
        "CRAWL-004",
        f"{failing_pages}/{total_pages} page(s) have a plain-HTTP page URL or internal link.",
        offenders,
        fraction=(total_pages - failing_pages) / total_pages,
    )


@check("CRAWL-005")
def check_redirects_are_clean_301s(site: dict):
    """Reads `redirectStatus` (the first hop's HTTP status) and
    `redirectHops` (total hop count), populated by the crawl step's
    resolveUrl()."""
    combined = _combined_resolutions(site)
    redirects = [r for r in combined.values() if r.get("redirected")]
    offenders = []
    for r in redirects:
        if r.get("redirectStatus") != 301:
            offenders.append(f"{r['url']} — {r.get('redirectStatus')} redirect, not 301")
        elif (r.get("redirectHops") or 1) > 1:
            offenders.append(f"{r['url']} — {r.get('redirectHops')}-hop redirect chain")
    total = len(redirects)
    if total == 0:
        return passed("CRAWL-005", "No internal redirects found to check.")
    if not offenders:
        return passed("CRAWL-005", f"All {total} redirect(s) are clean, single-hop 301s.")
    return failed(
        "CRAWL-005",
        f"{len(offenders)}/{total} redirect(s) use a non-301 status or a multi-hop chain.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


# At least this fraction of a page's JS-rendered word count should already
# be present in the raw HTML for a non-JS-executing crawler to see the page
# as substantive rather than an empty shell.
_NO_JS_RATIO_THRESHOLD = 0.5


@check("CRAWL-006")
def check_content_present_without_js(site: dict):
    """Reads `noJsWordCount` — word count from a plain (no browser, no JS
    execution) fetch of the same page, populated by the crawl step
    specifically for this check. Compared against the JS-rendered
    `wordCount` every other check already uses."""
    assessable = [p for p in site["pages"] if p.get("wordCount", 0) > 0 and p.get("noJsWordCount") is not None]
    if not assessable:
        return blocked("CRAWL-006")
    offenders = []
    for p in assessable:
        ratio = p["noJsWordCount"] / p["wordCount"]
        if ratio < _NO_JS_RATIO_THRESHOLD:
            offenders.append(f"{p['url']} — raw HTML has {round(ratio * 100)}% of the rendered word count")
    total = len(assessable)
    if not offenders:
        return passed("CRAWL-006", f"All {total} page(s) carry most of their content in the raw HTML.")
    return failed(
        "CRAWL-006",
        f"{len(offenders)}/{total} page(s) rely on JavaScript for most of their content.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


_CLEAN_URL_SEGMENT = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


@check("CRAWL-007")
def check_clean_url_paths(site: dict):
    offenders = []
    for p in site["pages"]:
        parsed = urlparse(p["url"])
        if parsed.query:
            offenders.append(f"{p['url']} — has a query string")
            continue
        segments = [s for s in parsed.path.split("/") if s]
        if any(not _CLEAN_URL_SEGMENT.match(seg) for seg in segments):
            offenders.append(f"{p['url']} — path isn't lowercase/hyphen-separated")
    total = len(site["pages"])
    if not offenders:
        return passed("CRAWL-007", f"All {total} page URLs are clean (lowercase, hyphenated, no query cruft).")
    return failed(
        "CRAWL-007",
        f"{len(offenders)}/{total} page URL(s) aren't clean.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


@check("CRAWL-008")
def check_sitemap_submitted_to_gsc(site: dict):
    """A sitemap.xml existing on the server (CRAWL-001) says nothing about
    whether Google actually has it registered — a site can have a perfect
    sitemap that was never submitted. Needs a separate Search Console
    enrichment step, same pattern as PERF-002/003 needing a PageSpeed
    enrichment step: blocked when this crawl wasn't enriched, not a
    vacuous pass."""
    gsc = site.get("searchConsole")
    if not gsc:
        return blocked("CRAWL-008")
    if not gsc.get("sitemapSubmitted"):
        return failed("CRAWL-008", "No sitemap has been submitted to Google Search Console.", [], fraction=0.0)
    errors = gsc.get("sitemapErrors", 0)
    warnings = gsc.get("sitemapWarnings", 0)
    if errors:
        return failed(
            "CRAWL-008",
            f"Sitemap is submitted but Search Console reports {errors} error(s).",
            [f"{errors} error(s), {warnings} warning(s) as of last processing"],
            fraction=0.0,
        )
    detail = "Sitemap is submitted to Search Console with no errors"
    detail += f" ({warnings} warning(s))." if warnings else "."
    return passed("CRAWL-008", detail)
