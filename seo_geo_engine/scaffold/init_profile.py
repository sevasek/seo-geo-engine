"""
Scaffolds a brand-new, empty profile directory: a site.yaml stub, an empty
standard/extensions.md + checks_ext.py + handlers.py, an empty
remediation-plan.md, a filled-in Skill (from the engine's shipped
template), and a traceability test importing the engine's reusable
assertions instead of duplicating them.

Usage:
    python3 -m seo_geo_engine.scaffold.init_profile ./my-site-profile \
        --org-name "Acme Widgets" --base-url "https://www.acme-widgets.example"
"""
import argparse
import sys
from pathlib import Path

from seo_geo_engine.paths import routine_template_dir, skill_template_dir

SITE_YAML_TEMPLATE = """\
site:
  base_url: "{base_url}"
  org_name: "{org_name}"
  org_name_fallback: "{org_name}"
  locale: "en-US"

pages:
  service_page_pattern: ""   # e.g. "/services/" — leave blank if not applicable
  service_index_url: ""
  title_separator: "|"

entity_clusters: {{}}

contact:
  phone_pattern: ""          # e.g. AU_MOBILE_LANDLINE, US_NANP, UK_GENERAL
  address_patterns: []

crawl:
  sitemap_url: ""            # blank -> derived as `${{base_url}}/sitemap.xml`
  user_agent: ""

local_dev: {{}}
  # start_command: "npm run dev"
  # port: 3000
  # ready_url: "http://localhost:3000/"
  # ready_timeout_s: 60
  # stop_command: null

disabled_ids: []

standard_extension_paths:
  - standard/extensions.md

checks_module: "checks_ext"
handlers_module: "handlers"
"""

EXTENSIONS_MD_TEMPLATE = """\
# {org_name} — standard extensions

Add rows here for anything that needs a fact specific to {org_name} (an
entity/cluster map, a map-embed convention, ...) — see seo-geo-engine's own
CLAUDE.md for the engine-vs-profile decision procedure. Empty until the
first real angle comes in.

When you add your first rule: a `## Category` heading, then a table with
columns ID, Rule, Source, Weight, Status, Unblock requirement (weight 1-5;
status "open" or "blocked") — see seo_geo_engine/standard/default/*.md in
the engine repo, or examples/sample-profile/standard/extensions.md, for
real examples. (Deliberately not shown as a literal table here — this
file's own parser scans for table syntax on every line, comment or not, so
a placeholder example would silently become a real, garbage standard row.)
"""

CHECKS_EXT_TEMPLATE = '''\
"""
{org_name}'s own checks — add one @check(id) per row in standard/extensions.md.
Imported by seo_geo_engine.profile.import_profile_code() via `checks_module`
in site.yaml.
"""
# from seo_geo_engine.checks.framework import check, passed, failed, blocked
# from seo_geo_engine.checks.helpers import pages
#
# @check("CATEGORY-001")
# def check_something(site: dict):
#     ...
'''

HANDLERS_TEMPLATE = '''\
"""
{org_name}'s own remediation handlers — one @remediate(id, kind=...) or
manual(id, playbook=...) per non-passing row in remediation-plan.md.
Imported by seo_geo_engine.profile.import_profile_code() via
`handlers_module` in site.yaml.
"""
# from seo_geo_engine.remediation.remediation_framework import RemediationResult, manual, remediate
#
# @remediate("CATEGORY-001", kind="script")
# def remediate_category_001(site: dict) -> RemediationResult:
#     ...
'''

REMEDIATION_PLAN_TEMPLATE = """\
# {org_name} — Remediation Plan

One row per currently non-passing standard item — see seo-geo-engine's own
README for the full contract. Empty until the first audit runs.

| ID | Approach | Depends on | Status | Notes |
|---|---|---|---|---|
"""

TEST_TRACEABILITY_TEMPLATE = '''\
from pathlib import Path

from seo_geo_engine.paths import default_standard_paths
from seo_geo_engine.profile import effective_standard, import_profile_code, load_profile
from seo_geo_engine.testing.traceability import assert_standard_has_full_check_coverage

PROFILE_PATH = Path(__file__).resolve().parent.parent / "site.yaml"


def test_full_check_coverage():
    profile = load_profile(PROFILE_PATH)
    import_profile_code(profile)
    all_paths = default_standard_paths() + profile.standard_extension_paths
    assert_standard_has_full_check_coverage(all_paths)
'''

README_TEMPLATE = """\
# {org_name} — SEO/GEO profile

A profile for [seo-geo-engine](https://github.com/) — see that repo's own
README for the full engine documentation. This directory holds only what's
specific to {org_name}: `site.yaml`, `standard/extensions.md`,
`checks_ext.py`, `handlers.py`, `remediation-plan.md`, `playbooks/`.

```bash
pip install seo-geo-engine  # or an editable local checkout during co-development
python3 -m pytest
```

See `.claude/skills/seo-geo-audit/SKILL.md` for the audit workflow.
"""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def scaffold(target_dir: Path, org_name: str, base_url: str) -> None:
    if target_dir.exists() and any(target_dir.iterdir()):
        raise FileExistsError(f"{target_dir} already exists and isn't empty")

    _write(target_dir / "site.yaml", SITE_YAML_TEMPLATE.format(org_name=org_name, base_url=base_url))
    _write(target_dir / "standard" / "extensions.md", EXTENSIONS_MD_TEMPLATE.format(org_name=org_name))
    _write(target_dir / "checks_ext.py", CHECKS_EXT_TEMPLATE.format(org_name=org_name))
    _write(target_dir / "handlers.py", HANDLERS_TEMPLATE.format(org_name=org_name))
    _write(target_dir / "remediation-plan.md", REMEDIATION_PLAN_TEMPLATE.format(org_name=org_name))
    (target_dir / "playbooks").mkdir(parents=True, exist_ok=True)
    (target_dir / "playbooks" / ".gitkeep").touch()
    _write(target_dir / "tests" / "test_traceability.py", TEST_TRACEABILITY_TEMPLATE)
    (target_dir / "tests" / "__init__.py").touch()
    _write(target_dir / "README.md", README_TEMPLATE.format(org_name=org_name))

    skill_md = (skill_template_dir() / "SKILL.md").read_text(encoding="utf-8")
    skill_md = skill_md.replace("{{ORG_NAME}}", org_name)
    _write(target_dir / ".claude" / "skills" / "seo-geo-audit" / "SKILL.md", skill_md)

    routine_md = (routine_template_dir() / "pr-review-and-merge-template.md").read_text(encoding="utf-8")
    routine_md = routine_md.replace("{{ORG_NAME}}", org_name)
    _write(target_dir / ".claude" / "routines" / "pr-review-and-merge.md", routine_md)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_dir", type=Path)
    parser.add_argument("--org-name", required=True)
    parser.add_argument("--base-url", default="")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    scaffold(args.target_dir, args.org_name, args.base_url)
    print(f"Scaffolded a new profile at {args.target_dir}")


if __name__ == "__main__":
    main()
