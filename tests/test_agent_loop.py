import io
import json
import shutil
from pathlib import Path

from seo_geo_engine.run import run as run_run
from seo_geo_engine.verify import diff_reports, run as verify_run


def _item(item_id, verdict, *, weight=5, fraction=None):
    if fraction is None:
        fraction = 1.0 if verdict == "pass" else 0.0
    return {
        "id": item_id,
        "category": "Test",
        "rule": item_id,
        "source": "",
        "weight": weight,
        "status": "open",
        "verdict": verdict,
        "detail": "",
        "evidence": [],
        "fraction": fraction,
        "points_earned": round(weight * fraction, 2),
    }


def _report(items, date="2026-09-10"):
    earned = round(sum(i["points_earned"] for i in items), 2)
    possible = sum(i["weight"] for i in items)
    percent = round(earned / possible * 100, 1) if possible else 0.0
    return {
        "site_label": "test",
        "date": date,
        "score": {"earned": earned, "possible": possible, "percent": percent},
        "top_issues": [],
        "items": items,
    }


def _write_report(path: Path, report: dict) -> Path:
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def test_diff_reports_score_and_transitions():
    before = _report(
        [
            _item("SCHEMA-001", "fail"),
            _item("META-001", "fail", fraction=0.16),
            _item("HEAD-003", "pass"),
            _item("PERF-002", "blocked", fraction=0.0),
        ]
    )
    after = _report(
        [
            _item("SCHEMA-001", "pass"),
            _item("META-001", "fail", fraction=0.42),
            _item("HEAD-003", "pass"),
            _item("PERF-002", "fail", fraction=0.0),
        ],
        date="2026-09-18",
    )
    diff = diff_reports(before, after)
    by_id = {item.id: item for item in diff.items}
    assert by_id["SCHEMA-001"].became_pass
    assert by_id["SCHEMA-001"].id_improved
    assert by_id["META-001"].fraction_increased
    assert by_id["META-001"].id_improved
    assert not by_id["HEAD-003"].changed
    assert by_id["PERF-002"].verdict_changed
    assert diff.earned_delta > 0
    assert diff.regressions == []


def test_verify_id_pass_and_unchanged_fail(tmp_path):
    before = _write_report(
        tmp_path / "before.json",
        _report([_item("SCHEMA-001", "fail"), _item("HEAD-003", "pass")]),
    )
    after_pass = _write_report(
        tmp_path / "after-pass.json",
        _report([_item("SCHEMA-001", "pass"), _item("HEAD-003", "pass")], date="2026-09-18"),
    )
    after_same = _write_report(
        tmp_path / "after-same.json",
        _report([_item("SCHEMA-001", "fail"), _item("HEAD-003", "pass")], date="2026-09-18"),
    )

    buf = io.StringIO()
    assert (
        verify_run(
            ["--before", str(before), "--after", str(after_pass), "--id", "SCHEMA-001"],
            stdout=buf,
        )
        == 0
    )
    assert "SCHEMA-001  fail → pass" in buf.getvalue()
    assert "--id SCHEMA-001: ok" in buf.getvalue()

    buf = io.StringIO()
    assert (
        verify_run(
            ["--before", str(before), "--after", str(after_same), "--id", "SCHEMA-001"],
            stdout=buf,
        )
        == 1
    )
    assert "not improved" in buf.getvalue()


def test_verify_id_fraction_increase_counts_as_improved(tmp_path):
    before = _write_report(tmp_path / "before.json", _report([_item("META-001", "fail", fraction=0.16)]))
    after = _write_report(
        tmp_path / "after.json",
        _report([_item("META-001", "fail", fraction=0.42)], date="2026-09-18"),
    )
    buf = io.StringIO()
    assert (
        verify_run(
            ["--before", str(before), "--after", str(after), "--id", "META-001"],
            stdout=buf,
        )
        == 0
    )
    assert "fraction increased" in buf.getvalue()


