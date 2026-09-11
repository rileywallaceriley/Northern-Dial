#!/usr/bin/env python3
"""Build indexable French-Canadian artist pages from reviewed translation batches.

Translations live separately from the English research source so English profile
rebuilds cannot overwrite editorial French copy. Each batch is capped at 50.
"""

from html import escape
from pathlib import Path
from urllib.parse import quote
import json
import re
import xml.etree.ElementTree as ET

from build_artist_pages import BASE_URL, LOGO_URL, load_profiles, load_enrichments, slugify

TRANSLATION_DIR = Path("artist_translation_batches")
FRENCH_ARTIST_DIR = Path("fr/artists")
ENGLISH_ARTIST_DIR = Path("artists")
SITEMAP_FILE = Path("sitemap.xml")
AUDIT_FILE = Path("artist_translation_audit.json")
BATCH_LIMIT = 50

PROVINCES_FR = {
    "British Columbia": "Colombie-Britannique",
    "Nova Scotia": "Nouvelle-Écosse",
    "New Brunswick": "Nouveau-Brunswick",
    "Newfoundland and Labrador": "Terre-Neuve-et-Labrador",
    "Prince Edward Island": "Île-du-Prince-Édouard",
    "Northwest Territories": "Territoires du Nord-Ouest",
}


