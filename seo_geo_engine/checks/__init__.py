"""
Import every built-in check module so its @check(...) decorators run and
populate seo_geo_engine.checks.framework.REGISTRY. Anything that imports
seo_geo_engine.checks gets the full built-in registry for free — that's the
only reason this file exists. A profile's own checks_ext.py does the same
thing for its own additional/overriding checks.
"""
from seo_geo_engine.checks import (  # noqa: F401
    metadata_checks,
    open_graph_checks,
    heading_checks,
    structured_data_checks,
    content_checks,
    image_checks,
    linking_checks,
    performance_checks,
    crawlability_checks,
    mobile_checks,
    analytics_checks,
)
from seo_geo_engine.checks.framework import REGISTRY  # noqa: F401
