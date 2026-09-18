class EnrichmentError(Exception):
    """A requested enricher cannot run. The CLI maps this to exit code 2."""
