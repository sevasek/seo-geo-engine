"""
Compare two dated standard-report JSON files and show what actually
flipped — score delta and per-ID verdict/fraction transitions.

This is the only place two audit dates are compared. It does not write
the remediation plan, does not mark rows verified, and does not crawl.

Usage:
    seo-geo-verify --before audits/data/standard-report-2026-09-10.json \\
                   --after  audits/data/standard-report-2026-09-18.json
    seo-geo-verify --before <old.json> --after <new.json> --id SCHEMA-001
    seo-geo-verify --before <old.json> --after <new.json> --require-not-worse
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path


def _earned_fraction(item: dict) -> float:
    """0–1 credit for one report row. Blocked always earns 0; otherwise
    prefer the check's own fraction, then points_earned/weight, then the
    binary pass/fail default. Same precedence as scoring, reconstructed
    from the JSON so this module does not re-run checks."""
    verdict = item.get("verdict") or ""
    if verdict == "blocked":
        return 0.0
    if item.get("fraction") is not None:
        return float(item["fraction"])
    weight = item.get("weight")
    points = item.get("points_earned")
    if weight and points is not None:
        return float(points) / float(weight)
    return 1.0 if verdict == "pass" else 0.0


def _index(report: dict) -> dict[str, dict]:
    items = report.get("items")
    if not isinstance(items, list):
        raise ValueError("report JSON has no items list — pass a standard-report-*.json, not markdown")
    by_id = {}
    for item in items:
        if not isinstance(item, dict) or "id" not in item:
            raise ValueError("report item is missing an id")
        by_id[item["id"]] = item
    return by_id


def _score(report: dict) -> dict:
    score = report.get("score")
    if not isinstance(score, dict) or "earned" not in score or "possible" not in score:
        raise ValueError("report JSON has no score.earned/possible — regenerate with seo-geo-report")
    return {
        "earned": float(score["earned"]),
        "possible": float(score["possible"]),
        "percent": float(score.get("percent") or 0.0),
    }


@dataclass(frozen=True)
class ItemDelta:
    id: str
    before_verdict: str | None
    after_verdict: str | None
    before_fraction: float | None
    after_fraction: float | None

    @property
    def verdict_changed(self) -> bool:
        return self.before_verdict != self.after_verdict

    @property
    def fraction_increased(self) -> bool:
        if self.before_fraction is None or self.after_fraction is None:
            return self.before_fraction is None and self.after_fraction is not None and self.after_fraction > 0
        return self.after_fraction > self.before_fraction + 1e-9

    @property
    def fraction_decreased(self) -> bool:
        if self.before_fraction is None or self.after_fraction is None:
            return False
        return self.after_fraction < self.before_fraction - 1e-9

    @property
    def became_pass(self) -> bool:
        return self.after_verdict == "pass"

    @property
    def id_improved(self) -> bool:
        """--id success: now pass, or a strictly higher fraction while iterating."""
        return self.became_pass or self.fraction_increased

    @property
    def got_worse(self) -> bool:
        """Regression: was pass and is not, or earned fraction dropped."""
        if self.before_verdict == "pass" and self.after_verdict != "pass":
            return True
        return self.fraction_decreased

    @property
    def changed(self) -> bool:
        return self.verdict_changed or self.fraction_increased or self.fraction_decreased


@dataclass
class ReportDiff:
    before_score: dict
    after_score: dict
    items: list[ItemDelta]

    @property
    def earned_delta(self) -> float:
        return round(self.after_score["earned"] - self.before_score["earned"], 2)

    @property
    def percent_delta(self) -> float:
        return round(self.after_score["percent"] - self.before_score["percent"], 1)

    @property
    def transitions(self) -> list[ItemDelta]:
        return [d for d in self.items if d.changed]

    @property
    def regressions(self) -> list[ItemDelta]:
        return [d for d in self.items if d.got_worse]


def diff_reports(before: dict, after: dict) -> ReportDiff:
    before_by_id = _index(before)
    after_by_id = _index(after)
    ids = sorted(set(before_by_id) | set(after_by_id))
    items: list[ItemDelta] = []
    for item_id in ids:
        b = before_by_id.get(item_id)
        a = after_by_id.get(item_id)
        items.append(
            ItemDelta(
                id=item_id,
                before_verdict=b.get("verdict") if b else None,
                after_verdict=a.get("verdict") if a else None,
                before_fraction=_earned_fraction(b) if b else None,
                after_fraction=_earned_fraction(a) if a else None,
            )
        )
    return ReportDiff(before_score=_score(before), after_score=_score(after), items=items)


def load_report(path: Path) -> dict:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"report JSON not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a report object")
    _index(data)
    _score(data)
    return data


def render_diff(diff: ReportDiff) -> str:
    b, a = diff.before_score, diff.after_score
    earned_sign = "+" if diff.earned_delta >= 0 else ""
    percent_sign = "+" if diff.percent_delta >= 0 else ""
    lines = [
        f"Score: {b['earned']}/{b['possible']} ({b['percent']}%) → "
        f"{a['earned']}/{a['possible']} ({a['percent']}%)  "
        f"earned Δ {earned_sign}{diff.earned_delta}  "
        f"percent Δ {percent_sign}{diff.percent_delta}",
        "",
        "Transitions:",
    ]
    changed = diff.transitions
    if not changed:
        lines.append("  (none — every ID's verdict and fraction is unchanged)")
    else:
        for item in changed:
            before_v = item.before_verdict or "(absent)"
            after_v = item.after_verdict or "(absent)"
            extra = ""
            if (
                item.before_fraction is not None
                and item.after_fraction is not None
                and abs(item.after_fraction - item.before_fraction) > 1e-9
            ):
                extra = f"  (fraction {item.before_fraction:.3f} → {item.after_fraction:.3f})"
            lines.append(f"  {item.id}  {before_v} → {after_v}{extra}")
    return "\n".join(lines) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, help="earlier standard-report-*.json")
    parser.add_argument("--after", required=True, help="later standard-report-*.json")
    parser.add_argument(
        "--id",
        dest="item_id",
        help="assert this ID became pass, or its earned fraction strictly increased",
    )
    parser.add_argument(
        "--require-not-worse",
        action="store_true",
        help="exit 1 if any ID moved pass→non-pass or its earned fraction dropped",
    )
    return parser


def run(argv: list[str] | None = None, *, stdout=None, stderr=None) -> int:
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    parser = _build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    try:
        before = load_report(Path(args.before))
        after = load_report(Path(args.after))
        diff = diff_reports(before, after)
    except ValueError as exc:
        print(f"seo-geo-verify: {exc}", file=err)
        return 2

    print(render_diff(diff), end="", file=out)

    failed = False
    if args.item_id:
        match = next((item for item in diff.items if item.id == args.item_id), None)
        if match is None:
            print(f"--id {args.item_id}: not present in either report", file=out)
            failed = True
        elif match.id_improved:
            why = "pass" if match.became_pass else "fraction increased"
            print(f"--id {args.item_id}: ok ({why})", file=out)
        else:
            print(
                f"--id {args.item_id}: not improved "
                f"({match.before_verdict or 'absent'} → {match.after_verdict or 'absent'}, "
                f"fraction {match.before_fraction} → {match.after_fraction})",
                file=out,
            )
            failed = True

    if args.require_not_worse:
        if diff.regressions:
            ids = ", ".join(item.id for item in diff.regressions)
            print(f"--require-not-worse: regressions: {ids}", file=out)
            failed = True
        else:
            print("--require-not-worse: ok", file=out)

    return 1 if failed else 0


def main(argv: list[str] | None = None) -> None:
    sys.exit(run(argv))


if __name__ == "__main__":
    main()
