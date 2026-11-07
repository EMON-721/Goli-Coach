# GoliCoach AI

A Bangla-first cricket practice companion. This is implemented source, with a static browser app and an optional private Python server. It is a working baseline, **not a completed V5 production release**.

## Built
- Responsive Bangla/English workspace, original cricket-green visual identity and code-drawn pose illustration.
- Batting/bowling clip flow, consent, segment selection, slow playback, privacy-blurred preview, MediaPipe pose adapter and landmark overlay.
- Image-plane knee angles (aspect-ratio corrected), low-visibility abstention, own-session comparison, manual-review fallback.
- Device-local or signed-in report and journal save/delete, explicit device-to-account copying, JSON and printable PDF reports, six original drills and 18-term glossary.
- Optional authenticated FastAPI endpoint that actually loaded and ran the model. SQLite ownership checks, cookie auth, session-level reports and bilingual drill content.

## Run browser app

```sh
npm ci
node scripts/prepare-assets.mjs
python scripts/download_model.py
npm run dev
```

## Run complete local server

```sh
python -m venv .venv
.venv/bin/pip install -r server/requirements.lock
npm run build
REQUIRE_EMAIL_VERIFICATION=0 SECURE_COOKIES=0 .venv/bin/python server/app.py
```

Open http://127.0.0.1:8000 to use the local server.

## Check

```sh
npm run lint
npm run typecheck
npm test
.venv/bin/python -m pytest tests/test_api.py tests/model_inference_test.py tests/test_bangladesh_evaluation.py tests/test_auth_recovery.py tests/test_maintenance.py -q
npm run build
```

The model smoke harness takes a locally supplied fixture: `.venv/bin/python scripts/evaluate_model.py /path/to/pose.jpg`. It constructs two technical videos, calls the real authenticated endpoint, and compares nonempty versus empty pose output. See docs/MODEL_SMOKE_RESULTS.json for actual measurements. This is not a Bangladesh cricket benchmark.

## Honest availability

The hosted static version uses device-local storage and browser inference; accounts and server inference require the separately run Python server. Cloud provisioning is deferred by the owner. The CMS and signed-in journal were expanded on 29 October; 32 Node and 40 Python checks pass. Desktop layout was inspected, but browser interactions and mobile QA are not marked passed. No Bangladesh training observations were imported. IsolationForest remains untrained; real cricket evaluation needs consented annotated data. See docs/CONTINUATION_2026-10-29.md and docs/APP_ARCHITECTURE.md for exact remaining work.

GitHub target: https://github.com/emonhossain24/Goli-Coach. Generated model/WASM files, secrets, deployment identity and private data are excluded from this repository.

Documentation: docs/USER_GUIDE_BN.md, docs/MODEL_CARD.md, docs/DATASET_REGISTER.md, docs/DEPLOYMENT.md, docs/APP_ARCHITECTURE.md.

## Continuation — 29 October 2026

See [the current checkpoint](docs/CONTINUATION_2026-10-29.md) for completed changes and the exact remaining deployment/data work. Cloud provisioning is deferred at the owner’s request. Source is maintained in EMON-721/Goli-Coach.

## 30 October continuation
Email verification and password recovery (SMTP configuration required), single-use hashed tokens, secure backup/restore and expired-auth cleanup are implemented. See [operations guide](docs/OPERATIONS.md) and [current checkpoint](docs/CONTINUATION_2026-10-30.md). No real email was sent and no cloud service was provisioned. GitHub write access is still blocked by the integration (403).

## Website & repository links

- **Source repository:** https://github.com/emonhossain24/Goli-Coach