def test_verify_require_not_worse_catches_pass_to_fail(tmp_path):
    before = _write_report(
        tmp_path / "before.json",
        _report([_item("HEAD-003", "pass"), _item("SCHEMA-001", "fail")]),
    )
    after = _write_report(
        tmp_path / "after.json",
        _report([_item("HEAD-003", "fail"), _item("SCHEMA-001", "pass")], date="2026-09-18"),
    )
    buf = io.StringIO()
    assert (
        verify_run(
            ["--before", str(before), "--after", str(after), "--require-not-worse"],
            stdout=buf,
        )
        == 1
    )
    assert "HEAD-003" in buf.getvalue()

    after_ok = _write_report(
        tmp_path / "after-ok.json",
        _report([_item("HEAD-003", "pass"), _item("SCHEMA-001", "pass")], date="2026-09-19"),
    )
    buf = io.StringIO()
    assert (
        verify_run(
            ["--before", str(before), "--after", str(after_ok), "--require-not-worse", "--id", "SCHEMA-001"],
            stdout=buf,
        )
        == 0
    )


def test_verify_rejects_markdown_and_missing_file(tmp_path):
    md = tmp_path / "standard-report.md"
    md.write_text("# not json\n", encoding="utf-8")
    err = io.StringIO()
    assert verify_run(["--before", str(md), "--after", str(md)], stdout=io.StringIO(), stderr=err) == 2
    missing = tmp_path / "nope.json"
    err = io.StringIO()
    assert (
        verify_run(["--before", str(missing), "--after", str(missing)], stdout=io.StringIO(), stderr=err)
        == 2
    )


def test_run_from_crawl_writes_snapshot(tmp_path, sample_profile_path, sample_crawl_path):
    profile = Path(sample_profile_path)
    plan_path = tmp_path / "remediation-plan.md"
    shutil.copy(profile.parent / "remediation-plan.md", plan_path)
    out_dir = tmp_path / "audits"
    buf = io.StringIO()
    code = run_run(
        [
            "--profile",
            str(profile),
            "--from-crawl",
            str(sample_crawl_path),
            "--date",
            "2026-09-18",
            "--out-dir",
            str(out_dir),
            "--plan",
            str(plan_path),
        ],
        stdout=buf,
    )
    assert code == 0
    assert (out_dir / "data" / "site-crawl-2026-09-18.json").is_file()
    report_json = out_dir / "data" / "standard-report-2026-09-18.json"
    assert report_json.is_file()
    assert (out_dir / "standard-report-2026-09-18.md").is_file()
    assert (out_dir / "remediation-queue-2026-09-18.md").is_file()
    html = out_dir / "standard-report-2026-09-18.html"
    assert html.is_file()
    assert "SEO Scorecard" in html.read_text(encoding="utf-8")
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert "score" in payload
    assert payload["items"]
    # Sample crawl has non-passing IDs; plan-sync must have written rows.
    plan_text = plan_path.read_text(encoding="utf-8")
    assert "SCHEMA-001" in plan_text
    assert "seo-geo-run complete" in buf.getvalue()


def test_run_does_not_mutate_source_crawl(tmp_path, sample_profile_path, sample_crawl_path):
    original = sample_crawl_path.read_text(encoding="utf-8")
    plan_path = tmp_path / "remediation-plan.md"
    shutil.copy(Path(sample_profile_path).parent / "remediation-plan.md", plan_path)
    run_run(
        [
            "--profile",
            str(sample_profile_path),
            "--from-crawl",
            str(sample_crawl_path),
            "--date",
            "2026-09-18",
            "--out-dir",
            str(tmp_path / "audits"),
            "--plan",
            str(plan_path),
        ],
        stdout=io.StringIO(),
    )
    assert sample_crawl_path.read_text(encoding="utf-8") == original


def test_run_rejects_unknown_enricher(sample_profile_path, sample_crawl_path):
    err = io.StringIO()
    code = run_run(
        [
            "--profile",
            str(sample_profile_path),
            "--from-crawl",
            str(sample_crawl_path),
            "--enrich",
            "crux",
        ],
        stdout=io.StringIO(),
        stderr=err,
    )
    assert code == 2
    assert "unknown --enrich" in err.getvalue()


