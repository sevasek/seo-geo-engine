"""In-process MCP smoke test — no live host, no live crawl.

TODO C2: start the server in-process, call each of the five tools once
against examples/sample-profile/, assert no raise and run_site_audit's
result contains a score key.
"""
from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from seo_geo_engine.mcp.server import (  # noqa: E402
    _C2_TOOLS,
    _OPERATOR_TOOLS,
    bind_profile,
    create_server,
    reset_session,
    tool_payload,
)
from seo_geo_engine.mcp_server.server import create_server as create_server_alias

SAMPLE = Path(__file__).resolve().parent.parent / "examples" / "sample-profile"


@pytest.fixture
def mcp_env(tmp_path, sample_profile_path, sample_crawl_path):
    reset_session()
    plan = tmp_path / "remediation-plan.md"
    shutil.copy(SAMPLE / "remediation-plan.md", plan)
    out_dir = tmp_path / "audits"
    server = create_server(profile=sample_profile_path)
    yield {
        "server": server,
        "profile": str(sample_profile_path),
        "crawl": str(sample_crawl_path),
        "plan": str(plan),
        "out_dir": str(out_dir),
        "tmp": tmp_path,
    }
    reset_session()


def _call(server, name: str, arguments: dict) -> dict:
    result = asyncio.run(server.call_tool(name, arguments))
    return tool_payload(result)


def test_c2_five_tools_against_sample_profile(mcp_env):
    server = mcp_env["server"]
    date = "2026-09-18"
    audit = _call(
        server,
        "run_site_audit",
        {
            "from_crawl": mcp_env["crawl"],
            "date": date,
            "out_dir": mcp_env["out_dir"],
            "plan": mcp_env["plan"],
        },
    )
    assert "score" in audit
    assert "earned" in audit["score"]
    assert audit["items"]

    report_path = Path(mcp_env["out_dir"]) / "data" / f"standard-report-{date}.json"
    issues = _call(server, "get_audit_issues", {"report_path": str(report_path)})
    assert issues["issues"]

    from_crawl = _call(
        server,
        "get_audit_issues",
        {"crawl_path": mcp_env["crawl"], "n": 5},
    )
    assert from_crawl["issues"]

    queue = _call(
        server,
        "get_remediation_queue",
        {"crawl_path": mcp_env["crawl"], "plan": mcp_env["plan"]},
    )
    assert queue["queue"]
    assert any(row["id"] == "SCHEMA-001" for row in queue["queue"])

    status = _call(
        server,
        "set_remediation_status",
        {
            "item_id": "SCHEMA-001",
            "status": "in-progress",
            "plan": mcp_env["plan"],
        },
    )
    assert status["status"] == "in-progress"
    assert "SCHEMA-001" in Path(mcp_env["plan"]).read_text(encoding="utf-8")
    assert "in-progress" in Path(mcp_env["plan"]).read_text(encoding="utf-8")

    regen_dir = str(mcp_env["tmp"] / "regen")
    regen = _call(
        server,
        "regenerate_report",
        {
            "crawl_path": mcp_env["crawl"],
            "date": "2026-09-19",
            "out_dir": regen_dir,
        },
    )
    assert "score" in regen
    assert Path(regen["paths"]["json"]).is_file()
    assert Path(regen["paths"]["html"]).is_file()


def test_operator_tools_registered_and_aliases_work(mcp_env):
    server = mcp_env["server"]
    names = {tool.name for tool in asyncio.run(server.list_tools())}
    assert set(_C2_TOOLS) <= names
    assert set(_OPERATOR_TOOLS) <= names

    queue = _call(
        server,
        "queue",
        {"crawl_path": mcp_env["crawl"], "plan": mcp_env["plan"]},
    )
    assert queue["queue"]

    _call(
        server,
        "update_status",
        {
            "item_id": "OG-002",
            "status": "ready",
            "plan": mcp_env["plan"],
        },
    )
    assert "| OG-002 | script | — | ready |" in Path(mcp_env["plan"]).read_text(
        encoding="utf-8"
    )


def test_plan_sync_remediate_and_verify(mcp_env):
    server = mcp_env["server"]
    date = "2026-09-18"
    _call(
        server,
        "run_site_audit",
        {
            "from_crawl": mcp_env["crawl"],
            "date": date,
            "out_dir": mcp_env["out_dir"],
            "plan": mcp_env["plan"],
        },
    )

    synced = _call(
        server,
        "plan_sync",
        {"crawl_path": mcp_env["crawl"], "plan": mcp_env["plan"]},
    )
    assert "added" in synced
    assert "pruned" in synced

    drafted = _call(
        server,
        "remediate_script",
        {
            "crawl_path": mcp_env["crawl"],
            "item_id": "SCHEMA-001",
            "date": date,
            "out_dir": mcp_env["out_dir"],
        },
    )
    assert drafted["id"] == "SCHEMA-001"
    assert Path(drafted["path"]).is_file()

    report = Path(mcp_env["out_dir"]) / "data" / f"standard-report-{date}.json"
    verified = _call(
        server,
        "verify",
        {"before": str(report), "after": str(report), "item_id": "SCHEMA-001"},
    )
    assert verified["exit_code"] == 1
    assert verified["earned_delta"] == 0


def test_refuses_second_profile(mcp_env, tmp_path):
    other = tmp_path / "other-site.yaml"
    other.write_text("site:\n  base_url: https://other.example.test\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="already bound"):
        bind_profile(other)


def test_todo_c2_import_path_is_the_same_factory():
    assert create_server_alias is create_server
