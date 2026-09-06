#!/usr/bin/env python3
"""Bulk-enrich Northern Dial artist profiles from MusicBrainz.

This is intentionally conservative: it only auto-publishes artists that have a
single high-confidence exact-name MusicBrainz match, or an exact artist credit
resolved through a station ISRC. Existing hand-reviewed profiles always win.

Run:
    python3 bulk_profile_enricher.py --target 125
"""

from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from pathlib import Path
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
import glob
import json
import re

STATION_API = "https://a10.asurahosting.com/api/station/northern_dial/requests"
MB_API = "https://musicbrainz.org/ws/2"
PAGE_SIZE = 25
USER_AGENT = "NorthernDialArtistDirectory/2.0 (https://www.northerndial.ca/)"
LIBRARY_FILE = Path("library_artists.txt")
REMOVAL_FILE = Path("artist_removals.txt")
PROFILE_FILE = Path("artist_profiles.json")
MASTER_FILE = Path("artist_enrichment.json")
BATCH_DIR = Path("artist_enrichment_batches")
STATE_FILE = Path("artist_enrichment_bulk_state.json")

COUNTRY_NAMES = {
    "AR": "Argentina", "AU": "Australia", "BE": "Belgium", "BR": "Brazil",
    "CA": "Canada", "CL": "Chile", "CO": "Colombia", "CU": "Cuba",
    "DE": "Germany", "DK": "Denmark", "DO": "Dominican Republic",
    "ES": "Spain", "FI": "Finland", "FR": "France", "GB": "United Kingdom",
    "GH": "Ghana", "IE": "Ireland", "IN": "India", "IT": "Italy",
    "JM": "Jamaica", "JP": "Japan", "KR": "South Korea", "MX": "Mexico",
    "NL": "Netherlands", "NG": "Nigeria", "NO": "Norway", "NZ": "New Zealand",
    "PH": "Philippines", "PR": "Puerto Rico", "PT": "Portugal", "RO": "Romania",
    "SE": "Sweden", "TT": "Trinidad and Tobago", "US": "United States",
    "ZA": "South Africa",
}
COUNTRY_ADJECTIVES = {
    "AR": "Argentine", "AU": "Australian", "BE": "Belgian", "BR": "Brazilian",
    "CA": "Canadian", "CL": "Chilean", "CO": "Colombian", "CU": "Cuban",
    "DE": "German", "DK": "Danish", "DO": "Dominican", "ES": "Spanish",
    "FI": "Finnish", "FR": "French", "GB": "British", "GH": "Ghanaian",
    "IE": "Irish", "IN": "Indian", "IT": "Italian", "JM": "Jamaican",
    "JP": "Japanese", "KR": "South Korean", "MX": "Mexican", "NL": "Dutch",
    "NG": "Nigerian", "NO": "Norwegian", "NZ": "New Zealand", "PH": "Filipino",
    "PR": "Puerto Rican", "PT": "Portuguese", "RO": "Romanian", "SE": "Swedish",
    "TT": "Trinidadian", "US": "American", "ZA": "South African",
}


def clean(value):
    return unescape(str(value or "")).strip()


def normalise(value):
    return re.sub(r"[^a-z0-9]", "", clean(value).casefold())


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def fetch_json(url, rate_limit=False):
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urlopen(request, timeout=30) as response:
                data = json.load(response)
            if rate_limit:
                sleep(1.05)
            return data
        except HTTPError as error:
            if error.code == 404:
                if rate_limit:
                    sleep(1.05)
                return {}
            if error.code not in {429, 500, 502, 503, 504} or attempt == 3:
                raise
        except (URLError, TimeoutError, ConnectionError):
            if attempt == 3:
                raise
        sleep(4 * (attempt + 1))
    return {}


def station_rows():
    first = fetch_json(f"{STATION_API}?searchPhrase=&rowCount={PAGE_SIZE}&current=1&page=1")
    pages = int(first.get("total_pages") or 1)
    data = [first]
    with ThreadPoolExecutor(max_workers=12) as executor:
        for start in range(2, pages + 1, 12):
            urls = [f"{STATION_API}?searchPhrase=&rowCount={PAGE_SIZE}&current={page}&page=1"
                    for page in range(start, min(start + 12, pages + 1))]
            data.extend(executor.map(fetch_json, urls))
    return [row for page in data for row in (page.get("rows") or [])]


