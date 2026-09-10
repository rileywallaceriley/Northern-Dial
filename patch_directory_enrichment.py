#!/usr/bin/env python3
"""Reconcile standalone artist profiles with the static artist directory.

This pass never calls the station API. It makes the existing artists.html
accordions consistent with committed profile/enrichment data so a researched
artist cannot have a standalone page while its directory accordion is missing
its bio, canonical display name, anchor or View Full Profile action.
"""

from html import escape, unescape
from pathlib import Path
import json
import re
import unicodedata

DIRECTORY_FILE = Path("artists.html")
PROFILE_FILE = Path("artist_profiles.json")
ENRICHMENT_FILE = Path("artist_enrichment.json")
ENRICHMENT_BATCH_DIR = Path("artist_enrichment_batches")
DETAIL_PATTERN = re.compile(r"<details\b[^>]*>.*?</details>", re.IGNORECASE | re.DOTALL)
SUMMARY_PATTERN = re.compile(
    r'<summary>(?P<label>.*?)\s*<span class="artist-meta">',
    re.IGNORECASE | re.DOTALL,
)
TAG_PATTERN = re.compile(r"<[^>]+>")
DIV_TOKEN_PATTERN = re.compile(r"<div\b[^>]*>|</div>", re.IGNORECASE)


def slugify(value):
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.casefold()).strip("-")
    return slug or "artist"


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def load_profiles():
    data = load_json(PROFILE_FILE, {})
    return {str(key).casefold(): value for key, value in data.items() if isinstance(value, dict)}


def load_enrichments():
    """Merge enrichment records field-by-field so later small fixes remain safe."""
    merged = {}
    paths = [ENRICHMENT_FILE]
    paths.extend(sorted(ENRICHMENT_BATCH_DIR.glob("*.json")))
    for path in paths:
        if not path.exists():
            continue
        data = load_json(path, {})
        if not isinstance(data, dict):
            continue
        for key, value in data.items():
            normalized = str(key).casefold()
            if isinstance(value, dict):
                merged.setdefault(normalized, {}).update(value)
            else:
                merged[normalized] = value
    return merged


def index_records(records):
    by_name = {}
    by_slug = {}
    for key, value in records.items():
        if not isinstance(value, dict):
            continue
        canonical = value.get("display_name") or value.get("name") or key
        item = (str(key), value)
        by_name[str(key).casefold()] = item
        by_name[str(canonical).casefold()] = item
        by_slug.setdefault(slugify(canonical), item)
        by_slug.setdefault(slugify(key), item)
    return by_name, by_slug


def resolve_record(name, by_name, by_slug):
    return by_name.get(str(name).casefold()) or by_slug.get(slugify(name)) or ("", {})


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


def has_standalone_bio(profile, enrichment):
    return bool(profile.get("bio") or enrichment.get("bio"))


def directory_summary(profile, enrichment):
    return (
        enrichment.get("directory_summary")
        or profile.get("directory_summary")
        or profile.get("bio")
        or enrichment.get("bio")
        or ""
    )


def render_profile(profile, enrichment):
    summary = directory_summary(profile, enrichment)
    if not summary:
        return ""

    album_titles = enrichment.get("album_titles", [])
    summary_html = render_editorial_text(summary, album_titles)
    location = enrichment.get("city") or enrichment.get("country") or profile.get("city") or profile.get("country")
    location_html = f'<p class="profile-location">{escape(str(location))}</p>' if location else ""

    links = []
    website = profile.get("website") or enrichment.get("website")
    instagram = profile.get("instagram") or enrichment.get("instagram")
    if website:
        links.append(f'<a href="{escape(str(website), quote=True)}" target="_blank" rel="noopener">Official site</a>')
    if instagram:
        links.append(f'<a href="{escape(str(instagram), quote=True)}" target="_blank" rel="noopener">Instagram</a>')
    if profile.get("feature"):
        links.append(f'<a href="{escape(str(profile["feature"]), quote=True)}">Northern Dial feature</a>')
    if enrichment.get("musicbrainz_artist_id"):
        mbid = escape(str(enrichment["musicbrainz_artist_id"]), quote=True)
        links.append(f'<a href="https://musicbrainz.org/artist/{mbid}" target="_blank" rel="noopener">MusicBrainz</a>')
    link_html = f'<div class="profile-links">{" · ".join(links)}</div>' if links else ""

    sources = [url for url in enrichment.get("sources", []) if url]
    source_html = ""
    if sources:
        source_links = " · ".join(
            f'<a href="{escape(str(url), quote=True)}" target="_blank" rel="noopener">Source {index}</a>'
            for index, url in enumerate(sources, 1)
        )
        source_html = f'<div class="profile-sources"><span>Sources:</span> {source_links}</div>'

    return (
        '<div class="artist-profile">'
        f'<p class="profile-bio">{summary_html}</p>'
        f'{location_html}{link_html}{source_html}'
        '</div>'
    )


