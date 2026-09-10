"""
Layer 2 of the fixture-based test harness: a real, deliberately-broken
static site (tests/fixtures/badseo_site/pages/) crawled end-to-end by the
real packaged crawl.js, then scored by the real check registry — proving
the crawler and the checks agree on what "broken" looks like in actual
HTML, not just in a hand-written JSON fixture (which Layer 1 already
covers). Pilot subset: META-002, HEAD-002, SCHEMA-001, LINK-005, CRAWL-001
— see tests/fixtures/badseo_site/pages/*.html for which page breaks which
rule.

Slow (spawns a real Chromium + a local HTTP server) and requires
`npm install` + `npx playwright install chromium` to have been run in
seo_geo_engine/crawler/ — skipped automatically if that setup is missing.
Excluded from the default run: `pytest -m "not slow"`.
"""
import json
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from seo_geo_engine.checks.standard_loader import load_standard
from seo_geo_engine.paths import crawler_dir, default_standard_paths
from seo_geo_engine.report import run_report

BADSEO_DIR = Path(__file__).parent / "fixtures" / "badseo_site"
CRAWLER_DIR = crawler_dir()

pytestmark = pytest.mark.slow

_NEEDS_SETUP = not (CRAWLER_DIR / "node_modules").exists()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for(url: str, timeout_s: float = 10.0) -> None:
    import urllib.request

    deadline = time.time() + timeout_s
    last_error = None
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1).read()
            return
        except Exception as e:  # noqa: BLE001 - genuinely any failure means "not ready yet"
            last_error = e
            time.sleep(0.2)
    raise RuntimeError(f"{url} never became ready: {last_error}")


@pytest.mark.skipif(_NEEDS_SETUP, reason="crawler/node_modules missing — run `npm install` in seo_geo_engine/crawler/ first")
def test_badseo_site_pilot_checks(tmp_path):
    port = _free_port()
    origin = f"http://127.0.0.1:{port}"

    # Copy the fixture pages into a temp dir so sitemap.xml's __ORIGIN__
    # placeholder can be substituted without touching the checked-in files.
    served_dir = tmp_path / "pages"
    shutil.copytree(BADSEO_DIR / "pages", served_dir)
    sitemap_path = served_dir / "sitemap.xml"
    sitemap_path.write_text(sitemap_path.read_text().replace("__ORIGIN__", origin))

    server_proc = subprocess.Popen(
        [sys.executable, str(BADSEO_DIR / "server.py"), str(port), str(served_dir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_for(f"{origin}/index.html")

        out_path = tmp_path / "site-crawl.json"
        result = subprocess.run(
            ["node", str(CRAWLER_DIR / "crawl.js"), "--origin", origin, "--ua", "badseo-integration-test", "--out", str(out_path)],
            cwd=CRAWLER_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"crawl.js failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        assert out_path.exists()
    finally:
        server_proc.terminate()
        server_proc.wait(timeout=5)

    site = json.loads(out_path.read_text())
    items = load_standard(default_standard_paths())
    results = run_report(site, items=items)
    by_id = {item.id: result for item, result in results}

    assert by_id["META-002"].verdict == "fail"
    assert any("meta-002-missing-description.html" in e for e in by_id["META-002"].evidence)

    assert by_id["HEAD-002"].verdict == "fail"
    assert any("head-002-numeral-heading.html" in e for e in by_id["HEAD-002"].evidence)

    assert by_id["SCHEMA-001"].verdict == "fail"
    assert any("schema-001-no-jsonld.html" in e for e in by_id["SCHEMA-001"].evidence)

    assert by_id["LINK-005"].verdict == "fail"
    assert any("orphan-page.html" in e for e in by_id["LINK-005"].evidence)

    assert by_id["CRAWL-001"].verdict == "fail"
    assert any("crawl-001-not-in-sitemap.html" in e for e in by_id["CRAWL-001"].evidence)
