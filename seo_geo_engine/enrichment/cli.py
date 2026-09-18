"""
Merge PageSpeed Insights and/or Search Console data into a crawl JSON.

Usage:
    seo-geo-enrich audits/data/site-crawl-<date>.json --profile site.yaml \\
        --pagespeed --gsc [--out PATH] [--no-cache]

Default --out overwrites the crawl JSON in place. Either flag may be
omitted; omitted keys stay absent/null and the corresponding checks stay
runtime-blocked. Credentials never live in site.yaml — see
docs/design/enrichment.md.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from seo_geo_engine.enrichment.errors import EnrichmentError
from seo_geo_engine.enrichment.pagespeed import enrich_pagespeed, resolve_pagespeed_api_key
from seo_geo_engine.enrichment.search_console import enrich_search_console
from seo_geo_engine.profile import load_profile


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Merge PageSpeed Insights / Search Console into a crawl JSON."
    )
    parser.add_argument(
        "site_crawl",
        help="path to a site-crawl JSON produced by the crawler",
    )
    parser.add_argument("--profile", required=True, help="path to a site.yaml profile")
    parser.add_argument(
        "--pagespeed",
        action="store_true",
        help="fetch PageSpeed Insights (mobile) for each crawled page URL",
    )
    parser.add_argument(
        "--gsc",
        action="store_true",
        help="fetch Search Console sitemap status for profile.enrichment.gsc_property",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="output path (default: overwrite the input crawl JSON in place)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="do not read or write audits/cache/pagespeed/",
    )
    return parser


def _write_site(path: Path, site: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(site, indent=2) + "\n", encoding="utf-8")


def run(
    argv: list[str] | None = None,
    *,
    env: dict[str, str] | None = None,
    psi_fetch=None,
    gsc_client_factory=None,
    sleep=None,
    stderr=None,
) -> int:
    """Programmable entry point. Returns a process exit code (0 or 2)."""
    err = stderr if stderr is not None else sys.stderr
    parser = _build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    environ = env if env is not None else os.environ

    crawl_path = Path(args.site_crawl)
    if not crawl_path.is_file():
        print(f"seo-geo-enrich: crawl JSON not found: {crawl_path}", file=err)
        return 2

    try:
        site = json.loads(crawl_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"seo-geo-enrich: invalid JSON in {crawl_path}: {exc}", file=err)
        return 2
    if not isinstance(site, dict):
        print(f"seo-geo-enrich: crawl JSON must be an object: {crawl_path}", file=err)
        return 2

    profile = load_profile(args.profile)
    out_path = Path(args.out) if args.out else crawl_path
    failures: list[str] = []
    ran = False

    if not args.pagespeed and not args.gsc:
        print(
            "seo-geo-enrich: neither --pagespeed nor --gsc given; crawl JSON unchanged "
            "(omitted keys stay absent/null)",
            file=err,
        )
        return 0

    if args.pagespeed:
        key = resolve_pagespeed_api_key(profile, environ)
        try:
            enrich_pagespeed(
                site,
                key,
                use_cache=not args.no_cache,
                fetch=psi_fetch,
                sleep=sleep,
            )
            ran = True
        except EnrichmentError as exc:
            print(f"seo-geo-enrich: {exc}", file=err)
            failures.append("pagespeed")

    if args.gsc:
        try:
            enrich_search_console(
                site,
                profile,
                client_factory=gsc_client_factory,
                env=environ,
                warn=lambda msg: print(f"seo-geo-enrich: {msg}", file=err),
            )
            ran = True
        except EnrichmentError as exc:
            print(f"seo-geo-enrich: {exc}", file=err)
            failures.append("gsc")

    if ran:
        _write_site(out_path, site)
        print(f"Wrote {out_path}")

    return 2 if failures else 0


def main(argv: list[str] | None = None) -> None:
    sys.exit(run(argv))


if __name__ == "__main__":
    main()
