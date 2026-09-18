"""Traceability for the engine's own shipped defaults only — no profile
involved. See tests/test_profile_merge.py for the profile-aware version
against the synthetic sample profile."""
from seo_geo_engine.paths import default_standard_paths
from seo_geo_engine.testing.traceability import (
    assert_engine_defaults_have_remediations,
    assert_every_weight_in_range,
    assert_standard_has_full_check_coverage,
)


def test_every_default_standard_item_has_a_check():
    assert_standard_has_full_check_coverage(default_standard_paths())


def test_default_weights_in_range():
    assert_every_weight_in_range(default_standard_paths())


def test_every_default_standard_item_has_an_engine_remediation():
    assert_engine_defaults_have_remediations()


def test_at_least_one_default_file_per_expected_category_exists():
    paths = default_standard_paths()
    names = {p.stem for p in paths}
    expected = {
        "metadata", "open-graph", "headings", "structured-data", "content",
        "images", "linking", "crawlability", "performance", "mobile", "analytics",
    }
    missing = expected - names
    assert not missing, f"Expected default standard files missing: {missing}"
