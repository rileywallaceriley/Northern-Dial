#!/usr/bin/env python3
"""Build Northern Dial Listening Paths and connect participating artist profiles."""

from html import escape
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

BASE_URL = "https://www.northerndial.ca"
DATA_FILE = Path("listening_paths.json")
OUTPUT_DIR = Path("listening-paths")
INDEX_FILE = Path("listening-paths.html")
ARTIST_DIR = Path("artists")
SITEMAP_FILE = Path("sitemap.xml")
LOGO_URL = "https://i.imgur.com/XIAPd0N.png"
START_MARKER = "<!-- listening-paths:start -->"
END_MARKER = "<!-- listening-paths:end -->"


def load_paths():
    if not DATA_FILE.exists():
        return {}
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def shell(title, description, canonical, body):
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#CC3333">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description, quote=True)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{escape(canonical, quote=True)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Oswald:wght@700&family=Roboto+Condensed:wght@400;700&display=swap" rel="stylesheet">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Northern Dial">
  <meta property="og:title" content="{escape(title, quote=True)}">
  <meta property="og:description" content="{escape(description, quote=True)}">
  <meta property="og:url" content="{escape(canonical, quote=True)}">
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
    .page {{ margin:0 auto; max-width:980px; padding:36px 20px 70px; }}
    .breadcrumbs {{ color:#696969; font-size:.9rem; margin-bottom:28px; }}
    .breadcrumbs a {{ color:#555; text-decoration:none; }}
    .hero {{ background:linear-gradient(135deg,#1a1a1a 0%,#292929 100%); border:4px solid #c33; border-radius:10px; color:#fff; padding:clamp(28px,5vw,54px); }}
    .eyebrow {{ color:#c33; font-family:'Oswald',sans-serif; font-size:.78rem; font-weight:700; letter-spacing:.16em; margin-bottom:8px; text-transform:uppercase; }}
    h1,h2,h3 {{ font-family:'Bebas Neue',sans-serif; font-weight:400; letter-spacing:.035em; text-transform:uppercase; }}
    h1 {{ font-size:clamp(3rem,8vw,5.4rem); line-height:.96; margin-bottom:14px; }}
    h2 {{ font-size:2.2rem; line-height:1; margin-bottom:12px; }}
    h3 {{ font-size:1.8rem; line-height:1; margin-bottom:8px; }}
    .dek {{ font-size:clamp(1.08rem,2vw,1.25rem); max-width:760px; }}
    .intro {{ font-size:1.08rem; margin-top:18px; max-width:780px; }}
    .path-list,.steps {{ display:grid; gap:18px; margin-top:28px; }}
    .card {{ background:#f7f7f7; border:1px solid #ddd; border-radius:10px; padding:26px 28px; }}
    .step-number {{ color:#c33; font-family:'Oswald',sans-serif; font-size:.82rem; letter-spacing:.12em; text-transform:uppercase; }}
    .artist-link {{ font-family:'Oswald',sans-serif; font-weight:700; text-decoration:none; }}
    .transition {{ border-left:3px solid #c33; color:#555; margin-top:16px; padding-left:16px; }}
    .cta {{ background:#c33; border-radius:7px; color:#fff; display:inline-block; font-family:'Oswald',sans-serif; font-size:.88rem; font-weight:700; letter-spacing:.09em; margin-top:16px; padding:10px 16px; text-decoration:none; text-transform:uppercase; }}
    .source-note {{ color:#666; font-size:.9rem; margin-top:28px; }}
    .site-footer {{ background:#1a1a1a; border-top:3px solid #c33; color:#aaa; padding:24px 20px; text-align:center; }}
    .site-footer a {{ color:#fff; text-decoration:none; }}
    @media (max-width:620px) {{ .site-nav a {{ flex:1 1 auto; padding:12px 10px; text-align:center; }} .page {{ padding-top:24px; }} .hero {{ border-width:3px; padding:28px 22px; }} .card {{ padding:22px; }} }}
  </style>
</head>
<body>
  <header class="site-header"><a class="logo" href="/index.html" aria-label="Northern Dial home"><img src="{LOGO_URL}" alt="Northern Dial"></a></header>
  <nav class="site-nav" aria-label="Primary navigation">
    <a href="/index.html">Listen</a><a href="/artists.html">Artists</a><a class="active" href="/listening-paths.html">Listening Paths</a><a href="/shows.html">Shows</a>
  </nav>
  {body}
  <footer class="site-footer">Independent Canadian music discovery · <a href="/index.html">Northern Dial</a></footer>
</body>
</html>'''


def build_index(paths):
    cards = []
    for slug, path in paths.items():
        artists = path.get("artists", [])
        names = " → ".join(item.get("name", "") for item in artists if item.get("name"))
        cards.append(
            f'<article class="card"><p class="eyebrow">{len(artists)} artists · Guided discovery</p>'
            f'<h2>{escape(path.get("title", slug))}</h2><p>{escape(path.get("dek", ""))}</p>'
            f'<p class="transition">{escape(names)}</p>'
            f'<a class="cta" href="./listening-paths/{escape(slug, quote=True)}.html">Start this path</a></article>'
        )
    body = f'''<main class="page">
    <nav class="breadcrumbs" aria-label="Breadcrumb"><a href="./index.html">Home</a> / Listening Paths</nav>
    <section class="hero"><p class="eyebrow">Northern Dial Listening Paths</p><h1>Find Your Way Through Canadian Music</h1><p class="dek">Curated journeys connecting artists through scenes, eras, influence and cultural history. Each path explains why one stop leads naturally to the next.</p></section>
    <section class="path-list" aria-label="Available Listening Paths">{"".join(cards)}</section>
  </main>'''
    INDEX_FILE.write_text(shell("Listening Paths | Northern Dial", "Guided journeys through Canadian music, connecting artists through scenes, eras, influence and cultural history.", f"{BASE_URL}/listening-paths.html", body), encoding="utf-8")


def build_path(slug, path):
    steps = []
    artists = path.get("artists", [])
    for index, item in enumerate(artists, 1):
        name = str(item.get("name", ""))
        artist_slug = str(item.get("slug", ""))
        transition = str(item.get("leads_to_next", ""))
        steps.append(
            f'<article class="card"><p class="step-number">Stop {index} of {len(artists)}</p>'
            f'<h2>{escape(name)}</h2><p>{escape(item.get("why_here", ""))}</p>'
            f'<a class="artist-link" href="../artists/{escape(artist_slug, quote=True)}.html">View {escape(name)} profile →</a>'
            + (f'<p class="transition"><strong>Why next:</strong> {escape(transition)}</p>' if transition else "")
            + '</article>'
        )
    body = f'''<main class="page">
    <nav class="breadcrumbs" aria-label="Breadcrumb"><a href="../index.html">Home</a> / <a href="../listening-paths.html">Listening Paths</a> / {escape(path.get("title", slug))}</nav>
    <section class="hero"><p class="eyebrow">Northern Dial Listening Path</p><h1>{escape(path.get("title", slug))}</h1><p class="dek">{escape(path.get("dek", ""))}</p><p class="intro">{escape(path.get("intro", ""))}</p></section>
    <section class="steps" aria-label="Listening Path stops">{"".join(steps)}</section>
    <p class="source-note">This path is editorially curated from the verified research used across Northern Dial artist profiles. Connections describe documented scene, era and cultural relationships, not necessarily direct personal influence.</p>
  </main>'''
    canonical = f"{BASE_URL}/listening-paths/{slug}.html"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / f"{slug}.html").write_text(shell(f"{path.get('title', slug)} | Northern Dial", path.get("dek", ""), canonical, body), encoding="utf-8")


def patch_artist_pages(paths):
    memberships = {}
    for path_slug, path in paths.items():
        for item in path.get("artists", []):
            artist_slug = str(item.get("slug", "")).strip()
            if artist_slug:
                memberships.setdefault(artist_slug, []).append((path_slug, path))

    patched = 0
    missing = []
    marker_pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER) + r"\n?", re.DOTALL)
    for artist_slug, artist_paths in memberships.items():
        file_path = ARTIST_DIR / f"{artist_slug}.html"
        if not file_path.exists():
            missing.append(artist_slug)
            continue
        html = marker_pattern.sub("", file_path.read_text(encoding="utf-8"))
        cards = []
        for path_slug, path in artist_paths:
            cards.append(
                f'<section class="card listening-path-card"><p class="eyebrow">Keep Listening</p>'
                f'<h2>{escape(path.get("title", path_slug))}</h2><p>{escape(path.get("dek", ""))}</p>'
                f'<a class="cta" href="../listening-paths/{escape(path_slug, quote=True)}.html">Continue this Listening Path</a></section>'
            )
        block = START_MARKER + "\n        " + "\n        ".join(cards) + "\n        " + END_MARKER + "\n      "
        needle = "</div>\n      <a class=\"back-link\""
        if needle not in html:
            missing.append(artist_slug)
            continue
        html = html.replace(needle, block + needle, 1)
        file_path.write_text(html, encoding="utf-8")
        patched += 1
    return patched, missing


def update_sitemap(paths):
    try:
        tree = ET.parse(SITEMAP_FILE)
        root = tree.getroot()
    except (FileNotFoundError, ET.ParseError):
        return
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", namespace)
    existing = {element.text for element in root.findall(f"{{{namespace}}}url/{{{namespace}}}loc") if element.text}
    targets = [(f"{BASE_URL}/listening-paths.html", "0.75")]
    targets.extend((f"{BASE_URL}/listening-paths/{slug}.html", "0.70") for slug in paths)
    changed = False
    for loc, priority in targets:
        if loc in existing:
            continue
        url = ET.SubElement(root, f"{{{namespace}}}url")
        ET.SubElement(url, f"{{{namespace}}}loc").text = loc
        ET.SubElement(url, f"{{{namespace}}}changefreq").text = "monthly"
        ET.SubElement(url, f"{{{namespace}}}priority").text = priority
        changed = True
    if changed:
        ET.indent(tree, space="  ")
        tree.write(SITEMAP_FILE, encoding="utf-8", xml_declaration=True)


def main():
    paths = load_paths()
    if not paths:
        print("No Listening Paths configured.")
        return
    build_index(paths)
    for slug, path in paths.items():
        build_path(slug, path)
    patched, missing = patch_artist_pages(paths)
    update_sitemap(paths)
    print(f"Built {len(paths)} Listening Path(s); connected {patched} artist profile(s).")
    if missing:
        print("Unpatched artist slugs: " + ", ".join(sorted(set(missing))))


if __name__ == "__main__":
    main()
