import json

from seo_geo_engine.checks.standard_loader import load_standard
from seo_geo_engine.paths import default_standard_paths
from seo_geo_engine.profile import effective_standard, import_profile_code, load_profile
from seo_geo_engine.report import compute_score, render_json, run_report


def test_json_points_earned_sums_to_score_earned(sample_profile_path, sample_crawl_path):
    """Guards against the headline score and the sum of displayed per-item
    points ever being computed two different ways (see report._points_earned
    docstring) — regression coverage for a real bug class found while
    building the site-specific repos this engine generalizes."""
    profile = load_profile(sample_profile_path)
    import_profile_code(profile)
    items = effective_standard(profile, default_standard_paths())
    site = json.loads(sample_crawl_path.read_text())
    results = run_report(site, items=items, profile=profile)

    js = render_json(results)
    summed = round(sum(i["points_earned"] for i in js["items"]), 2)
    assert summed == js["score"]["earned"]


def test_score_possible_equals_total_weight(sample_profile_path, sample_crawl_path):
    profile = load_profile(sample_profile_path)
    import_profile_code(profile)
    items = effective_standard(profile, default_standard_paths())
    site = json.loads(sample_crawl_path.read_text())
    results = run_report(site, items=items, profile=profile)

    score = compute_score(results)
    assert score["possible"] == sum(item.weight for item, _ in results)


def test_engine_defaults_alone_run_without_a_profile(sample_crawl_path):
    """No-profile mode: pure engine defaults, no site["profile"] merge —
    this is the path the plain `python3 -m seo_geo_engine.report` (no
    --profile flag) exercises."""
    items = load_standard(default_standard_paths())
    site = json.loads(sample_crawl_path.read_text())
    results = run_report(site, items=items)
    assert len(results) == len(items)
