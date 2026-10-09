#!/usr/bin/env python3
"""Prepare the next eligible Northern Dial artist profiles for French translation."""
from pathlib import Path
import json
import hashlib
import re
from html import unescape
from build_french_artist_pages import load_translations

BATCH_LIMIT = 50
ENRICHMENT_FILE = Path("artist_enrichment.json")
ENRICHMENT_BATCH_DIR = Path("artist_enrichment_batches")
TRANSLATION_BATCH_DIR = Path("artist_translation_batches")
OUTPUT = Path("artist_translation_candidates.json")
OUTPUT_JSONL = Path("artist_translation_candidates.jsonl")

# Known library aliases/metadata artefacts that should not become standalone translations.
EXCLUDED_KEYS = {"adelaide", "in essense", "junia-t"}
ALIAS_MARKERS = (
    "alternate northern dial library credit",
    "split at the ampersand",
    "duplicate library credit",
    "alias library credit",
)


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def merge_enrichment():
    merged = {}
    display_names = {}
    paths = [ENRICHMENT_FILE]
    paths.extend(sorted(ENRICHMENT_BATCH_DIR.glob("*.json")))
    for path in paths:
        data = load_json(path, {})
        if not isinstance(data, dict):
            continue
        for raw_name, value in data.items():
            if not isinstance(value, dict):
                continue
            key = str(raw_name).casefold()
            merged.setdefault(key, {}).update(value)
            display_names[key] = str(value.get("display_name") or display_names.get(key) or raw_name)
    return merged, display_names


def source_bio_sha(bio):
    plain = unescape(re.sub(r"<[^>]+>", "", str(bio or "")))
    return hashlib.sha256(" ".join(plain.split()).encode("utf-8")).hexdigest()


def translation_reason(record, translation):
    if not translation:
        return "missing_translation"
    expected = translation.get("source_bio_sha256")
    if expected and expected != source_bio_sha(record.get("bio")):
        return "english_bio_changed"
    english_words = len(str(record.get("bio") or "").split())
    french_words = len(str(translation.get("bio_fr") or "").split())
    # A screening heuristic, not a linguistic equivalence test. It catches the
    # old one-sentence summaries and sends them for editorial review.
    if english_words and french_words < 0.75 * english_words:
        return "short_translation_review"
    return None


def is_eligible(key, record):
    bio = str(record.get("bio") or "").strip()
    country = str(record.get("country") or "").strip().casefold()
    low_bio = bio.casefold()
    if key in EXCLUDED_KEYS or any(marker in low_bio for marker in ALIAS_MARKERS):
        return False
    return bool(bio) and record.get("reviewed") is True and country == "canada"


def main():
    merged, display_names = merge_enrichment()
    translations, _ = load_translations()
    queue = []
    for key in sorted(merged):
        record = merged[key]
        if not is_eligible(key, record):
            continue
        reason = translation_reason(record, translations.get(key))
        if not reason:
            continue
        queue.append({
            "key": key,
            "reason": reason,
            "source_bio_sha256": source_bio_sha(record.get("bio")),
            "display_name": display_names.get(key, key),
            "bio": record.get("bio", ""),
            "city": record.get("city", ""),
            "country": record.get("country", ""),
            "website": record.get("website", ""),
            "instagram": record.get("instagram", ""),
            "sources": record.get("sources", []),
        })
        if len(queue) >= BATCH_LIMIT:
            break

    OUTPUT.write_text(json.dumps({"batch_limit": BATCH_LIMIT, "candidate_count": len(queue), "candidates": queue}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUTPUT_JSONL.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in queue), encoding="utf-8")
    print(f"Prepared {len(queue)} French translation candidates.")


if __name__ == "__main__":
    main()
