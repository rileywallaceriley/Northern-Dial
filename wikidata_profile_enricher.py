#!/usr/bin/env python3
"""Bulk-enrich Northern Dial artists from Wikidata structured data.

The matcher is deliberately conservative. It requires an exact artist-name label
and a Wikidata description that clearly identifies a music role. Existing
hand-reviewed/batch profiles and the editorial removal list are skipped.
"""

from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from time import sleep
import glob
import json
import re

API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "NorthernDialArtistDirectory/2.0 (https://www.northerndial.ca/)"
LIBRARY_FILE = Path("library_artists.txt")
REMOVAL_FILE = Path("artist_removals.txt")
PROFILE_FILE = Path("artist_profiles.json")
MASTER_FILE = Path("artist_enrichment.json")
BATCH_DIR = Path("artist_enrichment_batches")
STATE_FILE = Path("artist_enrichment_wikidata_state.json")

MUSIC_TERMS = (
    "singer", "rapper", "musician", "band", "musical group", "music group",
    "record producer", "music producer", "producer and dj", "dj and producer",
    "disc jockey", "songwriter", "composer", "recording artist", "vocalist",
    "instrumentalist", "orchestra", "choir", "hip hop group", "hip-hop group",
    "r&b group", "rock group", "electronic music", "musical duo", "music duo",
    "musical collective", "music collective", "singer-songwriter",
)
US_WORDS = ("american singer", "american rapper", "american musician", "american band",
            "american record producer", "american dj", "american songwriter",
            "united states singer", "united states rapper")


def normalise(value):
    return re.sub(r"[^a-z0-9]", "", str(value or "").casefold())


def api(params, retries=4):
    query = dict(params)
    query.update({"format": "json", "formatversion": "2"})
    url = API + "?" + urlencode(query)
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == retries - 1:
                raise
        except (URLError, TimeoutError, ConnectionError):
            if attempt == retries - 1:
                raise
        sleep(2 * (attempt + 1))
    return {}


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def write_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def existing_keys():
    keys = set(read_json(MASTER_FILE, {}).keys()) | set(read_json(PROFILE_FILE, {}).keys())
    for filename in glob.glob(str(BATCH_DIR / "*.json")):
        data = read_json(Path(filename), {})
        if isinstance(data, dict):
            keys.update(data.keys())
    return {str(key).casefold() for key in keys}


