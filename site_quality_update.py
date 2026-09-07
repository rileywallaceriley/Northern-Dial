#!/usr/bin/env python3
from pathlib import Path
import html
import json
import re

BASE = 'https://www.northerndial.ca'


def write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def add_head_markup(path, markup, sentinel):
    path = Path(path)
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8', errors='ignore')
    if sentinel in text:
        return
    if '</head>' not in text:
        raise RuntimeError(f'{path}: no </head>')
    text = text.replace('</head>', markup + '\n</head>', 1)
    path.write_text(text, encoding='utf-8')


def add_noindex(path):
    path = Path(path)
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8', errors='ignore')
    if re.search(r'<meta[^>]+name=["\']robots["\']', text, re.I):
        text = re.sub(
            r'<meta[^>]+name=["\']robots["\'][^>]*>',
            '<meta name="robots" content="noindex,nofollow,noarchive">',
            text,
            count=1,
            flags=re.I,
        )
    else:
        marker = re.search(r'<meta[^>]+name=["\']viewport["\'][^>]*>', text, re.I)
        insert = '<meta name="robots" content="noindex,nofollow,noarchive">'
        if marker:
            text = text[:marker.end()] + '\n' + insert + text[marker.end():]
        else:
            text = text.replace('<head>', '<head>\n' + insert, 1)
    path.write_text(text, encoding='utf-8')


def ensure_library_seo():
    path = Path('library.html')
    text = path.read_text(encoding='utf-8')
    if 'rel="canonical"' not in text:
        text = text.replace(
            '<meta name="theme-color" content="#CC3333">',
            '<meta name="theme-color" content="#CC3333">\n'
            '    <link rel="canonical" href="https://www.northerndial.ca/library.html">\n'
            '    <meta property="og:title" content="Browse Canadian Songs | Northern Dial">\n'
            '    <meta property="og:description" content="Browse recently played Canadian songs and search the Northern Dial catalogue.">\n'
            '    <meta property="og:type" content="website">\n'
            '    <meta property="og:url" content="https://www.northerndial.ca/library.html">',
            1,
        )
    text = text.replace('<title>Browse Songs - Northern Dial</title>', '<title>Browse Canadian Songs | Northern Dial</title>')
    text = text.replace(
        'content="Browse recently played songs on Northern Dial and search our catalog"',
        'content="Browse recently played Canadian songs on Northern Dial and search our catalogue."',
        1,
    )
    path.write_text(text, encoding='utf-8')


def ensure_requests_seo():
    path = Path('requests.html')
    text = path.read_text(encoding='utf-8')
    if 'property="og:title"' not in text:
        text = text.replace(
            '<link rel="canonical" href="https://www.northerndial.ca/requests.html">',
            '<link rel="canonical" href="https://www.northerndial.ca/requests.html">\n'
            '  <meta property="og:title" content="Request a Canadian Song | Northern Dial">\n'
            '  <meta property="og:description" content="Search the Northern Dial catalogue and request a Canadian song or artist for the station.">\n'
            '  <meta property="og:type" content="website">\n'
            '  <meta property="og:url" content="https://www.northerndial.ca/requests.html">',
            1,
        )
    text = text.replace('<title>Request a Song | Northern Dial</title>', '<title>Request a Canadian Song | Northern Dial</title>')
    text = text.replace(
        'content="Request a song from Northern Dial\'s Canadian music radio library."',
        'content="Search the Northern Dial catalogue and request a Canadian song or artist for the station."',
        1,
    )
    if 'aria-label="Search for a song or artist"' not in text:
        text = re.sub(
            r'(<input\b[^>]*id=["\']searchInput["\'][^>]*)(>)',
            r'\1 aria-label="Search for a song or artist"\2',
            text,
            count=1,
            flags=re.I,
        )
    path.write_text(text, encoding='utf-8')


