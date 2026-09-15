#!/usr/bin/env python3
"""Shrink artists.html without changing its directory/profile contract.

The artist directory had grown to multiple megabytes because every artist
accordion embedded every track in rotation. This pass keeps the directory
crawlable and keeps profile/bio/actions intact, but only includes a small
preview of tracks per artist. The full station catalogue remains available via
the request/search experience and artist profile pages.
"""

from pathlib import Path
import re

DIRECTORY = Path("artists.html")
MAX_TRACKS_PER_ARTIST = 3

DETAIL_PATTERN = re.compile(r"<details\b[^>]*>.*?</details>", re.IGNORECASE | re.DOTALL)
TRACK_PATTERN = re.compile(
    r'<div\b[^>]*class="[^"]*\btrack\b[^"]*"[^>]*>.*?</div>',
    re.IGNORECASE | re.DOTALL,
)
STYLE_MARKER = "/* ND_ARTIST_DIRECTORY_PAYLOAD_OPTIMIZATION */"


def optimize_details(match):
    block = match.group(0)
    tracks = list(TRACK_PATTERN.finditer(block))
    if len(tracks) <= MAX_TRACKS_PER_ARTIST:
        return block

    keep_until = tracks[MAX_TRACKS_PER_ARTIST - 1].end()
    remove_start = tracks[MAX_TRACKS_PER_ARTIST].start()
    remove_end = tracks[-1].end()
    hidden = len(tracks) - MAX_TRACKS_PER_ARTIST

    note = (
        f'\n<div class="track-overflow-note" aria-label="{hidden} additional tracks in rotation">'
        f'+{hidden} more track{"s" if hidden != 1 else ""} in rotation'
        '</div>'
    )

    # Keep the first few track rows exactly as generated, then replace the rest
    # with a compact count. Everything after the final track stays untouched.
    return block[:keep_until] + note + block[remove_end:]


def add_styles(html):
    if STYLE_MARKER in html:
        return html
    css = f"""
{STYLE_MARKER}
.track-overflow-note {{
  color:#666;
  font-size:.9rem;
  font-weight:700;
  padding:10px 0 4px;
}}
"""
    return html.replace("</style>", css + "</style>", 1)


def main():
    original = DIRECTORY.read_text(encoding="utf-8")
    before_bytes = len(original.encode("utf-8"))
    before_tracks = len(TRACK_PATTERN.findall(original))

    optimized = DETAIL_PATTERN.sub(optimize_details, original)
    optimized = add_styles(optimized)

    after_bytes = len(optimized.encode("utf-8"))
    after_tracks = len(TRACK_PATTERN.findall(optimized))
    DIRECTORY.write_text(optimized, encoding="utf-8")

    saved = before_bytes - after_bytes
    pct = (saved / before_bytes * 100) if before_bytes else 0
    print(
        f"artists.html: {before_bytes:,} -> {after_bytes:,} bytes "
        f"({saved:,} saved, {pct:.1f}% smaller); "
        f"track rows: {before_tracks:,} -> {after_tracks:,}"
    )


if __name__ == "__main__":
    main()