def find_div_span(block, class_name):
    class_pattern = re.compile(
        rf'<div\b[^>]*class="[^"]*\b{re.escape(class_name)}\b[^"]*"[^>]*>',
        re.IGNORECASE,
    )
    start_match = class_pattern.search(block)
    if not start_match:
        return None
    depth = 0
    for token in DIV_TOKEN_PATTERN.finditer(block, start_match.start()):
        if token.group(0).lower().startswith("</div"):
            depth -= 1
        else:
            depth += 1
        if depth == 0:
            return start_match.start(), token.end()
    return None


def remove_divs_by_class(block, class_name):
    while True:
        span = find_div_span(block, class_name)
        if not span:
            return block
        block = block[:span[0]] + block[span[1]:]


def replace_or_insert_profile(block, profile_html):
    span = find_div_span(block, "artist-profile")
    if span:
        return block[:span[0]] + profile_html + block[span[1]:]
    first_track = re.search(r'<div class="track"', block, re.IGNORECASE)
    insert_at = first_track.start() if first_track else block.rfind("</details>")
    return block[:insert_at] + profile_html + "\n" + block[insert_at:]


def normalize_details_opening(block, slug, search_text):
    opening = re.match(r"<details\b(?P<attrs>[^>]*)>", block, re.IGNORECASE | re.DOTALL)
    if not opening:
        return block
    attrs = opening.group("attrs")
    attrs = re.sub(r'\s+(?:id|data-search)="[^"]*"', "", attrs, flags=re.IGNORECASE)
    new_opening = (
        f'<details id="artist-{escape(slug, quote=True)}" '
        f'data-search="{escape(search_text.casefold(), quote=True)}"{attrs}>'
    )
    return new_opening + block[opening.end():]


def canonicalize_summary(block, display_name, profile_url):
    match = SUMMARY_PATTERN.search(block)
    if not match:
        return block
    label = (
        f'<a class="artist-page-link" href="{profile_url}" '
        f'onclick="event.stopPropagation()">{escape(display_name)}</a>'
    )
    return block[:match.start("label")] + label + " " + block[match.end("label"):]


def insert_profile_action(block, profile_url):
    block = remove_divs_by_class(block, "profile-actions")
    cta = (
        '<div class="profile-actions">'
        f'<a class="profile-page-button" href="{profile_url}">View Full Profile</a>'
        '</div>\n'
    )
    first_track = re.search(r'<div class="track"', block, re.IGNORECASE)
    insert_at = first_track.start() if first_track else block.rfind("</details>")
    return block[:insert_at] + cta + block[insert_at:]


def cleanup_legacy_actions(html):
    """Remove old CTA blocks that were accidentally left after </details>."""
    pattern = re.compile(
        r'(</details>)\s*(<div class="profile-actions"[^>]*>.*?</div>)',
        re.IGNORECASE | re.DOTALL,
    )
    previous = None
    while html != previous:
        previous = html
        html = pattern.sub(r'\1\n', html)
    return html


def patch_directory_styles(html):
    """Keep directory controls consistently styled after generated rebuilds."""
    curation_rule = ".curation-links a:not(:first-child) { color:#1a1a1a; }"
    if curation_rule not in html:
        marker = ".curation-links a:first-child { background: #C33; border-color: #C33; color: #fff; }"
        if marker in html:
            html = html.replace(marker, marker + "\n" + curation_rule, 1)

    button_css = """
    .profile-actions { margin:12px 0 16px; }
    .profile-page-button {
      background:#C33;
      border:2px solid #C33;
      border-radius:6px;
      color:#fff;
      display:inline-block;
      font-weight:700;
      padding:9px 13px;
      text-decoration:none;
    }
    .profile-page-button:hover,
    .profile-page-button:focus {
      background:#8B2323;
      border-color:#8B2323;
      color:#fff;
    }
"""
    if ".profile-page-button {" not in html:
        html = html.replace("</style>", button_css + "</style>", 1)
    return html


