import { ApplicationsBoard } from "@/components/dashboard/applications-board";
import { LiveDataEmptyStateCard } from "@/components/live-data-empty-state-card";
import { LiveDataUnavailableCard } from "@/components/live-data-unavailable-card";
import { PageShell } from "@/components/page-shell";
import { loadDashboardSnapshot } from "@/lib/dashboard-data";
import { hasConfiguredLiveSources, hasWorkerActivity } from "@/lib/dashboard-presenters";

export default async function ApplicationsPage() {
  const result = await loadDashboardSnapshot();
  const snapshot = result.status === "ready" ? result.snapshot : null;
  const availabilityMessage =
    result.status === "unavailable" ? result.message : "Live application data is unavailable.";
  const hasConfiguredSources = snapshot ? hasConfiguredLiveSources(snapshot.tracker) : false;
  const hasTrackerActivity = snapshot ? hasWorkerActivity(snapshot.tracker) : false;
  const hasApplications = snapshot ? snapshot.applications.length > 0 : false;

  return (
    <PageShell
      activePath="/applications"
      eyebrow="Applications Tracker"
      title="Inspect packets, answers, statuses, and event logs without leaving the dashboard."
      description="Every application now carries its packet details, latest ATS outcome, and normalized event trail directly into the web tracker."
      snapshot={snapshot}
      availabilityMessage={result.status === "unavailable" ? result.message : null}
    >
      {snapshot ? (
        hasApplications ? (
          <ApplicationsBoard applications={snapshot.applications} />
        ) : hasConfiguredSources ? (
          <LiveDataEmptyStateCard
            title="No live applications yet"
            description="No applications have been created from live matches yet."
            hint={
              hasTrackerActivity
                ? "The worker has recorded activity, but nothing has reached the application tracker yet."
                : "Start the worker and wait for jobs, matches, and packets to be generated."
            }
          />
        ) : (
          <LiveDataEmptyStateCard
            title="No live sources configured"
            description="No live application pipeline can run until at least one Greenhouse or Lever source is configured."
            hint="Open the Sources page and register at least one Greenhouse board or Lever site."
          />
        )
      ) : (
        <LiveDataUnavailableCard
          title="Applications unavailable"
          message={availabilityMessage}
        />
      )}
    </PageShell>
  );
}
