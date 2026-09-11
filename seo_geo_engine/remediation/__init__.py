"""Remediation-tracking layer. Importing this package registers every
engine-owned default remediation (see defaults.py) the same way
`import seo_geo_engine.checks` registers built-in checks."""
from seo_geo_engine.remediation import defaults  # noqa: F401
from seo_geo_engine.remediation.remediation_framework import REGISTRY  # noqa: F401
