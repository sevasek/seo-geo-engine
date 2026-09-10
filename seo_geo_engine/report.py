"""
Runs every registered check against a crawled site dataset and renders a
report that mirrors the effective standard (engine defaults + a profile's
extensions) row for row — same order, same IDs, nothing added, nothing
dropped. That guarantee is what tests/test_default_traceability.py (and a
profile's own imported traceability tests) verify; this module is what
makes it true by construction (it iterates the standard, not the registry,
to decide what to include).

Also computes the merged top-level score (weighted, partial-credit) and
ranks the top current issues by how many points each would recover if
fixed.

Usage:
    python3 -m seo_geo_engine.report <site-crawl.json> --profile site.yaml
    python3 -m seo_geo_engine.report <site-crawl.json>   # engine defaults only, no profile
"""
import argparse
import json
import sys
from pathlib import Path

import seo_geo_engine.checks  # noqa: F401  (import triggers built-in check registration)
from seo_geo_engine.checks.framework import REGISTRY, CheckResult
from seo_geo_engine.checks.standard_loader import StandardItem, load_standard
from seo_geo_engine.paths import default_standard_paths
from seo_geo_engine.profile import SiteProfile, effective_standard, import_profile_code, load_profile

VERDICT_ICON = {"pass": "✅", "fail": "❌", "partial": "🟡", "blocked": "⛔"}
TOP_ISSUES_COUNT = 10


def run_report(
    site: dict,
    standard_paths=None,
    items: list[StandardItem] | None = None,
    profile: SiteProfile | None = None,
) -> list[tuple]:
    """Returns a list of (StandardItem, CheckResult) pairs, in standard order.

    Pass either `items` (an already-merged/filtered standard, e.g. from
    profile.effective_standard()) or `standard_paths` (loaded directly via
    load_standard()) — not both. Pass `profile` whenever a profile is in
    play so its data reaches every check as site["profile"]."""
    if items is None:
        items = load_standard(standard_paths if standard_paths is not None else default_standard_paths())

    if profile is not None:
        site = {**site, "profile": profile.to_dict()}

    results = []
    for item in items:
        registered = REGISTRY.get(item.id)
        if registered is None:
            # Traceability tests should already prevent this in CI; fail loud
            # if run_report() is ever called without the test suite having passed.
            raise RuntimeError(
                f"No check registered for standard item {item.id} — "
                f"add one under checks/ (or a profile's checks_ext.py) tagged @check({item.id!r})"
            )
        result = registered.fn(site)
        if result.verdict == "blocked" and not result.detail:
            result = CheckResult(
                id=result.id,
                verdict="blocked",
                detail=item.unblock_requirement,
                evidence=result.evidence,
            )
        results.append((item, result))
    return results


def _earned_fraction(result: CheckResult) -> float:
    """0.0 for blocked (always — an unverified rule earns no credit), the
    check's own fraction when it set one, else the binary pass/fail default."""
    if result.verdict == "blocked":
        return 0.0
    if result.fraction is not None:
        return result.fraction
    return 1.0 if result.verdict == "pass" else 0.0


def _points_earned(item, result: CheckResult) -> float:
    """The one place per-item points are computed — compute_score and the
    rendered reports all sum *this* value, so the displayed total and the
    sum of displayed per-item points can never drift apart from each other
    through separate rounding."""
    return round(item.weight * _earned_fraction(result), 2)


def compute_score(results: list[tuple]) -> dict:
    total_weight = sum(item.weight for item, _ in results)
    earned = round(sum(_points_earned(item, result) for item, result in results), 2)
    percent = (earned / total_weight * 100) if total_weight else 0.0
    return {"earned": earned, "possible": total_weight, "percent": round(percent, 1)}


def top_issues(results: list[tuple], n: int = TOP_ISSUES_COUNT) -> list[dict]:
    """Non-passing items ranked by points currently lost (weight * (1 - earned
    fraction)) — the single number that answers "if we fixed only this, how
    much would the score move." Ties break by weight, then ID, for stability."""
    scored = []
    for item, result in results:
        if result.verdict == "pass":
            continue
        points_lost = round(item.weight - _points_earned(item, result), 2)
        scored.append((points_lost, item, result))
    scored.sort(key=lambda t: (-t[0], -t[1].weight, t[1].id))
    return [
        {
            "id": item.id,
            "rule": item.rule,
            "category": item.category,
            "weight": item.weight,
            "verdict": result.verdict,
            "detail": result.detail,
            "points_lost": points_lost,
        }
        for points_lost, item, result in scored[:n]
    ]


