"""Post-crawl enricher. Recorded PSI/GSC payloads only — no live Google."""
from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from seo_geo_engine.checks.crawlability_checks import check_sitemap_submitted_to_gsc
from seo_geo_engine.checks.performance_checks import check_cls, check_inp, check_lcp
from seo_geo_engine.enrichment.cli import run as enrich_cli
from seo_geo_engine.enrichment.errors import EnrichmentError
from seo_geo_engine.enrichment.pagespeed import (
    apply_pagespeed,
    cache_filename,
    enrich_pagespeed,
    map_psi_response,
)
from seo_geo_engine.enrichment.urls import is_psi_unreachable_url
from seo_geo_engine.profile import load_profile

FIXTURES = Path(__file__).parent / "fixtures" / "enrichment"
SAMPLE_CRAWL = (
    Path(__file__).resolve().parent.parent
    / "examples"
    / "sample-profile"
    / "fixtures"
    / "site-crawl-sample.json"
)
SAMPLE_PROFILE = (
    Path(__file__).resolve().parent.parent / "examples" / "sample-profile" / "site.yaml"
)


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class RecordingGscClient:
    def __init__(self, sites, sitemaps):
        self._sites = sites
        self._sitemaps = sitemaps
        self.listed_property = None

    def list_sites(self):
        return list(self._sites)

    def list_sitemaps(self, site_url: str):
        self.listed_property = site_url
        return list(self._sitemaps)


def _public_profile_yaml(tmp_path: Path, key_env: str = "PAGESPEED_API_KEY") -> Path:
    text = (
        "site:\n"
        "  base_url: https://example.com\n"
        "crawl:\n"
        "  sitemap_url: https://example.com/sitemap.xml\n"
        "enrichment:\n"
        f"  pagespeed_api_key_env: {key_env}\n"
        "  gsc_property: https://www.example.com/\n"
    )
    path = tmp_path / "site.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_base_enrichment_import_does_not_need_google():
    import seo_geo_engine.enrichment as pkg
    import seo_geo_engine.enrichment.cli  # noqa: F401
    import seo_geo_engine.enrichment.search_console as gsc

    assert hasattr(gsc, "map_sitemaps")
    assert pkg.map_psi_response is map_psi_response


def test_map_psi_reproduces_sample_pagespeed():
    """Exit criterion: sample hand-written pageSpeed from recorded PSI fixtures."""
    sample = json.loads(SAMPLE_CRAWL.read_text(encoding="utf-8"))
    unenriched = _load("site-crawl-unenriched.json")
    payloads = _load("psi-sample-pages.json")

    assert all("pageSpeed" not in p for p in unenriched["pages"])
    apply_pagespeed(unenriched, payloads)

    expected = {p["url"]: p["pageSpeed"] for p in sample["pages"]}
    got = {p["url"]: p["pageSpeed"] for p in unenriched["pages"]}
    assert got == expected
    for blob in got.values():
        assert "inp" not in blob
        assert "inpMs" not in blob


def test_map_psi_omits_missing_lcp_and_never_writes_inp():
    mapped = map_psi_response(_load("psi-missing-lcp.json"))
    assert "lcpMs" not in mapped
    assert mapped["cls"] == 0.03
    assert mapped["hasFieldData"] is False
    assert "inpMs" not in mapped


def test_map_psi_omits_missing_cls():
    mapped = map_psi_response(_load("psi-missing-cls.json"))
    assert mapped["lcpMs"] == 1800
    assert "cls" not in mapped


def test_map_psi_has_field_data_from_loading_experience():
    mapped = map_psi_response(_load("psi-with-field-data.json"))
    assert mapped["hasFieldData"] is True
    assert mapped["lcpMs"] == 1500


def test_psi_unreachable_localhost_test_private_ip():
    assert is_psi_unreachable_url("http://localhost:8123/")
    assert is_psi_unreachable_url("http://127.0.0.1/")
    assert is_psi_unreachable_url("https://www.acme-example.test/")
    assert is_psi_unreachable_url("http://192.168.1.20/page")
    assert is_psi_unreachable_url("http://10.0.0.5/")
    assert is_psi_unreachable_url("http://[::1]/")
    assert not is_psi_unreachable_url("https://example.com/")
    assert not is_psi_unreachable_url("https://www.example.com/page/")