def ensure_home_quality():
    path = Path('index.html')
    text = path.read_text(encoding='utf-8')
    if 'hreflang="fr" href="https://www.northerndial.ca/?lang=fr"' not in text:
        marker = '<link rel="canonical" href="https://www.northerndial.ca/">'
        text = text.replace(
            marker,
            marker + '\n<link rel="alternate" hreflang="en" href="https://www.northerndial.ca/">'
            + '\n<link rel="alternate" hreflang="fr" href="https://www.northerndial.ca/?lang=fr">'
            + '\n<link rel="alternate" hreflang="x-default" href="https://www.northerndial.ca/">',
            1,
        )
    if 'accessibility_enhancements.js' not in text:
        text = text.replace(
            '<script src="/homepage_language.js"></script>',
            '<script src="/homepage_language.js"></script>\n<script src="/accessibility_enhancements.js"></script>',
            1,
        )
    # Add an inbound link to the standalone request page without changing the main nav.
    if 'href="/requests.html"' not in text and 'ND_PROJECT_LINKS_START' in text:
        text = text.replace(
            '<a href="/accessibility.html" style="color:#fff;font-family:\'Roboto Condensed\',sans-serif;font-weight:700;text-decoration:none;">Accessibility</a>',
            '<a href="/accessibility.html" style="color:#fff;font-family:\'Roboto Condensed\',sans-serif;font-weight:700;text-decoration:none;">Accessibility</a>\n'
            '      <a href="/requests.html" style="color:#fff;font-family:\'Roboto Condensed\',sans-serif;font-weight:700;text-decoration:none;">Request a Song</a>',
            1,
        )
    path.write_text(text, encoding='utf-8')


def ensure_language_url_state():
    path = Path('homepage_language.js')
    text = path.read_text(encoding='utf-8')
    if 'function updateUrlForLanguage' not in text:
        marker = '  function updateMetadata(lang) {'
        helper = '''  function updateUrlForLanguage(lang) {\n    const url = new URL(window.location.href);\n    if (lang === 'fr') url.searchParams.set('lang', 'fr');\n    else url.searchParams.delete('lang');\n    const next = `${url.pathname}${url.search}${url.hash}`;\n    window.history.replaceState({}, '', next);\n  }\n\n'''
        text = text.replace(marker, helper + marker, 1)
    if 'const canonical = document.querySelector(\'link[rel="canonical"]\');' not in text:
        old = '    const description = document.querySelector(\'meta[name="description"]\');\n'
        new = old + '    const canonical = document.querySelector(\'link[rel="canonical"]\');\n'
        text = text.replace(old, new, 1)
        text = text.replace(
            "      if (description) description.setAttribute('content', 'Northern Dial est une radio canadienne indépendante diffusée 24 heures sur 24 pour découvrir des artistes, des chansons et des émissions d’ici.');",
            "      if (description) description.setAttribute('content', 'Northern Dial est une radio canadienne indépendante diffusée 24 heures sur 24 pour découvrir des artistes, des chansons et des émissions d’ici.');\n      if (canonical) canonical.setAttribute('href', 'https://www.northerndial.ca/?lang=fr');",
            1,
        )
        text = text.replace(
            "      if (description) description.setAttribute('content', 'Northern Dial is independent 24/7 Canadian music radio: discover emerging artists, Canadian songs, and curated shows from coast to coast.');",
            "      if (description) description.setAttribute('content', 'Northern Dial is independent 24/7 Canadian music radio: discover emerging artists, Canadian songs, and curated shows from coast to coast.');\n      if (canonical) canonical.setAttribute('href', 'https://www.northerndial.ca/');",
            1,
        )
    if 'updateUrlForLanguage(lang);' not in text:
        text = text.replace('    updateMetadata(lang);\n    if (persist)', '    updateMetadata(lang);\n    if (persist) updateUrlForLanguage(lang);\n    if (persist)', 1)
    old_init = "    const saved = localStorage.getItem(STORAGE_KEY);\n    applyLanguage(saved === 'fr' ? 'fr' : 'en', false);"
    new_init = "    const requested = new URLSearchParams(window.location.search).get('lang');\n    const saved = localStorage.getItem(STORAGE_KEY);\n    const initial = requested === 'fr' ? 'fr' : (requested === 'en' ? 'en' : (saved === 'fr' ? 'fr' : 'en'));\n    applyLanguage(initial, false);"
    if old_init in text:
        text = text.replace(old_init, new_init, 1)
    path.write_text(text, encoding='utf-8')


def clean_fr_hub_hreflang():
    path = Path('fr/index.html')
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'<link rel="alternate" hreflang="(?:en|fr)" href="[^"]+">', '', text)
    path.write_text(text, encoding='utf-8')


