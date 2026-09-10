"""A trivial static file server for the Layer-2 real-HTML/real-crawler
integration tests — serves a directory of HTML pages (by default
tests/fixtures/badseo_site/pages/) over plain HTTP so the real packaged
crawl.js can crawl it end-to-end.

Usage: python3 server.py <port> [directory]

`directory` defaults to the pages/ dir next to this script — the test
harness instead points it at a temp copy (with sitemap.xml's __ORIGIN__
placeholder substituted for the real port), so the checked-in fixture
directory is never mutated.
"""
import functools
import http.server
import sys
from pathlib import Path

DEFAULT_PAGES_DIR = Path(__file__).parent / "pages"


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    pages_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PAGES_DIR
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(pages_dir))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving {pages_dir} on port {httpd.server_address[1]}", flush=True)
        httpd.serve_forever()


if __name__ == "__main__":
    main()