def test_enrich_pagespeed_refuses_test_tld():
    site = _load("site-crawl-unenriched.json")
    with pytest.raises(EnrichmentError, match="refusing --pagespeed"):
        enrich_pagespeed(site, "fake-key", fetch=lambda url, key: (_ for _ in ()).throw(AssertionError("network")))


def test_cli_pagespeed_without_key_exits_2(tmp_path):
    crawl = tmp_path / "crawl.json"
    crawl.write_text((FIXTURES / "site-crawl-public.json").read_text(), encoding="utf-8")
    profile = _public_profile_yaml(tmp_path)
    err = io.StringIO()
    code = enrich_cli(
        [str(crawl), "--profile", str(profile), "--pagespeed"],
        env={},
        stderr=err,
        psi_fetch=lambda url, key: (_ for _ in ()).throw(AssertionError("network")),
    )
    assert code == 2
    assert "PAGESPEED_API_KEY" in err.getvalue()
    written = json.loads(crawl.read_text())
    assert "pageSpeed" not in written["pages"][0]


def test_cli_pagespeed_refuses_sample_test_urls(tmp_path):
    crawl = tmp_path / "crawl.json"
    crawl.write_text((FIXTURES / "site-crawl-unenriched.json").read_text(), encoding="utf-8")
    err = io.StringIO()
    code = enrich_cli(
        [str(crawl), "--profile", str(SAMPLE_PROFILE), "--pagespeed"],
        env={"PAGESPEED_API_KEY": "not-a-real-key"},
        stderr=err,
        psi_fetch=lambda url, key: (_ for _ in ()).throw(AssertionError("network")),
    )
    assert code == 2
    assert "refusing --pagespeed" in err.getvalue()


def test_cli_pagespeed_mocked_http_writes_pagespeed_and_perf002_unblocks(tmp_path):
    crawl = tmp_path / "crawl.json"
    crawl.write_text((FIXTURES / "site-crawl-public.json").read_text(), encoding="utf-8")
    profile = _public_profile_yaml(tmp_path)
    payload = _load("psi-with-field-data.json")
    calls = []

    def fetch(url, key):
        calls.append((url, key))
        assert key == "test-key"
        assert url == "https://example.com/"
        return payload

    err = io.StringIO()
    code = enrich_cli(
        [str(crawl), "--profile", str(profile), "--pagespeed", "--no-cache"],
        env={"PAGESPEED_API_KEY": "test-key"},
        stderr=err,
        psi_fetch=fetch,
        sleep=lambda _s: None,
    )
    assert code == 0
    assert calls == [("https://example.com/", "test-key")]
    site = json.loads(crawl.read_text())
    assert site["pages"][0]["pageSpeed"] == {
        "hasFieldData": True,
        "lcpMs": 1500,
        "cls": 0.02,
    }
    assert check_lcp(site).verdict == "pass"
    assert check_cls(site).verdict == "pass"
    assert check_inp(site).verdict == "blocked"


def test_cli_pagespeed_uses_named_env_var(tmp_path):
    crawl = tmp_path / "crawl.json"
    crawl.write_text((FIXTURES / "site-crawl-public.json").read_text(), encoding="utf-8")
    profile = _public_profile_yaml(tmp_path, key_env="MY_PSI_KEY")
    keys = []

    def fetch(url, key):
        keys.append(key)
        return _load("psi-with-field-data.json")

    code = enrich_cli(
        [str(crawl), "--profile", str(profile), "--pagespeed", "--no-cache"],
        env={"MY_PSI_KEY": "from-named-var", "PAGESPEED_API_KEY": "wrong"},
        stderr=io.StringIO(),
        psi_fetch=fetch,
        sleep=lambda _s: None,
    )
    assert code == 0
    assert keys == ["from-named-var"]


