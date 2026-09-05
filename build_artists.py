#!/usr/bin/env python3
"""Build the crawlable Northern Dial artist catalogue from the public API.

Run from the repository root with:
    python3 build_artists.py
"""

from concurrent.futures import ThreadPoolExecutor
from html import escape
from urllib.parse import quote
from urllib.request import urlopen
import json
import re


API = "https://a10.asurahosting.com/api/station/northern_dial/requests"
PAGE_SIZE = 25
TEMPLATE = "artists.html"
CATALOGUE_START = "      <!-- STATIC_ARTIST_CATALOGUE_START -->"
CATALOGUE_END = "      <!-- STATIC_ARTIST_CATALOGUE_END -->"
NAV_START = "    <!-- STATIC_ARTIST_LETTER_NAV_START -->"
NAV_END = "    <!-- STATIC_ARTIST_LETTER_NAV_END -->"


def fetch_page(page):
    url = f"{API}?searchPhrase=&rowCount={PAGE_SIZE}&current={page}&page=1"
    with urlopen(url, timeout=30) as response:
        return json.load(response)


def clean_artist(value):
    name = str(value or "Unknown Artist")
    name = re.sub(r"^\s*\d{1,3}\s*[.-]\s*", "", name).strip()
    return name or "Unknown Artist"


def catalogue_rows():
    first = fetch_page(1)
    pages = int(first.get("total_pages") or 1)
    page_data = [first]
    with ThreadPoolExecutor(max_workers=12) as executor:
        for start in range(2, pages + 1, 12):
            page_data.extend(executor.map(fetch_page, range(start, min(start + 12, pages + 1))))
    return [row for page in page_data for row in (page.get("rows") or [])]


def build_groups(rows):
    groups = {}
    for item in rows:
        song = item.get("song") or item
        name = clean_artist(song.get("artist"))
        key = name.casefold()
        group = groups.setdefault(key, {"name": name, "songs": {}})
        song_key = song.get("id") or f"{name}:{song.get('title', '')}"
        group["songs"].setdefault(song_key, {
            "title": song.get("title") or "Unknown title",
            "album": song.get("album") or song.get("genre") or "Northern Dial library",
        })
    return sorted(groups.values(), key=lambda group: group["name"].casefold())


def render_groups(groups):
    rendered = []
    previous_letter = None
    for group in groups:
        name = group["name"]
        letter = name[0].casefold() if name and name[0].isalpha() else "0"
        anchor = ""
        if letter != previous_letter:
            anchor = f'      <div id="letter-{letter}" class="letter-anchor" aria-hidden="true"></div>\n'
            previous_letter = letter
        search = escape(name.casefold(), quote=True)
        request_url = f"./index.html?request={quote(name)}"
        songs = list(group["songs"].values())
        tracks = []
        for song in sorted(songs, key=lambda value: (value["title"].casefold(), value["album"].casefold())):
            title = song["title"]
            album = song["album"]
            track_search = escape(f"{name} {title} {album}".casefold(), quote=True)
            tracks.append(
                f'        <div class="track" data-search="{track_search}">'
                f'<div><div class="track-title">{escape(title)}</div>'
                f'<div class="track-album">{escape(album)}</div></div>'
                f'<a class="request-link" href="{request_url}">Request this artist</a></div>'
            )
        rendered.append(
            anchor + f'      <details data-search="{search}">'
            f'<summary>{escape(name)} <span class="artist-meta">'
            f'({len(songs)} track{"" if len(songs) == 1 else "s"})</span></summary>'
            '<div class="artist-meta"><span class="social-note">'
            'Instagram / official links: to be verified</span></div>\n'
            + "\n".join(tracks)
            + "</details>"
        )
    return "\n".join(rendered)


def render_letter_nav(groups):
    letters = []
    for group in groups:
        letter = group["name"][0].casefold() if group["name"] and group["name"][0].isalpha() else "0"
        if letter not in letters:
            letters.append(letter)
    links = ['<a href="#artistList">All</a>']
    links.extend(f'<a href="#letter-{letter}">{"#" if letter == "0" else letter.upper()}</a>' for letter in letters)
    return '    <nav class="letter-nav" aria-label="Jump to artist letter">' + "".join(links) + "</nav>"


def replace_block(template, start_marker, end_marker, content):
    start = template.index(start_marker) + len(start_marker)
    end = template.index(end_marker, start)
    return template[:start] + "\n" + content + "\n" + template[end:]


def main():
    rows = catalogue_rows()
    groups = build_groups(rows)
    with open(TEMPLATE, "r", encoding="utf-8") as handle:
        template = handle.read()
    if CATALOGUE_START not in template or CATALOGUE_END not in template:
        raise SystemExit(f"Catalogue markers not found in {TEMPLATE}")
    output = replace_block(template, CATALOGUE_START, CATALOGUE_END, render_groups(groups))
    if NAV_START not in output or NAV_END not in output:
        raise SystemExit(f"Letter navigation markers not found in {TEMPLATE}")
    output = replace_block(output, NAV_START, NAV_END, render_letter_nav(groups))
    with open(TEMPLATE, "w", encoding="utf-8") as handle:
        handle.write(output)
    print(f"Generated {len(groups):,} artists and {len(rows):,} songs in {TEMPLATE}")


if __name__ == "__main__":
    main()
