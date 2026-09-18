"""SCHEMA-001 — draft Service JSON-LD from crawl fields. Nothing invented."""
import json

from seo_geo_engine.checks.helpers import service_pages
from seo_geo_engine.remediation.remediation_framework import RemediationResult, remediate


@remediate("SCHEMA-001", kind="script", depends_on="—")
def remediate_schema_001(site: dict) -> RemediationResult:
    """Drafts a Service JSON-LD block per service page missing one, built
    entirely from fields the crawl already has — nothing invented."""
    org_name = (site.get("profile") or {}).get("site", {}).get("org_name", "")
    targets = [p for p in service_pages(site) if "Service" not in (p.get("jsonLdTypes") or [])]
    if not targets:
        return RemediationResult(
            id="SCHEMA-001",
            kind="script",
            detail="Nothing to draft — every service page already has Service schema.",
        )

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
        detail=(
            f"Drafted Service JSON-LD for {len(targets)} page(s) missing it — "
            "still needs CMS access to publish."
        ),
        artifact="\n\n".join(blocks),
        evidence=[p["url"] for p in targets],
    )
