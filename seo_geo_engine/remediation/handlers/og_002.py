"""OG-002 — reuse metaDesc as og:description. Never invent copy."""
from seo_geo_engine.checks.helpers import pages
from seo_geo_engine.remediation.remediation_framework import RemediationResult, remediate


@remediate("OG-002", kind="script", depends_on="—")
def remediate_og_002(site: dict) -> RemediationResult:
    """Drafts an og:description from the page's own meta description when
    one exists and og:description is missing/empty — no new copy invented."""
    targets = [p for p in pages(site) if not (p.get("ogDescription") or "").strip()]
    if not targets:
        return RemediationResult(
            id="OG-002",
            kind="script",
            detail="Nothing to draft — every page already has an og:description.",
        )

    lines = []
    for p in targets:
        fallback = (p.get("metaDesc") or "").strip()
        if fallback:
            lines.append(f'{p["url"]}\n<meta property="og:description" content="{fallback}">')
        else:
            lines.append(
                f"{p['url']} — no meta description to reuse either; "
                "needs real copy, not draftable from crawl data alone."
            )

    return RemediationResult(
        id="OG-002",
        kind="script",
        detail=(
            f"Drafted og:description for {len(targets)} page(s) "
            "(reusing the existing meta description where one exists)."
        ),
        artifact="\n\n".join(lines),
        evidence=[p["url"] for p in targets],
    )
