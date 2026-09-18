"""
Reusable traceability assertions: every standard row has exactly one
registered check, every registered check maps back to a standard row,
blocked rows carry a real unblock requirement and open rows don't. A
profile's own tests import these functions and parameterize them with its
own effective-standard paths, instead of copy-pasting the ~50+ lines this
used to take in each site-specific repo.

Usage (from a profile's own tests/test_traceability.py):

    from seo_geo_engine.testing.traceability import assert_standard_has_full_check_coverage
    from seo_geo_engine.paths import default_standard_paths

    def test_traceability():
        assert_standard_has_full_check_coverage(
            default_standard_paths() + [Path("standard/extensions.md")]
        )
"""
from pathlib import Path

import seo_geo_engine.checks  # noqa: F401  (triggers built-in check registration)
import seo_geo_engine.remediation  # noqa: F401
from seo_geo_engine.checks.framework import REGISTRY
from seo_geo_engine.checks.standard_loader import load_standard_by_id
from seo_geo_engine.paths import default_standard_paths
from seo_geo_engine.remediation.remediation_framework import REGISTRY as REMEDIATION_REGISTRY
from seo_geo_engine.remediation.remediation_framework import playbook_path


def assert_standard_has_full_check_coverage(paths: list[Path]) -> None:
    by_id = load_standard_by_id(paths)
    standard_ids = set(by_id)
    registered_ids = set(REGISTRY)

    missing_checks = standard_ids - registered_ids
    assert not missing_checks, (
        f"These standard rows have no @check(...) implementing them: {sorted(missing_checks)}. "
        f"Add one tagged @check({sorted(missing_checks)[0]!r})."
    )

    orphan_checks = registered_ids - standard_ids
    assert not orphan_checks, (
        f"These @check(...) functions are registered but no standard row claims them: "
        f"{sorted(orphan_checks)}. Add the row, or remove the check."
    )

    for item_id, item in by_id.items():
        if item.status == "blocked":
            assert item.unblock_requirement and item.unblock_requirement != "—", (
                f"{item_id} is status=blocked but has no unblock requirement text."
            )
        else:
            assert item.status == "open", f"{item_id} has an invalid status {item.status!r}"


def assert_every_weight_in_range(paths: list[Path], min_weight: int = 1, max_weight: int = 5) -> None:
    by_id = load_standard_by_id(paths)
    bad = {i: item.weight for i, item in by_id.items() if not (min_weight <= item.weight <= max_weight)}
    assert not bad, f"Standard rows with an out-of-range weight: {bad}"


def assert_engine_defaults_have_remediations() -> None:
    """Every shipped default standard ID has an engine-owned remediation
    (script or manual). Manual playbook files must exist. Engine remediations
    must not claim IDs that aren't in the default standard — those belong in
    a profile. See docs/design/engine-owned-remediation.md."""
    by_id = load_standard_by_id(default_standard_paths())
    engine_ids = {item_id for item_id, reg in REMEDIATION_REGISTRY.items() if reg.origin == "engine"}

    missing = set(by_id) - engine_ids
    assert not missing, (
        f"These default standard rows have no engine-owned remediation: {sorted(missing)}. "
        f"Add a @remediate / manual in seo_geo_engine.remediation.defaults."
    )

    orphans = engine_ids - set(by_id)
    assert not orphans, (
        f"Engine remediations for IDs that are not default standard rows: {sorted(orphans)}. "
        f"Profile-only IDs belong in a profile's handlers.py."
    )

    for item_id, registered in REMEDIATION_REGISTRY.items():
        if registered.origin != "engine" or registered.kind != "manual":
            continue
        path = playbook_path(registered)
        assert path.is_file(), f"{item_id}: engine manual playbook missing at {path}"
