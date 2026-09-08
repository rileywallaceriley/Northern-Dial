#!/usr/bin/env python3
"""Generate standalone SEO pages for researched Northern Dial artists.

This build is intentionally independent of the live station API. It uses the
committed profile/enrichment data as its source of truth so artist SEO pages
can still publish when the station endpoint is unavailable.
"""

from html import escape
from pathlib import Path
from urllib.parse import quote
import json
import re
import unicodedata
import xml.etree.ElementTree as ET

BASE_URL = "https://www.northerndial.ca"
PROFILE_FILE = Path("artist_profiles.json")
ENRICHMENT_FILE = Path("artist_enrichment.json")
ENRICHMENT_BATCH_DIR = Path("artist_enrichment_batches")
ARTIST_DIR = Path("artists")
SITEMAP_FILE = Path("sitemap.xml")


def slugify(value):
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.casefold()).strip("-")
    return slug or "artist"


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_profiles():
    data = load_json(PROFILE_FILE, {})
    return {str(name).casefold(): (str(name), value or {}) for name, value in data.items()}


def load_enrichments():
    merged = {}
    paths = [ENRICHMENT_FILE]
    paths.extend(sorted(ENRICHMENT_BATCH_DIR.glob("*.json")))
    for path in paths:
        if not path.exists():
            continue
        data = load_json(path, {})
        if not isinstance(data, dict):
            continue
        for name, value in data.items():
            merged[str(name).casefold()] = (str(name), value or {})
    return merged


def entity_type(bio):
    text = bio.casefold()
    group_terms = (" group", " band", " duo", " trio", " collective", " crew")
    return "MusicGroup" if any(term in text for term in group_terms) else "Person"


def description_for(name, bio, city, country):
    if bio:
        clean = re.sub(r"\s+", " ", bio).strip()
        if len(clean) > 155:
            clean = clean[:152].rsplit(" ", 1)[0] + "..."
        return clean
    location = ", ".join(value for value in (city, country) if value)
    if location:
        return f"Explore {name}, a Canadian artist connected to {location}, on Northern Dial. Read the artist profile and request their music."
    return f"Explore {name} on Northern Dial. Read the artist profile, follow official links and request their music on Canadian independent radio."


