#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path('.')
issues = []


def read(path):
    return path.read_text(encoding='utf-8', errors='ignore')


def noindex(text):
    m = re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)', text, re.I)
    return bool(m and 'noindex' in m.group(1).lower())


def title(text):
    m = re.search(r'<title>(.*?)</title>', text, re.I | re.S)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''


def meta_description(text):
    for p in [
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)',
        r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']',
    ]:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1).strip()
    return ''


def canonical(text):
    for p in [
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)',
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
    ]:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1).strip()
    return ''


def dynamic_href(href):
    return any(token in href for token in ('${', '{{', '<%', '\\/', '[^', '`'))


def target_for(source, href):
    href = href.strip()
    if not href or dynamic_href(href) or href.startswith(('#', 'mailto:', 'tel:', 'javascript:', 'data:')):
        return None
    parts = urlsplit(href)
    if parts.netloc and parts.netloc not in ('www.northerndial.ca', 'northerndial.ca'):
        return None
    raw = unquote(parts.path)
    if not raw:
        return None
    if raw == '/':
        return Path('index.html')
    target = Path(raw.lstrip('/')) if raw.startswith('/') else source.parent / raw
    if raw.endswith('/'):
        target /= 'index.html'
    return target


def sitemap_path(url):
    p = urlsplit(url).path or '/'
    if p == '/':
        return Path('index.html')
    result = Path(p.lstrip('/'))
    if p.endswith('/'):
        result /= 'index.html'
    return result


html_files = sorted(ROOT.glob('*.html')) + sorted((ROOT / 'blog').glob('*.html')) + sorted((ROOT / 'fr').glob('*.html'))
texts = {p: read(p) for p in html_files}
indexable = {p for p, t in texts.items() if not noindex(t)}

sitemap_file = ROOT / 'sitemap.xml'
if not sitemap_file.exists():
    issues.append('missing sitemap.xml')
    sitemap_paths = set()
else:
    tree = ET.parse(sitemap_file)
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    sitemap_paths = {sitemap_path(el.text.strip()) for el in tree.findall('.//s:loc', ns) if el.text}

robots_file = ROOT / 'robots.txt'
if not robots_file.exists():
    issues.append('missing robots.txt')
else:
    robots = read(robots_file)
    if 'Sitemap: https://www.northerndial.ca/sitemap.xml' not in robots:
        issues.append('robots.txt missing sitemap declaration')
    if 'Disallow: /admin.html' not in robots:
        issues.append('robots.txt missing admin disallow')

for path, text in texts.items():
    is_noindex = noindex(text)
    if not re.search(r'<html[^>]+lang=["\'][^"\']+', text, re.I):
        issues.append(f'{path}: missing html lang')
    if not title(text):
        issues.append(f'{path}: missing title')
    if not is_noindex and len(re.findall(r'<h1\b', text, re.I)) != 1:
        issues.append(f'{path}: expected exactly one h1')
    for tag in re.findall(r'<img\b[^>]*>', text, re.I):
        if not re.search(r'\balt\s*=', tag, re.I):
            issues.append(f'{path}: image missing alt')
    if is_noindex:
        if path in sitemap_paths:
            issues.append(f'{path}: noindex page appears in sitemap')
        continue
    if not meta_description(text):
        issues.append(f'{path}: missing meta description')
    if not canonical(text):
        issues.append(f'{path}: missing canonical')
    if path not in sitemap_paths:
        issues.append(f'{path}: indexable page missing from sitemap')
    for href in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\']', text, re.I):
        target = target_for(path, href)
        if target is not None and not target.exists():
            issues.append(f'{path}: broken internal link {href}')

for path in sitemap_paths:
    if not path.exists():
        issues.append(f'sitemap references missing file: {path}')
    elif path in texts and noindex(texts[path]):
        issues.append(f'sitemap references noindex page: {path}')

for label, getter in [('title', title), ('description', meta_description), ('canonical', canonical)]:
    seen = {}
    for path in indexable:
        value = getter(texts[path])
        if value:
            seen.setdefault(value, []).append(path)
    for value, paths in seen.items():
        if len(paths) > 1:
            issues.append(f'duplicate {label}: {", ".join(str(p) for p in sorted(paths))}')

inbound = {p: 0 for p in indexable}
for source in indexable:
    for href in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\']', texts[source], re.I):
        target = target_for(source, href)
        if target in inbound and target != source:
            inbound[target] += 1
for path, count in inbound.items():
    if path != Path('index.html') and count == 0:
        issues.append(f'{path}: orphan indexable page')

for utility in ('admin.html', 'instagram-dashboard.html', 'library_artist_profiles.html', 'sample-explorer.html', 'zen-scene.html', '404.html'):
    p = Path(utility)
    if p.exists() and not noindex(read(p)):
        issues.append(f'{p}: utility page must be noindex')

home = read(Path('index.html'))
for marker in ('data-language-toggle', 'homepage_language.js', 'accessibility_enhancements.js'):
    if marker not in home:
        issues.append(f'index.html: missing {marker}')

print(f'Checked {len(html_files)} HTML files; {len(indexable)} indexable.')
if issues:
    print('Site quality findings:')
    for issue in issues:
        print('-', issue)
    sys.exit(1)
print('Site quality audit passed.')
