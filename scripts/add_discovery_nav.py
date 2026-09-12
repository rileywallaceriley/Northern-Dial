#!/usr/bin/env python3
from pathlib import Path
import re

NEW_LINKS = [
    ('New Releases', '/new-releases.html'),
    ('New Artists', '/new-canadian-artists.html'),
]


def patch_shell():
    path = Path('nd-shell.js')
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')

    english_block = """    : [
        ['Home', '/'],
        ['Songs', '/library.html'],
        ['Artists', '/artists.html'],
        ['Discover', '/discover.html'],
        ['Blog', '/blog/']
      ];"""
    english_replacement = """    : [
        ['Home', '/'],
        ['Songs', '/library.html'],
        ['Artists', '/artists.html'],
        ['Discover', '/discover.html'],
        ['New Releases', '/new-releases.html'],
        ['New Artists', '/new-canadian-artists.html'],
        ['Blog', '/blog/']
      ];"""
    if "['New Releases', '/new-releases.html']" not in text:
        if english_block not in text:
            raise RuntimeError('Could not find English shared-nav block in nd-shell.js')
        text = text.replace(english_block, english_replacement, 1)
    path.write_text(text, encoding='utf-8')


def patch_homepage():
    path = Path('index.html')
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    nav_match = re.search(r'(<nav class="site-nav mobile-menu-nav nd-home-nav".*?</nav>)', text, re.S)
    if not nav_match:
        raise RuntimeError('Could not find homepage navigation')
    nav = nav_match.group(1)
    if 'new-releases.html' not in nav:
        nav = nav.replace(
            '        <a href="discover.html">Discover</a>\n        <a href="blog/">Blog</a>',
            '        <a href="discover.html">Discover</a>\n'
            '        <a href="new-releases.html">New Releases</a>\n'
            '        <a href="new-canadian-artists.html">New Artists</a>\n'
            '        <a href="blog/">Blog</a>',
            1,
        )
    text = text[:nav_match.start()] + nav + text[nav_match.end():]
    path.write_text(text, encoding='utf-8')


def main():
    patch_shell()
    patch_homepage()
    print('New Releases and New Artists added to shared and homepage navigation.')


if __name__ == '__main__':
    main()
