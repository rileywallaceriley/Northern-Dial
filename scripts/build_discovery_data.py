#!/usr/bin/env python3
from __future__ import annotations

import html as html_lib
import json
import re
import unicodedata
try:
    from .discovery_profiles import extract_profile, extract_relationships
except ImportError:
    from discovery_profiles import extract_profile, extract_relationships
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
    # Match complete musical terms, never fragments such as 'rap' in
    # 'Pornographers'. Pop-culture references describe lyrics, not pop music.
    haystack = re.sub(r"\bpop[ -]culture\b", "", normalize(value))
    return [
        key
        for key, terms in GENRES.items()
        if any(re.search(r"(?<!\w)" + re.escape(normalize(term)) + r"(?!\w)", haystack) for term in terms)
    ]


TRAITS = {
    "backburner": r"\bbackburner\b",
    "wordplay": r"\b(wordplay|witty lyricism|playful lyricism|intricate lyricism)\b",
    "humour": r"\b(humou?r|comedic|comedy)\b",
    "underground-rap": r"\bunderground (?:hip[ -]hop|rap)\b",
    "boom-bap": r"\bboom[ -]bap\b",
    "storytelling": r"\b(storytelling|autobiographical|personal writing)\b",
    "turntablism": r"\b(turntablism|turntablist|scratching)\b",
    "abstract-rap": r"\b(abstract rap|experimental hip[ -]hop)\b",
    "neo-soul": r"\bneo[ -]soul\b",
    "trip-hop": r"\btrip[ -]hop\b",
    "downtempo": r"\bdowntempo\b",
    "shoegaze": r"\bshoegaze\b",
    "dream-pop": r"\bdream[ -]pop\b",
    "power-pop": r"\bpower[ -]pop\b",
    "post-punk": r"\bpost[ -]punk\b",
    "synth-pop": r"\b(synth[ -]?pop|electropop)\b",
    "house": r"\bhouse (?:music|producer|production)|\b(?:deep|soulful|dancehall and) house\b",
    "techno": r"\btechno\b",
    "pop-punk": r"\bpop[ -]punk\b",
    "post-hardcore": r"\bpost[ -]hardcore\b",
    "folk-rock": r"\bfolk[ -]rock\b",
}


def classify_traits(value: str) -> list[str]:
    return [key for key, pattern in TRAITS.items() if re.search(pattern, normalize(value))]


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

    removed = {normalize(line) for line in (ROOT / "artist_removals.txt").read_text().splitlines() if line.strip()}
    connections = json.loads((ROOT / "discovery-connections.json").read_text())["connections"]
    artists = []
    seen: set[str] = set()

    for block in blocks:
        summary_html = first_match(r"<summary\b[^>]*>([\s\S]*?)</summary>", block)
        if not summary_html:
            continue

        name = clean_text(summary_html)
        name = re.sub(r"\(\s*\d+\s+tracks?\s*\)\s*$", "", name, flags=re.I).strip()
        key = normalize(name)

        if not name or key in seen or key in removed or key == "ari lennox":
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

        # Album titles and featured artist names are not genre evidence.
        genres = classify_genres(bio)
        eras = infer_eras(signals)
        image = image_map.get(key, "")

        if genres:
            item["genres"] = genres
            intro_genres = classify_genres(re.split(r"(?<=[.!?])\s+", bio)[0])
            item["primaryGenre"] = intro_genres[0] if intro_genres else genres[0]
        traits = classify_traits(bio)
        if traits:
            item["traits"] = traits
        if eras:
            item["eras"] = eras
        if image:
            item["image"] = image

        item["fullBio"] = bio
        item["signals"] = extract_profile(bio, location)
        related = []
        for connection in connections:
            names = connection["artists"]
            if key in [normalize(n) for n in names]:
                other = next(n for n in names if normalize(n) != key)
                related.append({"artist": other, "reason": connection["reason"], "source": connection["source"]})
        if related:
            item["connections"] = related
        artists.append(item)

    automatic = extract_relationships(artists)
    for artist in artists:
        links = artist.setdefault("connections", [])
        known = {normalize(c["artist"]) for c in links}
        for connection in automatic:
            if artist["name"] in connection["artists"]:
                other = next(n for n in connection["artists"] if n != artist["name"])
                if normalize(other) not in known:
                    links.append({"artist":other, **{k:v for k,v in connection.items() if k != "artists"}})
                    known.add(normalize(other))
        artist.pop("fullBio", None)
        for signal in artist["signals"]:
            signal["source"] = artist.get("profileHref") or "/artists.html"
    report = {"artists": len(artists), "automaticRelationships":len(automatic),
        "withSignals":sum(bool(a["signals"]) for a in artists),
        "withConnections":sum(bool(a["connections"]) for a in artists),
        "needsEnrichment":[a["name"] for a in artists if not a["signals"] and not a["connections"]]}
    (ROOT / "data/discovery-quality.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    return {
        "version": 5,
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