def load_translations():
    merged = {}
    batches = []
    TRANSLATION_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(TRANSLATION_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SystemExit(f"Translation batch must be an object: {path}")
        if len(data) > BATCH_LIMIT:
            raise SystemExit(f"{path} contains {len(data)} profiles; maximum batch size is {BATCH_LIMIT}.")
        batches.append({"file": str(path), "count": len(data)})
        for key, value in data.items():
            if not isinstance(value, dict) or not str(value.get("bio_fr") or "").strip():
                raise SystemExit(f"Missing bio_fr for {key} in {path}")
            merged[str(key).casefold()] = value
    return merged, batches


def fr_location(city, country):
    city = str(city or "")
    country = str(country or "")
    for english, french in PROVINCES_FR.items():
        city = city.replace(english, french)
    if country == "Canada":
        return ", ".join(x for x in (city, "Canada") if x)
    return ", ".join(x for x in (city, country) if x)


def description_for(name, bio):
    clean = re.sub(r"\s+", " ", str(bio or "")).strip()
    if not clean:
        return f"Découvrez {name} dans le répertoire d’artistes canadiens de Northern Dial."
    if len(clean) > 155:
        clean = clean[:152].rsplit(" ", 1)[0] + "..."
    return clean


def add_hreflang_to_english(slug):
    path = ENGLISH_ARTIST_DIR / f"{slug}.html"
    if not path.exists():
        return False
    html = path.read_text(encoding="utf-8")
    fr_url = f"{BASE_URL}/fr/artists/{slug}.html"
    en_url = f"{BASE_URL}/artists/{slug}.html"
    if 'hreflang="fr-CA"' not in html:
        marker = re.search(r'<link rel="canonical"[^>]*>\s*', html)
        tags = (
            f'  <link rel="alternate" hreflang="en-CA" href="{en_url}">\n'
            f'  <link rel="alternate" hreflang="fr-CA" href="{fr_url}">\n'
            f'  <link rel="alternate" hreflang="x-default" href="{en_url}">\n'
        )
        if marker:
            html = html[:marker.end()] + tags + html[marker.end():]
        else:
            html = html.replace('</head>', tags + '</head>', 1)
        path.write_text(html, encoding="utf-8")
        return True
    return False


def render_page(name, profile, enrichment, translation):
    slug = slugify(name)
    bio = str(translation["bio_fr"]).strip()
    website = profile.get("website") or enrichment.get("website") or ""
    instagram = profile.get("instagram") or enrichment.get("instagram") or ""
    feature = profile.get("feature") or ""
    sources = [u for u in enrichment.get("sources", []) if u] or [u for u in profile.get("sources", []) if u]
    location = fr_location(enrichment.get("city"), enrichment.get("country"))
    canonical = f"{BASE_URL}/fr/artists/{slug}.html"
    english = f"{BASE_URL}/artists/{slug}.html"
    title = f"{name} | Artiste canadien | Northern Dial"
    description = description_for(name, bio)

    links = []
    if website:
        links.append(f'<a class="link-chip" href="{escape(website, quote=True)}" target="_blank" rel="noopener">Site officiel</a>')
    if instagram:
        links.append(f'<a class="link-chip" href="{escape(instagram, quote=True)}" target="_blank" rel="noopener">Instagram</a>')
    if feature:
        feature_path = feature.lstrip("./")
        fr_feature = f"/fr/{feature_path}" if (Path("fr") / feature_path).exists() else f"/{feature_path}"
        links.append(f'<a class="link-chip" href="{escape(fr_feature, quote=True)}">Article Northern Dial</a>')
    link_html = f'<div class="official-links">{"".join(links)}</div>' if links else ""

    source_html = ""
    if sources:
        items = "".join(
            f'<li><a href="{escape(url, quote=True)}" target="_blank" rel="noopener">Source de recherche {i}</a></li>'
            for i, url in enumerate(sources, 1)
        )
        source_html = f'<section class="sources card"><p class="eyebrow">Profil vérifié</p><h2>Sources</h2><ul>{items}</ul></section>'

    artist_type = "MusicGroup" if any(term in bio.casefold() for term in (" groupe", " duo", " trio", " collectif")) else "Person"
    schema = {
        "@context": "https://schema.org",
        "@type": artist_type,
        "name": name,
        "url": canonical,
        "description": description,
        "inLanguage": "fr-CA",
    }
    same_as = [u for u in (website, instagram) if u]
    if same_as:
        schema["sameAs"] = same_as
    if location:
        schema["homeLocation"] = {"@type": "Place", "name": location}

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type":"ListItem","position":1,"name":"Northern Dial","item":f"{BASE_URL}/fr/"},
            {"@type":"ListItem","position":2,"name":"Artistes","item":f"{BASE_URL}/fr/artists.html"},
            {"@type":"ListItem","position":3,"name":name,"item":canonical},
        ],
    }

    location_html = f'<p class="location">{escape(location)}</p>' if location else ""
    request_url = f"/?request={quote(name)}&lang=fr"

    return f'''<!doctype html>
<html lang="fr-CA">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#CC3333">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description, quote=True)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" hreflang="fr-CA" href="{canonical}">
  <link rel="alternate" hreflang="en-CA" href="{english}">
  <link rel="alternate" hreflang="x-default" href="{english}">
  <meta property="og:type" content="profile">
  <meta property="og:site_name" content="Northern Dial">
  <meta property="og:title" content="{escape(title, quote=True)}">
  <meta property="og:description" content="{escape(description, quote=True)}">
  <meta property="og:url" content="{canonical}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{escape(title, quote=True)}">
  <meta name="twitter:description" content="{escape(description, quote=True)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Oswald:wght@700&family=Roboto+Condensed:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/nd-shell.css?v=20260907b">
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
  <script type="application/ld+json">{json.dumps(breadcrumb, ensure_ascii=False)}</script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}html,body{{background:#fff;color:#1a1a1a}}body{{font-family:'Roboto Condensed',sans-serif;line-height:1.6}}a{{color:#8b2323}}.page{{margin:0 auto;max-width:1100px;padding:36px 20px 70px}}.breadcrumbs{{color:#696969;font-size:.9rem;margin-bottom:28px}}.breadcrumbs a{{color:#555;text-decoration:none}}.hero{{background:linear-gradient(135deg,#1a1a1a,#292929);border:4px solid #c33;border-radius:10px;box-shadow:0 8px 28px rgba(0,0,0,.16);color:#fff;padding:clamp(28px,5vw,54px)}}.eyebrow{{color:#c33;font-family:'Oswald',sans-serif;font-size:.78rem;font-weight:700;letter-spacing:.16em;margin-bottom:8px;text-transform:uppercase}}h1,h2{{font-family:'Bebas Neue',sans-serif;font-weight:400;letter-spacing:.035em;text-transform:uppercase}}h1{{font-size:clamp(3rem,9vw,6rem);line-height:.94;margin-bottom:10px}}h2{{font-size:2.25rem;line-height:1;margin-bottom:14px}}.location{{color:#d4d4d4;font-family:'Oswald',sans-serif;font-size:.95rem;letter-spacing:.08em;margin-bottom:24px;text-transform:uppercase}}.bio{{font-size:clamp(1.05rem,2vw,1.22rem);line-height:1.7;max-width:760px}}.official-links{{display:flex;flex-wrap:wrap;gap:10px;margin-top:28px}}.link-chip{{border:1px solid #666;border-radius:6px;color:#fff;font-family:'Oswald',sans-serif;font-size:.82rem;letter-spacing:.08em;padding:9px 13px;text-decoration:none;text-transform:uppercase}}.cta{{background:#c33;border:2px solid #c33;border-radius:7px;color:#fff;display:inline-block;font-family:'Oswald',sans-serif;font-size:.92rem;font-weight:700;letter-spacing:.1em;margin-top:30px;padding:12px 20px;text-decoration:none;text-transform:uppercase}}.content-grid{{display:grid;gap:24px;grid-template-columns:1fr;margin-top:28px}}.card{{background:#f7f7f7;border:1px solid #ddd;border-radius:10px;padding:26px 28px}}.sources ul{{list-style:none}}.sources li+li{{border-top:1px solid #ddd;margin-top:10px;padding-top:10px}}.back-link{{display:inline-block;font-family:'Oswald',sans-serif;font-size:.88rem;letter-spacing:.08em;margin-top:30px;text-decoration:none;text-transform:uppercase}}@media(max-width:620px){{.page{{padding-top:24px}}.hero{{border-width:3px;padding:28px 22px}}.card{{padding:22px}}}}
  </style>
</head>
<body>
<main class="page">
  <nav class="breadcrumbs" aria-label="Fil d’Ariane"><a href="/fr/">Accueil</a> / <a href="/fr/artists.html">Artistes</a> / {escape(name)}</nav>
  <article>
    <section class="hero">
      <p class="eyebrow">Profil d’artiste Northern Dial</p>
      <h1>{escape(name)}</h1>
      {location_html}
      <p class="bio">{escape(bio)}</p>
      {link_html}
      <a class="cta" href="{request_url}">Demander {escape(name)}</a>
    </section>
    <div class="content-grid">{source_html}</div>
    <a class="back-link" href="/fr/artists.html#artist-{slug}">← Retour au répertoire d’artistes</a>
  </article>
</main>
<script src="/nd-shell.js?v=20260911i18n1" defer></script>
</body>
</html>'''


