from pathlib import Path

import pytest

from seo_geo_engine.checks.standard_loader import StandardFormatError, merge_standards
from seo_geo_engine.paths import default_standard_paths
from seo_geo_engine.profile import effective_standard, import_profile_code, load_profile
from seo_geo_engine.testing.traceability import assert_standard_has_full_check_coverage


def test_sample_profile_has_full_check_coverage(sample_profile_path):
    profile = load_profile(sample_profile_path)
    import_profile_code(profile)
    all_paths = default_standard_paths() + profile.standard_extension_paths
    assert_standard_has_full_check_coverage(all_paths)


def test_profile_extension_rows_present_in_effective_standard(sample_profile_path):
    profile = load_profile(sample_profile_path)
    items = effective_standard(profile, default_standard_paths())
    ids = {item.id for item in items}
    for extension_id in ("LOCAL-001", "TRUST-001", "LINK-001", "LINK-002"):
        assert extension_id in ids


def test_disabled_ids_are_filtered_out(sample_profile_path):
    from seo_geo_engine.profile import DisabledRule

    profile = load_profile(sample_profile_path)
    profile.disabled_ids = [DisabledRule(id="MOBILE-001", reason="test-only disable")]
    items = effective_standard(profile, default_standard_paths())
    ids = {item.id for item in items}
    assert "MOBILE-001" not in ids


def test_merge_last_file_wins_on_duplicate_id(tmp_path):
    base = tmp_path / "base.md"
    base.write_text(
        "## Cat\n\n"
        "| ID | Rule | Source | Weight | Status | Unblock requirement |\n"
        "|---|---|---|---|---|---|\n"
        "| TEST-001 | Original rule text. | src | 2 | open | — |\n"
    )
    override = tmp_path / "override.md"
    override.write_text(
        "## Cat\n\n"
        "| ID | Rule | Source | Weight | Status | Unblock requirement |\n"
        "|---|---|---|---|---|---|\n"
        "| TEST-001 | Overridden rule text. | src2 | 4 | open | — |\n"
    )
    merged = merge_standards([base, override])
    assert len(merged) == 1
    assert merged[0].rule == "Overridden rule text."
    assert merged[0].weight == 4


def test_disabled_id_without_reason_raises(tmp_path):
    site_yaml = tmp_path / "site.yaml"
    site_yaml.write_text("disabled_ids:\n  - id: MOBILE-001\n    reason: ''\n")
    with pytest.raises(ValueError):
        load_profile(site_yaml)