def removed_keys():
    if not REMOVAL_FILE.exists():
        return set()
    return {line.strip().casefold() for line in REMOVAL_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")}


def is_music_description(description):
    text = str(description or "").casefold()
    return any(term in text for term in MUSIC_TERMS)


def search_one(name):
    data = api({
        "action": "wbsearchentities",
        "search": name,
        "language": "en",
        "uselang": "en",
        "type": "item",
        "limit": 8,
    })
    exact = []
    for item in data.get("search") or []:
        label = item.get("label") or ""
        aliases = item.get("aliases") or []
        names = [label] + list(aliases)
        if any(normalise(candidate) == normalise(name) for candidate in names):
            if is_music_description(item.get("description")):
                exact.append(item)
    ids = {item.get("id") for item in exact if item.get("id")}
    if len(ids) != 1:
        return name, None, "ambiguous_exact" if ids else "no_music_exact"
    item = exact[0]
    return name, {"id": item["id"], "description": item.get("description") or ""}, "ok"


def chunks(values, size=50):
    values = list(values)
    for index in range(0, len(values), size):
        yield values[index:index + size]


def fetch_entities(ids):
    result = {}
    for chunk in chunks(ids, 50):
        data = api({
            "action": "wbgetentities",
            "ids": "|".join(chunk),
            "props": "labels|descriptions|claims",
            "languages": "en",
        })
        for entity in data.get("entities") or []:
            if entity.get("id"):
                result[entity["id"]] = entity
    return result


def claim_ids(entity, prop):
    values = []
    for claim in (entity.get("claims") or {}).get(prop, []):
        try:
            value = claim["mainsnak"]["datavalue"]["value"]
            if isinstance(value, dict) and value.get("id"):
                values.append(value["id"])
        except (KeyError, TypeError):
            pass
    return values


def string_claim(entity, prop):
    for claim in (entity.get("claims") or {}).get(prop, []):
        try:
            value = claim["mainsnak"]["datavalue"]["value"]
            if isinstance(value, str) and value.strip():
                return value.strip()
        except (KeyError, TypeError):
            pass
    return ""


def label(entity):
    return ((entity.get("labels") or {}).get("en") or {}).get("value") or ""


def resolve_labels(qids):
    entities = fetch_entities(sorted(set(qids))) if qids else {}
    return {qid: label(entity) for qid, entity in entities.items() if label(entity)}


def artist_role(description):
    desc = re.sub(r"\s*\([^)]*\)\s*$", "", str(description or "").strip())
    if not desc:
        return "recording artist"
    # Wikidata descriptions are CC0; preserve the useful role phrase while
    # normalizing only the initial article/capitalization in the final sentence.
    return desc[0].lower() + desc[1:] if desc else "recording artist"


def genre_phrase(genres):
    genres = [g for g in genres if g][:3]
    if not genres:
        return ""
    if len(genres) == 1:
        return genres[0]
    if len(genres) == 2:
        return f"{genres[0]} and {genres[1]}"
    return f"{genres[0]}, {genres[1]} and {genres[2]}"


def make_bio(name, description, genres):
    role = artist_role(description)
    sentence = f"{name} is a {role}"
    # Avoid awkward double articles for descriptions that already start with one.
    sentence = sentence.replace(" is a an ", " is an ").replace(" is a a ", " is a ")
    phrase = genre_phrase(genres)
    if phrase and phrase.casefold() not in role.casefold():
        sentence += f" whose work is associated with {phrase}"
    return sentence.rstrip(".") + "."


def next_batch_path():
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    nums = []
    for path in BATCH_DIR.glob("batch-wikidata-*.json"):
        match = re.search(r"(\d+)$", path.stem)
        if match:
            nums.append(int(match.group(1)))
    return BATCH_DIR / f"batch-wikidata-{max(nums, default=0) + 1:03d}.json"


def main():
    parser = ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Maximum candidates to search; 0 means all")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()

    done = existing_keys()
    removed = removed_keys()
    names = [line.strip() for line in LIBRARY_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    names = [name for name in names if name.casefold() not in done and name.casefold() not in removed]
    if args.limit:
        names = names[:args.limit]

    matched = {}
    deferred = {}
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(search_one, name): name for name in names}
        for future in as_completed(futures):
            name = futures[future]
            try:
                _, item, reason = future.result()
                if item:
                    matched[name] = item
                else:
                    deferred[name.casefold()] = {"artist": name, "reason": reason}
            except Exception as error:
                deferred[name.casefold()] = {"artist": name, "reason": f"{type(error).__name__}: {error}"}

    print(f"Exact music matches: {len(matched):,} / {len(names):,}")
    entities = fetch_entities([item["id"] for item in matched.values()])

    referenced = set()
    for entity in entities.values():
        for prop in ("P27", "P17", "P19", "P740", "P136", "P106"):
            referenced.update(claim_ids(entity, prop))
    labels = resolve_labels(referenced)

    profiles = {}
    for name, match in matched.items():
        entity = entities.get(match["id"])
        if not entity:
            deferred[name.casefold()] = {"artist": name, "reason": "entity_missing", "wikidata_id": match["id"]}
            continue

        country_ids = claim_ids(entity, "P27") or claim_ids(entity, "P17")
        country_names = [labels.get(qid, "") for qid in country_ids]
        country_names = [value for value in country_names if value]
        description = match.get("description") or (((entity.get("descriptions") or {}).get("en") or {}).get("value") or "")
        if "United States" in country_names or any(term in description.casefold() for term in US_WORDS):
            deferred[name.casefold()] = {"artist": name, "reason": "us_artist_not_on_removal_list", "wikidata_id": match["id"]}
            continue

        place_ids = claim_ids(entity, "P740") or claim_ids(entity, "P19")
        city = labels.get(place_ids[0], "") if place_ids else ""
        genre_names = [labels.get(qid, "") for qid in claim_ids(entity, "P136")]
        genre_names = [value for value in genre_names if value]
        website = string_claim(entity, "P856")
        instagram_user = string_claim(entity, "P2003")
        instagram = f"https://www.instagram.com/{instagram_user.strip('/')}/" if instagram_user else ""

        # Require useful structured metadata beyond just the exact label/description.
        if not (country_names or city or genre_names or website or instagram):
            deferred[name.casefold()] = {"artist": name, "reason": "insufficient_structured_metadata", "wikidata_id": match["id"]}
            continue

        sources = [f"https://www.wikidata.org/wiki/{match['id']}"]
        if website:
            sources.append(website)
        if instagram:
            sources.append(instagram)
        profile = {
            "bio": make_bio(name, description, genre_names),
            "website": website,
            "instagram": instagram,
            "country": country_names[0] if country_names else "",
            "reviewed": True,
            "wikidata_id": match["id"],
            "match_method": "wikidata_exact_music_label",
            "confidence": 0.94,
            "sources": sources,
        }
        if city:
            profile["city"] = city
        profiles[name.casefold()] = profile

    output = next_batch_path()
    write_json(output, profiles)
    write_json(STATE_FILE, {
        "searched": len(names),
        "exact_music_matches": len(matched),
        "published": len(profiles),
        "deferred_count": len(deferred),
        "deferred": deferred,
        "last_batch": str(output),
    })
    print(f"Published {len(profiles):,} profiles to {output}; deferred {len(deferred):,}")


if __name__ == "__main__":
    main()
