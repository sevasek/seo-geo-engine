from pathlib import Path

from seo_geo_engine.scaffold.init_profile import scaffold


def test_scaffold_writes_engine_repo_url_and_empty_plan(tmp_path):
    target = tmp_path / "acme-profile"
    scaffold(target, "Acme Widgets", "https://www.acme-widgets.example")

    readme = (target / "README.md").read_text(encoding="utf-8")
    assert "https://github.com/sevasek/seo-geo-engine" in readme
    assert "seo-geo-run" in readme
    assert "seo-geo-verify" in readme

    plan = (target / "remediation-plan.md").read_text(encoding="utf-8")
    assert "| ID | Approach | Depends on | Status | Notes |" in plan

    skill = (target / ".claude" / "skills" / "seo-geo-audit" / "SKILL.md").read_text(encoding="utf-8")
    assert "Acme Widgets" in skill
    assert "seo-geo-plan-sync" in skill
    assert "seo-geo-run" in skill
    assert "seo-geo-verify" in skill
    assert "docs/design/data-contract.md" in skill
    assert "docs/design/enrichment.md" in skill
