"""URL classification for enrichment.

PageSpeed Insights cannot fetch localhost, `.test`, or private IPs — refuse
`--pagespeed` rather than spending quota on a guaranteed failure. Search
Console is about the live property, so the same URLs only warn for `--gsc`.
"""
from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


def hostname_of(url: str) -> str:
    host = urlparse(url).hostname or ""
    return host.strip("[]").rstrip(".").lower()


def is_psi_unreachable_url(url: str) -> bool:
    """True for localhost, `.test`, and private/loopback/link-local IPs."""
    host = hostname_of(url)
    if not host:
        return True
    if host == "localhost" or host.endswith(".localhost"):
        return True
    if host == "test" or host.endswith(".test"):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def unreachable_page_urls(site: dict) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for page in site.get("pages") or []:
        url = page.get("url") or ""
        if url and url not in seen and is_psi_unreachable_url(url):
            seen.add(url)
            found.append(url)
    return found


def crawl_looks_local(site: dict) -> bool:
    return bool(unreachable_page_urls(site))
