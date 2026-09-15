# Northern Dial AzuraCast control plane

This branch contains a minimal read-only bridge for querying Northern Dial's AzuraCast media library through GitHub Actions without exposing the AzuraCast API key in the public repository.

## Required GitHub configuration

In the repository settings, add this Actions secret:

- `AZURACAST_API_KEY` — the API key created in AzuraCast.

Optional repository variable:

- `AZURACAST_STATION` — defaults to `northern_dial`. If the hosted AzuraCast installation requires a numeric station ID instead, set this variable to that ID.

The AzuraCast base URL is currently fixed to:

`https://a10.asurahosting.com`

## How the inventory job runs

The workflow can be launched manually from GitHub Actions or automatically whenever `azuracast/request-inventory.txt` changes on this branch.

The job calls:

`GET /api/station/{station}/files`

using the API key as a Bearer token. The response is saved only as a short-lived GitHub Actions artifact named `azuracast-inventory`; it is not committed to the public repository.

## Security note

Do not commit API keys, SFTP credentials or other secrets to this repository. Keep them in GitHub Actions secrets or another server-side secret store.

Before enabling automated media uploads or other write operations, confirm the hosted AzuraCast installation is current. AzuraCast versions at or below 0.23.5 were affected by a 2026 authenticated media-upload path traversal vulnerability; 0.23.6 or newer contains the fix.
