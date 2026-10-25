#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get("AZURACAST_BASE_URL", "https://a10.asurahosting.com").rstrip("/")
API_KEY = os.environ.get("AZURACAST_API_KEY")
STATION = os.environ.get("AZURACAST_STATION", "northern_dial")
OUTPUT = os.environ.get("AZURACAST_OUTPUT", "azuracast-inventory.json")

if not API_KEY:
    print("AZURACAST_API_KEY is not set", file=sys.stderr)
    sys.exit(2)

url = f"{BASE_URL}/api/station/{STATION}/files"
req = urllib.request.Request(
    url,
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "User-Agent": "Northern-Dial-AzuraCast-Bridge/1.0",
    },
)

try:
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read().decode("utf-8")
        payload = json.loads(raw)
except urllib.error.HTTPError as exc:
    body = exc.read().decode("utf-8", errors="replace")
    print(f"AzuraCast returned HTTP {exc.code}: {body[:1000]}", file=sys.stderr)
    sys.exit(3)
except Exception as exc:
    print(f"AzuraCast request failed: {exc}", file=sys.stderr)
    sys.exit(4)

# Keep the API key out of all outputs. Only the returned media data is written.
with open(OUTPUT, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, ensure_ascii=False, indent=2)

count = len(payload) if isinstance(payload, list) else "unknown"
print(f"Wrote media inventory to {OUTPUT}; entries: {count}")
