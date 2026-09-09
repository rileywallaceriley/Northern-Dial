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
PROFILE_ACTION_PATTERN = re.compile(
    r'\s*<div class="profile-actions"><a class="request-link" '
    r'href="\./artists/[^"]+">View Full Profile</a></div>\s*',
    re.IGNORECASE,
)


def slugify(value):
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.casefold()).strip("-")
    return slug or "artist"


def load_enrichments():
    """Merge enrichment records field-by-field so partial layers do not erase bios."""
    merged = {}
    paths = [ENRICHMENT_FILE]
    paths.extend(sorted(ENRICHMENT_BATCH_DIR.glob("*.json")))
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
    """Escape editorial copy while emphasizing only verified release titles."""
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


def cleanup_legacy_profile_actions(html):
    """Remove profile CTA blocks left outside accordions by older patch runs."""
    pattern = re.compile(
        r'(</details>)(?:' + PROFILE_ACTION_PATTERN.pattern + r')+',
        re.IGNORECASE,
    )
    return pattern.sub(r'\1\n', html)


def patch_block(name, block, enrichment):
    summary = enrichment.get("directory_summary")
    if summary:
        rendered_summary = render_editorial_text(summary, enrichment.get("album_titles", []))
        bio_pattern = re.compile(r'<p class="profile-bio">.*?</p>', re.DOTALL)
        if bio_pattern.search(block):
            block = bio_pattern.sub(f'<p class="profile-bio">{rendered_summary}</p>', block, count=1)
            block = re.sub(
                r'(<p class="profile-bio">.*?</p>)(?:<p class="profile-bio">.*?</p>)+',
                r'\1',
                block,
                flags=re.DOTALL,
            )

    # Be idempotent: remove any CTA already inside this accordion, then insert
    # exactly one before the first track so it is visible when the accordion opens.
    block = PROFILE_ACTION_PATTERN.sub("\n", block)
    profile_url = f"./artists/{slugify(name)}.html"
    cta = (
        f'<div class="profile-actions"><a class="request-link" href="{profile_url}">'
        'View Full Profile</a></div>\n'
    )
    first_track = re.search(r'<div class="track"\b', block)
    if first_track:
        block = block[:first_track.start()] + cta + block[first_track.start():]
    else:
        block = block.replace("</details>", cta + "</details>", 1)
    return block


def patch_directory_styles(html):
    """Keep outlined curation buttons on-brand instead of browser-link blue."""
    rule = ".curation-links a:not(:first-child) { color:#1a1a1a; }"
    if rule not in html:
        marker = ".curation-links a:first-child { background: #C33; border-color: #C33; color: #fff; }"
        if marker in html:
            html = html.replace(marker, marker + "\n" + rule, 1)
    return html


def main():
    html = DIRECTORY_FILE.read_text(encoding="utf-8")
    html = cleanup_legacy_profile_actions(html)
    html = patch_directory_styles(html)
    enrichments = load_enrichments()
    patched = 0

    for name, enrichment in enrichments.items():
        if not isinstance(enrichment, dict):
            continue
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
