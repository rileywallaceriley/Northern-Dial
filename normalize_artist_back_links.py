#!/usr/bin/env python3
"""Normalize standalone artist return links against the current directory.

Profile pages can outlive a station-catalogue entry. Current catalogue artists
should return to their exact accordion anchor; profiles no longer represented
in artists.html should return to the directory root instead of a dead fragment.
This is a build-time normalization step, not a hand edit of generated pages.
"""

from pathlib import Path
import re

DIRECTORY_FILE = Path("artists.html")
ARTIST_DIR = Path("artists")
DETAIL_ID_PATTERN = re.compile(r'<details\b[^>]*\bid="(artist-[^"]+)"', re.IGNORECASE)
BACK_LINK_PATTERN = re.compile(
    r'(<a\b[^>]*class="[^"]*\bback-link\b[^"]*"[^>]*href=")([^"]+)("[^>]*>)',
    re.IGNORECASE,
)
ARTICLE_CLOSE_PATTERN = re.compile(r'</article>', re.IGNORECASE)


def main():
    directory = DIRECTORY_FILE.read_text(encoding="utf-8")
    anchors = set(DETAIL_ID_PATTERN.findall(directory))
    checked = 0
    changed = 0
    inserted = 0
    anchored = 0
    directory_only = 0

    for path in sorted(ARTIST_DIR.glob("*.html")):
        checked += 1
        slug = path.stem
        expected_anchor = f"artist-{slug}"
        expected_href = (
            f"../artists.html#{expected_anchor}"
            if expected_anchor in anchors
            else "../artists.html"
        )
        if expected_anchor in anchors:
            anchored += 1
        else:
            directory_only += 1

        html = path.read_text(encoding="utf-8")
        match = BACK_LINK_PATTERN.search(html)
        if match:
            if match.group(2) == expected_href:
                continue
            html = html[:match.start(2)] + expected_href + html[match.end(2):]
            path.write_text(html, encoding="utf-8")
            changed += 1
            continue

        article_close = ARTICLE_CLOSE_PATTERN.search(html)
        if not article_close:
            continue

        back_link = (
            f'<a class="back-link" href="{expected_href}">← Back to the artist directory</a>'
        )
        html = html[:article_close.start()] + back_link + html[article_close.start():]
        path.write_text(html, encoding="utf-8")
        changed += 1
        inserted += 1

    print(
        f"Artist back-link normalization: {checked} profiles checked; "
        f"{changed} changed ({inserted} inserted); {anchored} anchored to current accordions; "
        f"{directory_only} safely return to artists.html."
    )


if __name__ == "__main__":
    main()
