# Northern Dial Direct Mix Email

Status: code prepared, direct email disabled until an SMTP sender and HTTPS backend are configured. No real email has been sent in testing.

## Deploy

Run `backend/mix-email-server.py` with Python 3.11+ on the Northern Dial VPS, as a dedicated system service behind an HTTPS reverse proxy. It listens on localhost port 8787 by default. Keep the SQLite database outside the public website and back it up with restrictive file permissions.

Configure secrets in the service environment, never in Git or browser code:

- `SMTP_HOST`, `SMTP_PORT` (587 STARTTLS or 465 TLS), `SMTP_USER`, `SMTP_PASSWORD`
- `SMTP_FROM`: verified Northern Dial sender address
- `MIX_PUBLIC_URL`: public HTTPS URL of this backend, without `/send-mix`
- `SENDER_CONTACT`: Northern Dial contact information to include in recommendation opt-in emails
- `RATE_SECRET`: random secret for hashing email/IP rate-limit keys
- `MIX_DB`: private persistent path for the SQLite database
- `TRUST_PROXY=1` only when the reverse proxy overwrites `X-Real-IP` and localhost is the sole entry point

Proxy `/send-mix`, `/confirm`, `/unsubscribe` to this service. Require TLS publicly. Set JSON request body maximum to 8 KB. The service permits the Northern Dial production origins only, limits each IP to five attempts per hour, each recipient to one attempt per ten minutes and the pilot to 100 attempts per day. Limits include failed attempts. CORS is not authentication; review hosting-level bot protection before broad promotion.

After validating real delivery to your own test address, change `/mix-config.json` to `{"enabled":true,"endpoint":"https://YOUR-BACKEND/send-mix"}`. Keep the flag false until the service is working. The direct-send form and opt-in remain hidden while false; the existing copy/download/email-app options continue to work.

## Behavior

- The browser retains songs until the SMTP server accepts the send. Provider acceptance is not proof of inbox delivery.
- Successful direct sends remove only the songs in that request. Songs added while sending remain.
- The unchecked recommendation option creates a pending subscriber with the selected artist/song preferences and exact opt-in wording. The mix email contains a confirmation link and unsubscribe link. Only confirmed subscribers are eligible for future campaigns.
- One-off recipients are not added to the subscriber table. Delivery records store request IDs and hashes, not the recipient address or song list.
- Duplicate retries reuse the request ID. A successful retry gets the prior acceptance without sending again. Ambiguous SMTP timeouts remain pending to avoid duplicate emails; an operator must check the mail provider and reconcile those records. Definitive recipient rejection remains pending as well in this initial conservative implementation.
- Pending subscriptions expire after seven days when the next request triggers cleanup. Rate records expire; delivery records are retained seven days. Schedule additional housekeeping if strict expiry without new traffic is required.
- Recommendation campaigns, personalization logic, actual YouTube playlist creation and delivery webhooks are future work. This service does not send recurring newsletters.

Run `python backend/test_mix_email.py` for the validation and simulated-delivery checks. No live SMTP provider is contacted by these tests.
