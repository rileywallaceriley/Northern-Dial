#!/usr/bin/env python3
"""Audit Northern Dial artist-directory/profile integrity.

The directory, standalone pages and source data are generated independently
enough that small inconsistencies can otherwise drift in unnoticed. This audit
checks the contract users actually experience: researched directory artists
must have a visible summary, linked name, View Full Profile action, real target
page and working return anchor. It also catches stale/broken local profile
links and duplicate profile UI inside an accordion.
"""

from collections import Counter
from html import unescape
from pathlib import Path
import json
import re

from patch_directory_enrichment import (
    DETAIL_PATTERN,
    SUMMARY_PATTERN,
    TAG_PATTERN,
    has_standalone_bio,
    index_records,
    load_enrichments,
    load_profiles,
    resolve_record,
    slugify,
)

DIRECTORY_FILE = Path("artists.html")
ARTIST_DIR = Path("artists")
REPORT_FILE = Path("artist_directory_integrity_audit.json")
PROFILE_LINK_PATTERN = re.compile(
    r'<a\b[^>]*class="[^"]*\bartist-page-link\b[^"]*"[^>]*href="([^"]+)"[^>]*>',
    re.IGNORECASE,
)
CTA_PATTERN = re.compile(
    r'<a\b[^>]*href="([^"]+)"[^>]*>\s*View Full Profile\s*</a>',
    re.IGNORECASE,
)
BIO_PATTERN = re.compile(
    r'<p\b[^>]*class="[^"]*\bprofile-bio\b[^"]*"[^>]*>\s*(.*?)\s*</p>',
    re.IGNORECASE | re.DOTALL,
)
PROFILE_BLOCK_PATTERN = re.compile(
    r'<div\b[^>]*class="[^"]*\bartist-profile\b[^"]*"',
    re.IGNORECASE,
)
HREF_PATTERN = re.compile(r'<a\b[^>]*href="([^"]+)"', re.IGNORECASE)
DETAIL_OPEN_PATTERN = re.compile(r'^<details\b([^>]*)>', re.IGNORECASE | re.DOTALL)
ID_PATTERN = re.compile(r'\bid="([^"]+)"', re.IGNORECASE)
BACK_LINK_PATTERN = re.compile(
    r'class="[^"]*\bback-link\b[^"]*"[^>]*href="([^"]+)"',
    re.IGNORECASE,
)


def visible_summary_name(block):
    match = SUMMARY_PATTERN.search(block)
    if not match:
        return ""
    return unescape(TAG_PATTERN.sub("", match.group("label"))).strip()


def details_id(block):
    opening = DETAIL_OPEN_PATTERN.search(block)
    if not opening:
        return ""
    match = ID_PATTERN.search(opening.group(1))
    return match.group(1) if match else ""


def expected_record(name, profile_by_name, profile_by_slug, enrichment_by_name, enrichment_by_slug):
    _, profile = resolve_record(name, profile_by_name, profile_by_slug)
    _, enrichment = resolve_record(name, enrichment_by_name, enrichment_by_slug)
    return profile, enrichment


def add_issue(issues, kind, artist, detail):
    issues.append({"type": kind, "artist": artist, "detail": detail})