def test_pagespeed_cache_hit_skips_network(tmp_path):
    site = json.loads((FIXTURES / "site-crawl-public.json").read_text())
    payload = _load("psi-with-field-data.json")
    cache_dir = tmp_path / "cache"
    fetches = []

    def fetch(url, key):
        fetches.append(url)
        return payload

    enrich_pagespeed(
        site,
        "k",
        cache_dir=cache_dir,
        fetch=fetch,
        sleep=lambda _s: None,
        now=datetime(2026, 9, 11, tzinfo=timezone.utc),
    )
    assert fetches == ["https://example.com/"]
    cache_path = cache_dir / cache_filename("https://example.com/", "2026-09-11")
    assert cache_path.is_file()

    fetches.clear()
    site2 = json.loads((FIXTURES / "site-crawl-public.json").read_text())
    enrich_pagespeed(
        site2,
        "k",
        cache_dir=cache_dir,
        fetch=fetch,
        sleep=lambda _s: None,
        now=datetime(2026, 9, 11, tzinfo=timezone.utc),
    )
    assert fetches == []
    assert site2["pages"][0]["pageSpeed"]["lcpMs"] == 1500


def test_no_cache_skips_existing_cache(tmp_path):
    site = json.loads((FIXTURES / "site-crawl-public.json").read_text())
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    stale = {"lighthouseResult": {"audits": {}}}
    path = cache_dir / cache_filename("https://example.com/", "2026-09-11")
    path.write_text(json.dumps(stale), encoding="utf-8")
    fetches = []

    def fetch(url, key):
        fetches.append(url)
        return _load("psi-with-field-data.json")

    enrich_pagespeed(
        site,
        "k",
        cache_dir=cache_dir,
        use_cache=False,
        fetch=fetch,
        sleep=lambda _s: None,
        now=datetime(2026, 9, 11, tzinfo=timezone.utc),
    )
    assert fetches == ["https://example.com/"]
    assert site["pages"][0]["pageSpeed"]["lcpMs"] == 1500


def test_sequential_delay_between_psi_calls():
    site = {
        "pages": [
            {"url": "https://example.com/a"},
            {"url": "https://example.com/b"},
        ]
    }
    slept = []
    payload = _load("psi-with-field-data.json")
    enrich_pagespeed(
        site,
        "k",
        use_cache=False,
        fetch=lambda url, key: payload,
        sleep=slept.append,
        delay_s=0.25,
    )
    assert slept == [0.25]


def test_omitted_flags_leave_keys_absent(tmp_path):
    crawl = tmp_path / "crawl.json"
    original = (FIXTURES / "site-crawl-unenriched.json").read_text()
    crawl.write_text(original, encoding="utf-8")
    err = io.StringIO()
    code = enrich_cli(
        [str(crawl), "--profile", str(SAMPLE_PROFILE)],
        env={"PAGESPEED_API_KEY": "k"},
        stderr=err,
    )
    assert code == 0
    assert "neither --pagespeed nor --gsc" in err.getvalue()
    assert json.loads(crawl.read_text()) == json.loads(original)


def test_map_sitemaps_matches_profile_url_only():
    from seo_geo_engine.enrichment.search_console import map_sitemaps

    blob = map_sitemaps(
        _load("gsc-sitemaps.json")["sitemap"],
        ["https://www.acme-example.test/sitemap.xml"],
    )
    assert blob == {
        "sitemapSubmitted": True,
        "sitemapErrors": 0,
        "sitemapWarnings": 1,
    }


def test_map_sitemaps_false_when_none_match():
    from seo_geo_engine.enrichment.search_console import map_sitemaps

    blob = map_sitemaps(
        _load("gsc-sitemaps.json")["sitemap"],
        ["https://www.acme-example.test/other.xml"],
    )
    assert blob["sitemapSubmitted"] is False
    assert blob["sitemapErrors"] == 0
    assert blob["sitemapWarnings"] == 0


def test_gsc_property_not_in_site_list_exits_2_does_not_write(tmp_path):
    from seo_geo_engine.enrichment.search_console import enrich_search_console

    site = _load("site-crawl-unenriched.json")
    profile = load_profile(SAMPLE_PROFILE)
    client = RecordingGscClient(
        sites=[{"siteUrl": "https://www.example.com/", "permissionLevel": "siteFullUser"}],
        sitemaps=_load("gsc-sitemaps.json")["sitemap"],
    )
    with pytest.raises(EnrichmentError, match="not in this credential's site list"):
        enrich_search_console(site, profile, client=client)
    assert site.get("searchConsole") is None


