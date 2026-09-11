"""
Bootstrap / prune a profile's remediation-plan.md from the current
non-passing set.

Usage:
    python3 -m seo_geo_engine.remediation.plan_sync <site-crawl.json> --profile site.yaml
    python3 -m seo_geo_engine.remediation.plan_sync <site-crawl.json> --profile site.yaml --plan path/to/remediation-plan.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import seo_geo_engine.remediation  # noqa: F401  — engine defaults
from seo_geo_engine.paths import default_standard_paths
from seo_geo_engine.profile import SiteProfile, effective_standard, import_profile_code, load_profile
from seo_geo_engine.remediation.remediation_framework import REGISTRY
from seo_geo_engine.remediation.remediation_loader import (
    RemediationFormatError,
    RemediationItem,
    load_remediation_plan,
)
from seo_geo_engine.report import run_report

_TABLE_HEADER = "| ID | Approach | Depends on | Status | Notes |"
_TABLE_SEP = "|---|---|---|---|---|"


def _notes_for(registered) -> str:
    if registered.kind == "script":
        return f"Drafted by `{registered.fn.__name__}`."
    return f"See `{registered.playbook}`."


def _render_row(item: RemediationItem) -> str:
    return (
        f"| {item.id} | {item.approach} | {item.depends_on} | {item.status} | {item.notes} |"
    )


def _split_preamble_and_table(text: str) -> tuple[str, str]:
    """Keep everything above the remediation table; the table itself is rewritten."""
    lines = text.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and "id" in line.lower():
            header_idx = i
            break
    if header_idx is None:
        preamble = text.rstrip() + "\n\n" if text.strip() else ""
        return preamble, ""
    preamble = "\n".join(lines[:header_idx]).rstrip() + "\n\n"
    return preamble, "\n".join(lines[header_idx:])


def sync_plan(
    site: dict,
    plan_path: Path,
    *,
    items=None,
    profile: SiteProfile | None = None,
) -> dict:
    """Add rows for currently non-passing IDs missing from the plan; delete
    rows whose verdict is now pass. Returns a summary dict.

    Never changes Status or Notes on a row that still exists and is still
    non-passing. If Approach disagrees with the registered handler, warn
    and correct Approach (status/notes stay).
    """
    plan_path = Path(plan_path)
    if not plan_path.exists():
        raise FileNotFoundError(f"No remediation plan at {plan_path}")

    original_text = plan_path.read_text(encoding="utf-8")
    existing_items = load_remediation_plan(plan_path)
    existing = {row.id: row for row in existing_items}

    results = run_report(site, items=items, profile=profile)
    non_passing = {item.id: (item, result) for item, result in results if result.verdict != "pass"}
    passing_ids = {item.id for item, result in results if result.verdict == "pass"}

    missing_handlers = sorted(item_id for item_id in non_passing if item_id not in REGISTRY)
    if missing_handlers:
        raise RemediationFormatError(
            "Non-passing IDs with no registered remediation handler: "
            + ", ".join(missing_handlers)
            + ". Engine defaults cover shipped rules; a profile extension needs "
            "@remediate / manual in handlers.py."
        )

    added: list[str] = []
    pruned: list[str] = []
    approach_fixed: list[str] = []
    kept: list[RemediationItem] = []

    for row in existing_items:
        if row.id in passing_ids:
            pruned.append(row.id)
            continue
        if row.id not in non_passing:
            # ID is no longer in the effective standard (disabled / removed).
            pruned.append(row.id)
            continue
        registered = REGISTRY[row.id]
        if registered.kind != row.approach:
            print(
                f"warning: {row.id} approach {row.approach!r} disagrees with "
                f"handler kind {registered.kind!r}; correcting Approach, "
                f"leaving Status/Notes untouched.",
                file=sys.stderr,
            )
            row = RemediationItem(
                id=row.id,
                approach=registered.kind,
                depends_on=row.depends_on,
                status=row.status,
                notes=row.notes,
                line_no=row.line_no,
            )
            approach_fixed.append(row.id)
        kept.append(row)

    kept_ids = {row.id for row in kept}
    for item_id in sorted(non_passing):
        if item_id in kept_ids:
            continue
        registered = REGISTRY[item_id]
        kept.append(
            RemediationItem(
                id=item_id,
                approach=registered.kind,
                depends_on=registered.depends_on,
                status="not-started",
                notes=_notes_for(registered),
                line_no=0,
            )
        )
        added.append(item_id)

    preamble, _old_table = _split_preamble_and_table(original_text)
    if not preamble.strip():
        org = (profile.org_name if profile else "") or "Site"
        preamble = (
            f"# {org} — Remediation Plan\n\n"
            "One row per currently non-passing standard item. Generated by "
            "`seo-geo-plan-sync` — do not add/delete rows by hand; use "
            "`seo-geo-update-status` to change Status/Notes.\n\n"
        )

    body = preamble + _TABLE_HEADER + "\n" + _TABLE_SEP + "\n"
    if kept:
        body += "\n".join(_render_row(row) for row in kept) + "\n"
    plan_path.write_text(body, encoding="utf-8")

    return {
        "added": added,
        "pruned": pruned,
        "approach_fixed": approach_fixed,
        "kept": [row.id for row in kept],
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site_path")
    parser.add_argument("--profile", required=True, help="path to a site.yaml profile")
    parser.add_argument(
        "--plan",
        help="path to remediation-plan.md (defaults to <profile dir>/remediation-plan.md)",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    profile = load_profile(args.profile)
    import_profile_code(profile)
    items = effective_standard(profile, default_standard_paths())
    plan_path = Path(args.plan) if args.plan else profile.root / "remediation-plan.md"

    site = json.loads(Path(args.site_path).read_text(encoding="utf-8"))
    summary = sync_plan(site, plan_path, items=items, profile=profile)

    print(f"Synced {plan_path}")
    print(f"  added:   {len(summary['added'])} {summary['added']}")
    print(f"  pruned:  {len(summary['pruned'])} {summary['pruned']}")
    print(f"  kept:    {len(summary['kept'])}")
    if summary["approach_fixed"]:
        print(f"  approach corrected: {summary['approach_fixed']}")


if __name__ == "__main__":
    main()