def render_page(name, profile, enrichment):
    bio = profile.get("bio") or enrichment.get("bio") or ""
    website = profile.get("website") or enrichment.get("website") or ""
    instagram = profile.get("instagram") or enrichment.get("instagram") or ""
    feature = profile.get("feature") or ""
    city = enrichment.get("city") or ""
    country = enrichment.get("country") or ""
    sources = [url for url in enrichment.get("sources", []) if url]
    slug = slugify(name)
    canonical = f"{BASE_URL}/artists/{slug}.html"
    request_url = f"../index.html?request={quote(name)}"
    description = description_for(name, bio, city, country)
    location = ", ".join(value for value in (city, country) if value)

    same_as = [url for url in (website, instagram) if url]
    if enrichment.get("musicbrainz_artist_id"):
        same_as.append(f"https://musicbrainz.org/artist/{enrichment['musicbrainz_artist_id']}")

    artist_schema = {
        "@context": "https://schema.org",
        "@type": entity_type(bio),
        "name": name,
        "url": canonical,
        "description": description,
    }
    if same_as:
        artist_schema["sameAs"] = same_as
    if city or country:
        artist_schema["homeLocation"] = {
            "@type": "Place",
            "name": location,
        }

    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Northern Dial", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Artists", "item": f"{BASE_URL}/artists.html"},
            {"@type": "ListItem", "position": 3, "name": name, "item": canonical},
        ],
    }

    links = []
    if website:
        links.append(f'<a href="{escape(website, quote=True)}" target="_blank" rel="noopener">Official site</a>')
    if instagram:
        links.append(f'<a href="{escape(instagram, quote=True)}" target="_blank" rel="noopener">Instagram</a>')
    if feature:
        links.append(f'<a href="../{escape(feature.lstrip("./"), quote=True)}">Northern Dial feature</a>')
    if enrichment.get("musicbrainz_artist_id"):
        mbid = escape(enrichment["musicbrainz_artist_id"], quote=True)
        links.append(f'<a href="https://musicbrainz.org/artist/{mbid}" target="_blank" rel="noopener">MusicBrainz</a>')

    source_html = ""
    if sources:
        source_items = "".join(
            f'<li><a href="{escape(url, quote=True)}" target="_blank" rel="noopener">Research source {index}</a></li>'
            for index, url in enumerate(sources, 1)
        )
        source_html = f'<section class="sources"><h2>Sources</h2><ul>{source_items}</ul></section>'

    link_html = f'<div class="official-links">{" · ".join(links)}</div>' if links else ""
    bio_html = f'<p class="bio">{escape(bio)}</p>' if bio else ""
    location_html = f'<p class="location">{escape(location)}</p>' if location else ""
    title = f"{name} | Canadian Artist | Northern Dial"

    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description, quote=True)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="profile">
  <meta property="og:site_name" content="Northern Dial">
  <meta property="og:title" content="{escape(title, quote=True)}">
  <meta property="og:description" content="{escape(description, quote=True)}">
  <meta property="og:url" content="{canonical}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{escape(title, quote=True)}">
  <meta name="twitter:description" content="{escape(description, quote=True)}">
  <script type="application/ld+json">{json.dumps(artist_schema, ensure_ascii=False)}</script>
  <script type="application/ld+json">{json.dumps(breadcrumb_schema, ensure_ascii=False)}</script>
  <style>
    :root {{ color-scheme: dark; --bg:#080808; --panel:#121212; --text:#f4f4f4; --muted:#aaa; --line:#2b2b2b; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; line-height:1.6; }}
    header, main, footer {{ width:min(880px,calc(100% - 32px)); margin:auto; }}
    header {{ padding:28px 0 16px; border-bottom:1px solid var(--line); }}
    nav a, a {{ color:inherit; }}
    .brand {{ font-weight:800; letter-spacing:.08em; text-transform:uppercase; text-decoration:none; }}
    main {{ padding:48px 0 64px; }}
    .breadcrumbs {{ color:var(--muted); font-size:.95rem; margin-bottom:24px; }}
    h1 {{ font-size:clamp(2.25rem,7vw,4.75rem); line-height:1; margin:.15em 0 .25em; }}
    h2 {{ margin-top:40px; }}
    .location {{ color:var(--muted); font-weight:650; }}
    .bio {{ font-size:1.15rem; max-width:72ch; }}
    .official-links {{ margin:24px 0; }}
    .cta {{ display:inline-block; margin-top:24px; padding:12px 18px; border:1px solid var(--text); text-decoration:none; font-weight:750; }}
    .sources {{ margin-top:48px; padding-top:24px; border-top:1px solid var(--line); }}
    footer {{ padding:24px 0 40px; border-top:1px solid var(--line); color:var(--muted); }}
  </style>
</head>
<body>
  <header><a class="brand" href="../index.html">Northern Dial</a></header>
  <main>
    <nav class="breadcrumbs" aria-label="Breadcrumb"><a href="../index.html">Home</a> / <a href="../artists.html">Artists</a> / {escape(name)}</nav>
    <article>
      <h1>{escape(name)}</h1>
      {location_html}
      {bio_html}
      {link_html}
      <a class="cta" href="{request_url}">Request {escape(name)}</a>
      {source_html}
    </article>
  </main>
  <footer><a href="../artists.html#artist-{slug}">Back to the Northern Dial artist directory</a></footer>
</body>
</html>
'''


def update_sitemap(slugs):
    if not SITEMAP_FILE.exists():
        return
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    tree = ET.parse(SITEMAP_FILE)
    root = tree.getroot()
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    for node in list(root):
        loc = node.find(f"{namespace}loc")
        if loc is not None and loc.text and "/artists/" in loc.text:
            root.remove(node)
    for slug in sorted(slugs):
        url = ET.SubElement(root, f"{namespace}url")
        ET.SubElement(url, f"{namespace}loc").text = f"{BASE_URL}/artists/{slug}.html"
        ET.SubElement(url, f"{namespace}priority").text = "0.7"
    ET.indent(tree, space="  ")
    tree.write(SITEMAP_FILE, encoding="utf-8", xml_declaration=True)


def main():
    profiles = load_profiles()
    enrichments = load_enrichments()
    keys = sorted(set(profiles) | set(enrichments))
    ARTIST_DIR.mkdir(exist_ok=True)

    generated = []
    expected_files = set()
    for key in keys:
        profile_name, profile = profiles.get(key, ("", {}))
        enrichment_name, enrichment = enrichments.get(key, ("", {}))
        if not profile and not enrichment.get("reviewed"):
            continue
        name = profile_name or enrichment_name
        if not name:
            continue
        slug = slugify(name)
        path = ARTIST_DIR / f"{slug}.html"
        path.write_text(render_page(name, profile, enrichment), encoding="utf-8")
        generated.append(slug)
        expected_files.add(path.name)

    for path in ARTIST_DIR.glob("*.html"):
        if path.name not in expected_files:
            path.unlink()

    update_sitemap(generated)
    print(f"Generated {len(generated):,} standalone artist pages and updated {SITEMAP_FILE}")


if __name__ == "__main__":
    main()
