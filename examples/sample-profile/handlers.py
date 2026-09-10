"""
Acme Example Co's remediation handlers — mirrors checks_ext.py's pattern.
Two IDs get a real `script` handler that drafts fix content directly from
crawl data (the mechanically-generatable case); everything else non-passing
is `manual`, pointing at a written playbook under playbooks/ (the
editorial/access-gated case). Imported by
seo_geo_engine.profile.import_profile_code() via the `handlers_module` name
in site.yaml.
"""
import json

from seo_geo_engine.checks.helpers import pages, service_pages
from seo_geo_engine.remediation.remediation_framework import RemediationResult, manual, remediate


@remediate("SCHEMA-001", kind="script")
def remediate_schema_001(site: dict) -> RemediationResult:
    """Drafts a Service JSON-LD block per service page missing one, built
    entirely from fields the crawl already has — nothing invented."""
    org_name = (site.get("profile") or {}).get("site", {}).get("org_name", "")
    targets = [p for p in service_pages(site) if "Service" not in (p.get("jsonLdTypes") or [])]
    if not targets:
        return RemediationResult(id="SCHEMA-001", kind="script", detail="Nothing to draft — every service page already has Service schema.")

    blocks = []
    for p in targets:
        snippet = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": p.get("title", "").split("|")[0].strip(),
            "url": p["url"],
            "provider": {"@type": "Organization", "name": org_name},
        }
        blocks.append(f"<!-- {p['url']} -->\n" + json.dumps(snippet, indent=2))

    return RemediationResult(
        id="SCHEMA-001",
        kind="script",
        detail=f"Drafted Service JSON-LD for {len(targets)} page(s) missing it — still needs CMS access to publish.",
        artifact="\n\n".join(blocks),
        evidence=[p["url"] for p in targets],
    )


@remediate("OG-002", kind="script")
def remediate_og_002(site: dict) -> RemediationResult:
    """Drafts an og:description from the page's own meta description when
    one exists and is missing/empty as og:description — no new copy
    invented, just reused from a field the page already has."""
    targets = [p for p in pages(site) if not (p.get("ogDescription") or "").strip()]
    if not targets:
        return RemediationResult(id="OG-002", kind="script", detail="Nothing to draft — every page already has an og:description.")

    lines = []
    for p in targets:
        fallback = (p.get("metaDesc") or "").strip()
        if fallback:
            lines.append(f"{p['url']}\n<meta property=\"og:description\" content=\"{fallback}\">")
        else:
            lines.append(f"{p['url']} — no meta description to reuse either; needs real copy, not draftable from crawl data alone.")

    return RemediationResult(
        id="OG-002",
        kind="script",
        detail=f"Drafted og:description for {len(targets)} page(s) (reusing the existing meta description where one exists).",
        artifact="\n\n".join(lines),
        evidence=[p["url"] for p in targets],
    )


_MANUAL_IDS = [
    "ANALYTICS-001", "CONTENT-001", "CONTENT-002", "CONTENT-003", "CONTENT-004",
    "CONTENT-005", "CONTENT-006", "CONTENT-007", "CONTENT-008", "CRAWL-001",
    "CRAWL-003", "CRAWL-006", "CRAWL-008", "HEAD-001", "HEAD-002", "IMG-001",
    "IMG-002", "LINK-004", "LINK-006", "LINK-007", "LINK-008", "META-001",
    "META-002", "MOBILE-001", "OG-001", "PERF-001", "PERF-002", "PERF-003",
    "PERF-004", "SCHEMA-002", "LOCAL-001", "LINK-001", "LINK-002",
]

for _id in _MANUAL_IDS:
    manual(_id, playbook=f"playbooks/{_id}.md")
