# Architecture

Next.js 16 + React 19 + TypeScript standard static export. No vinext, Wrangler, Worker runtime, R2 or Supabase dependency. Native Sites is used only to host the static export for owner review. The same source is deployable on Vercel with output directory out.

Browser: 3-step workflow → selected local video → lazy same-origin MediaPipe WASM/weights → sampled landmarks → image-plane metrics → editable notes → device-local report. Demo is explicitly separate and has no fake measurements. Large video bytes are never placed in localStorage. Original videos are not persisted. Reports contain landmark arrays, timestamps and notes. Exports omit videos.

Optional full server: FastAPI serves out/ and /api on one origin. SQLite persists hashed-password users, cookie sessions, owned reports, consent records, jobs, CMS revisions, source metadata, feedback, audit events and model switches. Browser detects /api/health. Without this server, accounts/admin/sync/server inference are honestly unavailable; local reports and browser inference still function. Production deployment of the Python backend is not completed.

Auth: scrypt password hashes, opaque hashed cookie sessions, strict SameSite, HttpOnly, secure cookies by default. Authorisation always derives from server session, never a browser role parameter. Cross-owner records return 404, including for superadmins. CMS fields render as escaped React text. CMS publish/rollback uses DB transactions. Model operation checks require reviewer/superadmin. No backend video persistence beyond temporary inference files.

Operational limits: single-process prototype; in-memory rate limiting is per process. Email verification/reset and local backup/restore rehearsal are implemented as of 30 October; production SMTP remains unconfigured. No distributed queue, MFA, malware scanner, external object storage, remote encrypted backups, retention scheduler, safe share links or managed multi-instance Postgres. Not a public-production security certification.
