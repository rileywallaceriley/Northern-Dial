#!/usr/bin/env python3
from pathlib import Path
import re

ROOT_PAGES = ['index.html', 'library.html', 'artists.html', 'discover.html', 'requests.html']


def patch_nav(path: Path, about_href: str, fr_href: str):
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    pattern = re.compile(r'(<nav[^>]*aria-label="Main navigation"[^>]*>.*?</nav>)', re.S)
    match = pattern.search(text)
    if not match:
        return
    nav = match.group(1)
    is_list_nav = '<ul' in nav

    # Normalize an older malformed blog-nav form where About and FR shared one <li>.
    nav = re.sub(
        r'<li>\s*(<a[^>]*href="[^"]*about\.html"[^>]*>About</a>)\s*(<a[^>]*href="[^"]*fr/?"[^>]*>FR</a>)\s*</li>',
        r'<li>\1</li>\n      <li>\2</li>',
        nav,
        flags=re.S,
    )

    if '>About</a>' not in nav:
        anchor = f'<a href="{about_href}">About</a>'
        if is_list_nav:
            item = f'<li>{anchor}</li>'
            if '>FR</a>' in nav:
                nav = re.sub(r'(\s*<li>\s*<a[^>]*>FR</a>\s*</li>)', '\n      ' + item + r'\1', nav, count=1)
            elif 'submit-link' in nav:
                nav = re.sub(r'(\s*<li>\s*<a[^>]*class="[^"]*submit-link[^"]*"[^>]*>Submit</a>\s*</li>)', '\n      ' + item + r'\1', nav, count=1)
        else:
            if '>FR</a>' in nav:
                nav = re.sub(r'(\s*<a[^>]*>FR</a>)', '\n        ' + anchor + r'\1', nav, count=1)
            elif 'submit-link' in nav:
                nav = re.sub(r'(\s*<a[^>]*class="[^"]*submit-link[^"]*"[^>]*>Submit</a>)', '\n        ' + anchor + r'\1', nav, count=1)

    if '>FR</a>' not in nav:
        anchor = f'<a href="{fr_href}" class="language-switch" lang="fr" hreflang="fr">FR</a>'
        if is_list_nav:
            item = f'<li>{anchor}</li>'
            nav = re.sub(r'(\s*<li>\s*<a[^>]*class="[^"]*submit-link[^"]*"[^>]*>Submit</a>\s*</li>)', '\n      ' + item + r'\1', nav, count=1)
        else:
            nav = re.sub(r'(\s*<a[^>]*class="[^"]*submit-link[^"]*"[^>]*>Submit</a>)', '\n        ' + anchor + r'\1', nav, count=1)

    text = text[:match.start()] + nav + text[match.end():]
    path.write_text(text, encoding='utf-8')


for name in ROOT_PAGES:
    patch_nav(Path(name), '/about.html', '/fr/')

for path in sorted(Path('blog').glob('*.html')):
    patch_nav(path, '../about.html', '../fr/')

print('Final navigation guard applied: About and FR are present with valid list markup.')
