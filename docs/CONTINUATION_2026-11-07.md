# Checkpoint — 7 November 2026

Brand: Goli-Coach, without an AI suffix. The Site display title, page metadata, sidebar, header, footer, default CMS content, API title and account email text use this name. Legacy default CMS brand values are normalised on display. Storage identifiers remain compatible with existing device data.

Added owner-created report summary snapshots with 1–168 hour expiry, hashed tokens, optional notes, a ten-active-link limit, owner-only listing/revocation, blocked-owner checks and cascade deletion. Shared summaries exclude raw landmarks, media and account identity. Token transport uses a URL fragment then POST body. Offline restore clears shares; maintenance removes expired shares.

Added browser pose-only WebM export with progress/cancel and supported-browser checks. The export canvas contains a skeleton, timestamp and explanatory text, without original footage/audio. This is a pose replay export, not a blurred original-video export.

Added Dockerfile, Compose, HTTPS proxy and a deployment readiness command plus superadmin-only readiness API. No CPU host, DNS or SMTP credentials were supplied. The currently hosted Site remains static/device-local. Multi-instance Postgres, distributed processing queue, MFA, malware scanning and scheduled encrypted off-host backups remain outstanding.

No consented, annotated Bangladesh cricket dataset has been obtained; actual Bangladesh cricket evaluation remains NOT EVALUATED. Existing evaluation tooling is retained.

Verification: 57 Python API/recovery/maintenance/evaluation/sharing tests and 32 Node tests passed; typecheck and production build passed. Browser preview rendered the new brand, but the demo click did not change state in the preview. Production browser interaction checks follow publication. Docker runtime, real SMTP and end-to-end pose-video download are not verified by these checks.

## Netlify integration continuation

Removed the requested sidebar encouragement card; the journal remains accessible as a simple sidebar-bottom link. Added an optional production-only API proxy built from BACKEND_ORIGIN, exact configured APP_ORIGIN validation on the Python server, and SERVER_VIDEO_ENABLED=0 support to keep inference in the browser behind Netlify. Deploy previews never receive the production API proxy. Hosting accounts and SMTP credentials remain unconnected; these changes do not constitute live activation.

## Free-tier backend continuation

The owner requires no card and no paid resources. The default Render Blueprint now uses Free compute without a disk, requires external PostgreSQL and uses Resend HTTPS email instead of blocked SMTP ports. Added PostgreSQL schema/driver support, a guard against ephemeral hosted SQLite, HTTP email transport and tests. Neon connection was confirmed by the client. Actual project provisioning and live email delivery must be verified separately; credentials are never placed in the repository.
