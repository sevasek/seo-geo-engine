"""
Thin MCP host adapter over the existing operator-path functions.

Same ``load_profile`` / ``run`` / ``run_report`` / ``build_queue`` /
``update_status`` / plan-sync / enrich / verify the CLIs already call.
No scoring logic here, no CMS writes, one profile per process (the
global ``REGISTRY`` is not multi-profile-safe).

    pip install seo-geo-engine[mcp]
    seo-geo-mcp --profile site.yaml

mcp 2.x exposes ``MCPServer``; mcp 1.x used ``FastMCP``. Both have
``@server.tool()`` and in-process ``await server.call_tool(name, args)``.
"""
from __future__ import annotations

import argparse
import datetime as _datetime
import io
import json
import sys
from pathlib import Path
from typing import Any

from seo_geo_engine.paths import default_standard_paths
from seo_geo_engine.profile import effective_standard, import_profile_code, load_profile
from seo_geo_engine.remediation.plan import build_queue, run_script_handler, write_artifact
from seo_geo_engine.remediation.plan_sync import sync_plan
from seo_geo_engine.remediation.remediation_loader import update_status
from seo_geo_engine.render_html_report import render as render_html
from seo_geo_engine.report import render_json, render_markdown, run_report, top_issues
from seo_geo_engine.run import run as run_run
from seo_geo_engine.verify import diff_reports, load_report, render_diff, run as verify_run

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:  # mcp 1.x
    try:
        from mcp.server.fastmcp import FastMCP as MCPServer
    except ImportError as exc:  # pragma: no cover — extra missing
        raise ImportError(
            "seo-geo-mcp requires the [mcp] extra: pip install seo-geo-engine[mcp]"
        ) from exc


_INSTRUCTIONS = (
    "Thin wrapper over seo-geo-engine's operator path. One profile per "
    "process. Do not hand-edit generated reports, the queue, or the HTML "
    "dashboard — regenerate them. Do not write to a CMS; script tools draft "
    "artifacts only. Follow the profile Skill for order and when to stop "
    "and ask a human. The CLI is equivalent if this host has no MCP."
)

_C2_TOOLS = (
    "run_site_audit",
    "get_audit_issues",
    "get_remediation_queue",
    "set_remediation_status",
    "regenerate_report",
)

_OPERATOR_TOOLS = (
    "crawl",
    "enrich",
    "score",
    "plan_sync",
    "queue",
    "remediate_script",
    "update_status",
    "verify",
)


class _Session:
    """Process-wide bound profile. Re-binding a *different* profile is refused."""

    path: Path | None = None


def bind_profile(path: str | Path) -> None:
    resolved = Path(path).resolve()
    if _Session.path is not None and _Session.path != resolved:
        raise RuntimeError(
            f"this MCP process is already bound to {_Session.path}; "
            "start a new process per profile (REGISTRY is not multi-profile-safe)"
        )
    profile = load_profile(resolved)
    import_profile_code(profile)
    _Session.path = resolved


def reset_session() -> None:
    """Test helper — does not unload already-imported profile modules."""
    _Session.path = None


def _profile_path(profile: str | None) -> Path:
    if profile:
        bind_profile(profile)
    if _Session.path is None:
        raise ValueError("pass profile= or start seo-geo-mcp --profile site.yaml")
    return _Session.path


def _load_bound_profile(profile: str | None):
    path = _profile_path(profile)
    return load_profile(path), path


