"""
Local-serve-and-crawl mode: boots the sample profile's local_dev server
(a plain `python3 -m http.server` standing in for a real repo's own dev
command), crawls it with the same real packaged crawl.js Layer 2 uses, and
confirms two things: the resulting site dict has the same shape a live-URL
crawl would produce, and the dev server's port is actually freed on
teardown (the stop path, not just the happy path).

Slow (spawns a real Chromium + a real subprocess server) — requires the
same crawler setup as tests/test_badseo_integration.py.
"""
import json
import socket

import pytest

from seo_geo_engine.crawl.local_serve import LocalDevConfig, LocalServeError, LocalServer
from seo_geo_engine.crawl.run import _run_crawl_js
from seo_geo_engine.paths import crawler_dir
from seo_geo_engine.profile import load_profile

_NEEDS_SETUP = not (crawler_dir() / "node_modules").exists()


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


@pytest.mark.slow
@pytest.mark.skipif(_NEEDS_SETUP, reason="crawler/node_modules missing — run `npm install` in seo_geo_engine/crawler/ first")
def test_local_serve_crawl_matches_live_crawl_shape(sample_profile_path, tmp_path):
    profile = load_profile(sample_profile_path)
    config = LocalDevConfig.from_profile_dict(profile.local_dev, profile.root)

    assert _port_is_free(config.port), "test setup assumption violated: port already in use before starting"

    out_path = tmp_path / "local-crawl.json"
    with LocalServer(config) as base_url:
        assert base_url == f"http://localhost:{config.port}"
        _run_crawl_js(base_url, out_path, ua=profile.user_agent)

    # Teardown already ran (context manager exited) — the stop path, not
    # just the happy path.
    assert _port_is_free(config.port), "LocalServer did not free the port on teardown"

    site = json.loads(out_path.read_text())
    for key in ("sitemapUrls", "robotsTxt", "pages", "discoveredNonSitemapPages", "linkResolutions"):
        assert key in site, f"local-serve crawl output is missing {key!r} — shape must match a live-URL crawl"
    assert len(site["pages"]) == 2
    assert {p["url"] for p in site["pages"]} == {
        "http://localhost:8123/index.html",
        "http://localhost:8123/about.html",
    }


def test_local_dev_config_requires_start_command():
    with pytest.raises(LocalServeError):
        LocalDevConfig.from_profile_dict({"port": 8123}, "/tmp")
