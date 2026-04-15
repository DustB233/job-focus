import { LiveDataEmptyStateCard } from "@/components/live-data-empty-state-card";
import { LiveDataUnavailableCard } from "@/components/live-data-unavailable-card";
import { PageShell } from "@/components/page-shell";
import { ShortlistBoard } from "@/components/dashboard/shortlist-board";
import { loadDashboardSnapshot } from "@/lib/dashboard-data";
import { hasConfiguredLiveSources, hasWorkerActivity } from "@/lib/dashboard-presenters";

export default async function ShortlistedPage() {
  const result = await loadDashboardSnapshot();
  const snapshot = result.status === "ready" ? result.snapshot : null;
  const availabilityMessage =
    result.status === "unavailable" ? result.message : "Live shortlist data is unavailable.";
  const hasConfiguredSources = snapshot ? hasConfiguredLiveSources(snapshot.tracker) : false;
  const hasTrackerActivity = snapshot ? hasWorkerActivity(snapshot.tracker) : false;
  const hasMatches = snapshot ? snapshot.matches.length > 0 : false;

  return (
    <PageShell
      activePath="/shortlisted"
      eyebrow="Shortlisted Jobs"
      title="Inspect the strongest roles before spending human review time."
      description="Matches are grouped into a shortlist with score, company, source, and structured why-matched context."
      snapshot={snapshot}
      availabilityMessage={result.status === "unavailable" ? result.message : null}
    >
      {snapshot ? (
        hasMatches ? (
          <ShortlistBoard
            applications={snapshot.applications}
            jobs={snapshot.jobs}
            matches={snapshot.matches}
          />
        ) : hasConfiguredSources ? (
          <LiveDataEmptyStateCard
            title="No live matches yet"
            description="Jobs need to be ingested and scored before this shortlist can populate."
            hint={
              hasTrackerActivity
                ? "The worker has recorded activity, but no matches have been produced yet."
                : "Start the worker after configuring live sources."
            }
          />
        ) : (
          <LiveDataEmptyStateCard
            title="No live sources configured"
            description="There are no configured live sources yet, so no shortlist can be generated."
            hint="Set GREENHOUSE_BOARD_TOKENS and/or LEVER_SITE_NAMES in both the API and worker environment."
          />
        )
      ) : (
        <LiveDataUnavailableCard
          title="Shortlist unavailable"
          message={availabilityMessage}
        />
      )}
    </PageShell>
  );
}
