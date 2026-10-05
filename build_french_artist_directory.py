#!/usr/bin/env python3
"""Build a crawlable French directory from the published French profiles."""

from html import escape
from html.parser import HTMLParser
from pathlib import Path
import unicodedata
import xml.etree.ElementTree as ET

BASE = 'https://www.northerndial.ca'
DIRECTORY = Path('fr/artists.html')


class ProfileName(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_heading = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'h1':
            self.in_heading = True

    def handle_endtag(self, tag):
        if tag == 'h1':
            self.in_heading = False

    def handle_data(self, data):
        if self.in_heading:
            self.parts.append(data)


def sort_key(name):
    return ''.join(c for c in unicodedata.normalize('NFKD', name.casefold())
                   if not unicodedata.combining(c))


def main():
    artists = []
    for path in sorted(Path('fr/artists').glob('*.html')):
        parser = ProfileName()
        parser.feed(path.read_text(encoding='utf-8'))
        name = ' '.join(''.join(parser.parts).split())
        if not name:
            raise SystemExit(f'Missing artist name: {path}')
        artists.append((name, path.stem))
    if not artists:
        raise SystemExit('No published French artist profiles found.')
    artists.sort(key=lambda item: (sort_key(item[0]), item[1]))
    links = '\n'.join(
        f'      <li id="artist-{escape(slug, quote=True)}"><a href="/fr/artists/{escape(slug, quote=True)}.html">{escape(name)}</a></li>'
        for name, slug in artists
    )
    DIRECTORY.write_text(f'''<!doctype html>
<html lang="fr-CA">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#CC3333">
  <title>Répertoire des artistes canadiens en français | Northern Dial</title>
  <meta name="description" content="Découvrez les artistes canadiens de Northern Dial : biographies en français, scènes musicales et liens pour poursuivre votre découverte.">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{BASE}/fr/artists.html">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Northern Dial">
  <meta property="og:title" content="Répertoire des artistes canadiens en français | Northern Dial">
  <meta property="og:description" content="Explorez les profils d’artistes canadiens de Northern Dial en français.">
  <meta property="og:url" content="{BASE}/fr/artists.html">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Oswald:wght@700&family=Roboto+Condensed:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/nd-shell.css?v=20260927e">
  <link rel="stylesheet" href="/nd-banner.css?v=20260914a">
  <style>
    *{{box-sizing:border-box}}body{{margin:0;background:#fff;color:#1a1a1a;font-family:'Roboto Condensed',sans-serif;line-height:1.6}}
    a{{color:#8b2323}}.page{{max-width:1100px;margin:auto;padding:36px 20px 70px}}
    .breadcrumbs{{margin-bottom:24px}}.hero{{background:#1a1a1a;border:4px solid #c33;border-radius:10px;color:#fff;padding:28px}}
    h1{{font-family:'Bebas Neue',sans-serif;font-size:clamp(2.6rem,7vw,4.5rem);font-weight:400;line-height:1.05;margin:0 0 16px}}
    .hero p{{margin:0}}.directory{{margin-top:28px}}.directory label{{display:block;font-weight:700;margin-bottom:8px}}
    input{{width:100%;max-width:540px;padding:12px;border:2px solid #777;border-radius:6px;font:inherit}}
    a:focus-visible,input:focus-visible{{outline:3px solid #c33;outline-offset:3px}}
    .artist-list{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px 24px;list-style:none;padding:0;margin:24px 0}}
    .artist-list li{{scroll-margin-top:100px}}.artist-list a{{display:block;padding:10px 12px;background:#f7f7f7;border:1px solid #ddd;border-radius:6px;text-decoration:none;overflow-wrap:anywhere}}
    .artist-list a:hover{{text-decoration:underline}}.artist-list [hidden]{{display:none}}
    @media(max-width:760px){{.artist-list{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
    @media(max-width:480px){{.artist-list{{grid-template-columns:1fr}}}}
  </style>
</head>
<body>
  <main class="page">
    <nav class="breadcrumbs" aria-label="Fil d’Ariane"><a href="/fr/">Accueil</a> / Artistes</nav>
    <section class="hero"><h1>Découvrez les artistes canadiens</h1><p>Explorez les biographies en français des artistes du répertoire Northern Dial.</p></section>
    <section class="directory" aria-label="Répertoire des artistes">
      <label for="artist-search">Rechercher un artiste</label>
      <input id="artist-search" type="search" placeholder="Nom de l’artiste" autocomplete="off">
      <p id="artist-count" role="status" aria-live="polite">{len(artists)} artistes</p>
      <ul class="artist-list">
{links}
      </ul>
      <p><a href="/artists.html" lang="en">Browse the full English artist directory</a></p>
    </section>
  </main>
  <script>
    (() => {{
      const search = document.getElementById('artist-search');
      const items = Array.from(document.querySelectorAll('.artist-list li'));
      const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr-CA');
      search.addEventListener('input', () => {{
        const query = normalize(search.value.trim());
        let count = 0;
        items.forEach(item => {{
          item.hidden = !normalize(item.textContent).includes(query);
          if (!item.hidden) count++;
        }});
        document.getElementById('artist-count').textContent = count + (count === 1 ? ' artiste' : ' artistes');
      }});
    }})();
  </script>
  <script src="/nd-shell.js?v=20260927e" defer></script>
</body>
</html>
''', encoding='utf-8')
    namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    tree = ET.parse('sitemap.xml')
    root = tree.getroot()
    url = f'{BASE}/fr/artists.html'
    if not any(loc.text == url for loc in root.findall(f'{{{namespace}}}url/{{{namespace}}}loc')):
        # Preserve the existing sitemap formatting and entries.
        path = Path('sitemap.xml')
        text = path.read_text(encoding='utf-8')
        path.write_text(text.replace('</urlset>', f'  <url>\n    <loc>{url}</loc>\n    <priority>0.9</priority>\n  </url>\n</urlset>'), encoding='utf-8')
    print(f'Built French directory with {len(artists)} direct profile links.')


if __name__ == '__main__':
    main()