def _load_site(crawl_path: str) -> dict:
    path = Path(crawl_path)
    if not path.is_file():
        raise ValueError(f"crawl JSON not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _plan_path(profile_root: Path, plan: str | None) -> Path:
    return Path(plan) if plan else profile_root / "remediation-plan.md"


def _today(date: str | None) -> str:
    return date or _datetime.date.today().isoformat()


def _nonzero(code: int, stderr: io.StringIO, label: str) -> None:
    if code != 0:
        detail = stderr.getvalue().strip() or f"{label} exited {code}"
        raise RuntimeError(detail)


def create_server(profile: str | Path | None = None):
    """Build an in-process MCP server. Pass ``profile`` to bind this process."""
    if profile is not None:
        bind_profile(profile)

    server = MCPServer(
        name="seo-geo-engine",
        instructions=_INSTRUCTIONS,
    )

    @server.tool(
        description=(
            "Gather-and-score: crawl (or reuse --from-crawl) → optional enrich "
            "→ report → plan-sync → queue → HTML. Wraps seo-geo-run. Returns "
            "the report JSON (includes score). Does not write to a CMS."
        )
    )
    def run_site_audit(
        profile: str | None = None,
        date: str = "",
        from_crawl: str = "",
        local: bool = False,
        enrich: str = "",
        out_dir: str = "audits",
        plan: str = "",
    ) -> dict:
        profile_path = _profile_path(profile)
        snapshot = _today(date)
        argv = [
            "--profile",
            str(profile_path),
            "--date",
            snapshot,
            "--out-dir",
            out_dir,
        ]
        if from_crawl:
            argv += ["--from-crawl", from_crawl]
        if local:
            argv.append("--local")
        if enrich:
            argv += ["--enrich", enrich]
        if plan:
            argv += ["--plan", plan]
        stdout, stderr = io.StringIO(), io.StringIO()
        _nonzero(run_run(argv, stdout=stdout, stderr=stderr), stderr, "seo-geo-run")
        json_path = Path(out_dir) / "data" / f"standard-report-{snapshot}.json"
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        payload["paths"] = {
            "crawl": str(Path(out_dir) / "data" / f"site-crawl-{snapshot}.json"),
            "report": str(Path(out_dir) / f"standard-report-{snapshot}.md"),
            "json": str(json_path),
            "queue": str(Path(out_dir) / f"remediation-queue-{snapshot}.md"),
            "html": str(Path(out_dir) / f"standard-report-{snapshot}.html"),
            "plan": plan or str(_plan_path(profile_path.parent, None)),
        }
        payload["log"] = stdout.getvalue()
        return payload

    @server.tool(
        description=(
            "Top current issues by points lost. Wraps report.top_issues. "
            "Pass report_path (a standard-report JSON) or crawl_path + profile."
        )
    )
    def get_audit_issues(
        profile: str | None = None,
        crawl_path: str = "",
        report_path: str = "",
        n: int = 10,
    ) -> dict:
        if report_path:
            data = json.loads(Path(report_path).read_text(encoding="utf-8"))
            issues = list(data.get("top_issues") or [])
            return {"issues": issues[:n]}
        if not crawl_path:
            raise ValueError("pass crawl_path or report_path")
        profile_obj, _ = _load_bound_profile(profile)
        items = effective_standard(profile_obj, default_standard_paths())
        results = run_report(_load_site(crawl_path), items=items, profile=profile_obj)
        return {"issues": top_issues(results, n)}

    @server.tool(
        description=(
            "Ranked non-passing work queue. Wraps remediation.plan.build_queue."
        )
    )
    def get_remediation_queue(
        profile: str | None = None,
        crawl_path: str = "",
        plan: str = "",
    ) -> dict:
        if not crawl_path:
            raise ValueError("crawl_path is required")
        profile_obj, path = _load_bound_profile(profile)
        items = effective_standard(profile_obj, default_standard_paths())
        queue = build_queue(
            _load_site(crawl_path),
            _plan_path(path.parent, plan or None),
            items=items,
            profile=profile_obj,
        )
        return {"queue": queue}

    @server.tool(
        description=(
            "Set one remediation-plan.md row's Status (and optional Notes). "
            "Wraps update_status. Does not mark verified from a draft."
        )
    )
    def set_remediation_status(
        item_id: str,
        status: str,
        plan: str = "",
        notes: str = "",
        profile: str | None = None,
    ) -> dict:
        path = _profile_path(profile)
        plan_path = _plan_path(path.parent, plan or None)
        update_status(item_id, status, plan_path, notes=notes or None)
        return {"id": item_id, "status": status, "plan": str(plan_path)}

    @server.tool(
        description=(
            "Rewrite markdown/JSON/HTML reports from a crawl JSON. Wraps "
            "render_markdown, render_json, and the HTML renderer. Does not crawl."
        )
    )
    def regenerate_report(
        profile: str | None = None,
        crawl_path: str = "",
        date: str = "",
        out_dir: str = "audits",
        site_label: str = "",
    ) -> dict:
        if not crawl_path:
            raise ValueError("crawl_path is required")
        profile_obj, path = _load_bound_profile(profile)
        items = effective_standard(profile_obj, default_standard_paths())
        snapshot = _today(date)
        label = site_label or profile_obj.org_name or profile_obj.base_url or path.stem
        results = run_report(_load_site(crawl_path), items=items, profile=profile_obj)
        payload = render_json(results, label, snapshot)
        out = Path(out_dir)
        (out / "data").mkdir(parents=True, exist_ok=True)
        md_path = out / f"standard-report-{snapshot}.md"
        json_path = out / "data" / f"standard-report-{snapshot}.json"
        html_path = out / f"standard-report-{snapshot}.html"
        md_path.write_text(render_markdown(results, label, snapshot), encoding="utf-8")
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        render_html(
            json_path,
            html_path,
            eyebrow=f"SEO / GEO Standard  ·  {label}",
            title="SEO Scorecard",
        )
        payload["paths"] = {
            "report": str(md_path),
            "json": str(json_path),
            "html": str(html_path),
        }
        return payload

    @server.tool(description="Live or --local crawl only. Wraps seo-geo-crawl. No scoring.")
    def crawl(
        profile: str | None = None,
        out: str = "",
        local: bool = False,
    ) -> dict:
        from seo_geo_engine.crawl.run import main as crawl_main

        profile_path = _profile_path(profile)
        if not out:
            raise ValueError("out is required")
        argv = ["--profile", str(profile_path), "--out", out]
        if local:
            argv.append("--local")
        crawl_main(argv)
        return {"out": out}

    @server.tool(
        description=(
            "Merge PageSpeed Insights and/or Search Console into a crawl JSON. "
            "Wraps seo-geo-enrich. Credentials stay in the environment."
        )
    )
    def enrich(
        profile: str | None = None,
        crawl_path: str = "",
        pagespeed: bool = False,
        gsc: bool = False,
        out: str = "",
    ) -> dict:
        from seo_geo_engine.enrichment.cli import run as enrich_run

        profile_path = _profile_path(profile)
        if not crawl_path:
            raise ValueError("crawl_path is required")
        argv = [crawl_path, "--profile", str(profile_path)]
        if pagespeed:
            argv.append("--pagespeed")
        if gsc:
            argv.append("--gsc")
        dest = out or crawl_path
        if out:
            argv += ["--out", out]
        stderr = io.StringIO()
        _nonzero(enrich_run(argv, stderr=stderr), stderr, "seo-geo-enrich")
        return {"out": dest}

    @server.tool(
        description=(
            "Add currently failing IDs to remediation-plan.md and prune passes. "
            "Wraps plan_sync.sync_plan."
        )
    )
    def plan_sync(
        profile: str | None = None,
        crawl_path: str = "",
        plan: str = "",
    ) -> dict:
        if not crawl_path:
            raise ValueError("crawl_path is required")
        profile_obj, path = _load_bound_profile(profile)
        items = effective_standard(profile_obj, default_standard_paths())
        return sync_plan(
            _load_site(crawl_path),
            _plan_path(path.parent, plan or None),
            items=items,
            profile=profile_obj,
        )

    @server.tool(
        description=(
            "Run one script handler and write audits/artifacts/<date>/<ID>.txt. "
            "Does not publish and does not call update_status."
        )
    )
    def remediate_script(
        profile: str | None = None,
        crawl_path: str = "",
        item_id: str = "",
        date: str = "",
        out_dir: str = "audits",
    ) -> dict:
        if not crawl_path or not item_id:
            raise ValueError("crawl_path and item_id are required")
        profile_obj, _ = _load_bound_profile(profile)
        result = run_script_handler(_load_site(crawl_path), item_id, profile=profile_obj)
        artifact_path = write_artifact(result, Path(out_dir), _today(date))
        return {
            "id": result.id,
            "detail": result.detail,
            "path": str(artifact_path),
            "artifact": result.artifact,
        }

    @server.tool(
        description=(
            "Diff two standard-report JSON files. Wraps seo-geo-verify. "
            "item_id asserts that ID improved; require_not_worse flags regressions."
        )
    )
    def verify(
        before: str,
        after: str,
        item_id: str = "",
        require_not_worse: bool = False,
    ) -> dict:
        argv = ["--before", before, "--after", after]
        if item_id:
            argv += ["--id", item_id]
        if require_not_worse:
            argv.append("--require-not-worse")
        stdout, stderr = io.StringIO(), io.StringIO()
        code = verify_run(argv, stdout=stdout, stderr=stderr)
        if code == 2:
            raise RuntimeError(stderr.getvalue().strip() or "seo-geo-verify exited 2")
        before_report = load_report(Path(before))
        after_report = load_report(Path(after))
        delta = diff_reports(before_report, after_report)
        return {
            "exit_code": code,
            "text": stdout.getvalue(),
            "diff": render_diff(delta),
            "before_score": delta.before_score,
            "after_score": delta.after_score,
            "earned_delta": delta.earned_delta,
            "percent_delta": delta.percent_delta,
            "transitions": [
                {
                    "id": item.id,
                    "before_verdict": item.before_verdict,
                    "after_verdict": item.after_verdict,
                    "before_fraction": item.before_fraction,
                    "after_fraction": item.after_fraction,
                }
                for item in delta.transitions
            ],
        }

    # Design-doc names that are aliases of the C2 tools above.
    server.add_tool(
        regenerate_report,
        name="score",
        description="Alias of regenerate_report — write markdown/JSON/HTML from a crawl JSON.",
    )
    server.add_tool(
        get_remediation_queue,
        name="queue",
        description="Alias of get_remediation_queue — ranked non-passing work queue.",
    )
    server.add_tool(
        set_remediation_status,
        name="update_status",
        description="Alias of set_remediation_status — edit one plan row's Status/Notes.",
    )

    return server


def tool_payload(result: Any) -> dict:
    """Unwrap an in-process ``call_tool`` result to a JSON object."""
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured
    content = getattr(result, "content", None) or []
    if content:
        text = getattr(content[0], "text", None)
        if text:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return {"text": text}
            if isinstance(parsed, dict):
                return parsed
    if isinstance(result, dict):
        return result
    raise TypeError(f"unparseable MCP tool result: {type(result)!r}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        required=True,
        help="path to a site.yaml — this process is bound to that one profile",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    server = create_server(profile=args.profile)
    server.run()


if __name__ == "__main__":
    main()
