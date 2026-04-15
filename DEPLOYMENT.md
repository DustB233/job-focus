# Deployment Guide

This repository is ready to deploy as three separate services:

- `apps/web` on Vercel
- `apps/api` on Render
- `apps/worker` on Render

Use managed Render Postgres and Render Key Value for the production datastore layer. The frontend is already live-data only and production startup no longer auto-seeds demo rows.

## Target Architecture

- Web: Vercel project with `apps/web` as the root directory
- API: public Render web service
- Worker: Render background worker
- Database: Render Postgres
- Redis: Render Key Value

The API and worker remain separate services. Do not deploy the worker inside the web or API service.

## Files Added For Deployment

- [render.yaml](/C:/Users/admin/Downloads/Job%20Focus/render.yaml)
- [apps/web/.env.production.example](/C:/Users/admin/Downloads/Job%20Focus/apps/web/.env.production.example)
- [apps/api/.env.production.example](/C:/Users/admin/Downloads/Job%20Focus/apps/api/.env.production.example)
- [apps/worker/.env.production.example](/C:/Users/admin/Downloads/Job%20Focus/apps/worker/.env.production.example)
- [PRODUCTION_DATA_HYGIENE.md](/C:/Users/admin/Downloads/Job%20Focus/PRODUCTION_DATA_HYGIENE.md)

## Production Environment Variables

### Web on Vercel

Create these variables in the Vercel project for `apps/web`:

```bash
NEXT_PUBLIC_API_URL=https://job-focus-api.example.com
```

### API on Render

Create or confirm these variables on the Render API service:

```bash
APP_ENV=production
APP_NAME=Job Focus API
DATABASE_URL=postgresql+psycopg://...
REDIS_URL=redis://...
CORS_ORIGINS=https://job-focus.example.com
GREENHOUSE_BOARD_TOKENS=
LEVER_SITE_NAMES=
```

Notes:

- Render injects `PORT` automatically. The API start command now respects that runtime port.
- `DATABASE_URL` may be provided as `postgres://...`, `postgresql://...`, or `postgresql+psycopg://...`. The app normalizes all Postgres forms to the Psycopg 3 SQLAlchemy dialect internally.
- `CORS_ORIGINS` should contain the production Vercel origin, and any additional trusted web origins, comma-separated.
- Vercel preview deployments use different hostnames than production. Because profile and preference saves use browser-side API calls, either keep verification on the production web domain or explicitly add the preview origin to `CORS_ORIGINS` while testing it.

### Worker on Render

Create or confirm these variables on the Render worker service:

```bash
APP_NAME=Job Focus Worker
DATABASE_URL=postgresql+psycopg://...
REDIS_URL=redis://...
INGEST_INTERVAL_MINUTES=30
SCORE_INTERVAL_MINUTES=15
PACKET_INTERVAL_MINUTES=20
APPLY_INTERVAL_MINUTES=25
AUTO_APPLY_MIN_SCORE=85
GREENHOUSE_BOARD_TOKENS=
LEVER_SITE_NAMES=
SOURCE_REQUEST_TIMEOUT_SECONDS=10
SOURCE_REQUEST_INTERVAL_SECONDS=1
SOURCE_MAX_RETRIES=3
SOURCE_RETRY_BACKOFF_SECONDS=1
ATS_APPLY_TIMEOUT_SECONDS=10
BROWSER_ASSIST_ENABLED=false
BROWSER_FALLBACK_ENABLED=false
BROWSER_HEADLESS=true
BROWSER_AUTH_STATE_DIR=
BROWSER_RESUME_STORAGE_DIR=data/resumes
```

Keep `BROWSER_ASSIST_ENABLED=false` unless you are intentionally enabling browser assist and have provisioned its storage/runtime needs. LinkedIn and Handshake remain manual-only.
The worker accepts the same `DATABASE_URL` forms as the API and normalizes them to Psycopg 3 internally.

## Exact Build, Start, And Migration Commands

### Web on Vercel

Vercel manages startup for Next.js. Set the project root directory to `apps/web`.

- Install command: `npm install`
- Build command: leave the Vercel Next.js default, or use `next build`
- Runtime entrypoint: managed by Vercel

### API on Render

- Build command: `pip install -e ./packages/shared -e ./apps/api`
- Start command: `cd apps/api && python -m scripts.start_api`
- Migration command: `cd apps/api && alembic upgrade head`
- Health check URL: `https://job-focus-api.example.com/health`
- API docs URL: `https://job-focus-api.example.com/docs`

### Worker on Render

