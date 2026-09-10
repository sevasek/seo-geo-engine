"""
Gathers a crawl dataset for a profile — live URL by default, or a profile's
own repo booted locally with --local. Either way this shells out to the
same packaged crawl.js; local-serve only changes how the target URL is
obtained (see local_serve.py), the crawl itself and everything downstream
(report/remediation) is identical either way.

Usage:
    python3 -m seo_geo_engine.crawl.run --profile site.yaml --out audits/data/site-crawl-2026-09-10.json
    python3 -m seo_geo_engine.crawl.run --profile site.yaml --local --out /tmp/site-crawl.json
"""
import argparse
import subprocess
import sys
from pathlib import Path

from seo_geo_engine.crawl.local_serve import LocalDevConfig, LocalServer
from seo_geo_engine.paths import crawler_dir
from seo_geo_engine.profile import load_profile


def _run_crawl_js(origin: str, out_path: Path, ua: str = "", sitemap_url: str = "", pages_file: str = "") -> None:
    cmd = ["node", str(crawler_dir() / "crawl.js"), "--origin", origin, "--out", str(out_path)]
    if ua:
        cmd += ["--ua", ua]
    if pages_file:
        cmd += ["--pages-file", pages_file]
    elif sitemap_url:
        cmd += ["--sitemap-url", sitemap_url]
    result = subprocess.run(cmd, cwd=crawler_dir(), capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"crawl.js failed (exit {result.returncode}):\n{result.stdout}\n{result.stderr}")
    print(result.stderr, file=sys.stderr)  # crawl.js logs progress to stderr


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, help="path to a site.yaml profile")
    parser.add_argument("--local", action="store_true", help="boot the profile's own local_dev server instead of crawling its live base_url")
    parser.add_argument("--out", required=True, help="output path for the crawl JSON")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    profile = load_profile(args.profile)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.local:
        config = LocalDevConfig.from_profile_dict(profile.local_dev, profile.root)
        pages_file = profile.local_dev.get("pages_file", "")
        if pages_file:
            pages_file = str((profile.root / pages_file).resolve())
        with LocalServer(config) as base_url:
            _run_crawl_js(base_url, out_path, ua=profile.user_agent, pages_file=pages_file)
    else:
        if not profile.base_url:
            parser.error("This profile has no site.base_url in site.yaml — required for a live crawl.")
        _run_crawl_js(profile.base_url, out_path, ua=profile.user_agent, sitemap_url=profile.sitemap_url)

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
