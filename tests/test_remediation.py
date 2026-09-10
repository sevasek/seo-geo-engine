import json
import shutil

import pytest

from seo_geo_engine.paths import default_standard_paths
from seo_geo_engine.profile import effective_standard, import_profile_code, load_profile
from seo_geo_engine.remediation.plan import build_queue
from seo_geo_engine.remediation.remediation_framework import REGISTRY as REMEDIATION_REGISTRY
from seo_geo_engine.remediation.remediation_loader import load_remediation_plan_by_id, update_status
from seo_geo_engine.report import run_report


@pytest.fixture
def sample_profile(sample_profile_path):
    profile = load_profile(sample_profile_path)
    import_profile_code(profile)
    return profile


def test_every_non_passing_item_has_a_remediation_row(sample_profile, sample_crawl_path):
    items = effective_standard(sample_profile, default_standard_paths())
    site = json.loads(sample_crawl_path.read_text())
    results = run_report(site, items=items, profile=sample_profile)

    plan_path = sample_profile.root / "remediation-plan.md"
    plan_by_id = load_remediation_plan_by_id(plan_path)

    non_passing_ids = {item.id for item, result in results if result.verdict != "pass"}
    missing = non_passing_ids - set(plan_by_id)
    assert not missing, f"Non-passing items with no remediation-plan.md row: {sorted(missing)}"

    passing_ids = {item.id for item, result in results if result.verdict == "pass"}
    stale = passing_ids & set(plan_by_id)
    assert not stale, f"remediation-plan.md rows for now-passing items (should be deleted): {sorted(stale)}"


def test_every_remediation_row_has_a_registered_handler(sample_profile):
    plan_path = sample_profile.root / "remediation-plan.md"
    plan_by_id = load_remediation_plan_by_id(plan_path)
    missing = set(plan_by_id) - set(REMEDIATION_REGISTRY)
    assert not missing, f"remediation-plan.md rows with no @remediate/manual handler: {sorted(missing)}"


def test_remediation_row_approach_matches_handler_kind(sample_profile):
    plan_path = sample_profile.root / "remediation-plan.md"
    plan_by_id = load_remediation_plan_by_id(plan_path)
    mismatched = [
        item_id for item_id, row in plan_by_id.items()
        if item_id in REMEDIATION_REGISTRY and REMEDIATION_REGISTRY[item_id].kind != row.approach
    ]
    assert not mismatched, f"Approach column disagrees with the registered handler's kind: {mismatched}"


def test_manual_playbook_files_exist(sample_profile):
    plan_path = sample_profile.root / "remediation-plan.md"
    plan_by_id = load_remediation_plan_by_id(plan_path)
    missing = [
        item_id for item_id, row in plan_by_id.items()
        if row.approach == "manual" and not (sample_profile.root / "playbooks" / f"{item_id}.md").exists()
    ]
    assert not missing, f"Manual remediation rows with no playbook file: {missing}"


def test_script_handlers_produce_an_artifact(sample_profile, sample_crawl_path):
    site = json.loads(sample_crawl_path.read_text())
    site = {**site, "profile": sample_profile.to_dict()}
    for item_id, registered in REMEDIATION_REGISTRY.items():
        if registered.kind != "script":
            continue
        result = registered.fn(site)
        assert result.artifact, f"{item_id}: a script handler produced no artifact"


def test_build_queue_ranks_by_points_lost(sample_profile, sample_crawl_path):
    items = effective_standard(sample_profile, default_standard_paths())
    site = json.loads(sample_crawl_path.read_text())
    plan_path = sample_profile.root / "remediation-plan.md"

    queue = build_queue(site, plan_path, items=items, profile=sample_profile)
    points = [q["points_lost"] for q in queue]
    assert points == sorted(points, reverse=True)
    assert len(queue) == 35


def test_update_status_round_trips(tmp_path, sample_profile):
    plan_path = tmp_path / "remediation-plan.md"
    shutil.copy(sample_profile.root / "remediation-plan.md", plan_path)

    update_status("PERF-004", "in-progress", plan_path, notes="Waiting on CrUX data.")
    reloaded = load_remediation_plan_by_id(plan_path)
    assert reloaded["PERF-004"].status == "in-progress"
    assert reloaded["PERF-004"].notes == "Waiting on CrUX data."

    # Every other row must be untouched.
    original = load_remediation_plan_by_id(sample_profile.root / "remediation-plan.md")
    for item_id, row in original.items():
        if item_id == "PERF-004":
            continue
        assert reloaded[item_id].status == row.status
        assert reloaded[item_id].notes == row.notes


def test_update_status_rejects_invalid_status(tmp_path, sample_profile):
    plan_path = tmp_path / "remediation-plan.md"
    shutil.copy(sample_profile.root / "remediation-plan.md", plan_path)
    with pytest.raises(ValueError):
        update_status("PERF-004", "done", plan_path)
