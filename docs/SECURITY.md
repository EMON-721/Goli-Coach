# Security boundaries

- Private reports require exact owner id from authenticated cookie; admins cannot override.
- Passwords scrypt-hashed; opaque session tokens hashed in DB; no defaults.
- Strict SameSite cookie, Secure by default, HttpOnly. Origin checks on writes. HTTPS required in production.
- SQLite parameterised queries. CMS fields rendered as escaped React text.
- Temporary video removed on success/failure. Type, dimensions, file size, time-range and processing-time checks. No public media storage.
- Browser reports are unencrypted device-local storage. Shared-device privacy notice is visible. No promise of cross-device sync without backend.
- Model metadata contains no user media; telemetry timing only. Admin audit contains actor/action/target, not raw report text.
- Scope limits: no antivirus/content disarm; upload decoder needs OS/container sandbox in a public deployment. No MFA/email verification/reset. Rate limits are process-local. Database encryption and encrypted backups require host configuration. Security testing is useful evidence, not an audit certification.
