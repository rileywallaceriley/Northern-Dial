#!/usr/bin/env python3
"""Apply committed artist enrichment to the static artist directory.

This pass does not call the station API. It updates existing researched artist
accordions in artists.html so editorial summaries and full-profile CTAs can
publish even when the live catalogue endpoint is unavailable.
"""

from html import escape
from pathlib import Path
import json
import re
import unicodedata

DIRECTORY_FILE = Path("artists.html")
ENRICHMENT_FILE = Path("artist_enrichment.json")
ENRICHMENT_BATCH_DIR = Path("artist_enrichment_batches")


def slugify(value):
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.casefold()).strip("-")
    return slug or "artist"


def load_enrichments():
    merged = {}
    paths = [ENRICHMENT_FILE]
    paths.extend(sorted(ENRICHMENT_BATCH_DIR.glob("*.json")))
    for path in paths:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            merged.update({str(key).casefold(): value or {} for key, value in data.items()})
    return merged


def render_editorial_text(value):
    """Escape text while allowing paired *release title* emphasis markers."""
    safe = escape(str(value or ""))
    return re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", safe)


def patch_block(name, block, enrichment):
    summary = enrichment.get("directory_summary")
    if summary:
        rendered_summary = render_editorial_text(summary)
        bio_pattern = re.compile(r'<p class="profile-bio">.*?</p>', re.DOTALL)
        if bio_pattern.search(block):
            block = bio_pattern.sub(f'<p class="profile-bio">{rendered_summary}</p>', block, count=1)
            # Directory summaries are intentionally one compact paragraph.
            block = re.sub(r'(<p class="profile-bio">.*?</p>)(?:<p class="profile-bio">.*?</p>)+', r'\1', block, flags=re.DOTALL)

    profile_url = f"./artists/{slugify(name)}.html"
    if "View Full Profile" not in block:
        cta = f'<div class="profile-actions"><a class="request-link" href="{profile_url}">View Full Profile</a></div>\n'
        first_track = re.search(r'<div class="track"\b', block)
        if first_track:
            block = block[:first_track.start()] + cta + block[first_track.start():]
        else:
            block += "\n" + cta
    return block


def main():
    html = DIRECTORY_FILE.read_text(encoding="utf-8")
    enrichments = load_enrichments()
    patched = 0

    for name, enrichment in enrichments.items():
        if not enrichment.get("reviewed") or not enrichment.get("directory_summary"):
            continue
        search_value = re.escape(escape(name.casefold(), quote=True))
        pattern = re.compile(
            rf'(<details data-search="{search_value}">.*?</details>)',
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(html)
        if not match:
            continue
        original = match.group(1)
        updated = patch_block(name, original, enrichment)
        if updated != original:
            html = html[:match.start(1)] + updated + html[match.end(1):]
            patched += 1

    DIRECTORY_FILE.write_text(html, encoding="utf-8")
    print(f"Applied static directory enrichment to {patched} artist accordions.")


if __name__ == "__main__":
    main()
