# Account email and data operations

## Account verification and recovery
Production defaults to REQUIRE_EMAIL_VERIFICATION=1. Configure APP_ORIGIN as the exact HTTPS origin without a path; SMTP_HOST, SMTP_FROM, SMTP_PORT, SMTP_SECURITY=starttls or ssl, SMTP_USER and SMTP_PASSWORD belong in the hosting secret store. Never commit real values. Clear-text SMTP is rejected.

New registration sends a verification link and does not create an authenticated session until verification and login. Email links use URL fragments, which are not sent as HTTP paths/referrers. The form removes the fragment after reading it. The app never returns a raw token in an API response. Tokens are random, stored as SHA-256 hashes, single-use, expire after 30 minutes, and are rate-limited. A successful password reset revokes all sessions and action tokens for that account. Blocked users cannot redeem links. Existing unverified accounts must verify their email after the upgrade. The console bootstrap tool can confirm the owner only after an explicit operator ownership check.

For loopback development only, REQUIRE_EMAIL_VERIFICATION=0 can be combined with SECURE_COOKIES=0. Do not use those flags in production. Missing mail configuration returns 503 before creating an account. Delivery failures log only account_email_delivery_failed; monitor this event. A recovery request gives the same generic response for unknown and eligible accounts. Configure and verify real SMTP delivery before claiming email works in production; tests use a fake transport and send nothing externally.

API additions:
- POST /api/auth/forgot-password {email}
- POST /api/auth/resend-verification {email}
- POST /api/auth/verify-email {token}
- POST /api/auth/reset-password {token,password}

## Backups and restore rehearsal
Use an operator console, never a public HTTP route. The SQLite backup API produces a consistent snapshot while the database is active. Each backup has integrity checks, a checksum sidecar, table counts and owner-only file permissions. Backup files contain private data: store them outside the public directory, encrypt remote copies, and use a retention policy. Remote encryption/upload/scheduling is not configured by this code.

```sh
python -m server.maintenance backup /private/golicoach.sqlite /private/backups/golicoach-2026-10-30.sqlite
python -m server.maintenance restore /private/backups/golicoach-2026-10-30.sqlite /private/rehearsal.sqlite
```

Backup and restore both refuse an existing destination. Restore validates the checksum and integrity, preserves user data and clears every authentication/session/action token so an old backup cannot resurrect revoked sessions. Inspect the restored database and point a stopped server at it only after an operator checks it. The tool does not swap or overwrite the active database.

## Expired authentication records

```sh
python -m server.maintenance cleanup /private/golicoach.sqlite
python -m server.maintenance cleanup /private/golicoach.sqlite --apply
```

The first command is a dry run. --apply deletes only expired sessions and email-action tokens, never reports, journals, users or audit history. No timer/cron is installed. Configure an operator-owned schedule after choosing the hosting environment.
