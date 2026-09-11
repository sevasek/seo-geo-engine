"""
A "profile" is everything specific to one website: base URL, entity/topical
cluster map, contact-info patterns, extra standard rows, and (for
local-serve mode) how to boot the site's own repo locally. It's loaded from
a site.yaml file plus, optionally, a sibling Python module that registers
profile-specific checks/remediation handlers by import side-effect — same
mechanism the engine's own built-in checks use (see checks/__init__.py).

This is the ONE place site-specific facts enter the engine. Every built-in
check reads site["profile"] (a plain dict, via SiteProfile.to_dict()) rather
than importing a constant, so a profile plugs in by data, not by forking code.
"""
import importlib
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from seo_geo_engine.checks.standard_loader import StandardItem, merge_standards

# A handful of named phone-pattern presets so a profile can write
# `contact.phone_pattern: AU_MOBILE_LANDLINE` instead of hand-rolling a
# regex for a common locale. `phone_regex_override` covers anything not
# listed here.
PHONE_PATTERN_PRESETS = {
    "AU_MOBILE_LANDLINE": r"\+?61\s?\d[\d ]{7,}\d|\(0\d\)\s?\d[\d ]{6,}\d",
    "US_NANP": r"\+?1?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}",
    "UK_GENERAL": r"\+?44\s?\d[\d ]{8,}\d|0\d[\d ]{9,}\d",
}


@dataclass
class DisabledRule:
    id: str
    reason: str


@dataclass
class SiteProfile:
    # Where this profile lives — every relative path in site.yaml (extension
    # standard files, fixture paths, the checks module) resolves against
    # this directory, so a profile is portable regardless of caller cwd.
    root: Path

    base_url: str = ""
    org_name: str = ""
    org_name_fallback: str = ""
    locale: str = "en-US"

    service_page_pattern: str = ""
    service_index_url: str = ""
    title_separator: str = ""

    entity_clusters: dict = field(default_factory=dict)

    phone_pattern: str = ""
    phone_regex_override: str = ""
    address_patterns: list = field(default_factory=list)

    sitemap_url: str = ""
    user_agent: str = ""

    local_dev: dict = field(default_factory=dict)

    disabled_ids: list[DisabledRule] = field(default_factory=list)

    standard_extension_paths: list[Path] = field(default_factory=list)
    checks_module: str = ""
    handlers_module: str = ""

    def resolved_phone_regex(self) -> str:
        if self.phone_regex_override:
            return self.phone_regex_override
        return PHONE_PATTERN_PRESETS.get(self.phone_pattern, "")

    def to_dict(self) -> dict:
        """The shape every check reads as site["profile"]."""
        return {
            "site": {
                "base_url": self.base_url,
                "org_name": self.org_name,
                "org_name_fallback": self.org_name_fallback,
                "locale": self.locale,
            },
            "pages": {
                "service_page_pattern": self.service_page_pattern,
                "service_index_url": self.service_index_url,
                "title_separator": self.title_separator,
            },
            "entity_clusters": self.entity_clusters,
            "contact": {
                "phone_pattern": self.phone_pattern,
                "phone_regex": self.resolved_phone_regex(),
                "address_patterns": self.address_patterns,
            },
            "crawl": {
                "sitemap_url": self.sitemap_url,
                "user_agent": self.user_agent,
            },
            "local_dev": self.local_dev,
        }


def load_profile(path: str | Path) -> SiteProfile:
    path = Path(path).resolve()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    root = path.parent

    site = data.get("site", {}) or {}
    pages = data.get("pages", {}) or {}
    contact = data.get("contact", {}) or {}
    crawl = data.get("crawl", {}) or {}

    disabled = [
        DisabledRule(id=d["id"], reason=d["reason"])
        for d in (data.get("disabled_ids") or [])
    ]
    for d in disabled:
        if not d.reason.strip():
            raise ValueError(f"{path}: disabled_ids entry {d.id!r} needs a non-empty reason")

    ext_paths = [root / p for p in (data.get("standard_extension_paths") or [])]

    return SiteProfile(
        root=root,
        base_url=site.get("base_url", ""),
        org_name=site.get("org_name", ""),
        org_name_fallback=site.get("org_name_fallback", site.get("org_name", "")),
        locale=site.get("locale", "en-US"),
        service_page_pattern=pages.get("service_page_pattern", ""),
        service_index_url=pages.get("service_index_url", ""),
        title_separator=pages.get("title_separator", ""),
        entity_clusters=data.get("entity_clusters", {}) or {},
        phone_pattern=contact.get("phone_pattern", ""),
        phone_regex_override=contact.get("phone_regex_override", ""),
        address_patterns=contact.get("address_patterns", []) or [],
        sitemap_url=crawl.get("sitemap_url", ""),
        user_agent=crawl.get("user_agent", ""),
        local_dev=data.get("local_dev", {}) or {},
        disabled_ids=disabled,
        standard_extension_paths=ext_paths,
        checks_module=data.get("checks_module", ""),
        handlers_module=data.get("handlers_module", ""),
    )


def import_profile_code(profile: SiteProfile) -> None:
    """Import the profile's own checks_ext/handlers_ext modules (by dotted
    module name, resolved with the profile's own directory on sys.path) so
    their @check(...)/@remediate(...) decorators run. Call this once, before
    running a report/remediation pass against this profile.

    Engine remediations load first; the profile's handlers_module is then
    imported with origin="profile" so it may overwrite an engine ID.
    """
    import seo_geo_engine.checks  # noqa: F401
    import seo_geo_engine.remediation  # noqa: F401
    from seo_geo_engine.remediation.remediation_framework import registration_origin

    if str(profile.root) not in sys.path:
        sys.path.insert(0, str(profile.root))
    if profile.checks_module:
        importlib.import_module(profile.checks_module)
    token = registration_origin.set("profile")
    try:
        if profile.handlers_module:
            importlib.import_module(profile.handlers_module)
    finally:
        registration_origin.reset(token)


def effective_standard(profile: SiteProfile, engine_default_paths: list[Path]) -> list[StandardItem]:
    """Engine defaults + this profile's extensions, merged (profile rows win
    on ID collision), then filtered by disabled_ids."""
    all_paths = list(engine_default_paths) + list(profile.standard_extension_paths)
    items = merge_standards(all_paths)
    disabled = {d.id for d in profile.disabled_ids}
    return [item for item in items if item.id not in disabled]
