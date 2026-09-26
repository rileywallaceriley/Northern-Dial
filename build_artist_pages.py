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
PROFILE_INDEX_FILE = Path("artist-profile-index.json")
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
    """Merge enrichment records field-by-field and preserve editorial display casing."""
    merged = {}
    display_names = {}
    paths = [ENRICHMENT_FILE]
    paths.extend(sorted(ENRICHMENT_BATCH_DIR.glob("*.json")))
    for path in paths:
        if not path.exists():
            continue
        data = load_json(path, {})
        if not isinstance(data, dict):
            continue
        for name, value in data.items():
            key = str(name).casefold()
            if isinstance(value, dict):
                display_names[key] = str(value.get("display_name") or name)
                merged.setdefault(key, {}).update(value)
            else:
                display_names[key] = str(name)
                merged[key] = value
    return {key: (display_names.get(key, key), value) for key, value in merged.items()}


def render_editorial_text(value, album_titles=()):
    """Escape editorial copy while allowing only verified album-title emphasis."""
    text = str(value or "")
    titles = sorted({str(title) for title in album_titles if title}, key=len, reverse=True)
    if not titles:
        return escape(text)
    pattern = re.compile("|".join(re.escape(title) for title in titles))
    output = []
    position = 0
    for match in pattern.finditer(text):
        output.append(escape(text[position:match.start()]))
        output.append(f"<em>{escape(match.group(0))}</em>")
        position = match.end()
    output.append(escape(text[position:]))
    return "".join(output)


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
    bio = enrichment.get("bio") or profile.get("bio") or ""
    album_titles = enrichment.get("album_titles", [])
    website = profile.get("website") or enrichment.get("website") or ""
    instagram = profile.get("instagram") or enrichment.get("instagram") or ""
    feature_items = []
    for source in (profile, enrichment):
        legacy_feature = source.get("feature") or ""
        if legacy_feature:
            feature_items.append({"href": legacy_feature, "label": "Northern Dial Feature"})
        features = source.get("features") or []
        if isinstance(features, str):
            features = [features]
        for item in features:
            if isinstance(item, str) and item:
                feature_items.append({"href": item, "label": "Northern Dial Feature"})
            elif isinstance(item, dict) and item.get("href"):
                feature_items.append({
                    "href": item["href"],
                    "label": item.get("label") or "Northern Dial Feature",
                })
    deduped_features = []
    seen_feature_hrefs = set()
    for item in feature_items:
        href = str(item["href"]).strip()
        if not href or href in seen_feature_hrefs:
            continue
        seen_feature_hrefs.add(href)
        deduped_features.append({"href": href, "label": str(item["label"]).strip() or "Northern Dial Feature"})
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
    for feature_item in deduped_features:
        href = escape(feature_item["href"].lstrip("./"), quote=True)
        label = escape(feature_item["label"])
        links.append(f'<a class="link-chip" href="../{href}">{label}</a>')
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
    bio_html = "".join(
        f'<p class="bio">{render_editorial_text(part, album_titles)}</p>'
        for part in paragraphs
    )
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
  <link rel="stylesheet" href="/nd-shell.css?v=20260907b">
  <link rel="stylesheet" href="/nd-banner.css?v=20260914a">
  <style>
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    html,body {{ background:#F6F1E7; color:#1a1a1a; }}
    body {{ font-family:'Roboto Condensed',sans-serif; line-height:1.6; min-height:100vh; }}
    a {{ color:#8b2323; }}
    .site-header {{ background:#fff; border-bottom:4px solid #C33; padding:12px 18px; text-align:center; }}
    .logo {{ display:inline-block; }}
    .logo img {{ display:block; height:76px; width:auto; }}
    .site-nav {{ background:#1a1a1a; border-bottom:2px solid #c33; display:flex; justify-content:center; flex-wrap:wrap; }}
    .site-nav a {{ color:#fff; font-family:'Oswald',sans-serif; font-size:.9rem; font-weight:700; letter-spacing:.1em; padding:13px 20px; text-decoration:none; text-transform:uppercase; }}
    .site-nav a:hover,.site-nav a:focus,.site-nav a.active {{ background:#262626; color:#c33; }}
    .page {{ margin:0 auto; max-width:1120px; padding:38px 18px 72px; }}
    .breadcrumbs {{ color:#696969; font-size:.9rem; margin-bottom:28px; }}
    .breadcrumbs a {{ color:#555; text-decoration:none; }}
    .breadcrumbs a:hover {{ color:#c33; }}
    .hero {{ background:linear-gradient(135deg,#151515,#2a2a2a); border:5px solid #c33; border-radius:14px; box-shadow:0 8px 28px rgba(0,0,0,.16); color:#fff; padding:clamp(30px,5vw,48px); }}
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
    .card {{ background:#fff; border:4px solid #1a1a1a; border-radius:12px; padding:26px 28px; }}
    .sources ul {{ list-style:none; }}
    .sources li + li {{ border-top:1px solid #ddd; margin-top:10px; padding-top:10px; }}
    .sources a {{ overflow-wrap:anywhere; }}
    .back-link {{ display:inline-block; font-family:'Oswald',sans-serif; font-size:.88rem; letter-spacing:.08em; margin-top:30px; text-decoration:none; text-transform:uppercase; }}
    .site-footer {{ border-top:3px solid #1a1a1a; color:#666; margin:48px auto 0; max-width:1120px; padding:22px 18px 32px; text-align:left; }}
    .site-footer a {{ color:#8b2323; font-weight:700; text-decoration:none; }}
    @media (max-width:620px) {{
      .site-header {{ padding:10px 14px; }}
      .logo img {{ height:62px; }}
      .site-nav a {{ flex:1 1 auto; padding:12px 10px; text-align:center; }}
      .page {{ padding:26px 12px 56px; }}
      .hero {{ border-width:4px; padding:30px 23px; }}
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
  <script src="/nd-shell.js?v=20260907b" defer></script>
</body>
</html>'''


def update_sitemap(slugs):
    try:
        root = ET.parse(SITEMAP_FILE).getroot()
    except (FileNotFoundError, ET.ParseError):
        return
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", namespace)
    existing = {element.text for element in root.findall(f"{{{namespace}}}url/{{{namespace}}}loc") if element.text}
    changed = False
    for slug in sorted(slugs):
        loc = f"{BASE_URL}/artists/{slug}.html"
        if loc in existing:
            continue
        url = ET.SubElement(root, f"{{{namespace}}}url")
        ET.SubElement(url, f"{{{namespace}}}loc").text = loc
        ET.SubElement(url, f"{{{namespace}}}changefreq").text = "weekly"
        ET.SubElement(url, f"{{{namespace}}}priority").text = "0.65"
        changed = True
    if changed:
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(SITEMAP_FILE, encoding="utf-8", xml_declaration=True)


def main():
    profiles = load_profiles()
    enrichments = load_enrichments()
    ARTIST_DIR.mkdir(parents=True, exist_ok=True)
    slugs = set()
    profile_index = {}

    names = sorted(set(profiles) | set(enrichments))
    for key in names:
        profile_name, profile = profiles.get(key, (None, {}))
        enrichment_name, enrichment = enrichments.get(key, (None, {}))
        name = enrichment_name or profile_name or key
        if not profile and not enrichment:
            continue
        if not (profile.get("bio") or enrichment.get("bio")):
            continue
        slug = slugify(name)
        (ARTIST_DIR / f"{slug}.html").write_text(render_page(name, profile, enrichment), encoding="utf-8")
        slugs.add(slug)
        profile_index[name] = f"/artists/{slug}.html"

    PROFILE_INDEX_FILE.write_text(
        json.dumps(dict(sorted(profile_index.items(), key=lambda item: item[0].casefold())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    update_sitemap(slugs)
    print(f"Built {len(slugs)} artist profile pages and refreshed {PROFILE_INDEX_FILE}.")


if __name__ == "__main__":
    main()
