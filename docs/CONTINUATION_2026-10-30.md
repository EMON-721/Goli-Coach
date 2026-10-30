# Resume checkpoint — 30 October 2026

Previous application/CMS/journal work was retained. This continuation adds:
- SMTP-ready email verification and password recovery; default verification requirement, 30-minute single-use hashed tokens, resend cooldown, reset session revocation, blocked-user protection and account forms.
- Offline SQLite backup/restore with checksums and integrity validation; restore clears all authentication tokens. A real test database was backed up and restored during tests.
- Dry-run/apply cleanup of expired authentication records; private reports/journals are preserved.
- Dedicated recovery/security/maintenance tests and operational setup guide.

The desktop live-site checks completed at the end of the previous run: BN/EN switching, guest journal save and persistence after reload, demo review/result navigation, bowling drill filtering, drill dialog, Escape dismissal and device-mode account messaging. The older 29 October checkpoint recorded the preview limitation before these live checks; production interactions worked. Mobile, browser video inference and online admin tests are not completed. Auth/SMTP flow is API-tested with a fake mail transport; no real email has been sent.

GitHub access resolved on 30 October: the owner granted integration write access. The complete prepared source was pushed to EMON-721/Goli-Coach main as c572d2f9c566a3cb1f2cfe387a297ed98c4af81c, preserving the initial commit. The remote branch SHA was verified. GitHub Actions started; see the repository Actions tab for its result.

Still externally blocked:
1. Owner previously chose to prepare code and defer cloud provisioning. No different Supabase organisation, CPU host or SMTP provider was supplied. The hosted static Site remains device-local; accounts/admin need the backend online on the same HTTPS origin.
2. No consented, annotated Bangladesh cricket frames were supplied. Evaluation harness exists; actual Bangladesh model evaluation remains NOT EVALUATED. No data was invented or imported.

Other production gaps still apply: managed multi-instance database, real email delivery verification, MFA, async job queue, remote encrypted backups, retention schedule, malware scanning, safe share links and video export. This is not a completed V5 production release.

Verification: 13 newly added recovery/maintenance tests passed; existing API/evaluation tests also passed. The model-file checksum check passed. TypeScript, ESLint and production build were run for this continuation. These checks do not prove live SMTP or cloud hosting.
