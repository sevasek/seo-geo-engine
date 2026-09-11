"""Search Console sitemap list → `site.searchConsole`.

GSC client libraries are an optional extra (`pip install seo-geo-engine[enrich]`).
This module lazy-imports them so a base `pip install` stays Google-free.
"""
from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from seo_geo_engine.enrichment.errors import EnrichmentError
from seo_geo_engine.enrichment.urls import crawl_looks_local

GSC_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
LOCAL_GSC_WARNING = (
    "warning: crawl looks local (localhost / .test / private IP); "
    "--gsc will merge live Search Console data onto this snapshot"
)


def gsc_property_url(profile) -> str:
    enrichment = getattr(profile, "enrichment", None) or {}
    return (enrichment.get("gsc_property") or "").strip()


def expected_sitemap_urls(profile) -> list[str]:
    """Profile crawl.sitemap_url, plus `${base_url}/sitemap.xml`."""
    found: list[str] = []
    sitemap = (getattr(profile, "sitemap_url", None) or "").strip()
    if sitemap:
        found.append(sitemap)
    base = (getattr(profile, "base_url", None) or "").strip().rstrip("/")
    if base:
        fallback = f"{base}/sitemap.xml"
        if fallback not in found:
            found.append(fallback)
    return found


def _norm_url(url: str) -> str:
    parsed = urlparse(url.strip())
    path = parsed.path.rstrip("/") or ""
    netloc = parsed.netloc.lower()
    scheme = (parsed.scheme or "https").lower()
    if parsed.scheme == "" and url.strip().lower().startswith("sc-domain:"):
        return url.strip().lower()
    return f"{scheme}://{netloc}{path}"


def urls_match(left: str, right: str) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True
    return _norm_url(left) == _norm_url(right)


def property_in_site_list(property_url: str, site_entries: Iterable[dict]) -> bool:
    for entry in site_entries:
        candidate = (entry.get("siteUrl") or "").strip()
        if candidate and urls_match(candidate, property_url):
            return True
    return False


def _as_int(value: Any) -> int:
    if value is None or value is False:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def map_sitemaps(
    sitemaps: Iterable[dict],
    expected_urls: Iterable[str],
) -> dict[str, Any]:
    """`sitemapSubmitted` is true if any GSC sitemap URL matches the profile.

    Errors/warnings are summed for matching sitemaps only.
    """
    expected = [u for u in expected_urls if u]
    matching = [
        row
        for row in sitemaps
        if any(urls_match(row.get("path") or "", exp) for exp in expected)
    ]
    return {
        "sitemapSubmitted": bool(matching),
        "sitemapErrors": sum(_as_int(row.get("errors")) for row in matching),
        "sitemapWarnings": sum(_as_int(row.get("warnings")) for row in matching),
    }


def apply_search_console(
    site: dict,
    blob: dict[str, Any],
) -> dict:
    site["searchConsole"] = blob
    return site


class GscClient:
    """Thin wrapper so tests can fake sites.list / sitemaps.list without Google libs."""

    def list_sites(self) -> list[dict]:
        raise NotImplementedError

    def list_sitemaps(self, site_url: str) -> list[dict]:
        raise NotImplementedError


class DiscoveryGscClient(GscClient):
    def __init__(self, service):
        self._service = service

    def list_sites(self) -> list[dict]:
        response = self._service.sites().list().execute()
        return list(response.get("siteEntry") or [])

    def list_sitemaps(self, site_url: str) -> list[dict]:
        response = self._service.sitemaps().list(siteUrl=site_url).execute()
        return list(response.get("sitemap") or [])


def google_libs_available() -> bool:
    try:
        import google.auth  # noqa: F401
        import googleapiclient.discovery  # noqa: F401
    except ImportError:
        return False
    return True


def _credentials_from_env(env: dict[str, str]):
    path = (env.get("GSC_CREDENTIALS_JSON") or "").strip()
    if path:
        from google.oauth2 import service_account

        cred_path = Path(path)
        if not cred_path.is_file():
            raise EnrichmentError(
                f"--gsc: GSC_CREDENTIALS_JSON path does not exist: {path}"
            )
        return service_account.Credentials.from_service_account_file(
            str(cred_path), scopes=[GSC_SCOPE]
        )
    import google.auth

    try:
        creds, _project = google.auth.default(scopes=[GSC_SCOPE])
    except Exception as exc:
        raise EnrichmentError(
            "--gsc requires Application Default Credentials or GSC_CREDENTIALS_JSON "
            "(a path to a service-account JSON file)"
        ) from exc
    if creds is None:
        raise EnrichmentError(
            "--gsc requires Application Default Credentials or GSC_CREDENTIALS_JSON "
            "(a path to a service-account JSON file)"
        )
    return creds


def build_gsc_client(env: dict[str, str] | None = None) -> GscClient:
    if not google_libs_available():
        raise EnrichmentError(
            "--gsc requires the optional extra: pip install seo-geo-engine[enrich]"
        )
    from googleapiclient.discovery import build

    environ = env if env is not None else os.environ
    creds = _credentials_from_env(dict(environ))
    service = build("webmasters", "v3", credentials=creds, cache_discovery=False)
    return DiscoveryGscClient(service)


def enrich_search_console(
    site: dict,
    profile,
    *,
    client: GscClient | None = None,
    client_factory: Callable[[], GscClient] | None = None,
    env: dict[str, str] | None = None,
    warn: Callable[[str], None] | None = None,
) -> dict:
    property_url = gsc_property_url(profile)
    if not property_url:
        raise EnrichmentError(
            "--gsc requires profile.enrichment.gsc_property (the Search Console "
            "property URL, not a secret)"
        )

    if crawl_looks_local(site) and warn is not None:
        warn(LOCAL_GSC_WARNING)

    gsc = client
    if gsc is None:
        factory = client_factory or (lambda: build_gsc_client(env))
        gsc = factory()

    try:
        site_entries = gsc.list_sites()
    except EnrichmentError:
        raise
    except Exception as exc:
        raise EnrichmentError(f"--gsc: failed to list Search Console sites: {exc}") from exc

    if not property_in_site_list(property_url, site_entries):
        raise EnrichmentError(
            f"--gsc: property {property_url!r} is not in this credential's site list; "
            "not writing a fake sitemapSubmitted: false"
        )

    try:
        sitemaps = gsc.list_sitemaps(property_url)
    except Exception as exc:
        raise EnrichmentError(
            f"--gsc: failed to list sitemaps for {property_url}: {exc}"
        ) from exc

    blob = map_sitemaps(sitemaps, expected_sitemap_urls(profile))
    return apply_search_console(site, blob)
