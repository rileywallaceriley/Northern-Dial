#!/usr/bin/env python3
from __future__ import annotations

import html as html_lib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTISTS_PATH = ROOT / "artists.html"
IMAGES_PATH = ROOT / "library_artist_images.tsv"
OUTPUT_PATH = ROOT / "discovery-data.json"

GENRES = {
    "hip-hop": ["hip-hop", "hip hop", "rapper", " rap ", "rap.", "rap,", "boom bap", "trap", "drill", "emcee"],
    "rnb-soul": ["r&b", "rnb", "rhythm and blues", "neo-soul", "neo soul", "soul", "soulful"],
    "pop": [" pop ", "synth-pop", "synthpop", "dance-pop", "art-pop", "electropop", "dream pop", "indie-pop", "indie pop", "scandi-pop"],
    "rock": [" rock ", "garage rock", "hard rock", "classic rock", "post-rock", "rockabilly"],
    "indie-alternative": ["indie", "alternative", "alt-", "shoegaze", "post-punk", "new wave", "dream pop", "art rock", "experimental"],
    "electronic-dance": ["electronic", "electronica", "house", "techno", " dance ", "club", "edm", "ambient", "trip-hop", "trip hop", "downtempo", "synth"],
    "folk-songwriter": ["folk", "singer-songwriter", "singer songwriter", "acoustic", "roots music"],
    "country-americana": ["country", "americana", "alt-country", "bluegrass", "honky tonk"],
    "jazz": ["jazz", "bebop", "improvisation", "improvised music"],
    "punk-hardcore": ["punk", "hardcore", "post-hardcore", "emo", "ska punk"],
    "metal": ["metal", "doom", "black metal", "death metal", "thrash", "sludge", "metalcore"],
    "reggae-dancehall": ["reggae", "dancehall", "dub", "soca", "caribbean"],
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFD", value or "")
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return value.lower().replace("’", "'").replace("‘", "'").strip()


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]*>", " ", value or "")
    return re.sub(r"\s+", " ", html_lib.unescape(value)).strip()


def first_match(pattern: str, value: str) -> str:
    match = re.search(pattern, value, flags=re.I | re.S)
    return match.group(1) if match else ""


def classify_genres(value: str) -> list[str]:
    haystack = f" {normalize(value)} "
    return [
        key
        for key, terms in GENRES.items()
        if any(normalize(term) in haystack for term in terms)
    ]


def infer_eras(value: str) -> list[str]:
    value = normalize(value)
    eras: list[str] = []

    def add(era: str) -> None:
        if era not in eras:
            eras.append(era)

    for year_text in re.findall(r"\b(19[5-9]\d|20[0-2]\d)\b", value):
        year = int(year_text)
        if year >= 2020:
            add("2020s")
        elif year >= 2010:
            add("2010s")
        elif year >= 2000:
            add("2000s")
        elif year >= 1990:
            add("1990s")
        else:
            add("pre-1990")

    if re.search(r"\b(current|contemporary|emerging|2020s)\b", value):
        add("2020s")
    if re.search(r"\b(2010s|streaming era)\b", value):
        add("2010s")
    if re.search(r"\b(2000s|aughts)\b", value):
        add("2000s")
    if re.search(r"\b(1990s|90s|nineties)\b", value):
        add("1990s")
    if re.search(r"\b(1980s|80s|1970s|70s|1960s|60s|legacy)\b", value):
        add("pre-1990")

    return eras


def load_images() -> dict[str, str]:
    images: dict[str, str] = {}
    lines = IMAGES_PATH.read_text(encoding="utf-8").splitlines()
    for line in lines[1:]:
        if "\t" not in line:
            continue
        name, url = line.split("\t", 1)
        key = normalize(name)
        if key and url.strip() and key not in images:
            images[key] = url.strip()
    return images


def build() -> dict:
    source = ARTISTS_PATH.read_text(encoding="utf-8")
    image_map = load_images()
    blocks = re.findall(
        r"<details\b[^>]*data-search[^>]*>[\s\S]*?</details>",
        source,
        flags=re.I,
    )

    artists = []
    seen: set[str] = set()

    for block in blocks:
        summary_html = first_match(r"<summary\b[^>]*>([\s\S]*?)</summary>", block)
        if not summary_html:
            continue

        name = clean_text(summary_html)
        name = re.sub(r"\(\s*\d+\s+tracks?\s*\)\s*$", "", name, flags=re.I).strip()
        key = normalize(name)

        if not name or key in seen or key == "ari lennox":
            continue
        seen.add(key)

        bio = clean_text(first_match(r'class="profile-bio"[^>]*>([\s\S]*?)</p>', block))
        location = clean_text(first_match(r'class="profile-location"[^>]*>([\s\S]*?)</p>', block))
        albums = [
            clean_text(item)
            for item in re.findall(r'class="track-album"[^>]*>([\s\S]*?)</div>', block, flags=re.I)
        ][:12]
        track = clean_text(first_match(r'class="track-title"[^>]*>([\s\S]*?)</div>', block))

        profile_href = html_lib.unescape(
            first_match(r'class="artist-page-link"[^>]*href="([^"]+)"', block)
        )

        feature = ""
        for href, label in re.findall(
            r'<a\b[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>',
            block,
            flags=re.I,
        ):
            if re.search(r"northern dial feature", clean_text(label), flags=re.I):
                feature = html_lib.unescape(href)
                break

        signals = " ".join([bio, *albums])
        short_bio = bio
        if len(short_bio) > 190:
            short_bio = re.sub(r"\s+\S*$", "", short_bio[:190]) + "…"

        item = {"name": name}
        if short_bio:
            item["bio"] = short_bio
        if location:
            item["location"] = location
        if track:
            item["track"] = track
        if feature:
            item["feature"] = feature
        if profile_href:
            item["profileHref"] = profile_href

        genres = classify_genres(signals)
        eras = infer_eras(signals)
        image = image_map.get(key, "")

        if genres:
            item["genres"] = genres
        if eras:
            item["eras"] = eras
        if image:
            item["image"] = image

        artists.append(item)

    return {
        "version": 2,
        "count": len(artists),
        "generatedFrom": "artists.html + library_artist_images.tsv",
        "artists": artists,
    }


def main() -> None:
    payload = build()
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Wrote {payload['count']} artists to {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
