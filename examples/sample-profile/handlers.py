"""
Acme Example Co's profile-owned remediation handlers.

Engine defaults already cover every shipped standard ID (SCHEMA-001 and
OG-002 as scripts; the rest as generic playbooks). This module only
registers the sample's *extension* IDs — the ones that need a business
fact the engine must not own. Imported via `handlers_module` in site.yaml
with origin="profile", so a later override of an engine ID would be
allowed; this sample deliberately overrides none.
"""
from seo_geo_engine.remediation.remediation_framework import manual

for _id, _depends_on in (
    ("LOCAL-001", "CMS-ACCESS"),
    ("LINK-001", "CMS-ACCESS"),
    ("LINK-002", "KEYWORD-MAP"),
):
    manual(_id, playbook=f"playbooks/{_id}.md", depends_on=_depends_on)
