# Netlify deployment

Netlify is the selected frontend host. Import `emonhossain24/Goli-Coach` from GitHub and select the `main` branch. The repository's netlify.toml supplies the build settings:

| Setting | Value |
|---|---|
| Base directory | Repository root (leave empty) |
| Build command | `python3 scripts/download_model.py && npm run build` |
| Publish directory | `out` |
| Node | 24 |
| Next runtime plugin | Skipped for this static export |

Next.js already uses `output: 'export'`; do not add the removed `next export` command. Netlify installs npm dependencies before the build. The build downloads the version-pinned model and checks its SHA-256, then copies WASM from the pinned MediaPipe package. The model and WASM are served from the same origin as the app.

Leave NEXT_PUBLIC_API_BASE empty. Do not put SMTP passwords or database credentials into any NEXT_PUBLIC variable. Do not set a wildcard SPA rewrite: it would turn missing API requests into HTML and conceal configuration errors.

## What this deployment runs

The deployed frontend supports browser video analysis, local session history, journal, drills, comparisons, reports and pose replay export. Its health check will detect the absence of the account backend and display device mode.

The existing server/app.py is a persistent Python/FastAPI application with SQLite and optional CPU MediaPipe. Netlify Functions support JavaScript/TypeScript and Go; this Python server is not deployed by netlify.toml. Online accounts, CMS, sharing and SMTP therefore still require the separate Python host, or a separately implemented Netlify-native backend with a managed database. No such migration is claimed by this configuration.

## Connecting the existing backend later

Keep frontend requests on the Netlify origin by adding a narrowly scoped `/api/*` proxy to the actual authorised HTTPS backend after it is deployed. Configure the backend's allowed public origin, email link origin and host-only cookies for the Netlify URL; verify login and CSRF handling end to end before enabling accounts. The existing API's origin boundary currently compares the request Origin with the backend Host, so a proxy rule alone is not sufficient. Do not solve this by disabling origin protection or exposing a database in the browser.

Netlify's external proxy timeout is 26 seconds. Keep pose inference in the browser; the current synchronous Python video endpoint can run longer and must not be assumed to work through this proxy. Large private clip processing needs an asynchronous worker/upload design before being offered on the split deployment.

After deployment, check the homepage, BN/EN switch, demo, drill dialog, camera permission flow and a real local clip. Verify the .task and .wasm assets load. Browser MediaRecorder support varies; test the pose replay download on the target browser.

References: https://nextjs.org/docs/app/guides/static-exports ; https://docs.netlify.com/build/functions/get-started/ ; https://docs.netlify.com/manage/routing/redirects/rewrites-proxies/
