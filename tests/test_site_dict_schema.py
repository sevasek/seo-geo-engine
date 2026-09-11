"""Validate crawl JSON (Layer 1 fixtures, sample fixture, and — in the slow
suite — a live crawler snapshot) against the shipped site-dict schema."""
import json
from pathlib import Path

import pytest

from seo_geo_engine.paths import site_dict_schema_path

jsonschema = pytest.importorskip("jsonschema")

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).parent / "fixtures" / "checks"
SAMPLE = REPO_ROOT / "examples" / "sample-profile" / "fixtures" / "site-crawl-sample.json"
CRAWLER_REQUIRED = {
    "sitemapUrls",
    "robotsTxt",
    "pages",
    "discoveredNonSitemapPages",
    "linkResolutions",
}


@pytest.fixture(scope="module")
def schema():
    return json.loads(site_dict_schema_path().read_text(encoding="utf-8"))


def test_schema_file_is_draft_2020_12(schema):
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    jsonschema.Draft202012Validator.check_schema(schema)
    assert set(schema["$defs"]["crawlerSnapshot"]["required"]) == CRAWLER_REQUIRED


@pytest.mark.parametrize(
    "path",
    sorted(FIXTURES.glob("*/good.json")) + sorted(FIXTURES.glob("*/bad.json")),
    ids=lambda p: f"{p.parent.name}/{p.name}",
)
def test_layer1_fixtures_match_site_dict_schema(schema, path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(data)


def test_sample_crawl_matches_crawler_snapshot_schema(schema):
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(data)
    missing = CRAWLER_REQUIRED - set(data)
    assert not missing, f"Sample crawl is missing crawler snapshot keys: {sorted(missing)}"
