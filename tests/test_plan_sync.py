import json
import shutil

import pytest

from seo_geo_engine.paths import default_standard_paths
from seo_geo_engine.profile import effective_standard, import_profile_code, load_profile
from seo_geo_engine.remediation.plan import main as remediate_main, run_script_handler
from seo_geo_engine.remediation.plan_sync import sync_plan
from seo_geo_engine.remediation.remediation_framework import REGISTRY, registration_origin
from seo_geo_engine.remediation.remediation_loader import (
    RemediationFormatError,
    load_remediation_plan,
    load_remediation_plan_by_id,
    main as update_status_main,
)
from seo_geo_engine.report import run_report


def test_empty_plan_file_is_legal(tmp_path):
    path = tmp_path / "remediation-plan.md"
    path.write_text(
        "# Empty\n\n| ID | Approach | Depends on | Status | Notes |\n|---|---|---|---|---|\n",
        encoding="utf-8",
    )
    assert load_remediation_plan(path) == []
    assert load_remediation_plan_by_id(path) == {}


def test_plan_sync_adds_and_prunes(tmp_path, sample_profile_path, sample_crawl_path):
    profile = load_profile(sample_profile_path)
    import_profile_code(profile)
    items = effective_standard(profile, default_standard_paths())
    site = json.loads(sample_crawl_path.read_text())

    plan_path = tmp_path / "remediation-plan.md"
    plan_path.write_text(
        "# Test plan\n\n| ID | Approach | Depends on | Status | Notes |\n"
        "|---|---|---|---|---|\n"
        "| META-001 | manual | CMS-ACCESS | in-progress | keep me if still failing |\n"
        "| HEAD-003 | manual | CMS-ACCESS | applied | should be pruned — this passes |\n",
        encoding="utf-8",
    )

    summary = sync_plan(site, plan_path, items=items, profile=profile)
    reloaded = load_remediation_plan_by_id(plan_path)

    assert "HEAD-003" in summary["pruned"]
    assert "HEAD-003" not in reloaded

    non_passing = {item.id for item, result in run_report(site, items=items, profile=profile) if result.verdict != "pass"}
    assert set(reloaded) == non_passing
    assert "META-001" in reloaded
    # Existing status/notes preserved for a still-failing row.
    assert reloaded["META-001"].status == "in-progress"
    assert reloaded["META-001"].notes == "keep me if still failing"
    # Newly added rows start not-started.
    for item_id in summary["added"]:
        assert reloaded[item_id].status == "not-started"
        assert reloaded[item_id].approach == REGISTRY[item_id].kind


def test_plan_sync_refuses_missing_handler(tmp_path, sample_profile_path, sample_crawl_path):
    profile = load_profile(sample_profile_path)
    import_profile_code(profile)
    items = effective_standard(profile, default_standard_paths())
    site = json.loads(sample_crawl_path.read_text())

    # LOCAL-001 is a profile extension that fails on the sample crawl.
    saved = REGISTRY.pop("LOCAL-001")
    plan_path = tmp_path / "remediation-plan.md"
    plan_path.write_text(
        "| ID | Approach | Depends on | Status | Notes |\n|---|---|---|---|---|\n",
        encoding="utf-8",
    )
    try:
        with pytest.raises(RemediationFormatError, match="LOCAL-001"):
            sync_plan(site, plan_path, items=items, profile=profile)
    finally:
        REGISTRY["LOCAL-001"] = saved


def test_run_script_handler_writes_artifact(tmp_path, sample_profile_path, sample_crawl_path):
    profile = load_profile(sample_profile_path)
    import_profile_code(profile)
    site = json.loads(sample_crawl_path.read_text())
    result = run_script_handler(site, "SCHEMA-001", profile=profile)
    assert result.artifact
    assert "@type" in result.artifact

    remediate_main(
        [
            str(sample_crawl_path),
            "2026-09-11",
            "--profile",
            str(sample_profile_path),
            "--id",
            "OG-002",
            "--out-dir",
            str(tmp_path),
        ]
    )
    artifact = tmp_path / "artifacts" / "2026-09-11" / "OG-002.txt"
    assert artifact.is_file()
    assert artifact.read_text(encoding="utf-8").strip()


def test_run_script_handler_rejects_manual(sample_profile_path, sample_crawl_path):
    profile = load_profile(sample_profile_path)
    import_profile_code(profile)
    site = json.loads(sample_crawl_path.read_text())
    with pytest.raises(ValueError, match="not script"):
        run_script_handler(site, "META-001", profile=profile)


def test_update_status_cli(tmp_path, sample_profile_path):
    profile = load_profile(sample_profile_path)
    plan_path = tmp_path / "remediation-plan.md"
    shutil.copy(profile.root / "remediation-plan.md", plan_path)
    update_status_main(
        ["SCHEMA-001", "in-progress", "--plan", str(plan_path), "--notes", "Drafted."]
    )
    reloaded = load_remediation_plan_by_id(plan_path)
    assert reloaded["SCHEMA-001"].status == "in-progress"
    assert reloaded["SCHEMA-001"].notes == "Drafted."


def test_profile_may_overwrite_engine_handler():
    import seo_geo_engine.remediation  # noqa: F401
    from seo_geo_engine.remediation.remediation_framework import RemediationResult, remediate

    original = REGISTRY["OG-002"]
    token = registration_origin.set("profile")
    try:

        @remediate("OG-002", kind="script")
        def remediate_og_002_override(site: dict) -> RemediationResult:
            return RemediationResult(id="OG-002", kind="script", detail="override", artifact="overridden")

        assert REGISTRY["OG-002"].origin == "profile"
        assert REGISTRY["OG-002"].fn is remediate_og_002_override
        assert REGISTRY["OG-002"].fn({}).artifact == "overridden"
    finally:
        registration_origin.reset(token)
        REGISTRY["OG-002"] = original