def main():
    html = DIRECTORY_FILE.read_text(encoding="utf-8")
    profiles = load_profiles()
    enrichments = load_enrichments()
    profile_by_name, profile_by_slug = index_records(profiles)
    enrichment_by_name, enrichment_by_slug = index_records(enrichments)

    issues = []
    stats = Counter()
    directory_anchors = set()
    directory_profile_slugs = set()

    blocks = DETAIL_PATTERN.findall(html)
    stats["directory_accordions"] = len(blocks)

    for block in blocks:
        name = visible_summary_name(block)
        if not name:
            add_issue(issues, "missing_summary_name", "(unknown)", "Accordion has no parseable summary label")
            continue

        did = details_id(block)
        if did:
            directory_anchors.add(did)

        profile, enrichment = expected_record(
            name,
            profile_by_name,
            profile_by_slug,
            enrichment_by_name,
            enrichment_by_slug,
        )
        expected = has_standalone_bio(profile, enrichment)
        profile_links = PROFILE_LINK_PATTERN.findall(block)
        ctas = CTA_PATTERN.findall(block)
        bios = [TAG_PATTERN.sub("", value).strip() for value in BIO_PATTERN.findall(block)]
        profile_blocks = PROFILE_BLOCK_PATTERN.findall(block)

        if expected:
            stats["profile_backed_accordions"] += 1
            display_name = str(
                enrichment.get("display_name")
                or profile.get("display_name")
                or profile.get("name")
                or name
            )
            slug = slugify(display_name)
            directory_profile_slugs.add(slug)
            expected_href = f"./artists/{slug}.html"
            expected_file = ARTIST_DIR / f"{slug}.html"
            expected_anchor = f"artist-{slug}"

            if not any(bios):
                add_issue(issues, "missing_dropdown_bio", display_name, "Profile-backed accordion has no non-empty profile-bio")
            if profile_links != [expected_href]:
                add_issue(issues, "bad_profile_name_link", display_name, f"Expected one {expected_href}; found {profile_links}")
            if ctas != [expected_href]:
                add_issue(issues, "bad_profile_cta", display_name, f"Expected one View Full Profile link to {expected_href}; found {ctas}")
            if did != expected_anchor:
                add_issue(issues, "bad_profile_anchor", display_name, f"Expected id={expected_anchor}; found {did or '(none)'}")
            if not expected_file.is_file():
                add_issue(issues, "missing_profile_file", display_name, str(expected_file))
            if len(profile_blocks) != 1:
                add_issue(issues, "duplicate_or_missing_profile_block", display_name, f"Expected 1 artist-profile block; found {len(profile_blocks)}")

        # Any local artist-page link shown to users must point to a real file,
        # even if source-data matching failed for that accordion.
        for href in profile_links + ctas:
            if not href.startswith("./artists/") or not href.endswith(".html"):
                add_issue(issues, "malformed_local_profile_href", name, href)
                continue
            target = Path(href[2:])
            if not target.is_file():
                add_issue(issues, "broken_local_profile_link", name, href)

    # Catch any additional local artist links outside the expected summary/CTA
    # patterns that point to missing files.
    for href in HREF_PATTERN.findall(html):
        if href.startswith("./artists/") and href.endswith(".html"):
            target = Path(href[2:])
            if not target.is_file():
                add_issue(issues, "broken_local_artist_link_anywhere", "artists.html", href)

    # Standalone pages should return to a real directory anchor when that artist
    # is represented in the current catalogue. Pages absent from the current
    # catalogue may safely link to artists.html without a fragment.
    profile_files = sorted(ARTIST_DIR.glob("*.html"))
    stats["standalone_profile_files"] = len(profile_files)
    for path in profile_files:
        slug = path.stem
        page = path.read_text(encoding="utf-8")
        back_match = BACK_LINK_PATTERN.search(page)
        if not back_match:
            add_issue(issues, "missing_back_link", slug, str(path))
            continue
        href = back_match.group(1)
        if slug in directory_profile_slugs:
            expected_href = f"../artists.html#artist-{slug}"
            if href != expected_href:
                add_issue(issues, "bad_back_link", slug, f"Expected {expected_href}; found {href}")
            elif f"artist-{slug}" not in directory_anchors:
                add_issue(issues, "broken_back_anchor", slug, expected_href)
        else:
            # A page can outlive its current rotation entry. It should not point
            # at an anchor that cannot exist on the current directory.
            if "#artist-" in href:
                add_issue(issues, "orphan_back_anchor", slug, href)

    issue_counts = Counter(issue["type"] for issue in issues)
    report = {
        "directory_accordions": stats["directory_accordions"],
        "profile_backed_accordions": stats["profile_backed_accordions"],
        "standalone_profile_files": stats["standalone_profile_files"],
        "issue_count": len(issues),
        "issue_types": dict(sorted(issue_counts.items())),
        "issues": issues,
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({key: value for key, value in report.items() if key != "issues"}, indent=2))
    if issues:
        print("\nIntegrity defects:")
        for issue in issues[:100]:
            print(f"- {issue['type']}: {issue['artist']} — {issue['detail']}")
        if len(issues) > 100:
            print(f"...and {len(issues) - 100} more. See {REPORT_FILE}.")
        raise SystemExit(f"Artist directory integrity audit failed with {len(issues)} issue(s).")

    print("Artist directory integrity audit passed with zero missing bios or broken profile links.")


if __name__ == "__main__":
    main()
