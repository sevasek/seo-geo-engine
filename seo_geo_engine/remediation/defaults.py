"""
Engine-owned remediations for every default standard ID.

Load order (see docs/design/engine-owned-remediation.md): this module
first, then a profile's handlers_module via import_profile_code(). A
profile may overwrite an engine ID; two engine handlers for the same ID
is a hard error.

Script handlers live in remediation/handlers/. Everything else is a
manual playbook under remediation/playbooks/<ID>.md — including blocked
stubs, whose playbook names the genuine unblock rather than pretending a
fix exists.
"""
from seo_geo_engine.remediation.handlers import og_002, schema_001  # noqa: F401
from seo_geo_engine.remediation.remediation_framework import manual

# (id, depends_on) — depends_on is stored on the registration so plan-sync
# doesn't infer it from the ID string. "—" = ready to work in the queue.
_MANUAL: list[tuple[str, str]] = [
    ("ANALYTICS-001", "CMS-ACCESS"),
    ("CONTENT-001", "CMS-ACCESS"),
    ("CONTENT-002", "CMS-ACCESS"),
    ("CONTENT-003", "CMS-ACCESS"),
    ("CONTENT-004", "SEARCH-INTENT-MAP"),
    ("CONTENT-005", "STUFFING-METHOD"),
    ("CONTENT-006", "SKIMMABILITY-RUBRIC"),
    ("CONTENT-007", "COMPETITOR-CONTENT-CORPUS"),
    ("CONTENT-008", "CLAIMS-SOURCES-MAP"),
    ("CRAWL-001", "CMS-ACCESS"),
    ("CRAWL-002", "CMS-ACCESS"),
    ("CRAWL-003", "CMS-ACCESS"),
    ("CRAWL-004", "CMS-ACCESS"),
    ("CRAWL-005", "CMS-ACCESS"),
    ("CRAWL-006", "CMS-ACCESS"),
    ("CRAWL-007", "CMS-ACCESS"),
    ("CRAWL-008", "GSC-ACCESS"),
    ("HEAD-001", "CMS-ACCESS"),
    ("HEAD-002", "CMS-ACCESS"),
    ("HEAD-003", "CMS-ACCESS"),
    ("HEAD-004", "CMS-ACCESS"),
    ("IMG-001", "CMS-ACCESS"),
    ("IMG-002", "CMS-ACCESS"),
    ("LINK-004", "CMS-ACCESS"),
    ("LINK-005", "CMS-ACCESS"),
    ("LINK-006", "LINK-POLICY"),
    ("LINK-007", "REL-POLICY"),
    ("LINK-008", "NEW-PAGE-POLICY"),
    ("META-001", "CMS-ACCESS"),
    ("META-002", "CMS-ACCESS"),
    ("META-003", "CMS-ACCESS"),
    ("META-004", "CMS-ACCESS"),
    ("MOBILE-001", "CMS-ACCESS"),
    ("OG-001", "CMS-ACCESS"),
    ("PERF-001", "CMS-ACCESS"),
    ("PERF-002", "PSI-ACCESS"),
    ("PERF-003", "PSI-ACCESS"),
    ("PERF-004", "CRUX-DATA"),
    ("SCHEMA-002", "CMS-ACCESS"),
]

for _id, _depends_on in _MANUAL:
    manual(_id, playbook=f"playbooks/{_id}.md", depends_on=_depends_on)
