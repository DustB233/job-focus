# Job Focus

Monorepo scaffold for a job application automation platform with a Next.js dashboard, FastAPI backend, scheduled Python worker, shared DTO contracts, and local Postgres plus Redis development services.

## Workspace Layout

```text
.
|-- apps
|   |-- api
|   |   |-- alembic/versions
|   |   |-- app
|   |   |   |-- api/routes
|   |   |   |-- core
|   |   |   |-- db
|   |   |   |-- models
|   |   |   |-- repositories
|   |   |   `-- services
|   |   |-- scripts
|   |   |-- tests
|   |   |-- .env.example
|   |   |-- package.json
|   |   `-- pyproject.toml
|   |-- web
|   |   |-- app
|   |   |-- components
|   |   |-- lib
|   |   |-- tests
|   |   |-- .env.example
|   |   |-- package.json
|   |   `-- tsconfig.json
|   `-- worker
|       |-- tests
|       |-- worker
|       |   |-- clients
|       |   `-- tasks
|       |-- .env.example
|       |-- package.json
|       `-- pyproject.toml
|-- infra
|   `-- docker/postgres-init
|-- packages
|   `-- shared
|       |-- python/job_focus_shared
|       |-- src
|       `-- tests
|-- .env.example
|-- docker-compose.yml
|-- package.json
|-- requirements-dev.txt
|-- turbo.json
`-- tsconfig.base.json
```

## Included Scaffolding

- `apps/web`: Next.js App Router dashboard for overview, profile, jobs, matches, and applications.
- `apps/api`: FastAPI service with auth, profile, jobs, matches, applications, tracker, and health endpoints.
- `apps/api/alembic`: database migrations for the normalized application schema.
- `apps/worker`: APScheduler-based worker for Greenhouse and Lever ingestion, scoring, packet generation, direct ATS apply flows, and browser-assisted fallback behind a feature flag.
- `packages/shared`: TypeScript Zod schemas plus Python Pydantic DTOs and enums.
- `docker-compose.yml`: local Postgres and Redis services for development.
- `apps/api/scripts/reset_dev_demo_data.py`: guarded local-only reset script for one demo user, one resume, demo jobs, matches, and one queued application.

## Local Dev Demo Credentials

These only exist after you explicitly reset local development demo data.

- Email: `demo@jobfocus.dev`
- Password: `demo-password`

## Local Development Setup

1. Copy the environment templates you need.

```bash
cp .env.example .env
cp apps/web/.env.example apps/web/.env
cp apps/api/.env.example apps/api/.env
cp apps/worker/.env.example apps/worker/.env
```

2. Start Postgres and Redis.

```bash
docker compose up -d
```

3. Install JavaScript and Python dependencies.

```bash
npm install
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
```

4. Apply database migrations.

```bash
npm run migrate --workspace @job-focus/api
```

5. Optionally reset local development demo data.

```bash
npm run reset_dev_demo_data
```

6. Start everything together, or run services one by one.

```bash
npm run dev
```

```bash
npm run dev --workspace @job-focus/api
npm run dev --workspace @job-focus/web
npm run dev --workspace @job-focus/worker
```

7. Open the dashboard.

- Web: [http://localhost:3000](http://localhost:3000)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: [http://localhost:8000/health](http://localhost:8000/health)

## Useful Commands

```bash
npm run lint
npm run test
npm run build
npm run migrate --workspace @job-focus/api
npm run reset_dev_demo_data
npm run dev:once --workspace @job-focus/worker
```

## Production Startup

Production should never auto-seed demo rows. Run migrations first, then start each service without any demo reset command.

```bash
npm run migrate --workspace @job-focus/api
npm run start --workspace @job-focus/api
npm run start --workspace @job-focus/worker
npm run build --workspace @job-focus/web
npm run start --workspace @job-focus/web
```

See [DEPLOYMENT.md](/C:/Users/admin/Downloads/Job%20Focus/DEPLOYMENT.md) for the hosted Vercel + Render deployment path, production env templates, verification steps, and manual demo-row inspection guidance.

## Worker Source Config

Add board and site identifiers in both `apps/api/.env` and `apps/worker/.env` so the API can report source configuration honestly and the worker can ingest live jobs:

```bash
GREENHOUSE_BOARD_TOKENS=northstar,relay
LEVER_SITE_NAMES=acme,signal-foundry
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

## Browser Assist Mode

Browser-assisted application mode is disabled by default and must be explicitly turned on with:

```bash
BROWSER_ASSIST_ENABLED=true
```

When enabled, unsupported application pages can be opened in Playwright and filled with approved profile, packet, and screening-answer data. The worker stores auth state files in a secure directory outside the repo by default:

- Default auth state directory: `~/.job-focus/browser-auth`
- Default resume upload directory: `data/resumes`

To pre-save an authenticated browser session for a site, run:

```bash
python -m worker.browser_auth_cli --login-url https://example.com/login --state-key manual-example.com
```

The browser assist path is intentionally conservative:

- it uploads resume files when a matching file exists in `BROWSER_RESUME_STORAGE_DIR`
- it stops and returns the application to `waiting_review` if login, MFA, captcha, suspicious security pages, missing required fields, or uncertain confirmation states are detected
- it never auto-submits on LinkedIn or Handshake, even when browser assist is enabled
- Greenhouse and Lever still use the direct ATS adapters first; browser assist is for guarded fallback/manual-link style flows

## API Endpoints

- `POST /api/auth/login`
- `GET /api/profile/me`
- `GET /api/profile/me/resume`
- `GET /api/jobs`
- `GET /api/matches`
- `GET /api/applications`
- `POST /api/applications/{job_id}/apply`
- `GET /api/tracker/overview`
- `GET /health`

## Notes

- Applications move through the state machine `discovered -> shortlisted -> draft_ready -> needs_user_input -> waiting_review -> submitting -> submitted`, with `failed`, `blocked`, and `duplicate` available as exception states.
- The worker fetches Greenhouse and Lever jobs every 30 minutes by default, normalizes them into a common schema, and upserts them with deduplication on `source + external_job_id`.
- Greenhouse and Lever are the only direct ATS auto-apply targets. Every submission attempt writes `application_events`, successful submissions persist confirmation details, failures persist normalized error codes, and already-submitted applications are skipped idempotently.
- Browser-assisted application mode exists behind `BROWSER_ASSIST_ENABLED`, and it is disabled by default.
- LinkedIn and Handshake are placeholder manual-link adapters only. Automated scraping and automated submission are intentionally not implemented.
- The web app no longer falls back to shared demo data. If the API is unavailable, pages render explicit unavailable or empty states.
- The API and worker no longer auto-create tables on startup. Run migrations before starting services.
- Demo reset is development-only and guarded against non-local databases.
- The worker writes task freshness timestamps into Redis so the dashboard tracker can reflect pipeline activity.
- Tests use SQLite so lint and test commands can run without Docker.
