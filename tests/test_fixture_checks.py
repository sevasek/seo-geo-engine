"""
Layer 1 of the fixture-based test harness (inspired by open-seo's badseo/
completeness gate, adapted to JSON site-dict fixtures since that's the
actual shape a check receives — see tests/fixtures/badseo_site/ for the
slower, real-HTML Layer 2). Every "open"-status default check must have a
known-good and known-bad fixture proving it actually fires on real input,
not just that the standard/check ID sets match (that's test_default_traceability.py's job).
"""
import json
from pathlib import Path

import pytest

import seo_geo_engine.checks  # noqa: F401  (triggers built-in check registration)
from seo_geo_engine.checks.framework import REGISTRY
from seo_geo_engine.checks.standard_loader import load_standard_by_id
from seo_geo_engine.paths import default_standard_paths
from seo_geo_engine.testing.fixture_harness import check_ids_with_fixtures, discover_fixture_cases

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "checks"
CASES = list(discover_fixture_cases(FIXTURES_DIR))


@pytest.mark.parametrize(
    "check_id,variant,site_path,expected_path",
    CASES,
    ids=[f"{c[0]}-{c[1]}" for c in CASES],
)
def test_check_fixture(check_id, variant, site_path, expected_path):
    registered = REGISTRY[check_id]  # KeyError itself is a bug: a fixture for an unregistered ID
    site = json.loads(site_path.read_text())
    expected = json.loads(expected_path.read_text())

    result = registered.fn(site)

    assert result.verdict == expected["verdict"], (
        f"{check_id} ({variant}): expected verdict {expected['verdict']!r}, got {result.verdict!r} — {result.detail}"
    )
    if expected.get("fraction") is not None:
        assert result.fraction == pytest.approx(expected["fraction"]), (
            f"{check_id} ({variant}): expected fraction {expected['fraction']}, got {result.fraction}"
        )
    for snippet in expected.get("evidence_contains", []):
        assert any(snippet in e for e in result.evidence), (
            f"{check_id} ({variant}): no evidence entry contains {snippet!r} — evidence was {result.evidence}"
        )


def test_every_open_default_check_has_a_fixture():
    """The completeness gate: every check the engine ships with REAL logic
    (status="open" in the default standard) must have a known-good/known-bad
    fixture pair. Blocked one-line stubs are exempt — they ignore their
    input by construction, so a fixture would test nothing."""
    by_id = load_standard_by_id(default_standard_paths())
    open_ids = {item_id for item_id, item in by_id.items() if item.status == "open"}
    have_fixtures = check_ids_with_fixtures(FIXTURES_DIR)
    missing = open_ids - have_fixtures
    assert not missing, (
        f"Open default checks with no fixture under tests/fixtures/checks/: {sorted(missing)} — "
        f"add a good.json/bad.json pair (+ matching expected.json) proving each actually fires."
    )
