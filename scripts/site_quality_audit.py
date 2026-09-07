#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path('.')
BASE = 'https://www.northerndial.ca/'
SITEMAP = ROOT / 'sitemap.xml'
ROBOTS = ROOT / 'robots.txt'

issues = []
warnings = []


def read(path):
    return path.read_text(encoding='utf-8', errors='ignore')


def normalize_url_to_path(url):
    parts = urlsplit(url)
    path = unquote(parts.path or '/')
    if path == '/':
        return Path('index.html')
    p = Path(path.lstrip('/'))
    if path.endswith('/'):
        p = p / 'index.html'
    return p


def internal_target(source, href):
    href = href.strip()
    if not href or href.startswith('#'):
        return None
    if href.startswith(('mailto:', 'tel:', 'javascript:', 'data:')):
        return None
    parts = urlsplit(href)
    if parts.scheme or parts.netloc:
        if parts.netloc not in ('www.northerndial.ca', 'northerndial.ca'):
            return None
        return normalize_url_to_path(href)
    raw_path = unquote(parts.path)
    if not raw_path:
        return None
    if raw_path == '/':
        return Path('index.html')
    target = Path(raw_path.lstrip('/')) if raw_path.startswith('/') else source.parent / raw_path
    if raw_path.endswith('/'):
        target = target / 'index.html'
    return target


def has_noindex(text):
    match = re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)["\']', text, re.I)
    return bool(match and 'noindex' in match.group(1).lower())


def meta_content(text, name=None, prop=None):
    if name:
        patterns = [
            rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']*)["\']',
            rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']{re.escape(name)}["\']',
        ]
    else:
        patterns = [
            rf'<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']*)["\']',
            rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']{re.escape(prop)}["\']',
        ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(1).strip()
    return ''


def canonical(text):
    match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', text, re.I)
    if not match:
        match = re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']', text, re.I)
    return match.group(1).strip() if match else ''


def title(text):
    match = re.search(r'<title>(.*?)</title>', text, re.I | re.S)
    return re.sub(r'\s+', ' ', match.group(1)).strip() if match else ''


def all_html_files():
    files = sorted(ROOT.glob('*.html'))
    files += sorted((ROOT / 'blog').glob('*.html'))
    files += sorted((ROOT / 'fr').glob('*.html'))
    return files


if not SITEMAP.exists():
    issues.append('Missing sitemap.xml')
    sitemap_paths = set()
else:
    try:
        tree = ET.parse(SITEMAP)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        locs = [el.text.strip() for el in tree.findall('.//sm:loc', ns) if el.text]
        sitemap_paths = {normalize_url_to_path(url) for url in locs}
    except Exception as exc:
        issues.append(f'Invalid sitemap.xml: {exc}')
        sitemap_paths = set()

if not ROBOTS.exists():
    issues.append('Missing robots.txt')
else:
    robots = read(ROBOTS)
    if 'Sitemap: https://www.northerndial.ca/sitemap.xml' not in robots:
        issues.append('robots.txt does not declare the sitemap')
    if 'Disallow: /admin.html' not in robots:
        issues.append('robots.txt does not disallow admin.html')

html_files = all_html_files()
texts = {path: read(path) for path in html_files}
indexable = {path for path, text in texts.items() if not has_noindex(text)}

for path in html_files:
    text = texts[path]
    noindex = has_noindex(text)

    if not re.search(r'<html[^>]+lang=["\'][^"\']+["\']', text, re.I):
        issues.append(f'{path}: missing html lang')

    page_title = title(text)
    if not page_title:
        issues.append(f'{path}: missing title')

    h1_count = len(re.findall(r'<h1\b', text, re.I))
    if not noindex and h1_count != 1:
        issues.append(f'{path}: expected 1 h1, found {h1_count}')

    for tag in re.findall(r'<img\b[^>]*>', text, re.I):
        if not re.search(r'\balt\s*=', tag, re.I):
            issues.append(f'{path}: image missing alt')

    for attrs, body in re.findall(r'<button\b([^>]*)>(.*?)</button>', text, re.I | re.S):
        visible = re.sub(r'<[^>]+>', '', body).strip()
        if not visible and not re.search(r'aria-label\s*=', attrs, re.I):
            issues.append(f'{path}: button may lack accessible name')

    for href in re.findall(r'<a\b[^>]*\bhref=["\']([^"\']+)["\']', text, re.I):
        target = internal_target(path, href)
        if target is not None and not target.exists():
            issues.append(f'{path}: broken internal link {href} -> {target}')

    if noindex:
        if path in sitemap_paths:
            issues.append(f'{path}: noindex page must not be in sitemap')
        continue

    description = meta_content(text, name='description')
    if not description:
        issues.append(f'{path}: missing meta description')

    canon = canonical(text)
    if not canon:
        issues.append(f'{path}: missing canonical')

    if path not in sitemap_paths:
        issues.append(f'{path}: indexable page missing from sitemap')

# Every sitemap URL must exist and be indexable.
for path in sorted(sitemap_paths):
    if not path.exists():
        issues.append(f'sitemap references missing file: {path}')
    elif path in texts and has_noindex(texts[path]):
        issues.append(f'sitemap references noindex page: {path}')

# Duplicate titles/descriptions/canonicals among indexable HTML.
for label, extractor in [
    ('title', title),
    ('meta description', lambda t: meta_content(t, name='description')),
    ('canonical', canonical),
]:
    seen = {}
    for path in sorted(indexable):
        value = extractor(texts[path]).strip()
        if not value:
            continue
        seen.setdefault(value, []).append(path)
    for value, paths in seen.items():
        if len(paths) > 1:
            issues.append(f'duplicate {label}: {value!r} on {", ".join(map(str, paths))}')

# Orphan detection: every indexable page except home must receive at least one internal link
# from another indexable page.
inbound = {path: 0 for path in indexable}
for source in sorted(indexable):
    for href in re.findall(r'<a\b[^>]*\bhref=["\']([^"\']+)["\']', texts[source], re.I):
        target = internal_target(source, href)
        if target in inbound and target != source:
            inbound[target] += 1
for path, count in inbound.items():
    if path != Path('index.html') and count == 0:
        issues.append(f'{path}: orphan indexable page with no inbound internal links')

# Admin and utility pages should never be indexable.
for utility in [
    Path('admin.html'), Path('instagram-dashboard.html'), Path('library_artist_profiles.html'),
    Path('sample-explorer.html'), Path('zen-scene.html'), Path('404.html')
]:
    if utility.exists() and not has_noindex(read(utility)):
        issues.append(f'{utility}: utility page must be noindex')

# Homepage must expose the in-place language control and accessibility layer.
if Path('index.html').exists():
    home = read(Path('index.html'))
    if 'data-language-toggle' not in home:
        issues.append('index.html: missing in-place language toggle')
    if 'homepage_language.js' not in home:
        issues.append('index.html: missing homepage language script')
    if 'accessibility_enhancements.js' not in home:
        issues.append('index.html: missing accessibility enhancement script')

print(f'Checked {len(html_files)} HTML files; {len(indexable)} are indexable.')
if warnings:
    print('Warnings:')
    for warning in warnings:
        print('-', warning)
if issues:
    print('Site quality findings:')
    for issue in issues:
        print('-', issue)
    sys.exit(1)
print('Site quality audit passed: SEO structure, sitemap coverage, orphan detection, internal links and accessibility guardrails are clean.')