def add_blog_schema():
    for path in sorted(Path('blog').glob('*.html')):
        if path.name == 'index.html':
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        if '"@type": "BlogPosting"' in text or '"@type":"BlogPosting"' in text:
            continue
        title_match = re.search(r'<title>(.*?)</title>', text, re.I | re.S)
        desc_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', text, re.I)
        canon_match = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', text, re.I)
        if not (title_match and desc_match and canon_match):
            continue
        headline = re.sub(r'\s*\|\s*Northern Dial.*$', '', html.unescape(title_match.group(1)).strip())
        data = {
            '@context': 'https://schema.org',
            '@type': 'BlogPosting',
            'headline': headline,
            'description': html.unescape(desc_match.group(1)).strip(),
            'url': canon_match.group(1),
            'publisher': {'@type': 'Organization', 'name': 'Northern Dial', 'url': BASE + '/'},
            'inLanguage': 'en-CA',
        }
        script = '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>\n'
        text = text.replace('</head>', script + '</head>', 1)
        path.write_text(text, encoding='utf-8')


def ensure_sitemap():
    path = Path('sitemap.xml')
    text = path.read_text(encoding='utf-8')
    entry = '  <url><loc>https://www.northerndial.ca/requests.html</loc><priority>0.7</priority></url>\n'
    if 'https://www.northerndial.ca/requests.html' not in text:
        text = text.replace('</urlset>', entry + '</urlset>')
    path.write_text(text, encoding='utf-8')


def write_robots():
    write('robots.txt', '''User-agent: *\nAllow: /\nDisallow: /admin.html\nDisallow: /instagram-dashboard.html\nDisallow: /library_artist_profiles.html\nDisallow: /sample-explorer.html\nDisallow: /zen-scene.html\nDisallow: /docs/\n\nSitemap: https://www.northerndial.ca/sitemap.xml\n''')


def write_404():
    write('404.html', '''<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8">\n  <meta name="viewport" content="width=device-width,initial-scale=1">\n  <meta name="robots" content="noindex,nofollow">\n  <meta name="theme-color" content="#CC3333">\n  <title>Page Not Found | Northern Dial</title>\n  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Oswald:wght@700&family=Roboto+Condensed:wght@400;700&display=swap" rel="stylesheet">\n  <style>*{box-sizing:border-box}body{margin:0;background:#f7e5e5;color:#1a1a1a;font-family:"Roboto Condensed",sans-serif;min-height:100vh;display:grid;place-items:center;padding:20px}.card{background:#fff;border:5px solid #1a1a1a;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.15);max-width:760px;padding:42px;text-align:center}.eyebrow{color:#CC3333;font-family:"Oswald",sans-serif;font-weight:700;letter-spacing:.15em;text-transform:uppercase}h1{font-family:"Bebas Neue",sans-serif;font-size:clamp(4rem,12vw,7rem);font-weight:400;letter-spacing:.04em;line-height:.9;margin:12px 0}p{font-size:1.08rem;line-height:1.6}.links{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:25px}.links a{background:#1a1a1a;border-radius:7px;color:#fff;font-family:"Oswald",sans-serif;font-weight:700;letter-spacing:.08em;padding:11px 16px;text-decoration:none;text-transform:uppercase}.links a:first-child{background:#CC3333}@media(max-width:520px){.card{padding:30px 20px}}</style>\n</head>\n<body><main class="card"><div class="eyebrow">Northern Dial</div><h1>404</h1><p>The page you were looking for is not on this frequency. Head back to the station or keep discovering Canadian music.</p><nav class="links" aria-label="Helpful links"><a href="/">Home</a><a href="/library.html">Songs</a><a href="/artists.html">Artists</a><a href="/discover.html">Discover</a><a href="/blog/">Blog</a></nav></main></body>\n</html>\n''')


def main():
    for utility in ['admin.html', 'instagram-dashboard.html', 'library_artist_profiles.html', 'sample-explorer.html', 'zen-scene.html']:
        add_noindex(utility)
    ensure_library_seo()
    ensure_requests_seo()
    ensure_home_quality()
    ensure_language_url_state()
    clean_fr_hub_hreflang()
    add_blog_schema()
    ensure_sitemap()
    write_robots()
    write_404()
    print('Applied Northern Dial SEO, accessibility, indexing and orphan-page hardening.')


if __name__ == '__main__':
    main()
