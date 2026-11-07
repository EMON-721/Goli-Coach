# Deploy and run

For the prepared hosted-server activation path, see [Live backend setup](LIVE_BACKEND_SETUP.md).

## Static site / Vercel

`npm ci`
`node scripts/prepare-assets.mjs`
`python scripts/download_model.py`
`npm run build`

Host out/ as static files; Vercel preset Other, build command `npm run build`, output directory `out`. Asset preparation and model download must run before build, or keep the supplied release artifacts. Browser inference runs on the visitor CPU. Static hosting does NOT run Python, accounts or CMS APIs. No card/payment was entered in this task. No unlimited free-hosting claim.

## Full single-origin private server

Python 3.12: `python -m venv .venv`, install `server/requirements.lock`. Build web first. For loopback HTTP only: `REQUIRE_EMAIL_VERIFICATION=0 SECURE_COOKIES=0 .venv/bin/python server/app.py`. Open http://127.0.0.1:8000. On production HTTPS keep SECURE_COOKIES=1, configure a TLS reverse proxy, persist/backup private/golicoach.sqlite, restrict worker CPU/memory and apply origin/rate limits at ingress. The included server is a private baseline; complete the production gaps in APP_ARCHITECTURE.md before public rollout.

Vercel cannot host this permanent Python CV server as part of an ordinary static export. A separately approved CPU host or VM is required. Prefer same-origin reverse proxy for /api; cross-origin cookie auth is intentionally not enabled. No external backend was provisioned.

Production account verification is enabled by default. Complete the SMTP/APP_ORIGIN setup in OPERATIONS.md before registration. Existing users must verify or be independently verified through the console bootstrap. Keep the application and API on one HTTPS origin.

## Single-host Docker deployment

The Dockerfile builds the Next export and checksummed model, then runs FastAPI as UID 10001. Compose persists SQLite in coach-data, uses a read-only app filesystem and a bounded temporary upload directory, and exposes only Caddy on ports 80/443. Keep one application worker with this SQLite configuration.

Copy .env.example to .env on the chosen host. Set DOMAIN, APP_ORIGIN=https://DOMAIN, and the TLS SMTP settings. Configure DNS to that host, then run `docker compose up --build -d`. The host needs Docker Compose, outbound HTTPS for images/model/packages and SMTP access. No host was provisioned by this change. The container configuration has not been executed in this workspace because Docker is unavailable.

Run `docker compose exec app python -m server.readiness` after deployment. This checks database access, the web export, model checksum, secure cookies and email configuration. It does not prove SMTP delivery; verify delivery with an owner-controlled test account. Keep .env outside source control.

Sharing uses fragment tokens and a POST read request so capability tokens are excluded from HTTP request URLs. Anyone holding a valid link can read the selected summary. Delete the link to revoke it; deleting its report/account also revokes it. Restoring a backup clears shares as well as authentication tokens.
