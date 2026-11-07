# Free backend activation with Netlify frontend

[Deploy the prepared free backend](https://render.com/deploy?repo=https://github.com/emonhossain24/Goli-Coach).

The default render.yaml now uses Render Free with no paid disk. Do not enter payment details for the old paid Blueprint. Cancel it, refresh/recreate the Blueprint from the latest main branch and verify that the displayed plan is Free and no disk is listed. Provider anti-abuse verification may vary by account; stop if payment is still required.

## Accounts and persistence

Create a dedicated Neon Free project for Goli-Coach. Copy its TLS PostgreSQL connection string directly into the Render DATABASE_URL secret; never into GitHub or chat. REQUIRE_REMOTE_DATABASE=1 prevents the hosted app from silently saving accounts to temporary SQLite. The application creates its tables on startup. Existing local SQLite data is not automatically transferred; export and plan any real-data migration separately.

Set APP_ORIGIN on Render to the exact production Netlify origin, such as https://golicoach.netlify.app. Set BACKEND_ORIGIN on Netlify to the resulting Render HTTPS origin and redeploy Netlify. Leave NEXT_PUBLIC_API_BASE blank. Production API requests are proxied; previews remain in device mode. SERVER_VIDEO_ENABLED=0 keeps pose inference in the browser and avoids long synchronous video requests through the proxy.

## Email

Render Free blocks outbound SMTP ports 25/465/587. The free Blueprint instead selects MAIL_TRANSPORT=resend, using HTTPS on port 443. Create a Resend Free account and store RESEND_API_KEY and MAIL_FROM as Render secrets. The sender must be allowed/verified by Resend. Its testing sender is restricted to the account owner's address; sending to other users requires the provider's verified-domain setup. A Netlify subdomain alone does not establish ownership of a separate email-sending domain.

No live email is sent by these configuration steps. Registration and password recovery send account-action emails only when the configured user requests them. Validate an owner-controlled account first, including delivery and token redemption, then verify report persistence after a service restart.

## Free-tier limits

Render Free sleeps after 15 idle minutes, can cold-start slowly and is usage-limited. Its filesystem is disposable; the remote database stores user data. No paid instance, disk or expiring Render Free database is declared. Neon and Resend free allowances have their own limits. Free hosting is a hobby/testing setup, not an uptime guarantee.

Use PostgreSQL backups/export procedures from the database provider. The existing server.maintenance SQLite backup command is for local SQLite runs and must not be used as a Neon backup.

References: https://render.com/docs/free ; https://neon.com/pricing ; https://resend.com/pricing ; https://resend.com/docs/api-reference/emails/send-email
