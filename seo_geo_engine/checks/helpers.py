"""Small shared helpers for reading the crawled site dict. Not standard-tagged
themselves — just plumbing the check modules use.

Site-specific facts (which pages count as "service pages", etc.) are read
from site["profile"] rather than hardcoded, so these helpers work for any
profile. A profile that leaves a field unset gets the least-surprising
fallback: no `service_page_pattern` configured means "count every page" —
see check_word_count/check_service_schema_present docstrings for why that
matters (division by zero on an empty target list would be worse)."""


def pages(site: dict) -> list[dict]:
    return site["pages"]


def _profile(site: dict) -> dict:
    return site.get("profile") or {}


def service_pages(site: dict) -> list[dict]:
    """Individual service pages — excludes the profile's own service-index
    URL, if one is configured. With no `service_page_pattern` set, every
    page is treated as a service page (an empty pattern is a substring of
    every URL) — the least-surprising default for a profile that hasn't
    defined the concept."""
    cfg = _profile(site).get("pages", {})
    pattern = cfg.get("service_page_pattern", "")
    index_url = (cfg.get("service_index_url") or "").rstrip("/")
    return [
        p for p in pages(site)
        if pattern in p["url"]
        and (not index_url or p["url"].rstrip("/") != index_url)
    ]


def urls(items: list[dict]) -> list[str]:
    return [p["url"] for p in items]
