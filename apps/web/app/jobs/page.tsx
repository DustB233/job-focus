import { JobsBoard } from "@/components/dashboard/jobs-board";
import { SourceHealthStrip } from "@/components/dashboard/source-health-strip";
import { LiveDataEmptyStateCard } from "@/components/live-data-empty-state-card";
import { LiveDataUnavailableCard } from "@/components/live-data-unavailable-card";
import { PageShell } from "@/components/page-shell";
import { loadDashboardSnapshot } from "@/lib/dashboard-data";
import { hasConfiguredLiveSources, hasWorkerActivity } from "@/lib/dashboard-presenters";

export default async function JobsPage() {
  const result = await loadDashboardSnapshot();
  const snapshot = result.status === "ready" ? result.snapshot : null;
  const availabilityMessage =
    result.status === "unavailable" ? result.message : "Live jobs data is unavailable.";
  const hasConfiguredSources = snapshot ? hasConfiguredLiveSources(snapshot.tracker) : false;
  const hasTrackerActivity = snapshot ? hasWorkerActivity(snapshot.tracker) : false;
  const hasJobs = snapshot ? snapshot.jobs.length > 0 : false;

  return (
    <PageShell
      activePath="/jobs"
      eyebrow="Jobs Discovered"
      title="Track ATS ingestion, scoring coverage, and source health in one view."
      description="The jobs catalog is normalized across supported sources, with pipeline status and score context layered back onto each role."
      snapshot={snapshot}
      availabilityMessage={result.status === "unavailable" ? result.message : null}
    >
      {snapshot ? (
        hasJobs ? (
          <JobsBoard
            applications={snapshot.applications}
            jobs={snapshot.jobs}
            matches={snapshot.matches}
            sourceHealth={snapshot.sourceHealth}
            tracker={snapshot.tracker}
          />
        ) : hasConfiguredSources ? (
          <div className="section-stack">
            <SourceHealthStrip sourceHealth={snapshot.sourceHealth} tracker={snapshot.tracker} />
            <LiveDataEmptyStateCard
              title="No live jobs discovered yet"
              description="Live sources are configured, but the jobs catalog is still empty."
              hint={
                hasTrackerActivity
                  ? "The worker has run, but no live jobs have been ingested yet."
                  : "Start the worker and verify your configured sources can fetch jobs."
              }
            />
          </div>
        ) : (
          <LiveDataEmptyStateCard
            title="No live sources configured"
            description="There are no configured Greenhouse or Lever sources yet, so the jobs catalog is empty."
            hint="Set GREENHOUSE_BOARD_TOKENS and/or LEVER_SITE_NAMES in both the API and worker environment."
          />
        )
      ) : (
        <LiveDataUnavailableCard title="Jobs unavailable" message={availabilityMessage} />
      )}
    </PageShell>
  );
}
