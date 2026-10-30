# Deploy and run

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
