#!/usr/bin/env python3
from pathlib import Path
import re

ROOT_PAGES = [
    'index.html', 'library.html', 'artists.html', 'discover.html', 'requests.html',
    'about.html', 'sessions.html', 'archive.html', 'accessibility.html',
    'rights.html', 'survey.html'
]

HOME_LANGUAGE_STYLES = r'''
<style id="nd-home-language-styles">
.site-nav .language-toggle {
    appearance: none;
    background: transparent;
    border: 0;
    color: #fff;
    cursor: pointer;
    flex: 0 0 auto;
    font-family: 'Oswald', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    padding: 14px 28px;
    text-transform: uppercase;
    transition: color 0.2s ease, background-color 0.2s ease;
}
.site-nav .language-toggle:hover,
.site-nav .language-toggle:focus {
    background: #262626;
    color: #C33;
}
.site-nav .language-toggle:focus-visible {
    outline: 3px solid #C33;
    outline-offset: -3px;
}
@media (max-width: 768px) {
    .mobile-menu-links .language-toggle {
        background: #1a1a1a !important;
        border: 0 !important;
        border-bottom: 1px solid #343434 !important;
        border-radius: 0 !important;
        color: #ffffff !important;
        display: block !important;
        font-family: 'Oswald', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.11em !important;
        margin: 0 !important;
        padding: 14px 18px !important;
        text-align: left !important;
        text-transform: uppercase !important;
        width: 100% !important;
    }
    .mobile-menu-links .language-toggle:hover,
    .mobile-menu-links .language-toggle:focus {
        background: #262626 !important;
        color: #CC3333 !important;
    }
}
</style>
'''


def normalize_language_after_submit(nav: str, homepage: bool = False) -> str:
    is_list_nav = '<ul' in nav

    if homepage:
        # Remove any old homepage French link/button, then place the in-page toggle after Submit.
        nav = re.sub(
            r'\s*<a\s+href=["\']/fr/?["\'][^>]*>\s*(?:FR|Français)\s*</a>',
            '', nav, count=1, flags=re.I,
        )
        nav = re.sub(
            r'\s*<button[^>]*data-language-toggle[^>]*>.*?</button>',
            '', nav, count=1, flags=re.I | re.S,
        )
        button = ('<button type="button" class="language-switch language-toggle" '
                  'data-language-toggle lang="fr" '
                  'aria-label="Afficher la page d’accueil en français">Français</button>')
        submit = re.search(r'(<a[^>]*class="[^"]*submit-link[^"]*"[^>]*>Submit</a>)', nav, re.I)
        if submit:
            nav = nav[:submit.end()] + '\n        ' + button + nav[submit.end():]
        return nav

    if is_list_nav:
        lang_match = re.search(
            r'\s*<li>\s*(<a[^>]*(?:href="[^"]*fr/?"|hreflang="fr"|lang="fr")[^>]*>\s*(?:FR|Français)\s*</a>)\s*</li>',
            nav, re.I | re.S,
        )
        if not lang_match:
            return nav
        anchor = re.sub(r'>\s*FR\s*</a>', '>Français</a>', lang_match.group(1), flags=re.I)
        nav = nav[:lang_match.start()] + nav[lang_match.end():]
        submit = re.search(
            r'(<li>\s*<a[^>]*class="[^"]*submit-link[^"]*"[^>]*>Submit</a>\s*</li>)',
            nav, re.I | re.S,
        )
        if submit:
            nav = nav[:submit.end()] + '\n      <li>' + anchor + '</li>' + nav[submit.end():]
        return nav

    lang_match = re.search(
        r'\s*(<a[^>]*(?:href="[^"]*fr(?:/|/[^\"]*|\.html)?"|hreflang="fr"|lang="fr")[^>]*>\s*(?:FR|Français)\s*</a>)',
        nav, re.I | re.S,
    )
    if not lang_match:
        return nav
    anchor = re.sub(r'>\s*FR\s*</a>', '>Français</a>', lang_match.group(1), flags=re.I)
    nav = nav[:lang_match.start()] + nav[lang_match.end():]
    submit = re.search(r'(<a[^>]*class="[^"]*submit-link[^"]*"[^>]*>Submit</a>)', nav, re.I)
    if submit:
        nav = nav[:submit.end()] + '\n        ' + anchor + nav[submit.end():]
    return nav


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

    # Normalize an older malformed blog-nav form where About and French shared one <li>.
    nav = re.sub(
        r'<li>\s*(<a[^>]*href="[^"]*about\.html"[^>]*>About</a>)\s*(<a[^>]*(?:href="[^"]*fr/?"|hreflang="fr")[^>]*>(?:FR|Français)</a>)\s*</li>',
        r'<li>\1</li>\n      <li>\2</li>',
        nav,
        flags=re.S | re.I,
    )

    if '>About</a>' not in nav:
        anchor = f'<a href="{about_href}">About</a>'
        if is_list_nav:
            item = f'<li>{anchor}</li>'
            if 'submit-link' in nav:
                nav = re.sub(
                    r'(\s*<li>\s*<a[^>]*class="[^"]*submit-link[^"]*"[^>]*>Submit</a>\s*</li>)',
                    '\n      ' + item + r'\1', nav, count=1,
                )
        else:
            if 'submit-link' in nav:
                nav = re.sub(
                    r'(\s*<a[^>]*class="[^"]*submit-link[^"]*"[^>]*>Submit</a>)',
                    '\n        ' + anchor + r'\1', nav, count=1,
                )

    has_language_control = bool(re.search(r'(hreflang="fr"|lang="fr"|data-language-toggle)', nav, re.I))
    if not has_language_control and path.name != 'index.html':
        anchor = f'<a href="{fr_href}" class="language-switch" lang="fr" hreflang="fr">Français</a>'
        if is_list_nav:
            submit = re.search(
                r'(<li>\s*<a[^>]*class="[^"]*submit-link[^"]*"[^>]*>Submit</a>\s*</li>)',
                nav, re.I | re.S,
            )
            if submit:
                nav = nav[:submit.end()] + '\n      <li>' + anchor + '</li>' + nav[submit.end():]
        else:
            submit = re.search(r'(<a[^>]*class="[^"]*submit-link[^"]*"[^>]*>Submit</a>)', nav, re.I)
            if submit:
                nav = nav[:submit.end()] + '\n        ' + anchor + nav[submit.end():]

    nav = normalize_language_after_submit(nav, homepage=(path.name == 'index.html'))
    text = text[:match.start()] + nav + text[match.end():]
    path.write_text(text, encoding='utf-8')


def patch_home_language_assets():
    path = Path('index.html')
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    if 'id="nd-home-language-styles"' not in text:
        text = text.replace('</head>', HOME_LANGUAGE_STYLES + '\n</head>', 1)
    if 'src="/homepage_language.js"' not in text:
        text = text.replace('</body>', '<script src="/homepage_language.js"></script>\n</body>', 1)
    path.write_text(text, encoding='utf-8')


for name in ROOT_PAGES:
    path = Path(name)
    # Institutional pages already contain About; these hrefs are only fallbacks.
    patch_nav(path, '/about.html', '/fr/')

for path in sorted(Path('blog').glob('*.html')):
    patch_nav(path, '../about.html', '../fr/')

patch_home_language_assets()

print('Navigation finalized: Submit precedes Français, and the homepage language control translates in place.')
