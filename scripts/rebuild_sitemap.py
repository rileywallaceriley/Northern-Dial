#!/usr/bin/env python3
from pathlib import Path
import re
from xml.sax.saxutils import escape

BASE = 'https://www.northerndial.ca'
ROOT = Path('.')

EXCLUDED_PATHS = {
    '404.html',
    'admin.html',
    'instagram-dashboard.html',
    'library_artist_profiles.html',
    'sample-explorer.html',
    'zen-scene.html',
}
EXCLUDED_TOP_DIRS = {'.git', '.github', 'docs', 'archives', 'tools'}


def is_public_html(path: Path) -> bool:
    rel = path.as_posix()
    if path.suffix.lower() != '.html':
        return False
    if rel in EXCLUDED_PATHS:
        return False
    if path.parts and path.parts[0] in EXCLUDED_TOP_DIRS:
        return False
    text = path.read_text(encoding='utf-8', errors='ignore')
    robots = re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)', text, re.I)
    if robots and 'noindex' in robots.group(1).lower():
        return False
    return True


def url_for(path: Path) -> str:
    rel = path.as_posix()
    if rel == 'index.html':
        return BASE + '/'
    if rel.endswith('/index.html'):
        return BASE + '/' + rel[:-10]
    return BASE + '/' + rel


def priority_for(path: Path) -> str:
    rel = path.as_posix()
    if rel == 'index.html':
        return '1.0'
    if rel in {'artists.html', 'discover.html', 'new-releases.html', 'new-canadian-artists.html'}:
        return '0.9'
    if rel in {'library.html', 'blog/index.html', 'listening-paths.html'}:
        return '0.8'
    if rel.startswith('artists/') or rel.startswith('blog/') or rel.startswith('listening-paths/'):
        return '0.7'
    if rel.startswith('fr/'):
        return '0.7'
    return '0.6'


def main():
    pages = sorted((p for p in ROOT.rglob('*.html') if is_public_html(p)), key=lambda p: url_for(p))
    urls = []
    seen = set()
    for path in pages:
        url = url_for(path)
        if url in seen:
            continue
        seen.add(url)
        urls.append((url, priority_for(path)))

    lines = ["<?xml version='1.0' encoding='utf-8'?>", '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, priority in urls:
        lines.extend([
            '  <url>',
            f'    <loc>{escape(url)}</loc>',
            f'    <priority>{priority}</priority>',
            '  </url>',
        ])
    lines.append('</urlset>')
    Path('sitemap.xml').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Rebuilt sitemap.xml with {len(urls)} public HTML URLs.')


if __name__ == '__main__':
    main()
