#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re, sys

FILES = [
    Path('index.html'), Path('library.html'), Path('artists.html'),
    Path('discover.html'), Path('about.html'), Path('sessions.html'),
    Path('archive.html'), Path('accessibility.html'), Path('rights.html'),
    Path('survey.html'), Path('requests.html')
]
FILES += sorted(Path('blog').glob('*.html'))
FILES += sorted(Path('fr').glob('*.html'))
issues = []


def internal_target(source: Path, href: str):
    href = href.strip()
    if not href or href.startswith('#') or '${' in href:
        return None
    if href.startswith(('mailto:', 'tel:', 'javascript:', 'data:')):
        return None
    parts = urlsplit(href)
    if parts.scheme or parts.netloc:
        return None

    raw_path = unquote(parts.path)
    if not raw_path:
        return None
    if raw_path == '/':
        return Path('index.html')

    target = Path(raw_path.lstrip('/')) if raw_path.startswith('/') else source.parent / raw_path
    if raw_path.endswith('/'):
        target = target / 'index.html'
    return target


for p in FILES:
    if not p.exists():
        issues.append(f'{p}: missing file')
        continue

    t = p.read_text(encoding='utf-8', errors='ignore')

    if not re.search(r'<html[^>]+lang=["\'][^"\']+["\']', t, re.I):
        issues.append(f'{p}: missing html lang')
    if not re.search(r'<title>[^<]+</title>', t, re.I):
        issues.append(f'{p}: missing title')

    h1 = len(re.findall(r'<h1\b', t, re.I))
    if h1 != 1:
        issues.append(f'{p}: expected 1 h1, found {h1}')

    for tag in re.findall(r'<img\b[^>]*>', t, re.I):
        if not re.search(r'\balt=', tag, re.I):
            issues.append(f'{p}: image missing alt')

    for attrs, body in re.findall(r'<button\b([^>]*)>(.*?)</button>', t, re.I | re.S):
        visible = re.sub(r'<[^>]+>', '', body).strip()
        if not visible and not re.search(r'aria-label\s*=', attrs, re.I):
            issues.append(f'{p}: button may lack accessible name')

    for href in re.findall(r'<a\b[^>]*\bhref=["\']([^"\']+)["\']', t, re.I):
        target = internal_target(p, href)
        if target is not None and not target.exists():
            issues.append(f'{p}: internal link target missing: {href} -> {target}')

print(f'Checked {len(FILES)} public HTML files for structural accessibility and internal navigation.')
if issues:
    print('Accessibility/navigation guardrail findings:')
    for issue in issues:
        print('-', issue)
    sys.exit(1)

print('Automated guardrails passed. This is not WCAG certification; manual keyboard, screen-reader, focus-order and contrast testing remains required.')
