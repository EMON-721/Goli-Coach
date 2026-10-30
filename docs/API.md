# API contract

Same-origin cookie authentication; HTTPS secure HttpOnly strict SameSite cookie. Roles are server-owned. Error JSON uses FastAPI detail. Successful payloads are JSON except static assets. User records never become readable by staff merely because of staff role.

| Route | Method | Access |
|---|---|---|
| /api/health, /api/content, /api/ai/health | GET | Public read-only readiness/content |
| /api/auth/register, /api/auth/login | POST | Anonymous, rate-limited |
| /api/auth/logout | POST | Current cookie |
| /api/me | GET | Signed-in |
| /api/records | GET/POST | Signed-in owner; limit 500 results |
| /api/records/{id} | GET/PATCH/DELETE | Owner only, 404 otherwise |
| /api/account | DELETE | Owner; last superadmin protected |
| /api/ai/analyze | POST multipart | Signed-in, consent=true, allowed media, 50 MB, valid range |
| /api/jobs/{id} | GET | Owner only |
| /api/feedback | POST | Signed-in, 1–2000 chars |
| /api/admin/content | POST | Superadmin/editor/manager; safe known string fields |
| /api/admin/content/publish, /rollback | POST | Superadmin/editor/manager |
| /api/admin/sources | GET/POST | Curator/superadmin; auditors read only |
| /api/admin/models | POST | Superadmin/reviewer |
| /api/admin/users | GET | Superadmin/manager/support; metadata only |
| /api/admin/users/{id} | PATCH | Superadmin role assignment; last-owner gate |
| /api/admin/audit | GET | Superadmin/auditor/manager |
| /api/admin/feedback | GET | Superadmin/support/moderator |

Records upsert by UUID; cross-owner collisions denied. Model jobs are synchronous with persisted states and a 60-second processing budget, not a durable distributed worker queue. Inference can retry with a new job; it is not billed and no video is persisted. Source registration stores metadata only, never fetches URLs (no SSRF). Server OpenAPI at /docs when running FastAPI. Not exposed by static hosting.

## 29 October additions
- GET/POST /api/journal; DELETE /api/journal/{id}: owned notes, UUID, ISO date, nonblank text <=2000; account deletion cascades.
- GET /api/admin/content/revisions: editor roles only; includes draft payloads.
- POST /api/admin/content now returns id. Publish accepts {id}; rollback accepts an archived/superseded {id}. Existing clients may omit the body.
- CMS fields: original text fields plus mission_bn/en, team_bn/en, privacy_bn/en, terms_bn/en; structured faq, drills, navigation. Unknown fields, duplicate IDs and invalid collections are rejected. React renders copy as plain text. Core safety disclosures remain fixed.
- PATCH /api/admin/users/{id}: superadmin only, {role,blocked?}; revokes sessions; protects the final active superadmin.
- PATCH /api/admin/feedback/{id}: support/moderator/superadmin, {status:open|reviewing|resolved}.
- PATCH /api/admin/sources/{id}: curator/superadmin, {state,license_evidence,rights_confirmed}; approval requires evidence and explicit confirmation. No data is imported.
