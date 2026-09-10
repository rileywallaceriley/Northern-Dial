#!/usr/bin/env python3
"""Build the crawlable Northern Dial artist catalogue from the public API.

Run from the repository root with:
    python3 build_artists.py
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from html import escape
from urllib.parse import quote
from urllib.request import urlopen
import json
import re
import unicodedata

API = "https://a10.asurahosting.com/api/station/northern_dial/requests"
PAGE_SIZE = 25
TEMPLATE = "artists.html"
PROFILE_FILE = "artist_profiles.json"
ENRICHMENT_FILE = "artist_enrichment.json"
CATALOGUE_START = "      <!-- STATIC_ARTIST_CATALOGUE_START -->"
CATALOGUE_END = "      <!-- STATIC_ARTIST_CATALOGUE_END -->"
NAV_START = "    <!-- STATIC_ARTIST_LETTER_NAV_START -->"
NAV_END = "    <!-- STATIC_ARTIST_LETTER_NAV_END -->"
REMOVAL_FILE = "artist_removals.txt"
REMOVAL_BATCH_DIR = "artist_removal_batches"
ENRICHMENT_BATCH_DIR = "artist_enrichment_batches"
CREDIT_SEPARATOR = re.compile(
    r"\s*(?:,|/|&|\+|×|\bx\b|\bfeat(?:uring)?\.?|\bft\.?|\bwith\b)\s*",
    re.IGNORECASE,
)


def fetch_page(page):
    url = f"{API}?searchPhrase=&rowCount={PAGE_SIZE}&current={page}&page=1"
    with urlopen(url, timeout=30) as response:
        return json.load(response)


def clean_artist(value):
    name = str(value or "Unknown Artist")
    name = re.sub(r"^\s*\d{1,3}\s*[.-]\s*", "", name).strip()
    return name or "Unknown Artist"


def slugify(value):
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.casefold()).strip("-")
    return slug or "artist"


def hidden_artists():
    names = set()
    paths = [Path(REMOVAL_FILE)]
    paths.extend(sorted(Path(REMOVAL_BATCH_DIR).glob("*.txt")))
    for path in paths:
        if not path.exists():
            continue
        names.update(
            line.strip().casefold()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    return names


def load_enrichments():
    """Merge enrichment records field-by-field so later editorial layers can be small."""
    merged = {}
    paths = [Path(ENRICHMENT_FILE)]
    paths.extend(sorted(Path(ENRICHMENT_BATCH_DIR).glob("*.json")))
    for path in paths:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        for key, value in data.items():
            normalized = str(key).casefold()
            if isinstance(value, dict):
                merged.setdefault(normalized, {}).update(value)
            else:
                merged[normalized] = value
    return merged


def render_editorial_text(value, album_titles=()):
    """Escape editorial copy while allowing only verified album-title emphasis."""
    text = str(value or "")
    titles = sorted({str(title) for title in album_titles if title}, key=len, reverse=True)
    if not titles:
        return escape(text)
    pattern = re.compile("|".join(re.escape(title) for title in titles))
    output = []
    position = 0
    for match in pattern.finditer(text):
        output.append(escape(text[position:match.start()]))
        output.append(f"<em>{escape(match.group(0))}</em>")
        position = match.end()
    output.append(escape(text[position:]))
    return "".join(output)


def split_artists(value):
    credit = clean_artist(value)
    parts = [clean_artist(part) for part in CREDIT_SEPARATOR.split(credit)]
    return list(dict.fromkeys(part for part in parts if part))


def catalogue_rows():
    first = fetch_page(1)
    pages = int(first.get("total_pages") or 1)
    page_data = [first]
    with ThreadPoolExecutor(max_workers=12) as executor:
        for start in range(2, pages + 1, 12):
            page_data.extend(executor.map(fetch_page, range(start, min(start + 12, pages + 1))))
    return [row for page in page_data for row in (page.get("rows") or [])]


def build_groups(rows, hidden):
    groups = {}
    for item in rows:
        song = item.get("song") or item
        song_key = song.get("id") or f"{song.get('artist', 'Unknown Artist')}:{song.get('title', '')}"
        for name in split_artists(song.get("artist")):
            key = name.casefold()
            group = groups.setdefault(key, {"name": name, "songs": {}})
            group["songs"].setdefault(song_key, {
                "title": song.get("title") or "Unknown title",
                "album": song.get("album") or song.get("genre") or "Northern Dial library",
            })
    return sorted(
        (group for key, group in groups.items() if key not in hidden),
        key=lambda group: group["name"].casefold(),
    )


def render_profile(profile, enrichment=None):
    enrichment = enrichment or {}
    if not profile and not enrichment.get("reviewed"):
        return ""
    bio = enrichment.get("directory_summary") or profile.get("bio") or enrichment.get("bio", "")
    album_titles = enrichment.get("album_titles", [])
    links = []
    website = profile.get("website") or enrichment.get("website")
    instagram = profile.get("instagram") or enrichment.get("instagram")
    if website:
        links.append(f'<a href="{escape(website, quote=True)}" target="_blank" rel="noopener">Official site</a>')
    if instagram:
        links.append(f'<a href="{escape(instagram, quote=True)}" target="_blank" rel="noopener">Instagram</a>')
    if profile.get("feature"):
        links.append(f'<a href="{escape(profile["feature"], quote=True)}">Northern Dial feature</a>')
    if enrichment.get("musicbrainz_artist_id"):
        mbid = escape(enrichment["musicbrainz_artist_id"], quote=True)
        links.append(f'<a href="https://musicbrainz.org/artist/{mbid}" target="_blank" rel="noopener">MusicBrainz</a>')
    sources = [url for url in enrichment.get("sources", []) if url]
    source_html = ""
    if sources:
        source_links = " · ".join(
            f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener">Source {index}</a>'
            for index, url in enumerate(sources, 1)
        )
        source_html = f'<div class="profile-sources"><span>Sources:</span> {source_links}</div>'
    location = enrichment.get("city") or enrichment.get("country")
    location_html = f'<p class="profile-location">{escape(location)}</p>' if location else ""
    link_html = f'<div class="profile-links">{" · ".join(links)}</div>' if links else ""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", bio) if part.strip()]
    bio_html = "".join(
        f'<p class="profile-bio">{render_editorial_text(part, album_titles)}</p>'
        for part in paragraphs
    )
    return f'<div class="artist-profile">{bio_html}{location_html}{link_html}{source_html}</div>'


def canonical_display_name(raw_name, profile, enrichment):
    """Prefer reviewed editorial naming over raw station credit formatting."""
    return str(
        enrichment.get("display_name")
        or profile.get("display_name")
        or profile.get("name")
        or raw_name
    )


def render_groups(groups, profiles, enrichments):
    rendered = []
    previous_letter = None
    for group in groups:
        name = group["name"]
        letter = name[0].casefold() if name and name[0].isalpha() else "0"
        anchor = ""
        if letter != previous_letter:
            anchor = f'      <div id="letter-{letter}" class="letter-anchor" aria-hidden="true"></div>\n'
            previous_letter = letter
        songs = list(group["songs"].values())
        profile = profiles.get(name.casefold(), {})
        enrichment = enrichments.get(name.casefold(), {})
        display_name = canonical_display_name(name, profile, enrichment)
        search = escape(f"{name} {display_name}".casefold(), quote=True)
        request_url = f"./index.html?request={quote(name)}"
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
        profile_html = render_profile(profile, enrichment)
        has_artist_page = bool(profile) or bool(enrichment.get("reviewed"))
        details_id = ""
        if has_artist_page:
            slug = slugify(display_name)
            profile_url = f"./artists/{slug}.html"
            details_id = f' id="artist-{escape(slug, quote=True)}"'
            artist_name_html = (
                f'<a class="artist-page-link" href="{profile_url}" '
                f'onclick="event.stopPropagation()">{escape(display_name)}</a>'
            )
            profile_action_html = (
                f'<div class="profile-actions"><a class="profile-page-button" href="{profile_url}">View Full Profile</a></div>'
            )
        else:
            artist_name_html = escape(name)
            profile_action_html = ""
        rendered.append(
            anchor + f'      <details{details_id} data-search="{search}">'
            f'<summary>{artist_name_html} <span class="artist-meta">'
            f'({len(songs)} track{"" if len(songs) == 1 else "s"})</span></summary>'
            + profile_html + "\n" + profile_action_html + "\n" + "\n".join(tracks) + "</details>"
        )
    return "\n".join(rendered)


def render_letter_nav(groups):
    letters = []
    for group in groups:
        letter = group["name"][0].casefold() if group["name"] and group["name"][0].isalpha() else "0"
        if letter not in letters:
            letters.append(letter)
    options = ['<option value="">Jump to a letter…</option>', '<option value="artistList">All artists</option>']
    options.extend(f'<option value="letter-{letter}">{"#" if letter == "0" else letter.upper()}</option>' for letter in letters)
    return (
        '    <nav class="letter-nav" aria-label="Catalogue navigation">'
        '<label for="letterJump">Jump to:</label><select id="letterJump">'
        '<optgroup label="Artist sections">' + "".join(options) + '</optgroup></select>'
        '<a class="top-link" href="#top">Back to top ↑</a></nav>'
    )


def replace_block(template, start_marker, end_marker, content):
    start = template.index(start_marker) + len(start_marker)
    end = template.index(end_marker, start)
    return template[:start] + "\n" + content + "\n" + template[end:]


def main():
    rows = catalogue_rows()
    groups = build_groups(rows, hidden_artists())
    with open(PROFILE_FILE, "r", encoding="utf-8") as handle:
        profiles = {key.casefold(): value for key, value in json.load(handle).items()}
    enrichments = load_enrichments()
    with open(TEMPLATE, "r", encoding="utf-8") as handle:
        template = handle.read()
    if CATALOGUE_START not in template or CATALOGUE_END not in template:
        raise SystemExit(f"Catalogue markers not found in {TEMPLATE}")
    output = replace_block(template, CATALOGUE_START, CATALOGUE_END, render_groups(groups, profiles, enrichments))
    if NAV_START not in output or NAV_END not in output:
        raise SystemExit(f"Letter navigation markers not found in {TEMPLATE}")
    output = replace_block(output, NAV_START, NAV_END, render_letter_nav(groups))
    with open(TEMPLATE, "w", encoding="utf-8") as handle:
        handle.write(output)
    print(f"Generated {len(groups):,} artists and {len(rows):,} songs in {TEMPLATE}")


if __name__ == "__main__":
    main()