- Build command: `pip install -e ./packages/shared -e ./apps/api -e ./apps/worker`
- Start command: `cd apps/worker && python -m worker.main`
- One-off verification command: `cd apps/worker && python -m worker.main --once`

The worker does not expose an HTTP endpoint. Verify it via logs and tracker timestamps surfaced by the API.

## Health And Verification URLs

- Web availability URL: `https://job-focus.example.com/`
- API health URL: `https://job-focus-api.example.com/health`
- API docs URL: `https://job-focus-api.example.com/docs`
- Tracker overview URL: `https://job-focus-api.example.com/api/tracker/overview`
- Source health URL: `https://job-focus-api.example.com/api/tracker/sources`

## Exact Order Of Deployment

1. Provision managed Postgres.
2. Provision managed Redis / Key Value.
3. Create the Render API service and point it at the managed Postgres and Redis instances.
4. Run the API migration command:

```bash
cd apps/api && alembic upgrade head
```

5. Verify the API health endpoint returns database connectivity.
6. Create the Render worker service with the same `DATABASE_URL`, `REDIS_URL`, and live source env vars.
7. Verify the worker starts and logs scheduler startup.
8. Create the Vercel web project with `apps/web` as the root directory.
9. Set `NEXT_PUBLIC_API_URL` in Vercel to the public Render API base URL.
10. Set `CORS_ORIGINS` on the API to the production Vercel web origin.
11. Redeploy the API if `CORS_ORIGINS` changed.
12. Redeploy the web app and confirm live API traffic works.

## Render Blueprint Flow

If you prefer to let Render create the backend stack from the repository:

1. Commit [render.yaml](/C:/Users/admin/Downloads/Job%20Focus/render.yaml).
2. In Render, create a new Blueprint from this repository.
3. Fill the `sync: false` variables in the dashboard:
   - `CORS_ORIGINS`
   - `GREENHOUSE_BOARD_TOKENS`
   - `LEVER_SITE_NAMES`
4. Apply the Blueprint.
5. After the API service exists, confirm the migration command completed successfully.

## Production Data Hygiene

Before go-live, verify whether the current production database still contains old demo rows. Follow the manual checks in [PRODUCTION_DATA_HYGIENE.md](/C:/Users/admin/Downloads/Job%20Focus/PRODUCTION_DATA_HYGIENE.md).

Do not add any production delete endpoint. Do not auto-delete data. Inspect and clean the production database manually if needed.

## System Verification Guide

### 1. Verify the API is up

Open:

- `https://job-focus-api.example.com/health`
- `https://job-focus-api.example.com/docs`

Expected `/health` response shape:

```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok"
}
```

### 2. Verify the worker is up

Check the worker service logs for:

- `Worker scheduler started.`
- `Scheduler started`

Then confirm the API tracker reflects worker activity:

- `https://job-focus-api.example.com/api/tracker/overview`

Expected signals:

- `configuredLiveSourceCount` is greater than `0` when live sources are configured.
- `lastIngestAt`, `lastScoreAt`, `lastPacketAt`, and `lastApplyAt` populate after runs.

### 3. Verify the database is connected

- `/health` returns `"database": "ok"`.
- `/api/tracker/overview` returns without server errors.
- `/api/jobs` returns either real rows or an empty array, not a 500.

### 4. Verify Redis is connected

- `/health` returns `"redis": "ok"`.
- `/api/tracker/overview` returns `"redisConnected": true`.

If Redis is unavailable, the system can still serve API data, but freshness tracking will be degraded.

### 5. Verify source config is present

Check:

- `https://job-focus-api.example.com/api/tracker/overview`
- `https://job-focus-api.example.com/api/tracker/sources`

Expected behavior:

- If no live sources are configured, `configuredLiveSourceCount` is `0` and the web app should say no live sources are configured.
- If live sources are configured but empty, the web app should show empty-but-healthy states instead of demo rows.
- If the API is down, the web app should show unavailable states.

### 6. Verify one live ingest run works

Run a one-off worker pass:

```bash
cd apps/worker && python -m worker.main --once
```

Then verify:

- `/api/tracker/overview` has a recent `lastIngestAt`
- `/api/tracker/sources` shows configured sources
- `/api/jobs` contains discovered rows, or the source notes explain that no jobs were discovered yet
- the Vercel web app reflects the same state without any demo fallback

## Vercel Project Setup

For the `apps/web` project in Vercel:

1. Import the repository.
2. Set the Root Directory to `apps/web`.
3. Set `NEXT_PUBLIC_API_URL` to the public Render API URL.
4. Deploy.

No `vercel.json` is required for the current setup. The frontend is already a standard Next.js App Router app.
