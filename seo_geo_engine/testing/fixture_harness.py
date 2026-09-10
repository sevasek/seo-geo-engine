"""
Discovers Layer-1 fixture cases: tests/fixtures/checks/<ID>/{good,bad}.json
+ matching {good,bad}.expected.json. A profile can point this at its own
fixtures directory the same way it imports assert_standard_has_full_check_coverage
from testing/traceability.py — this isn't engine-only plumbing.
"""
from pathlib import Path


def discover_fixture_cases(fixtures_dir: Path):
    """Yields (check_id, variant, site_path, expected_path) for every
    variant ("good"/"bad") that has both a *.json site fixture and a
    matching *.expected.json."""
    if not fixtures_dir.exists():
        return
    for check_dir in sorted(fixtures_dir.iterdir()):
        if not check_dir.is_dir():
            continue
        for variant in ("good", "bad"):
            site_path = check_dir / f"{variant}.json"
            expected_path = check_dir / f"{variant}.expected.json"
            if site_path.exists() and expected_path.exists():
                yield check_dir.name, variant, site_path, expected_path


def check_ids_with_fixtures(fixtures_dir: Path) -> set[str]:
    if not fixtures_dir.exists():
        return set()
    return {d.name for d in fixtures_dir.iterdir() if d.is_dir()}
