import { ApplicationsBoard } from "@/components/dashboard/applications-board";
import { LiveDataEmptyStateCard } from "@/components/live-data-empty-state-card";
import { LiveDataUnavailableCard } from "@/components/live-data-unavailable-card";
import { PageShell } from "@/components/page-shell";
import { loadDashboardSnapshot } from "@/lib/dashboard-data";
import { hasConfiguredLiveSources, hasWorkerActivity } from "@/lib/dashboard-presenters";

export default async function LogsPage() {
  const result = await loadDashboardSnapshot();
  const snapshot = result.status === "ready" ? result.snapshot : null;
  const availabilityMessage =
    result.status === "unavailable" ? result.message : "Live failure log data is unavailable.";
  const hasConfiguredSources = snapshot ? hasConfiguredLiveSources(snapshot.tracker) : false;
  const hasTrackerActivity = snapshot ? hasWorkerActivity(snapshot.tracker) : false;
  const failedApplications = snapshot
    ? snapshot.applications.filter((application) => application.status === "failed")
    : [];

  return (
    <PageShell
      activePath="/logs"
      eyebrow="Failure Logs"
      title="Debug failed submissions with normalized errors and the full event trail."
      description="This view isolates ATS failures so you can inspect packet contents, error codes, and retry context without digging through worker logs."
      snapshot={snapshot}
      availabilityMessage={result.status === "unavailable" ? result.message : null}
    >
      {snapshot ? (
        failedApplications.length > 0 ? (
          <ApplicationsBoard applications={snapshot.applications} mode="failed" />
        ) : hasConfiguredSources ? (
          <LiveDataEmptyStateCard
            title="No failed applications"
            description="There are no live failed submissions to inspect right now."
            hint={
              hasTrackerActivity
                ? "The pipeline is running, but no submission failures have been recorded."
                : "Start the worker after configuring live sources to populate runtime logs."
            }
          />
        ) : (
          <LiveDataEmptyStateCard
            title="No live sources configured"
            description="Failure logs will stay empty until at least one live source is configured."
            hint="Open the Sources page and register at least one Greenhouse board or Lever site."
          />
        )
      ) : (
        <LiveDataUnavailableCard
          title="Failure logs unavailable"
          message={availabilityMessage}
        />
      )}
    </PageShell>
  );
}
