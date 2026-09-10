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
    r"\s*(?:,|/|&|\+|×|(?<!\S)x(?!\S)|\bfeat(?:uring)?\.?|\bft\.?|\bwith\b)\s*",
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
    if pages > 1:
        with ThreadPoolExecutor(max_workers=min(8, pages - 1)) as executor:
            page_data.extend(executor.map(fetch_page, range(2, pages + 1)))

    rows = []
    for data in page_data:
        for row in data.get("rows", []):
            rows.append(row)
    return rows


def normalize_track(row):
    song = row.get("song") or {}
    artist = clean_artist(song.get("artist"))
    title = str(song.get("title") or "Unknown title").strip() or "Unknown title"
    album = str(song.get("album") or "Northern Dial library").strip() or "Northern Dial library"
    request_id = row.get("request_id") or row.get("id") or ""
    return artist, title, album, request_id


def build_catalogue(rows):
    removals = hidden_artists()
    by_artist = {}
    for row in rows:
        artist_credit, title, album, request_id = normalize_track(row)
        for artist in split_artists(artist_credit):
            if artist.casefold() in removals:
                continue
            by_artist.setdefault(artist, []).append(
                {"title": title, "album": album, "request_id": request_id}
            )
    return by_artist


def profile_for(artist, enrichments, profiles):
    key = artist.casefold()
    profile = {}
    if isinstance(profiles.get(key), dict):
        profile.update(profiles[key])
    if isinstance(enrichments.get(key), dict):
        profile.update(enrichments[key])
    return profile


def render_source_links(sources):
    if not sources:
        return ""
    links = []
    for index, source in enumerate(sources, start=1):
        if isinstance(source, str):
            url = source
            label = f"Source {index}"
        elif isinstance(source, dict):
            url = source.get("url") or ""
            label = source.get("label") or f"Source {index}"
        else:
            continue
        if not url:
            continue
        links.append(
            f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(label)}</a>'
        )
    if not links:
        return ""
    return '<p class="artist-sources">Sources: ' + " · ".join(links) + "</p>"


def render_artist_links(profile):
    links = []
    for label, field in (("Official site", "official_site"), ("Instagram", "instagram")):
        url = profile.get(field)
        if url:
            links.append(
                f'<a href="{escape(str(url), quote=True)}" target="_blank" rel="noopener noreferrer">{label}</a>'
            )
    if not links:
        return ""
    return '<p class="artist-links">' + " · ".join(links) + "</p>"


def render_profile(artist, tracks, profile):
    slug = slugify(artist)
    title = escape(artist)
    count = len(tracks)
    reviewed = bool(profile.get("reviewed"))
    bio = profile.get("bio") if reviewed else None
    location = profile.get("location") if reviewed else None
    album_titles = {track.get("album") for track in tracks if track.get("album")}

    lines = [
        f'<article class="artist-card" id="artist-{slug}" data-artist="{escape(artist, quote=True)}">',
        '  <details class="artist-details">',
        f'    <summary><span class="artist-name">{title}</span> <span class="track-count">({count} track{"s" if count != 1 else ""})</span></summary>',
        '    <div class="artist-body">',
    ]
    if bio:
        lines.append(f'      <p class="artist-bio">{render_editorial_text(bio, album_titles)}</p>')
    if location:
        lines.append(f'      <p class="artist-location">{escape(str(location))}</p>')
    links = render_artist_links(profile)
    if links:
        lines.append("      " + links)
    sources = render_source_links(profile.get("sources") or [])
    if sources:
        lines.append("      " + sources)
    if reviewed:
        profile_url = f"/artists/{slug}.html"
        lines.append(f'      <p class="artist-profile-link"><a href="{profile_url}">View Full Profile</a></p>')

    lines.append('      <div class="artist-track-list">')
    for track in sorted(tracks, key=lambda item: item["title"].casefold()):
        request_id = track.get("request_id")
        if request_id:
            request_url = f"/?request_id={quote(str(request_id))}"
            request = f'<a class="request-track" href="{request_url}">Request this artist</a>'
        else:
            request = ""
        lines.extend(
            [
                '        <div class="artist-track">',
                f'          <span class="track-title">{escape(track["title"])}</span>',
                f'          <span class="track-album">{escape(track["album"])}</span>',
                (f"          {request}" if request else ""),
                "        </div>",
            ]
        )
    lines.extend(['      </div>', '    </div>', '  </details>', '</article>'])
    return "\n".join(line for line in lines if line != "")


def replace_between(text, start_marker, end_marker, replacement):
    start = text.index(start_marker) + len(start_marker)
    end = text.index(end_marker, start)
    return text[:start] + "\n" + replacement.rstrip() + "\n      " + text[end:]


def main():
    rows = catalogue_rows()
    by_artist = build_catalogue(rows)
    enrichments = load_enrichments()
    raw_profiles = json.loads(Path(PROFILE_FILE).read_text(encoding="utf-8")) if Path(PROFILE_FILE).exists() else {}
    profiles = {str(key).casefold(): value for key, value in raw_profiles.items()}

    artists = sorted(by_artist, key=str.casefold)
    catalogue = "\n".join(
        render_profile(artist, by_artist[artist], profile_for(artist, enrichments, profiles))
        for artist in artists
    )
    letters = []
    seen = set()
    for artist in artists:
        first = artist[0].upper() if artist else "#"
        letter = first if first.isalpha() else "#"
        if letter not in seen:
            seen.add(letter)
            letters.append(letter)
    nav = " ".join(
        f'<a href="#artist-{slugify(next(a for a in artists if ((a[0].upper() if a else "#") if (a[0].upper() if a else "#").isalpha() else "#") == letter))}">{escape(letter)}</a>'
        for letter in letters
    )

    template = Path(TEMPLATE).read_text(encoding="utf-8")
    template = replace_between(template, CATALOGUE_START, CATALOGUE_END, catalogue)
    template = replace_between(template, NAV_START, NAV_END, nav)
    Path(TEMPLATE).write_text(template, encoding="utf-8")

    Path("library_artists.txt").write_text("\n".join(artists) + "\n", encoding="utf-8")
    print(f"Wrote {len(artists):,} artists from {len(rows):,} catalogue rows")


if __name__ == "__main__":
    main()
