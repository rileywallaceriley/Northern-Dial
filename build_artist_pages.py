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
LOGO_URL = "https://i.imgur.com/XIAPd0N.png"


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
        artist_schema["homeLocation"] = {"@type": "Place", "name": location}

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
        links.append(f'<a class="link-chip" href="{escape(website, quote=True)}" target="_blank" rel="noopener">Official Site</a>')
    if instagram:
        links.append(f'<a class="link-chip" href="{escape(instagram, quote=True)}" target="_blank" rel="noopener">Instagram</a>')
    if feature:
        links.append(f'<a class="link-chip" href="../{escape(feature.lstrip("./"), quote=True)}">Northern Dial Feature</a>')
    if enrichment.get("musicbrainz_artist_id"):
        mbid = escape(enrichment["musicbrainz_artist_id"], quote=True)
        links.append(f'<a class="link-chip" href="https://musicbrainz.org/artist/{mbid}" target="_blank" rel="noopener">MusicBrainz</a>')

    source_html = ""
    if sources:
        source_items = "".join(
            f'<li><a href="{escape(url, quote=True)}" target="_blank" rel="noopener">Research source {index}</a></li>'
            for index, url in enumerate(sources, 1)
        )
        source_html = f'<section class="sources card"><p class="eyebrow">Verified profile</p><h2>Sources</h2><ul>{source_items}</ul></section>'

    link_html = f'<div class="official-links">{"".join(links)}</div>' if links else ""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", bio) if part.strip()]
    bio_html = "".join(f'<p class="bio">{escape(part)}</p>' for part in paragraphs)
    location_html = f'<p class="location">{escape(location)}</p>' if location else ""
    title = f"{name} | Canadian Artist | Northern Dial"

    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#CC3333">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description, quote=True)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{canonical}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Oswald:wght@700&family=Roboto+Condensed:wght@400;700&display=swap" rel="stylesheet">
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
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    html,body {{ background:#fff; color:#1a1a1a; }}
    body {{ font-family:'Roboto Condensed',sans-serif; line-height:1.6; }}
    a {{ color:#8b2323; }}
    .site-header {{ background:#fff; padding:28px 20px 18px; text-align:center; }}
    .logo {{ display:inline-block; max-width:420px; width:min(78vw,420px); }}
    .logo img {{ display:block; height:auto; width:100%; }}
    .site-nav {{ background:#1a1a1a; border-bottom:3px solid #c33; display:flex; justify-content:center; flex-wrap:wrap; }}
    .site-nav a {{ color:#fff; font-family:'Oswald',sans-serif; font-size:.9rem; font-weight:700; letter-spacing:.11em; padding:13px 22px; text-decoration:none; text-transform:uppercase; }}
    .site-nav a:hover,.site-nav a:focus,.site-nav a.active {{ background:#262626; color:#c33; }}
    .page {{ margin:0 auto; max-width:1100px; padding:36px 20px 70px; }}
    .breadcrumbs {{ color:#696969; font-size:.9rem; margin-bottom:28px; }}
    .breadcrumbs a {{ color:#555; text-decoration:none; }}
    .breadcrumbs a:hover {{ color:#c33; }}
    .hero {{ background:linear-gradient(135deg,#1a1a1a 0%,#292929 100%); border:4px solid #c33; border-radius:10px; box-shadow:0 8px 28px rgba(0,0,0,.16); color:#fff; padding:clamp(28px,5vw,54px); }}
    .eyebrow {{ color:#c33; font-family:'Oswald',sans-serif; font-size:.78rem; font-weight:700; letter-spacing:.16em; margin-bottom:8px; text-transform:uppercase; }}
    h1,h2 {{ font-family:'Bebas Neue',sans-serif; font-weight:400; letter-spacing:.035em; text-transform:uppercase; }}
    h1 {{ font-size:clamp(3rem,9vw,6rem); line-height:.94; margin-bottom:10px; }}
    h2 {{ font-size:2.25rem; line-height:1; margin-bottom:14px; }}
    .location {{ color:#d4d4d4; font-family:'Oswald',sans-serif; font-size:.95rem; letter-spacing:.08em; margin-bottom:24px; text-transform:uppercase; }}
    .bio {{ font-size:clamp(1.05rem,2vw,1.22rem); line-height:1.7; max-width:760px; }}
    .bio + .bio {{ margin-top:16px; }}
    .official-links {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:28px; }}
    .link-chip {{ border:1px solid #666; border-radius:6px; color:#fff; font-family:'Oswald',sans-serif; font-size:.82rem; letter-spacing:.08em; padding:9px 13px; text-decoration:none; text-transform:uppercase; }}
    .link-chip:hover,.link-chip:focus {{ border-color:#c33; color:#c33; }}
    .cta {{ background:#c33; border:2px solid #c33; border-radius:7px; color:#fff; display:inline-block; font-family:'Oswald',sans-serif; font-size:.92rem; font-weight:700; letter-spacing:.1em; margin-top:30px; padding:12px 20px; text-decoration:none; text-transform:uppercase; transition:.2s ease; }}
    .cta:hover,.cta:focus {{ background:#8b2323; border-color:#8b2323; transform:translateY(-2px); }}
    .content-grid {{ display:grid; gap:24px; grid-template-columns:minmax(0,1fr); margin-top:28px; }}
    .card {{ background:#f7f7f7; border:1px solid #ddd; border-radius:10px; padding:26px 28px; }}
    .sources ul {{ list-style:none; }}
    .sources li + li {{ border-top:1px solid #ddd; margin-top:10px; padding-top:10px; }}
    .sources a {{ overflow-wrap:anywhere; }}
    .back-link {{ display:inline-block; font-family:'Oswald',sans-serif; font-size:.88rem; letter-spacing:.08em; margin-top:30px; text-decoration:none; text-transform:uppercase; }}
    .site-footer {{ background:#1a1a1a; border-top:3px solid #c33; color:#aaa; padding:24px 20px; text-align:center; }}
    .site-footer a {{ color:#fff; text-decoration:none; }}
    @media (max-width:620px) {{
      .site-header {{ padding-top:20px; }}
      .site-nav a {{ flex:1 1 auto; padding:12px 10px; text-align:center; }}
      .page {{ padding-top:24px; }}
      .hero {{ border-width:3px; padding:28px 22px; }}
      .card {{ padding:22px; }}
    }}
  </style>
</head>
<body>
  <header class="site-header">
    <a class="logo" href="../index.html" aria-label="Northern Dial home"><img src="{LOGO_URL}" alt="Northern Dial"></a>
  </header>
  <nav class="site-nav" aria-label="Primary navigation">
    <a href="../index.html">Listen</a>
    <a class="active" href="../artists.html">Artists</a>
    <a href="../shows.html">Shows</a>
  </nav>
  <main class="page">
    <nav class="breadcrumbs" aria-label="Breadcrumb"><a href="../index.html">Home</a> / <a href="../artists.html">Artists</a> / {escape(name)}</nav>
    <article>
      <section class="hero">
        <p class="eyebrow">Northern Dial Artist Profile</p>
        <h1>{escape(name)}</h1>
        {location_html}
        {bio_html}
        {link_html}
        <a class="cta" href="{request_url}">Request {escape(name)}</a>
      </section>
      <div class="content-grid">
        {source_html}
      </div>
      <a class="back-link" href="../artists.html#artist-{slug}">← Back to the artist directory</a>
    </article>
  </main>
  <footer class="site-footer">Independent Canadian music discovery · <a href="../index.html">Northern Dial</a></footer>
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
