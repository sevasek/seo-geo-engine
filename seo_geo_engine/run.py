"""
Gather-and-score orchestrator: crawl (or reuse a crawl JSON) → optional
enrich → report → plan-sync → queue → HTML dashboard.

The work-the-queue half stays step-by-step (`seo-geo-remediate --id`,
`seo-geo-update-status`, apply out of band, then `seo-geo-verify`).
This command does not write to a CMS and does not mark rows verified.

Usage:
    seo-geo-run --profile site.yaml --date 2026-09-18
    seo-geo-run --profile site.yaml --local --date 2026-09-18
    seo-geo-run --profile site.yaml --enrich pagespeed,gsc --date 2026-09-18
    seo-geo-run --profile site.yaml --from-crawl path/to/site-crawl.json --date 2026-09-18
"""
from __future__ import annotations

import argparse
import datetime as _datetime
import shutil
import sys
from pathlib import Path

from seo_geo_engine.crawl.run import main as crawl_main
from seo_geo_engine.profile import load_profile
from seo_geo_engine.remediation.plan import main as queue_main
from seo_geo_engine.remediation.plan_sync import main as plan_sync_main
from seo_geo_engine.render_html_report import main as html_main
from seo_geo_engine.report import main as report_main


def _parse_enrich(raw: str) -> list[str]:
    if not raw:
        return []
    tokens = [part.strip().lower() for part in raw.split(",") if part.strip()]
    unknown = [t for t in tokens if t not in ("pagespeed", "gsc")]
    if unknown:
        raise ValueError(
            f"unknown --enrich value(s): {', '.join(unknown)} "
            "(expected pagespeed, gsc, or pagespeed,gsc)"
        )
    # Preserve order but drop duplicates.
    seen: list[str] = []
    for token in tokens:
        if token not in seen:
            seen.append(token)
    return seen


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, help="path to a site.yaml profile")
    parser.add_argument(
        "--date",
        default=_datetime.date.today().isoformat(),
        help="snapshot date (default: today, ISO YYYY-MM-DD)",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="boot the profile's local_dev server instead of crawling base_url",
    )
    parser.add_argument(
        "--from-crawl",
        help="skip a live crawl; copy this site-crawl JSON into the snapshot",
    )
    parser.add_argument(
        "--enrich",
        default="",
        help="optional comma-separated enrichers to run after crawl: pagespeed,gsc",
    )
    parser.add_argument(
        "--out-dir",
        default="audits",
        help="where to write the dated snapshot (default: ./audits)",
    )
    parser.add_argument(
        "--plan",
        help="path to remediation-plan.md (defaults to <profile dir>/remediation-plan.md)",
    )
    return parser


def run(argv: list[str] | None = None, *, stdout=None, stderr=None) -> int:
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    parser = _build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.local and args.from_crawl:
        print("seo-geo-run: --local and --from-crawl cannot be combined", file=err)
        return 2

    try:
        enrichers = _parse_enrich(args.enrich)
    except ValueError as exc:
        print(f"seo-geo-run: {exc}", file=err)
        return 2

    profile_path = Path(args.profile)
    try:
        profile = load_profile(profile_path)
    except Exception as exc:  # noqa: BLE001 — CLI: any load failure is exit 2
        print(f"seo-geo-run: failed to load profile {profile_path}: {exc}", file=err)
        return 2

    out_dir = Path(args.out_dir)
    date = args.date
    crawl_path = out_dir / "data" / f"site-crawl-{date}.json"
    plan_path = Path(args.plan) if args.plan else profile.root / "remediation-plan.md"
    org = profile.org_name or profile.base_url or profile_path.stem

    crawl_path.parent.mkdir(parents=True, exist_ok=True)

    if args.from_crawl:
        src = Path(args.from_crawl)
        if not src.is_file():
            print(f"seo-geo-run: crawl JSON not found: {src}", file=err)
            return 2
        if src.resolve() != crawl_path.resolve():
            shutil.copy2(src, crawl_path)
        print(f"Copied crawl snapshot to {crawl_path}", file=out)
    else:
        crawl_argv = ["--profile", str(profile_path), "--out", str(crawl_path)]
        if args.local:
            crawl_argv.append("--local")
        try:
            crawl_main(crawl_argv)
        except (RuntimeError, SystemExit) as exc:
            print(f"seo-geo-run: crawl failed: {exc}", file=err)
            return 2

    if enrichers:
        from seo_geo_engine.enrichment.cli import run as enrich_run

        enrich_argv = [str(crawl_path), "--profile", str(profile_path), "--out", str(crawl_path)]
        if "pagespeed" in enrichers:
            enrich_argv.append("--pagespeed")
        if "gsc" in enrichers:
            enrich_argv.append("--gsc")
        code = enrich_run(enrich_argv)
        if code != 0:
            print(f"seo-geo-run: enrichment failed (exit {code})", file=err)
            return code

    report_main(
        [
            str(crawl_path),
            date,
            org,
            "--profile",
            str(profile_path),
            "--out-dir",
            str(out_dir),
        ]
    )
    plan_sync_main(
        [
            str(crawl_path),
            "--profile",
            str(profile_path),
            "--plan",
            str(plan_path),
        ]
    )
    queue_main(
        [
            str(crawl_path),
            date,
            "--profile",
            str(profile_path),
            "--plan",
            str(plan_path),
            "--out-dir",
            str(out_dir),
        ]
    )

    json_path = out_dir / "data" / f"standard-report-{date}.json"
    html_path = out_dir / f"standard-report-{date}.html"
    html_main(
        [
            str(json_path),
            str(html_path),
            "--eyebrow",
            f"SEO / GEO Standard  ·  {org}",
            "--title",
            "SEO Scorecard",
        ]
    )

    print(f"seo-geo-run complete for {date}", file=out)
    print(f"  crawl:  {crawl_path}", file=out)
    print(f"  report: {out_dir / f'standard-report-{date}.md'}", file=out)
    print(f"  json:   {json_path}", file=out)
    print(f"  plan:   {plan_path}", file=out)
    print(f"  queue:  {out_dir / f'remediation-queue-{date}.md'}", file=out)
    print(f"  html:   {html_path}", file=out)
    return 0


def main(argv: list[str] | None = None) -> None:
    sys.exit(run(argv))


if __name__ == "__main__":
    main()
