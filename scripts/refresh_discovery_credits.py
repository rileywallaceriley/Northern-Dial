#!/usr/bin/env python3
"""Explicit, read-only station-credit refresh; normal builds use the saved snapshot."""
import json
import re
import urllib.request
from datetime import date
from pathlib import Path
from discovery_profiles import normalize, resolve_credit_names

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://a10.asurahosting.com/api/station/northern_dial/requests?limit=1000'

def refresh():
    library = json.loads((ROOT / 'discovery-data.json').read_text())['artists']
    names = {re.sub(r'[^a-z0-9]', '', normalize(n)):a['name']
             for a in library for n in [a['name'], *a.get('aliases', [])]}
    with urllib.request.urlopen(SOURCE, timeout=60) as response:
        rows = json.load(response)
    if not isinstance(rows, list) or not rows:
        raise ValueError('Expected the complete station requests list; snapshot unchanged')
    tracks = []
    for row in rows:
        song = row['song']
        people = resolve_credit_names(song['artist'], names)
        if not people:
            continue
        feature = re.search(r'\b(?:feat\.?|ft\.?|featuring)\s+([^)]*)', song['title'], re.I)
        if feature:
            people = list(dict.fromkeys([*people, *resolve_credit_names(feature[1], names)]))
        if len(people) > 1:
            tracks.append({'requestId':row['request_id'], 'artistCredit':song['artist'],
                           'title':song['title'], 'album':song['album']})
    payload = {'version':1, 'source':SOURCE, 'verifiedOn':date.today().isoformat(), 'tracks':tracks}
    (ROOT / 'discovery-track-credits.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False)+'\n')
    print(f'Saved {len(tracks)} co-artist credits from {len(rows)} station tracks')

if __name__ == '__main__':
    refresh()