def update_sitemap(slugs):
    try:
        tree = ET.parse(SITEMAP_FILE)
        root = tree.getroot()
    except (FileNotFoundError, ET.ParseError):
        return
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    existing = {el.text for el in root.findall(f"{{{ns}}}url/{{{ns}}}loc") if el.text}
    changed = False
    for slug in sorted(slugs):
        loc = f"{BASE_URL}/fr/artists/{slug}.html"
        if loc in existing:
            continue
        url = ET.SubElement(root, f"{{{ns}}}url")
        ET.SubElement(url, f"{{{ns}}}loc").text = loc
        ET.SubElement(url, f"{{{ns}}}changefreq").text = "weekly"
        ET.SubElement(url, f"{{{ns}}}priority").text = "0.65"
        changed = True
    if changed:
        ET.indent(tree, space="  ")
        tree.write(SITEMAP_FILE, encoding="utf-8", xml_declaration=True)


def main():
    translations, batches = load_translations()
    profiles = load_profiles()
    enrichments = load_enrichments()
    FRENCH_ARTIST_DIR.mkdir(parents=True, exist_ok=True)

    generated = []
    missing = []
    english_hreflang_updates = 0
    for key, translation in translations.items():
        profile_name, profile = profiles.get(key, (None, {}))
        enrichment_name, enrichment = enrichments.get(key, (None, {}))
        if not profile and not enrichment:
            missing.append(key)
            continue
        name = str(translation.get("display_name") or enrichment_name or profile_name or key)
        slug = slugify(name)
        (FRENCH_ARTIST_DIR / f"{slug}.html").write_text(
            render_page(name, profile, enrichment, translation), encoding="utf-8"
        )
        if add_hreflang_to_english(slug):
            english_hreflang_updates += 1
        generated.append(slug)

    update_sitemap(generated)
    audit = {
        "batch_limit": BATCH_LIMIT,
        "batches": batches,
        "translation_records": len(translations),
        "generated_pages": len(generated),
        "english_hreflang_updates": english_hreflang_updates,
        "missing_source_count": len(missing),
        "missing_sources": missing,
    }
    AUDIT_FILE.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Built {len(generated)} French artist pages from {len(translations)} translations; missing {len(missing)}.")


if __name__ == "__main__":
    main()
