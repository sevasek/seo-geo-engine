"""
Produces the actual work order: every non-passing standard item, ranked by
the same points-lost number the standard report's "Top issues" already
computes (weight x (1 - earned fraction)) — so this queue can never drift
from the score. Annotated with each item's remediation approach/status/
dependencies from a remediation-plan.md, and split into "ready to work now"
vs. "blocked on an access/decision gap" so effort doesn't get spent
scripting a fix for something nothing can unblock yet.

Usage:
    python3 -m seo_geo_engine.remediation.plan <site-crawl.json> --profile site.yaml
"""
import argparse
import json
import sys
from pathlib import Path

from seo_geo_engine.checks.standard_loader import StandardItem, load_standard
from seo_geo_engine.paths import default_standard_paths
from seo_geo_engine.profile import SiteProfile, effective_standard, import_profile_code, load_profile
from seo_geo_engine.remediation.remediation_framework import REGISTRY
from seo_geo_engine.remediation.remediation_loader import load_remediation_plan_by_id
from seo_geo_engine.report import _points_earned, run_report


def build_queue(
    site: dict,
    plan_path: Path,
    standard_paths=None,
    items: list[StandardItem] | None = None,
    profile: SiteProfile | None = None,
) -> list[dict]:
    """Returns non-passing standard items as dicts, ranked by points lost
    (desc), each annotated with its remediation-plan row and handler kind."""
    results = run_report(site, standard_paths=standard_paths, items=items, profile=profile)
    plan_by_id = load_remediation_plan_by_id(plan_path)

    queue = []
    for item, result in results:
        if result.verdict == "pass":
            continue
        points_lost = round(item.weight - _points_earned(item, result), 2)
        plan_row = plan_by_id.get(item.id)
        registered = REGISTRY.get(item.id)
        queue.append(
            {
                "id": item.id,
                "rule": item.rule,
                "weight": item.weight,
                "verdict": result.verdict,
                "points_lost": points_lost,
                "approach": plan_row.approach if plan_row else None,
                "depends_on": plan_row.depends_on if plan_row else None,
                "status": plan_row.status if plan_row else None,
                "notes": plan_row.notes if plan_row else None,
                "has_handler": registered is not None,
            }
        )

    queue.sort(key=lambda q: (-q["points_lost"], -q["weight"], q["id"]))
    return queue


def render_markdown(queue: list[dict], date: str) -> str:
    ready = [q for q in queue if (q["depends_on"] or "-") in ("-", "—")]
    blocked = [q for q in queue if q not in ready]

    lines = [
        f"# Remediation Queue — {date}",
        "",
        "Generated from the effective standard + remediation-plan.md via "
        "`python3 -m seo_geo_engine.remediation.plan` — ranked by points lost "
        "(weight x (1 - earned fraction)), the same number the standard report's "
        "Top Issues list uses. **Do not hand-edit this file** — regenerate it instead.",
        "",
        f"## Ready to work now ({len(ready)})",
        "",
        "No dependency listed — a script draft or manual edit can start today.",
        "",
    ]
    for q in ready:
        lines.append(
            f"- **{q['id']}** (-{q['points_lost']} pts, {q['approach']}, {q['status']}) — {q['rule']}"
        )
        if q["notes"]:
            lines.append(f"  {q['notes']}")

    lines += ["", f"## Blocked on an access/decision gap ({len(blocked)})", ""]
    for q in blocked:
        lines.append(
            f"- **{q['id']}** (-{q['points_lost']} pts, blocked on {q['depends_on']}) — {q['rule']}"
        )
        if q["notes"]:
            lines.append(f"  {q['notes']}")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site_path")
    parser.add_argument("date", nargs="?", default="undated")
    parser.add_argument("--profile", help="path to a site.yaml profile")
    parser.add_argument("--plan", help="path to remediation-plan.md (defaults to <profile dir>/remediation-plan.md)")
    parser.add_argument("--standard", action="append", help="extra standard .md path(s); only used without --profile")
    parser.add_argument("--out-dir", default="audits")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    site_path = Path(args.site_path)
    site = json.loads(site_path.read_text(encoding="utf-8"))

    profile = None
    if args.profile:
        profile = load_profile(args.profile)
        import_profile_code(profile)
        items = effective_standard(profile, default_standard_paths())
        plan_path = Path(args.plan) if args.plan else profile.root / "remediation-plan.md"
    else:
        paths = [Path(p) for p in args.standard] if args.standard else default_standard_paths()
        items = load_standard(paths)
        if not args.plan:
            parser.error("--plan is required when --profile is not given")
        plan_path = Path(args.plan)

    queue = build_queue(site, plan_path, items=items, profile=profile)
    md = render_markdown(queue, args.date)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"remediation-queue-{args.date}.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"{len(queue)} non-passing item(s) queued.")


if __name__ == "__main__":
    main()