def render_markdown(results: list[tuple], site_label: str, date: str) -> str:
    score = compute_score(results)
    issues = top_issues(results)

    lines = [
        f"# SEO/GEO Standard Compliance Report — {date}",
        "",
        f"Scope: {site_label}. Generated via `python3 -m seo_geo_engine.report` — "
        f"every row below corresponds to exactly one row in the effective standard "
        f"(engine defaults + this profile's extensions), in the same order.",
        "",
        f"## Score: {score['earned']} / {score['possible']} ({score['percent']}%)",
        "",
        "Weighted, partial-credit — a rule that's 80% fixed scores differently "
        "from one untouched. Blocked rules count their full weight against the "
        "possible total but earn zero until they can actually be assessed.",
        "",
    ]

    counts = {"pass": 0, "fail": 0, "partial": 0, "blocked": 0}
    for _, result in results:
        counts[result.verdict] += 1
    lines.append(
        f"**Verdict summary:** {counts['pass']} pass · {counts['fail']} fail · "
        f"{counts['partial']} partial · {counts['blocked']} blocked "
        f"(of {len(results)} standard items)."
    )
    lines.append("")

    lines.append(f"## Top {len(issues)} current issues")
    lines.append("")
    lines.append("Ranked by points lost (weight × how far from compliant) — fixing #1 moves the score the most.")
    lines.append("")
    for i, issue in enumerate(issues, start=1):
        icon = VERDICT_ICON[issue["verdict"]]
        lines.append(
            f"{i}. {icon} **{issue['id']}** (weight {issue['weight']}, "
            f"-{issue['points_lost']} pts) — {issue['rule']}"
        )
        lines.append(f"   {issue['detail']}")
    lines.append("")

    lines.append("## Full standard, by category")
    lines.append("")

    current_category = None
    for item, result in results:
        if item.category != current_category:
            current_category = item.category
            lines.append(f"### {current_category}")
            lines.append("")
        icon = VERDICT_ICON[result.verdict]
        earned_pts = _points_earned(item, result)
        lines.append(f"#### {icon} {item.id} — {item.rule}")
        lines.append("")
        lines.append(f"*Source: {item.source} · Weight: {item.weight} · Points: {earned_pts}/{item.weight}*")
        lines.append("")
        lines.append(f"**Verdict: {result.verdict}.** {result.detail}")
        if result.evidence:
            lines.append("")
            for e in result.evidence[:15]:
                lines.append(f"- {e}")
            if len(result.evidence) > 15:
                lines.append(f"- …and {len(result.evidence) - 15} more")
        lines.append("")

    return "\n".join(lines)


def render_json(results: list[tuple], site_label: str = "", date: str = "") -> dict:
    return {
        "site_label": site_label,
        "date": date,
        "score": compute_score(results),
        "top_issues": top_issues(results),
        "items": [
            {
                "id": item.id,
                "category": item.category,
                "rule": item.rule,
                "source": item.source,
                "weight": item.weight,
                "status": item.status,
                "verdict": result.verdict,
                "detail": result.detail,
                "evidence": result.evidence,
                "fraction": result.fraction,
                "points_earned": _points_earned(item, result),
            }
            for item, result in results
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score a site-crawl JSON against the effective SEO/GEO standard."
    )
    parser.add_argument("site_path", help="path to a site-crawl.json produced by the crawler")
    parser.add_argument("date", nargs="?", default="undated")
    parser.add_argument("site_label", nargs="?", default=None)
    parser.add_argument("--profile", help="path to a site.yaml profile (engine defaults only if omitted)")
    parser.add_argument(
        "--standard",
        action="append",
        help="extra standard .md path (repeatable); only used without --profile",
    )
    parser.add_argument("--out-dir", default="audits", help="where to write the .md/.json report (default: ./audits)")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv if argv is not None else sys.argv[1:])

    site_path = Path(args.site_path)
    site = json.loads(site_path.read_text(encoding="utf-8"))

    profile = None
    if args.profile:
        profile = load_profile(args.profile)
        import_profile_code(profile)
        items = effective_standard(profile, default_standard_paths())
        site_label = args.site_label or profile.base_url or site_path.stem
    else:
        paths = [Path(p) for p in args.standard] if args.standard else default_standard_paths()
        items = load_standard(paths)
        site_label = args.site_label or site_path.stem

    results = run_report(site, items=items, profile=profile)

    md = render_markdown(results, site_label, args.date)
    js = render_json(results, site_label, args.date)

    out_dir = Path(args.out_dir)
    (out_dir / "data").mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"standard-report-{args.date}.md"
    json_path = out_dir / "data" / f"standard-report-{args.date}.json"

    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(json.dumps(js, indent=2), encoding="utf-8")

    print(f"Wrote {md_path}")
    print(f"Wrote {json_path}")
    print(f"Score: {js['score']['earned']}/{js['score']['possible']} ({js['score']['percent']}%)")


if __name__ == "__main__":
    main()
