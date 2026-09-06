#!/usr/bin/env python3
"""Report retained Northern Dial artists that still lack a reviewed profile."""

from pathlib import Path
import glob
import json


def load_lines(path):
    file = Path(path)
    if not file.exists():
        return []
    return [
        line.strip()
        for line in file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def load_json(path, default):
    file = Path(path)
    if not file.exists():
        return default
    return json.loads(file.read_text(encoding="utf-8"))


def main():
    artists = load_lines("library_artists.txt")
    removed = {name.casefold() for name in load_lines("artist_removals.txt")}

    reviewed = set()

    profiles = load_json("artist_profiles.json", {})
    reviewed.update(str(key).casefold() for key in profiles)

    enrichment = load_json("artist_enrichment.json", {})
    reviewed.update(
        str(key).casefold()
        for key, value in enrichment.items()
        if isinstance(value, dict) and value.get("reviewed")
    )

    for filename in sorted(glob.glob("artist_enrichment_batches/*.json")):
        batch = load_json(filename, {})
        reviewed.update(
            str(key).casefold()
            for key, value in batch.items()
            if isinstance(value, dict) and value.get("reviewed")
        )

    retained = [name for name in artists if name.casefold() not in removed]
    unresolved = [name for name in retained if name.casefold() not in reviewed]
    enriched = [name for name in retained if name.casefold() in reviewed]

    report = {
        "total_library_artists": len(artists),
        "removed_non_canadian": len([name for name in artists if name.casefold() in removed]),
        "retained_artists": len(retained),
        "retained_with_profiles": len(enriched),
        "retained_without_profiles": len(unresolved),
        "completion_percent": round((len(enriched) / len(retained) * 100), 1) if retained else 100.0,
    }

    Path("artist_enrichment_audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    Path("artist_unresolved.txt").write_text(
        "\n".join(unresolved) + ("\n" if unresolved else ""),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print(f"Wrote {len(unresolved):,} unresolved retained artists to artist_unresolved.txt")


if __name__ == "__main__":
    main()
