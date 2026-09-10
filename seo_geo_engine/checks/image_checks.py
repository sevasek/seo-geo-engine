from seo_geo_engine.checks.framework import check, passed, failed
from seo_geo_engine.checks.helpers import pages


@check("IMG-001")
def check_supporting_image_count(site: dict):
    # "3 supporting images beyond the site logo" -> at least 4 images total,
    # assuming the logo is one of them.
    total = len(pages(site))
    offenders = [f"{p['url']} — {p.get('imageCount', 0)} image(s)" for p in pages(site) if p.get("imageCount", 0) < 4]
    if not offenders:
        return passed("IMG-001", f"All {total} pages carry 3+ images beyond the logo.")
    return failed(
        "IMG-001",
        f"{len(offenders)}/{total} pages have fewer than 4 images total (logo + 3 supporting).",
        offenders,
        fraction=(total - len(offenders)) / total,
    )


@check("IMG-002")
def check_all_images_have_alt(site: dict):
    offenders = []
    for p in pages(site):
        missing = p.get("imagesMissingAlt", 0)
        if missing:
            offenders.append(f"{p['url']} — {missing}/{p.get('imageCount', 0)} images missing alt text")
    total = len(pages(site))
    if not offenders:
        return passed("IMG-002", f"Every image on all {total} pages has alt text.")
    return failed(
        "IMG-002",
        f"{len(offenders)}/{total} pages have at least one image missing alt text.",
        offenders,
        fraction=(total - len(offenders)) / total,
    )