def main():
    html = DIRECTORY_FILE.read_text(encoding="utf-8")
    html = cleanup_legacy_actions(html)
    html = patch_directory_styles(html)

    profiles = load_profiles()
    enrichments = load_enrichments()
    profile_by_name, profile_by_slug = index_records(profiles)
    enrichment_by_name, enrichment_by_slug = index_records(enrichments)

    stats = {
        "page_backed_accordions": 0,
        "repaired_accordions": 0,
        "canonical_names_changed": 0,
        "missing_directory_blocks": 0,
    }
    seen_slugs = set()

    def reconcile(match):
        original = match.group(0)
        summary_match = SUMMARY_PATTERN.search(original)
        if not summary_match:
            return original
        raw_name = unescape(TAG_PATTERN.sub("", summary_match.group("label"))).strip()
        _, profile = resolve_record(raw_name, profile_by_name, profile_by_slug)
        _, enrichment = resolve_record(raw_name, enrichment_by_name, enrichment_by_slug)
        if not has_standalone_bio(profile, enrichment):
            return original

        stats["page_backed_accordions"] += 1
        display_name = str(
            enrichment.get("display_name")
            or profile.get("display_name")
            or profile.get("name")
            or raw_name
        )
        slug = slugify(display_name)
        seen_slugs.add(slug)
        profile_url = f"./artists/{slug}.html"

        block = original
        block = normalize_details_opening(block, slug, f"{raw_name} {display_name}")
        block = canonicalize_summary(block, display_name, profile_url)
        block = replace_or_insert_profile(block, render_profile(profile, enrichment))
        block = insert_profile_action(block, profile_url)

        if display_name != raw_name:
            stats["canonical_names_changed"] += 1
        if block != original:
            stats["repaired_accordions"] += 1
        return block

    html = DETAIL_PATTERN.sub(reconcile, html)

    problems = []
    for block in DETAIL_PATTERN.findall(html):
        summary_match = SUMMARY_PATTERN.search(block)
        if not summary_match:
            continue
        visible_name = unescape(TAG_PATTERN.sub("", summary_match.group("label"))).strip()
        _, profile = resolve_record(visible_name, profile_by_name, profile_by_slug)
        _, enrichment = resolve_record(visible_name, enrichment_by_name, enrichment_by_slug)
        if not has_standalone_bio(profile, enrichment):
            continue
        display_name = str(enrichment.get("display_name") or profile.get("display_name") or profile.get("name") or visible_name)
        slug = slugify(display_name)
        profile_url = f"./artists/{slug}.html"
        checks = {
            "anchor": f'id="artist-{slug}"' in block,
            "bio": bool(re.search(r'<p class="profile-bio">\s*.+?</p>', block, re.IGNORECASE | re.DOTALL)),
            "name_link": f'href="{profile_url}"' in summary_match.group(0),
            "profile_action": bool(re.search(rf'href="{re.escape(profile_url)}"[^>]*>View Full Profile</a>', block, re.IGNORECASE)),
        }
        missing = [label for label, ok in checks.items() if not ok]
        if missing:
            problems.append({"artist": display_name, "missing": missing})

    DIRECTORY_FILE.write_text(html, encoding="utf-8")

    print(
        "Directory integrity reconciliation: "
        f"{stats['page_backed_accordions']:,} page-backed accordions checked; "
        f"{stats['repaired_accordions']:,} changed; "
        f"{stats['canonical_names_changed']:,} canonical display-name corrections."
    )
    if problems:
        preview = "; ".join(f"{item['artist']}: {', '.join(item['missing'])}" for item in problems[:20])
        raise SystemExit(f"Directory integrity check failed for {len(problems)} artists. {preview}")


if __name__ == "__main__":
    main()
