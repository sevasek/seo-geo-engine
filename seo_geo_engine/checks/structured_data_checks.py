from seo_geo_engine.checks.framework import check, passed, failed
from seo_geo_engine.checks.helpers import service_pages, urls


@check("SCHEMA-001")
def check_service_schema_present(site: dict):
    targets = service_pages(site)
    if not targets:
        return passed("SCHEMA-001", "No service pages found for this profile — nothing to check.")
    offenders = [p["url"] for p in targets if "Service" not in (p.get("jsonLdTypes") or [])]
    if not offenders:
        return passed("SCHEMA-001", f"All {len(targets)} service pages carry Service schema.")
    return failed(
        "SCHEMA-001",
        f"{len(offenders)}/{len(targets)} service pages have no Service JSON-LD.",
        offenders,
        fraction=(len(targets) - len(offenders)) / len(targets),
    )


@check("SCHEMA-002")
def check_faqpage_schema_present(site: dict):
    targets = service_pages(site)
    if not targets:
        return passed("SCHEMA-002", "No service pages found for this profile — nothing to check.")
    with_schema = [p["url"] for p in targets if "FAQPage" in (p.get("jsonLdTypes") or [])]
    if len(with_schema) == len(targets):
        return passed("SCHEMA-002", f"All {len(targets)} service pages carry FAQPage schema.")
    return failed(
        "SCHEMA-002",
        f"{len(targets) - len(with_schema)}/{len(targets)} service pages carry no FAQPage schema.",
        urls(targets),
        fraction=len(with_schema) / len(targets),
    )