def test_cli_gsc_warns_on_local_crawl_and_writes_search_console(tmp_path):
    crawl = tmp_path / "crawl.json"
    crawl.write_text((FIXTURES / "site-crawl-unenriched.json").read_text(), encoding="utf-8")
    client = RecordingGscClient(
        sites=_load("gsc-sites.json")["siteEntry"],
        sitemaps=_load("gsc-sitemaps.json")["sitemap"],
    )
    err = io.StringIO()
    code = enrich_cli(
        [str(crawl), "--profile", str(SAMPLE_PROFILE), "--gsc"],
        env={},
        stderr=err,
        gsc_client_factory=lambda: client,
    )
    assert code == 0
    assert "crawl looks local" in err.getvalue()
    assert client.listed_property == "https://www.acme-example.test/"
    site = json.loads(crawl.read_text())
    assert site["searchConsole"] == {
        "sitemapSubmitted": True,
        "sitemapErrors": 0,
        "sitemapWarnings": 1,
    }
    assert check_sitemap_submitted_to_gsc(site).verdict == "pass"


def test_cli_gsc_without_libs_exits_2(tmp_path):
    crawl = tmp_path / "crawl.json"
    crawl.write_text((FIXTURES / "site-crawl-public.json").read_text(), encoding="utf-8")
    profile = _public_profile_yaml(tmp_path)
    err = io.StringIO()
    code = enrich_cli(
        [str(crawl), "--profile", str(profile), "--gsc"],
        env={},
        stderr=err,
    )
    assert code == 2
    assert "seo-geo-engine[enrich]" in err.getvalue() or "GSC" in err.getvalue() or "gsc" in err.getvalue().lower()
    site = json.loads(crawl.read_text())
    assert "searchConsole" not in site or site.get("searchConsole") in (None,)


def test_unenriched_runtime_blocks_open_rules():
    site = _load("site-crawl-unenriched.json")
    lcp = check_lcp(site)
    cls = check_cls(site)
    gsc = check_sitemap_submitted_to_gsc(site)
    assert lcp.verdict == "blocked"
    assert cls.verdict == "blocked"
    assert gsc.verdict == "blocked"
    assert "docs/design/enrichment.md" in lcp.detail
    assert "docs/design/enrichment.md" in cls.detail
    assert "docs/design/enrichment.md" in gsc.detail
    assert check_inp(site).verdict == "blocked"


def test_profile_loads_enrichment_block_without_secrets():
    profile = load_profile(SAMPLE_PROFILE)
    assert profile.enrichment["pagespeed_api_key_env"] == "PAGESPEED_API_KEY"
    assert profile.enrichment["gsc_property"] == "https://www.acme-example.test/"
    dumped = json.dumps(profile.to_dict())
    assert "AIza" not in dumped
    assert "BEGIN PRIVATE" not in dumped


def test_cli_mocked_urllib_pagespeed(tmp_path, monkeypatch):
    """HTTP is mocked at urlopen — no live Google."""
    crawl = tmp_path / "crawl.json"
    crawl.write_text((FIXTURES / "site-crawl-public.json").read_text(), encoding="utf-8")
    profile = _public_profile_yaml(tmp_path)
    payload = _load("psi-with-field-data.json")

    class FakeResp:
        def read(self):
            return json.dumps(payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    seen = []

    def fake_urlopen(req, timeout=30):
        parsed = urlparse(req.full_url)
        qs = parse_qs(parsed.query)
        seen.append(qs)
        assert qs["strategy"] == ["mobile"]
        assert "key" in qs
        return FakeResp()

    monkeypatch.setattr("seo_geo_engine.enrichment.pagespeed.urllib.request.urlopen", fake_urlopen)
    code = enrich_cli(
        [str(crawl), "--profile", str(profile), "--pagespeed", "--no-cache"],
        env={"PAGESPEED_API_KEY": "k"},
        stderr=io.StringIO(),
        sleep=lambda _s: None,
    )
    assert code == 0
    assert seen
    site = json.loads(crawl.read_text())
    assert site["pages"][0]["pageSpeed"]["lcpMs"] == 1500