def test_run_rejects_local_plus_from_crawl(sample_profile_path, sample_crawl_path):
    err = io.StringIO()
    code = run_run(
        [
            "--profile",
            str(sample_profile_path),
            "--local",
            "--from-crawl",
            str(sample_crawl_path),
            "--date",
            "2026-09-18",
        ],
        stdout=io.StringIO(),
        stderr=err,
    )
    assert code == 2
    assert "--local" in err.getvalue()


def test_run_enrich_is_invoked(monkeypatch, tmp_path, sample_profile_path, sample_crawl_path):
    called = {}

    def fake_enrich(argv, **kwargs):
        called["argv"] = argv
        return 0

    monkeypatch.setattr("seo_geo_engine.enrichment.cli.run", fake_enrich)
    plan_path = tmp_path / "remediation-plan.md"
    shutil.copy(Path(sample_profile_path).parent / "remediation-plan.md", plan_path)
    code = run_run(
        [
            "--profile",
            str(sample_profile_path),
            "--from-crawl",
            str(sample_crawl_path),
            "--enrich",
            "pagespeed,gsc",
            "--date",
            "2026-09-18",
            "--out-dir",
            str(tmp_path / "audits"),
            "--plan",
            str(plan_path),
        ],
        stdout=io.StringIO(),
    )
    assert code == 0
    assert "--pagespeed" in called["argv"]
    assert "--gsc" in called["argv"]


def test_run_stops_when_enrichment_fails(monkeypatch, tmp_path, sample_profile_path, sample_crawl_path):
    monkeypatch.setattr("seo_geo_engine.enrichment.cli.run", lambda argv, **kwargs: 2)
    plan_path = tmp_path / "remediation-plan.md"
    shutil.copy(Path(sample_profile_path).parent / "remediation-plan.md", plan_path)
    err = io.StringIO()
    code = run_run(
        [
            "--profile",
            str(sample_profile_path),
            "--from-crawl",
            str(sample_crawl_path),
            "--enrich",
            "pagespeed",
            "--date",
            "2026-09-18",
            "--out-dir",
            str(tmp_path / "audits"),
            "--plan",
            str(plan_path),
        ],
        stdout=io.StringIO(),
        stderr=err,
    )
    assert code == 2
    assert "enrichment failed" in err.getvalue()
    assert not (tmp_path / "audits" / "data" / "standard-report-2026-09-18.json").exists()


def test_verify_unchanged_sample_reports_fail_id(tmp_path, sample_profile_path, sample_crawl_path):
    """Applying an artifact to the profile repo (not the website) leaves the
    crawl unchanged — verify --id must fail, which is the designed miss."""
    plan_path = tmp_path / "remediation-plan.md"
    shutil.copy(Path(sample_profile_path).parent / "remediation-plan.md", plan_path)
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    assert (
        run_run(
            [
                "--profile",
                str(sample_profile_path),
                "--from-crawl",
                str(sample_crawl_path),
                "--date",
                "2026-09-10",
                "--out-dir",
                str(out_a),
                "--plan",
                str(plan_path),
            ],
            stdout=io.StringIO(),
        )
        == 0
    )
    assert (
        run_run(
            [
                "--profile",
                str(sample_profile_path),
                "--from-crawl",
                str(sample_crawl_path),
                "--date",
                "2026-09-18",
                "--out-dir",
                str(out_b),
                "--plan",
                str(plan_path),
            ],
            stdout=io.StringIO(),
        )
        == 0
    )
    buf = io.StringIO()
    code = verify_run(
        [
            "--before",
            str(out_a / "data" / "standard-report-2026-09-10.json"),
            "--after",
            str(out_b / "data" / "standard-report-2026-09-18.json"),
            "--id",
            "SCHEMA-001",
        ],
        stdout=buf,
    )
    assert code == 1
    assert "not improved" in buf.getvalue()
