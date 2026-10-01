from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PAGES = [
    SITE / "index.html",
    SITE / "demand-planning" / "index.html",
    SITE / "methodology" / "index.html",
    SITE / "data-notes" / "index.html",
    SITE / "404.html",
]
PUBLIC_PAGES = PAGES[:-1]


def test_pages_have_basic_metadata_and_one_h1():
    titles = []
    descriptions = []
    canonicals = []

    for path in PAGES:
        text = path.read_text(encoding="utf-8")
        title = re.search(r"<title>(.+?)</title>", text, re.I | re.S)
        description = re.search(r'<meta name="description" content="(.+?)">', text, re.I | re.S)
        canonical = re.search(r'<link rel="canonical" href="(.+?)">', text, re.I | re.S)

        assert title, path
        assert description, path
        assert canonical, path
        assert len(re.findall(r"<h1(?:\s|>)", text, re.I)) == 1, path
        assert "placeholder" not in text.lower(), path
        assert "todo" not in text.lower(), path
        assert "—" not in text, path

        titles.append(title.group(1))
        descriptions.append(description.group(1))
        canonicals.append(canonical.group(1))

    assert len(titles) == len(set(titles))
    assert len(descriptions) == len(set(descriptions))
    assert len(canonicals) == len(set(canonicals))


def test_public_pages_have_structured_data_and_social_metadata():
    for path in PUBLIC_PAGES:
        text = path.read_text(encoding="utf-8")
        assert 'type="application/ld+json"' in text, path
        assert 'property="og:title"' in text, path
        assert 'property="og:description"' in text, path
        assert 'property="og:image"' in text, path
        assert 'property="og:image:width" content="1200"' in text, path
        assert 'property="og:image:height" content="630"' in text, path


def test_site_has_discovery_files():
    assert (SITE / "sitemap.xml").exists()
    assert (SITE / "robots.txt").exists()
    assert (SITE / "llms.txt").exists()
    assert (SITE / "assets" / "favicon.svg").exists()
    assert (SITE / "assets" / "social-card.svg").exists()


def test_relative_internal_links_resolve():
    href_pattern = re.compile(r'href="([^"]+)"')
    for page in PAGES:
        text = page.read_text(encoding="utf-8")
        for href in href_pattern.findall(text):
            parsed = urlparse(href)
            if parsed.scheme or href.startswith("#"):
                continue
            target = (page.parent / parsed.path).resolve()
            if parsed.path.endswith("/") or parsed.path in {".", "..", "./", "../"}:
                target = target / "index.html"
            assert target.exists(), f"Broken link {href} in {page}"


def test_production_javascript_has_no_source_map_reference_or_console_errors():
    for path in (SITE / "assets").glob("*.js"):
        text = path.read_text(encoding="utf-8")
        assert "sourceMappingURL" not in text
        assert "console.error" not in text
        assert "—" not in text


def test_dashboard_json_has_required_sections():
    data = json.loads((SITE / "data" / "dashboard.json").read_text(encoding="utf-8"))
    assert {"overall", "history", "regions", "forecast_daily", "forecast_by_region", "exceptions"}.issubset(data)
    assert len(data["history"]) >= 80
    assert len(data["forecast_daily"]) == 14
    assert len(data["regions"]) == 4
