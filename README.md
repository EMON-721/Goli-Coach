# Goli-Coach

Goli-Coach is a Bangla-first cricket practice companion for reviewing batting and bowling movements, keeping training notes and building a regular practice habit.

## Features

- Bangla and English interface with a responsive cricket workspace.
- Local video upload or camera recording, 10–30 second clip selection, slow replay and pose overlays.
- Browser-based MediaPipe pose analysis, approximate knee angles, visibility checks and manual observations.
- Saved sessions, favourites, personal comparisons and a practice journal.
- Device-local storage and optional signed-in report synchronisation, with explicit copying of device records.
- JSON reports, printable PDFs and pose-only WebM replay exports.
- Expiring report-summary links with optional notes and owner-controlled revocation.
- Email accounts, email verification and password recovery.
- Six bilingual practice drills, an 18-term glossary and camera setup guidance.

## How it works

Choose a clip, confirm permission and select the part to review. The browser loads the pose model from the same origin and measures visible body landmarks. Results describe approximate image-plane movement; cricket skill scores require a separately validated model. You can add your observations, compare your own sessions and choose a drill for your next practice.

Original videos stay on the device during browser analysis. Server analysis requires separate consent. Report links contain a selected summary, and pose-video exports contain a drawn skeleton with no original footage or audio.

## Architecture

The interface uses Next.js, React and TypeScript. Browser inference uses MediaPipe Tasks Vision. The optional FastAPI server provides cookie-based accounts and owned reports backed by SQLite. A Docker Compose configuration runs the web export and API on a single HTTPS origin through Caddy.

## Documentation

- [User guide](docs/USER_GUIDE_BN.md)
- [Model and measurement details](docs/MODEL_CARD.md)
- [Data sources](docs/DATASET_REGISTER.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Netlify setup](docs/NETLIFY.md)
- [Operations](docs/OPERATIONS.md)

[Source repository](https://github.com/emonhossain24/Goli-Coach)