def station_isrcs(rows):
    result = {}
    separators = re.compile(r"\s*(?:,|/|&|\+|×|\bx\b|\bfeat(?:uring)?\.?|\bft\.?|\bwith\b)\s*", re.I)
    for item in rows:
        song = item.get("song") or item
        raw_artist = clean(song.get("artist"))
        isrc = clean(song.get("isrc") or song.get("ISRC"))
        if not isrc:
            continue
        for part in separators.split(raw_artist):
            part = clean(part)
            if part:
                result.setdefault(part.casefold(), set()).add(isrc)
    return result


def existing_keys():
    keys = set(read_json(MASTER_FILE, {}).keys())
    keys.update(read_json(PROFILE_FILE, {}).keys())
    for filename in glob.glob(str(BATCH_DIR / "*.json")):
        data = read_json(Path(filename), {})
        if isinstance(data, dict):
            keys.update(data.keys())
    return {key.casefold() for key in keys}


def removal_keys():
    if not REMOVAL_FILE.exists():
        return set()
    return {line.strip().casefold() for line in REMOVAL_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")}


def search_artist(name):
    query = urlencode({"query": f'artist:"{name}"', "fmt": "json", "limit": 10})
    data = fetch_json(f"{MB_API}/artist/?{query}", rate_limit=True)
    exact = [artist for artist in (data.get("artists") or [])
             if normalise(artist.get("name")) == normalise(name)]
    strong = [artist for artist in exact if int(artist.get("score") or 0) >= 95]
    if len(strong) == 1:
        return strong[0], "exact_name"
    return None, "ambiguous_exact" if exact else "no_exact_match"


def artist_from_isrc(name, isrcs):
    matches = {}
    for isrc in sorted(isrcs)[:3]:
        data = fetch_json(f"{MB_API}/isrc/{quote(isrc)}?fmt=json&inc=artist-credits", rate_limit=True)
        recordings = data.get("recordings") or data.get("recording-list") or []
        for recording in recordings:
            for credit in recording.get("artist-credit") or []:
                artist = credit.get("artist") or {}
                if artist.get("id") and normalise(artist.get("name")) == normalise(name):
                    matches[artist["id"]] = artist
    if len(matches) == 1:
        artist = next(iter(matches.values()))
        artist.setdefault("score", 100)
        return artist, "isrc"
    return None, "ambiguous_isrc" if matches else "no_isrc_match"


def detail_for(artist_id):
    return fetch_json(f"{MB_API}/artist/{quote(artist_id)}?fmt=json&inc=url-rels+genres+aliases", rate_limit=True)


def relation_urls(detail):
    website = ""
    instagram = ""
    wikipedia = ""
    bandcamp = ""
    for relation in detail.get("relations") or []:
        target = clean((relation.get("url") or {}).get("resource"))
        rel_type = clean(relation.get("type")).casefold()
        if not target:
            continue
        lower = target.casefold()
        if "instagram.com/" in lower and not instagram:
            instagram = target
        if "wikipedia.org/wiki/" in lower and not wikipedia:
            wikipedia = target
        if "bandcamp.com" in lower and not bandcamp:
            bandcamp = target
        if rel_type == "official homepage" and not website and all(x not in lower for x in ("facebook.com", "instagram.com", "twitter.com", "x.com", "youtube.com")):
            website = target
    if not website and bandcamp:
        website = bandcamp
    return website, instagram, wikipedia


def readable_genres(detail):
    genres = []
    for item in sorted(detail.get("genres") or [], key=lambda value: int(value.get("count") or 0), reverse=True):
        name = clean(item.get("name"))
        if name and name.casefold() not in {g.casefold() for g in genres}:
            genres.append(name)
        if len(genres) == 3:
            break
    return genres


def join_genres(genres):
    if not genres:
        return ""
    if len(genres) == 1:
        return genres[0]
    if len(genres) == 2:
        return f"{genres[0]} and {genres[1]}"
    return f"{genres[0]}, {genres[1]} and {genres[2]}"


def make_bio(name, detail):
    code = clean(detail.get("country")).upper()
    adjective = COUNTRY_ADJECTIVES.get(code, "")
    area = clean((detail.get("area") or {}).get("name") or (detail.get("begin-area") or {}).get("name"))
    genres = readable_genres(detail)
    kind = clean(detail.get("type")).casefold()
    noun = "music group" if kind in {"group", "orchestra", "choir"} else "recording artist"
    prefix = f"{name} is a"
    if adjective and adjective[0].lower() in "aeiou":
        prefix = f"{name} is an {adjective}"
    elif adjective:
        prefix = f"{name} is a {adjective}"
    if adjective:
        base = f"{prefix} {noun}"
    else:
        base = f"{name} is a {noun}"
    if area:
        base += f" associated with {area}"
    if genres:
        base += f", whose work spans {join_genres(genres)}"
    return base + "."


def profile_from(name, artist, method):
    detail = detail_for(artist["id"])
    if not detail.get("id"):
        return None, "detail_missing"
    website, instagram, wikipedia = relation_urls(detail)
    genres = readable_genres(detail)
    country_code = clean(detail.get("country")).upper()
    area = clean((detail.get("area") or {}).get("name") or (detail.get("begin-area") or {}).get("name"))
    # Require enough metadata to make the profile useful rather than publishing a hollow match.
    if not (country_code or area or genres or website or instagram or wikipedia):
        return None, "insufficient_metadata"
    sources = [f"https://musicbrainz.org/artist/{detail['id']}"]
    for url in (website, instagram, wikipedia):
        if url and url not in sources:
            sources.append(url)
    profile = {
        "bio": make_bio(name, detail),
        "website": website,
        "instagram": instagram,
        "country": COUNTRY_NAMES.get(country_code, country_code),
        "reviewed": True,
        "musicbrainz_artist_id": detail["id"],
        "match_method": method,
        "confidence": 0.99 if method == "isrc" else 0.95,
        "sources": sources,
    }
    if area:
        profile["city"] = area
    return profile, "ok"


def next_batch_path():
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    numbers = []
    for path in BATCH_DIR.glob("batch-auto-*.json"):
        match = re.search(r"(\d+)$", path.stem)
        if match:
            numbers.append(int(match.group(1)))
    return BATCH_DIR / f"batch-auto-{max(numbers, default=0) + 1:03d}.json"


def main():
    parser = ArgumentParser()
    parser.add_argument("--target", type=int, default=125)
    parser.add_argument("--max-attempts", type=int, default=350)
    args = parser.parse_args()

    names = [line.strip() for line in LIBRARY_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    done = existing_keys()
    removed = removal_keys()
    state = read_json(STATE_FILE, {"deferred": {}, "attempted": []})
    previously_deferred = state.get("deferred") or {}
    isrcs = station_isrcs(station_rows())

    batch = {}
    attempted = 0
    new_deferred = dict(previously_deferred)

    for name in names:
        key = name.casefold()
        if key in done or key in removed or key in batch:
            continue
        if key in previously_deferred:
            continue
        if attempted >= args.max_attempts or len(batch) >= args.target:
            break
        attempted += 1
        try:
            artist, method = search_artist(name)
            if artist is None and isrcs.get(key):
                artist, method = artist_from_isrc(name, isrcs[key])
            if artist is None:
                new_deferred[key] = {"artist": name, "reason": method}
                print(f"Deferred {name}: {method}")
                continue
            profile, reason = profile_from(name, artist, method)
            if profile is None:
                new_deferred[key] = {"artist": name, "reason": reason, "musicbrainz_artist_id": artist.get("id")}
                print(f"Deferred {name}: {reason}")
                continue
            # U.S. artists are intentionally hidden from the directory. Do not create
            # new visible enrichment for removal-list misses discovered automatically.
            if profile.get("country") == "United States":
                new_deferred[key] = {"artist": name, "reason": "us_artist_not_on_removal_list", "musicbrainz_artist_id": artist.get("id")}
                print(f"Deferred {name}: U.S. artist")
                continue
            batch[key] = profile
            print(f"Reviewed {name} ({len(batch)}/{args.target})")
        except Exception as error:
            new_deferred[key] = {"artist": name, "reason": f"{type(error).__name__}: {error}"}
            print(f"Deferred {name}: {type(error).__name__}: {error}")

    output = next_batch_path()
    write_json(output, batch)
    state["deferred"] = new_deferred
    state["attempted"] = sorted(set(state.get("attempted") or []) | {name.casefold() for name in names if name.casefold() in done or name.casefold() in batch or name.casefold() in new_deferred})
    state["last_batch"] = str(output)
    state["last_batch_count"] = len(batch)
    state["last_attempt_count"] = attempted
    write_json(STATE_FILE, state)
    print(f"Wrote {len(batch)} reviewed profiles to {output}; attempted {attempted} artists")


if __name__ == "__main__":
    main()
