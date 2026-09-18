"""Where the engine's own shipped assets live, resolved via importlib.resources
so this works identically whether the package is running from a source
checkout or from an installed wheel."""
from importlib.resources import as_file, files
from pathlib import Path


def _package_dir() -> Path:
    with as_file(files("seo_geo_engine")) as p:
        return Path(p)


def default_standard_paths() -> list[Path]:
    """Every *.md file under the engine's shipped standard/default/ — sorted
    so the merge order (and therefore category order in a report) is stable
    across machines/filesystems."""
    return sorted((_package_dir() / "standard" / "default").glob("*.md"))


def crawler_dir() -> Path:
    return _package_dir() / "crawler"


def skill_template_dir() -> Path:
    return _package_dir() / "skills" / "seo-geo-audit-template"


def routine_template_dir() -> Path:
    return _package_dir() / "routines"


def report_template_path() -> Path:
    return _package_dir() / "report_template.html"


def engine_playbooks_dir() -> Path:
    return _package_dir() / "remediation" / "playbooks"


def site_dict_schema_path() -> Path:
    return _package_dir() / "crawler" / "site-dict.schema.json"
