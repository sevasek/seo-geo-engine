"""PageSpeed Insights v5 → `page.pageSpeed` {lcpMs, cls, hasFieldData}.

One sequential request per crawled URL, strategy=mobile. Cache by
(url, date, strategy) under audits/cache/pagespeed/. Never writes INP.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from seo_geo_engine.enrichment.errors import EnrichmentError
from seo_geo_engine.enrichment.urls import unreachable_page_urls

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
PSI_STRATEGY = "mobile"
PSI_DELAY_S = 1.0
DEFAULT_CACHE_DIR = Path("audits/cache/pagespeed")
_LCP_AUDIT = "largest-contentful-paint"
_CLS_AUDIT = "cumulative-layout-shift"


def resolve_pagespeed_api_key(profile, env: dict[str, str] | None = None) -> str:
    """Read the API key from the env var named by the profile (default PAGESPEED_API_KEY)."""
    environ = env if env is not None else os.environ
    enrichment = getattr(profile, "enrichment", None) or {}
    var_name = enrichment.get("pagespeed_api_key_env") or "PAGESPEED_API_KEY"
    return (environ.get(var_name) or "").strip()


def _audits(payload: dict) -> dict:
    lighthouse = payload.get("lighthouseResult") or {}
    if isinstance(lighthouse.get("audits"), dict):
        return lighthouse["audits"]
    if isinstance(payload.get("audits"), dict):
        return payload["audits"]
    return {}


def _numeric_value(audits: dict, audit_id: str) -> float | int | None:
    node = audits.get(audit_id)
    if isinstance(node, dict) and "numericValue" in node:
        return node["numericValue"]
    metrics = audits.get("metrics")
    if isinstance(metrics, dict):
        nested = metrics.get(audit_id)
        if isinstance(nested, dict) and "numericValue" in nested:
            return nested["numericValue"]
    return None


def map_psi_response(payload: dict) -> dict[str, Any]:
    """Pin the JSON paths against a recorded PSI v5 body.

    Missing LCP/CLS → that key is omitted. INP is never copied.
    `hasFieldData` is bool(loadingExperience.metrics).
    """
    audits = _audits(payload)
    loading = payload.get("loadingExperience") or {}
    mapped: dict[str, Any] = {
        "hasFieldData": bool(loading.get("metrics")),
    }
    lcp = _numeric_value(audits, _LCP_AUDIT)
    if lcp is not None:
        mapped["lcpMs"] = lcp
    cls = _numeric_value(audits, _CLS_AUDIT)
    if cls is not None:
        mapped["cls"] = cls
    return mapped


def cache_filename(url: str, cache_date: str, strategy: str = PSI_STRATEGY) -> str:
    digest = hashlib.sha256(f"{url}\n{cache_date}\n{strategy}".encode()).hexdigest()[:16]
    return f"{cache_date}_{strategy}_{digest}.json"


def _utc_date(now: datetime | None = None) -> str:
    clock = now if now is not None else datetime.now(timezone.utc)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=timezone.utc)
    return clock.astimezone(timezone.utc).date().isoformat()


def default_psi_fetch(url: str, api_key: str, timeout: float = 30) -> dict:
    params = urllib.parse.urlencode(
        {"url": url, "strategy": PSI_STRATEGY, "key": api_key}
    )
    request = urllib.request.Request(
        f"{PSI_ENDPOINT}?{params}",
        headers={"User-Agent": "seo-geo-engine-enrich/0.1"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            body = resp.read()
    except urllib.error.HTTPError as exc:
        snippet = ""
        try:
            snippet = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            snippet = str(exc)
        raise EnrichmentError(
            f"PageSpeed Insights HTTP {exc.code} for {url}: {snippet}"
        ) from exc
    except urllib.error.URLError as exc:
        raise EnrichmentError(
            f"PageSpeed Insights request failed for {url}: {exc.reason}"
        ) from exc
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise EnrichmentError(f"PageSpeed Insights returned non-JSON for {url}") from exc
    if not isinstance(payload, dict):
        raise EnrichmentError(f"PageSpeed Insights returned a non-object for {url}")
    return payload


def _read_cache(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def apply_pagespeed(site: dict, payloads_by_url: dict[str, dict]) -> dict:
    """Merge mapped PSI payloads onto matching `pages` entries. Mutates `site`."""
    for page in site.get("pages") or []:
        url = page.get("url")
        if not url or url not in payloads_by_url:
            continue
        page["pageSpeed"] = map_psi_response(payloads_by_url[url])
    return site


def enrich_pagespeed(
    site: dict,
    api_key: str,
    *,
    cache_dir: Path | None = None,
    use_cache: bool = True,
    fetch: Callable[[str, str], dict] | None = None,
    sleep: Callable[[float], None] | None = None,
    now: datetime | None = None,
    delay_s: float = PSI_DELAY_S,
) -> dict:
    """Fetch (or cache-read) PSI for every crawled page and merge `pageSpeed`.

    Callers that already checked credentials/URL reachability pass an `api_key`.
    Sequential on purpose — PSI quota is why this is not inside the crawl loop.
    """
    blocked = unreachable_page_urls(site)
    if blocked:
        shown = ", ".join(blocked[:5])
        extra = f" (and {len(blocked) - 5} more)" if len(blocked) > 5 else ""
        raise EnrichmentError(
            "refusing --pagespeed: crawl contains URLs PageSpeed Insights cannot "
            f"fetch (localhost / .test / private IP): {shown}{extra}"
        )
    if not api_key:
        raise EnrichmentError(
            "--pagespeed requires an API key in PAGESPEED_API_KEY (or the env "
            "var named by profile.enrichment.pagespeed_api_key_env)"
        )

    pages = [p for p in (site.get("pages") or []) if p.get("url")]
    if not pages:
        return site

    cache_root = Path(cache_dir) if cache_dir is not None else DEFAULT_CACHE_DIR
    cache_date = _utc_date(now)
    fetch_fn = fetch or default_psi_fetch
    sleeper = sleep if sleep is not None else time.sleep
    payloads: dict[str, dict] = {}
    network_calls = 0

    for page in pages:
        url = page["url"]
        cache_path = cache_root / cache_filename(url, cache_date, PSI_STRATEGY)
        payload = _read_cache(cache_path) if use_cache else None
        if payload is None:
            if network_calls:
                sleeper(delay_s)
            payload = fetch_fn(url, api_key)
            network_calls += 1
            if use_cache:
                cache_root.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(
                    json.dumps(payload, indent=2) + "\n", encoding="utf-8"
                )
        payloads[url] = payload

    return apply_pagespeed(site, payloads)
