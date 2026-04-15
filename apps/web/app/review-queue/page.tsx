import { ApplicationsBoard } from "@/components/dashboard/applications-board";
import { LiveDataEmptyStateCard } from "@/components/live-data-empty-state-card";
import { LiveDataUnavailableCard } from "@/components/live-data-unavailable-card";
import { PageShell } from "@/components/page-shell";
import { loadDashboardSnapshot } from "@/lib/dashboard-data";
import { hasConfiguredLiveSources, hasWorkerActivity } from "@/lib/dashboard-presenters";

export default async function ReviewQueuePage() {
  const result = await loadDashboardSnapshot();
  const snapshot = result.status === "ready" ? result.snapshot : null;
  const availabilityMessage =
    result.status === "unavailable" ? result.message : "Live review queue data is unavailable.";
  const hasConfiguredSources = snapshot ? hasConfiguredLiveSources(snapshot.tracker) : false;
  const hasTrackerActivity = snapshot ? hasWorkerActivity(snapshot.tracker) : false;
  const reviewQueue = snapshot
    ? snapshot.applications.filter(
        (application) =>
          application.status === "waiting_review" || application.status === "needs_user_input"
      )
    : [];

  return (
    <PageShell
      activePath="/review-queue"
      eyebrow="Review Queue"
      title="Approve or reject draft applications before the worker submits them."
      description="The queue focuses on packets that still need a human go-ahead, while exposing the full packet payload and event history in the side drawer."
      snapshot={snapshot}
      availabilityMessage={result.status === "unavailable" ? result.message : null}
    >
      {snapshot ? (
        reviewQueue.length > 0 ? (
          <ApplicationsBoard applications={snapshot.applications} mode="review" />
        ) : hasConfiguredSources ? (
          <LiveDataEmptyStateCard
            title="Review queue is empty"
            description="No live applications are waiting for manual review right now."
            hint={
              hasTrackerActivity
                ? "The pipeline is running, but nothing currently needs a manual decision."
                : "Start the worker after configuring live sources."
            }
          />
        ) : (
          <LiveDataEmptyStateCard
            title="No live sources configured"
            description="The review queue will stay empty until at least one live source is configured."
            hint="Set GREENHOUSE_BOARD_TOKENS and/or LEVER_SITE_NAMES in both the API and worker environment."
          />
        )
      ) : (
        <LiveDataUnavailableCard
          title="Review queue unavailable"
          message={availabilityMessage}
        />
      )}
    </PageShell>
  );
}
