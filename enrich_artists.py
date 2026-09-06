#!/usr/bin/env python3
"""Create a reviewable MusicBrainz enrichment file for Northern Dial artists.

The script uses the station feed as its source, matches recordings by ISRC
where available, and falls back to exact artist-name searches. Results are
cached and only reviewed matches are consumed by build_artists.py.

Run:
    python3 enrich_artists.py --limit 50
    python3 enrich_artists.py --all
"""

from argparse import ArgumentParser
from http.client import RemoteDisconnected
from html import unescape
from pathlib import Path
from time import sleep
from urllib.parse import quote, urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
import re


API = "https://a10.asurahosting.com/api/station/northern_dial/requests"
MB_API = "https://musicbrainz.org/ws/2"
CACHE_FILE = Path(".musicbrainz-cache.json")
OUTPUT_FILE = Path("artist_enrichment.json")
REVIEW_FILE = Path("artist_match_review.json")
PROGRESS_FILE = Path(".musicbrainz-progress.json")
PAGE_SIZE = 25
USER_AGENT = "NorthernDialArtistDirectory/1.0 (https://www.northerndial.ca/)"


def clean(value):
    value = unescape(str(value or "")).strip()
    value = re.sub(r"^\s*\d{1,3}\s*[.-]\s*", "", value)
    return value


def normalise(value):
    return re.sub(r"[^a-z0-9]", "", clean(value).casefold())


def api_json(url, cache, refresh=False, rate_limit=True):
    if not refresh and url in cache:
        return cache[url]
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urlopen(request, timeout=30) as response:
                data = json.load(response)
            break
        except (HTTPError, URLError, RemoteDisconnected, TimeoutError, ConnectionError) as error:
            # MusicBrainz returns 404 when an ISRC has no indexed recording.
            # That is an ordinary miss, not a failed pilot; continue to name search.
            if isinstance(error, HTTPError) and error.code == 404 and "/isrc/" in url:
                data = {}
                break
            if isinstance(error, HTTPError) and error.code not in {429, 502, 503, 504}:
                raise
            if attempt == 3:
                raise
            sleep(5 * (attempt + 1))
    cache[url] = data
    if rate_limit:
        sleep(1.1)
    return data


def station_rows():
    first_url = f"{API}?searchPhrase=&rowCount={PAGE_SIZE}&current=1&page=1"
    station_cache = {}
    first = api_json(first_url, station_cache, refresh=True, rate_limit=False)
    pages = int(first.get("total_pages") or 1)
    rows = list(first.get("rows") or [])
    for page in range(2, pages + 1):
        url = f"{API}?searchPhrase=&rowCount={PAGE_SIZE}&current={page}&page=1"
        data = api_json(url, station_cache, refresh=True, rate_limit=False)
        rows.extend(data.get("rows") or [])
    return rows


def artist_names(rows):
    names = {}
    for item in rows:
        song = item.get("song") or item
        raw = clean(song.get("artist"))
        for name in re.split(r"\s*(?:,|/|&|\+|×|\bx\b|\bfeat(?:uring)?\.?|\bft\.?|\bwith\b)\s*", raw, flags=re.I):
            name = clean(name)
            if name:
                names.setdefault(name.casefold(), {"name": name, "isrcs": set()})
        isrc = song.get("isrc") or song.get("ISRC")
        if isrc:
            for record in names.values():
                if normalise(record["name"]) in normalise(raw):
                    record["isrcs"].add(str(isrc).strip())
    return names


def credits(recording):
    result = []
    for credit in recording.get("artist-credit") or []:
        artist = credit.get("artist") or {}
        if artist.get("id"):
            result.append({"id": artist["id"], "name": artist.get("name", "")})
    return result


def write_json(path, value):
    """Write a small checkpoint atomically so an interrupted run is resumable."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def main():
    parser = ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=5,
                        help="Maximum number of unprocessed artists this run handles")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--retry-failed", action="store_true",
                        help="Retry artists that failed in an earlier run")
    args = parser.parse_args()

    cache = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    rows = station_rows()
    artists = artist_names(rows)
    selected = list(artists.values()) if args.all else list(artists.values())[:args.limit]
    enrichment = json.loads(OUTPUT_FILE.read_text()) if OUTPUT_FILE.exists() else {}
    review = json.loads(REVIEW_FILE.read_text()) if REVIEW_FILE.exists() else []
    review_by_key = {item.get("artist", "").casefold(): item for item in review}
    progress = json.loads(PROGRESS_FILE.read_text()) if PROGRESS_FILE.exists() else {
        "completed": [],
        "failed": {},
        "selected_limit": args.limit,
    }
    completed = set(progress.get("completed") or [])
    failed = progress.get("failed") or {}

    pending = []
    for record in selected:
        key = record["name"].casefold()
        if key in completed and not (args.retry_failed and key in failed):
            continue
        if key in failed and not args.retry_failed:
            continue
        pending.append(record)
    batch = pending[:max(1, args.batch_size)]

    if not batch:
        print("No pending artists in this pilot. Use --retry-failed to retry failures.")
        return

    for record in batch:
        name = record["name"]
        try:
            candidates = []
            for isrc in sorted(record["isrcs"]):
                url = f"{MB_API}/isrc/{quote(isrc)}?fmt=json&inc=artist-credits"
                data = api_json(url, cache, args.refresh)
                for recording in data.get("recording-list") or []:
                    candidates.extend(credits(recording))
            if not candidates:
                query = urlencode({"query": f'artist:"{name}"', "fmt": "json", "limit": 10})
                data = api_json(f"{MB_API}/artist/?{query}", cache, args.refresh)
                candidates = [{"id": item.get("id"), "name": item.get("name", "")} for item in data.get("artists") or [] if item.get("id")]
            unique = {candidate["id"]: candidate for candidate in candidates}
            exact = [candidate for candidate in unique.values() if normalise(candidate["name"]) == normalise(name)]
            if len(exact) == 1:
                match = exact[0]
                enrichment[name.casefold()] = {
                    "musicbrainz_artist_id": match["id"],
                    "match_method": "isrc" if record["isrcs"] else "exact_name",
                    "confidence": 0.99 if record["isrcs"] else 0.90,
                    "reviewed": False,
                    "sources": [f"https://musicbrainz.org/artist/{match['id']}"]
                }
            else:
                review_by_key[name.casefold()] = {
                    "artist": name, "isrcs": sorted(record["isrcs"]),
                    "candidates": list(unique.values())
                }
            completed.add(name.casefold())
            failed.pop(name.casefold(), None)
        except Exception as error:
            failed[name.casefold()] = {"artist": name, "error": f"{type(error).__name__}: {error}"}
            print(f"Deferred {name}: {type(error).__name__}: {error}")

        # Checkpoint after every artist, including failures.
        write_json(CACHE_FILE, cache)
        write_json(OUTPUT_FILE, enrichment)
        write_json(REVIEW_FILE, list(review_by_key.values()))
        write_json(PROGRESS_FILE, {
            "completed": sorted(completed),
            "failed": failed,
            "selected_limit": args.limit,
        })
        print(f"Checkpointed {name} ({len(completed)}/{len(selected)} selected)")

    print(f"Processed {len(batch)} artist(s); {len(pending) - len(batch)} remain in this pilot")
    print(f"Candidate matches: {len(enrichment)}; review queue: {len(review_by_key)}; failed: {len(failed)}")


if __name__ == "__main__":
    main()
