import { LiveDataEmptyStateCard } from "@/components/live-data-empty-state-card";
import { LiveDataUnavailableCard } from "@/components/live-data-unavailable-card";
import { PageShell } from "@/components/page-shell";
import { SectionCard } from "@/components/section-card";
import { StatusBadge } from "@/components/status-badge";
import { SourceHealthStrip } from "@/components/dashboard/source-health-strip";
import {
  buildOverviewMetrics,
  formatLabel,
  formatSalary,
  formatTimestamp,
  loadDashboardSnapshot
} from "@/lib/dashboard-data";
import {
  hasConfiguredLiveSources,
  hasWorkerActivity,
  toneForApplicationStatus,
  toneForMatchStrength
} from "@/lib/dashboard-presenters";

export default async function OverviewPage() {
  const result = await loadDashboardSnapshot();
  const snapshot = result.status === "ready" ? result.snapshot : null;
  const availabilityMessage =
    result.status === "unavailable" ? result.message : "Live dashboard data is unavailable.";
  const metrics = snapshot ? buildOverviewMetrics(snapshot) : [];
  const topMatches = snapshot
    ? snapshot.matches
        .slice()
        .sort((left, right) => right.score - left.score)
        .slice(0, 3)
        .map((match) => ({
          match,
          job: snapshot.jobs.find((job) => job.id === match.jobId) ?? null
        }))
        .filter(
          (
            row
          ): row is {
            match: (typeof snapshot.matches)[number];
            job: (typeof snapshot.jobs)[number];
          } => row.job !== null
        )
    : [];
  const reviewQueue = snapshot
    ? snapshot.applications.filter((application) => application.status === "waiting_review")
    : [];
  const hasConfiguredSources = snapshot ? hasConfiguredLiveSources(snapshot.tracker) : false;
  const hasPipelineData = snapshot
    ? snapshot.jobs.length > 0 || snapshot.matches.length > 0 || snapshot.applications.length > 0
    : false;
  const hasTrackerActivity = snapshot ? hasWorkerActivity(snapshot.tracker) : false;

  return (
    <PageShell
      activePath="/"
      eyebrow="Overview"
      title="Run the application engine like an admin console."
      description="The dashboard now surfaces profile setup, source health, shortlist quality, packet review, and failed submission logs from the same shared contracts."
      snapshot={snapshot}
      availabilityMessage={result.status === "unavailable" ? result.message : null}
    >
      {snapshot ? (
        hasPipelineData ? (
          <>
            <section className="metrics-grid">
              {metrics.map((metric) => (
                <article key={metric.label} className="card">
                  <div className="metric-label">{metric.label}</div>
                  <div className="metric-value">{metric.value}</div>
                  <div className="muted">{metric.detail}</div>
                </article>
              ))}
            </section>

            <SourceHealthStrip sourceHealth={snapshot.sourceHealth} tracker={snapshot.tracker} />

            <section className="split-grid">
              <SectionCard title="Top matches" subtitle="Highest scoring roles from the matching engine">
                <div className="card-stack">
                  {topMatches.map(({ match, job }) => (
                    <article key={match.id} className="subcard">
                      <div className="job-headline">
                        <div className="section-stack">
                          <h4>{job.title}</h4>
                          <span className="muted">{job.company}</span>
                        </div>
                        <StatusBadge
                          label={`${match.score}/100`}
                          tone={toneForMatchStrength(match.strength)}
                        />
                      </div>
                      <p className="muted">{match.rationale}</p>
                      <div className="job-meta">
                        <span className="chip">{formatLabel(job.source)}</span>
                        <span className="chip">{job.location}</span>
                        <span className="chip mono">{formatSalary(job)}</span>
                      </div>
                    </article>
                  ))}
                  {topMatches.length === 0 ? (
                    <p className="muted">No live matches have been scored yet.</p>
                  ) : null}
                </div>
              </SectionCard>

              <SectionCard title="Review queue" subtitle="Applications waiting on a manual decision">
                <div className="card-stack">
                  {reviewQueue.map((application) => (
                    <article key={application.id} className="subcard">
                      <div className="job-headline">
                        <div className="section-stack">
                          <h4>{application.job.title}</h4>
                          <span className="muted">{application.job.company}</span>
                        </div>
                        <StatusBadge
                          label={formatLabel(application.status)}
                          tone={toneForApplicationStatus(application.status)}
                        />
                      </div>
                      <p className="muted">{application.notes}</p>
                      <div className="detail-list compact">
                        <div className="detail-row">
                          <span>Packet</span>
                          <strong>{formatLabel(application.packetStatus ?? "none")}</strong>
                        </div>
                        <div className="detail-row">
                          <span>Updated</span>
                          <strong>{formatTimestamp(application.updatedAt)}</strong>
                        </div>
                      </div>
                    </article>
                  ))}
                  {reviewQueue.length === 0 ? (
                    <p className="muted">Nothing is waiting for manual review right now.</p>
                  ) : null}
                </div>
              </SectionCard>
            </section>
          </>
        ) : (
          <LiveDataEmptyStateCard
            title={hasConfiguredSources ? "No live pipeline data yet" : "No live sources configured"}
            description={
              hasConfiguredSources
                ? "Live sources are configured, but there are no jobs, matches, or applications in the database yet."
                : "The backend is available, but no Greenhouse or Lever sources are configured yet."
            }
            hint={
              hasConfiguredSources
                ? hasTrackerActivity
                  ? "The worker has recorded activity, but no live records have been discovered yet."
                  : "Start the worker and verify the configured sources can fetch jobs."
                : "Set GREENHOUSE_BOARD_TOKENS and/or LEVER_SITE_NAMES in both the API and worker environment, then start the worker."
            }
          />
        )
      ) : (
        <LiveDataUnavailableCard
          title="Overview unavailable"
          message={availabilityMessage}
        />
      )}
    </PageShell>
  );
}
