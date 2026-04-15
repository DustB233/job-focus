# Production Data Hygiene

This repository includes local development demo data, but production must stay live-data only.

## Rules

- Do not run `reset_dev_demo_data` against a production database.
- Do not run `python -m scripts.seed_demo` against a production database.
- Run migrations explicitly before starting the API or worker.
- Configure live sources explicitly with `GREENHOUSE_BOARD_TOKENS` and/or `LEVER_SITE_NAMES`.
- If no live sources are configured, the dashboard should show an honest empty state instead of seeded content.

## Where demo data comes from

- Demo rows are defined in [apps/api/app/services/seeding.py](/C:/Users/admin/Downloads/Job%20Focus/apps/api/app/services/seeding.py:74).
- Local-only reset is exposed through [apps/api/scripts/reset_dev_demo_data.py](/C:/Users/admin/Downloads/Job%20Focus/apps/api/scripts/reset_dev_demo_data.py:1).
- The legacy [apps/api/scripts/seed_demo.py](/C:/Users/admin/Downloads/Job%20Focus/apps/api/scripts/seed_demo.py:1) is also guarded and should be treated as local-development-only.
- Shared frontend demo fixtures still exist in [packages/shared/src/demo/data.ts](/C:/Users/admin/Downloads/Job%20Focus/packages/shared/src/demo/data.ts:3), but the web app no longer imports them at runtime.

## Production-safe startup

1. Set production env vars, including `DATABASE_URL`, `REDIS_URL`, `NEXT_PUBLIC_API_URL`, and any live source identifiers.
2. Run:

```bash
npm run migrate --workspace @job-focus/api
```

3. Start services:

```bash
npm run start --workspace @job-focus/api
npm run start --workspace @job-focus/worker
npm run build --workspace @job-focus/web
npm run start --workspace @job-focus/web
```

## Local-only demo reset

This command is guarded to development/test environments and local databases only:

```bash
npm run reset_dev_demo_data
```

The guard blocks:

- non-local `DATABASE_URL` hosts
- `APP_ENV=production`

## Honest empty states

The dashboard now distinguishes:

- backend unavailable: API fetch fails and the page shows an unavailable state
- no live sources configured: `configuredLiveSourceCount === 0`
- no data yet: live sources are configured, but jobs/matches/applications/source health are still empty

## How to check for old demo rows in production

Do this manually in your managed Postgres console or with `psql`. Do not add an API route for this.

### High-signal checks

```sql
SELECT id, email, created_at
FROM users
WHERE email = 'demo@jobfocus.dev';
```

```sql
SELECT id, company, title, created_at
FROM jobs
WHERE company IN ('Northstar Labs', 'Relay Commerce', 'Meridian AI')
ORDER BY created_at ASC;
```

```sql
SELECT slug, display_name, is_active
FROM job_sources
ORDER BY display_name ASC;
```

If those rows appear in production, the database still contains legacy demo data.

### Broad inspection queries

```sql
SELECT COUNT(*) AS user_count FROM users;
SELECT COUNT(*) AS job_count FROM jobs;
SELECT COUNT(*) AS application_count FROM applications;
SELECT COUNT(*) AS event_count FROM application_events;
```

```sql
SELECT email, created_at
FROM users
ORDER BY created_at ASC
LIMIT 20;
```

```sql
SELECT jobs.company, jobs.title, jobs.external_job_id, jobs.created_at, source.slug
FROM jobs
JOIN job_sources AS source ON source.id = jobs.job_source_id
ORDER BY jobs.created_at ASC
LIMIT 20;
```

### Managed database console guidance

- Render Postgres: open the database dashboard, then use the query console or connect with the internal/external connection string.
- Railway Postgres: open the database service, then use the query editor or connect with the provided connection string.

If production still contains demo rows, remove them manually through your database tooling after confirming you are targeting the correct database. This repository intentionally does not provide a production delete endpoint or auto-delete routine.
