"""
Renders the standard-compliance report as a standalone, static HTML file —
the same data seo_geo_engine.report writes to
audits/data/standard-report-<date>.json, dropped into
report_template.html's placeholders. No hand editing: run
seo_geo_engine.report first, then this, every time.

Deliberately NOT a Claude/AI-authored artifact and NOT published through any
hosted "Artifact" system — this is a plain file on disk you can open
locally, serve with `python3 -m http.server`, or push to any static host
(GitHub Pages, S3, nginx, whatever). Nothing about the score, the top
issues, or the HTML itself is interpreted by an LLM; it's a deterministic
string-substitution template, same as this report has always been.

Usage:
    python3 -m seo_geo_engine.render_html_report \
        audits/data/standard-report-2026-08-20.json \
        audits/standard-report-2026-08-20.html \
        --eyebrow "SEO / GEO Standard  ·  example.com" \
        --title "SEO Scorecard"
"""
import argparse
import json
from pathlib import Path

from seo_geo_engine.paths import report_template_path

PLACEHOLDERS = {
    "__ITEMS_JSON__": "items",
    "__SCORE_JSON__": "score",
    "__TOP_ISSUES_JSON__": "top_issues",
}


def render(json_path: Path, out_path: Path, eyebrow: str = "SEO / GEO Standard", title: str = "SEO Scorecard") -> None:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    template = report_template_path().read_text(encoding="utf-8")
    html = template
    for placeholder, key in PLACEHOLDERS.items():
        if placeholder not in template:
            raise RuntimeError(f"{report_template_path()} has no {placeholder} placeholder — was it edited by hand?")
        if key not in data:
            raise RuntimeError(f"{json_path} has no {key!r} key — regenerate it with the current seo_geo_engine.report")
        html = html.replace(placeholder, json.dumps(data[key]))
    html = html.replace("__EYEBROW__", eyebrow).replace("__TITLE__", title)
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {out_path} ({len(data['items'])} items, score {data['score']['earned']}/{data['score']['possible']})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path)
    parser.add_argument("out_path", type=Path)
    parser.add_argument("--eyebrow", default="SEO / GEO Standard")
    parser.add_argument("--title", default="SEO Scorecard")
    args = parser.parse_args()
    render(args.json_path, args.out_path, args.eyebrow, args.title)


if __name__ == "__main__":
    main()
