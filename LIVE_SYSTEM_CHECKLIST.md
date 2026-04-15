# Live System Checklist

Use this checklist after starting the API, worker, and web app. Mark each item `PASS` or `FAIL`.

| Check | PASS criteria | FAIL criteria |
| --- | --- | --- |
| Homepage uses live API data | `/` loads counts, top matches, review queue, and source health from the running API. Stopping the API shows an unavailable state instead of seeded/demo content. | The page still shows realistic sample jobs, matches, or tracker data after the API is stopped. |
| Jobs page uses live API data | `/jobs` reflects current database records and source health. Filtering changes the visible live rows only. | The page renders example jobs when `/api/jobs` is unavailable or empty. |
| Tracker uses live API data | Sidebar freshness and `/api/tracker/overview` values match the API response. Redis outages show unavailable tracker data, not fake timestamps. | Tracker timestamps or Redis state are invented when the backend is unavailable. |
| Profile save persists to the database | Saving `/profile` updates the database and the refreshed page shows the saved values from `/api/profile/me`. | The save button appears successful, but a refresh reverts to old values or local-only state. |
| Preferences save persists to the database | Saving `/preferences` updates `/api/profile/me/preferences` and the refreshed page shows the stored values. | The page shows the edited values without the database actually changing. |
| Approve/reject actions persist correctly | Approve on `/review-queue` moves the application to `submitting`, then the worker can process it. Reject moves it to `blocked`, and both actions append application events. | The row changes visually without database status/event updates, or approved items never reach the worker queue. |
| No page silently falls back to demo data | Any API outage or missing dependency produces a clear unavailable or empty state across `/`, `/jobs`, `/shortlisted`, `/applications`, `/review-queue`, `/logs`, `/profile`, and `/preferences`. | Any page quietly swaps to hardcoded sample content when the API is unreachable. |

## Suggested verification steps

1. Start the API, worker, and web app with the same database URL.
2. Open the dashboard pages and confirm they load with current database content.
3. Stop the API and refresh each page once.
4. Confirm every page shows an unavailable state and no sample data appears.
5. Restart the API and verify the pages recover to live data.
