# Live backend and email activation

The owner selected Netlify for the frontend. Follow [Netlify deployment](NETLIFY.md) first. The Render link below remains an optional separate Python host, not the selected frontend deployment.

[Deploy the prepared repository to Render](https://render.com/deploy?repo=https://github.com/emonhossain24/Goli-Coach).

The prepared render.yaml creates a single Docker web service with a persistent 1 GB disk in Singapore. It uses a paid 1 CPU / 2 GB plan. Review the current price in the provider before approving creation. No paid resource has been created by this project update.

The complete web export and FastAPI API run on the same HTTPS origin. The current static review Site does not become an online-account server merely because this file exists. Use the resulting Render origin for the complete app, or connect a custom domain there.

During creation, supply APP_ORIGIN (the bare HTTPS app origin), SMTP_HOST, SMTP_FROM, SMTP_USER and SMTP_PASSWORD. Set SMTP_PORT and SMTP_SECURITY to match the provider; STARTTLS on 587 is the default, or SSL on 465. Store these in the hosting dashboard as secrets, never in GitHub or a chat message. For the selected Netlify frontend, APP_ORIGIN must be the exact production Netlify URL. Set BACKEND_ORIGIN in Netlify to the resulting Python-host origin and redeploy the frontend; the backend is not the public email-link origin. Set SERVER_VIDEO_ENABLED=0 for this proxy deployment. Verified sender/domain setup is managed by your SMTP provider.

The container remains non-root. Check that /data is writable by UID 10001 when the host attaches its disk; do not switch the app to root to hide a permission problem. Keep a single instance and worker with SQLite.

## Verification on the host

1. Run `python -m server.readiness`; all checks must pass.
2. Run `python -m server.check_smtp`; it tests TLS and authentication and sends no mail.
3. Register an owner-controlled test account through the deployed app and confirm actual delivery, the correct link origin, single-use verification and sign-in. Send only to the test account you control.
4. Save a report and journal entry, restart the service, then verify they remain available after signing in. A deployment health response alone does not prove persistence or email delivery.
5. Set up and rehearse the documented backup/restore procedure before real private data is stored.

Render/Railway account access and SMTP configuration are not connected in the current assistant session. Live deployment and delivery cannot be marked complete until these steps run on an authorised host.
