import type { DashboardSnapshotDTO, SourceHealthDTO, TrackerOverviewDTO } from "@job-focus/shared";

import { formatLabel, formatTimestamp } from "@/lib/dashboard-data";
import {
  hasConfiguredLiveSources,
  hasWorkerActivity,
  isLiveSource,
  sourceHealthSummary,
  toneForSourceHealth
} from "@/lib/dashboard-presenters";

import { Navigation } from "./navigation";
import { StatusBadge } from "./status-badge";

type PageShellProps = {
  activePath: string;
  eyebrow: string;
  title: string;
  description: string;
  snapshot?: DashboardSnapshotDTO | null;
  trackerOverride?: TrackerOverviewDTO | null;
  sourceHealthOverride?: SourceHealthDTO[] | null;
  summaryChips?: React.ReactNode;
  availabilityMessage?: string | null;
  children: React.ReactNode;
};

export function PageShell({
  activePath,
  eyebrow,
  title,
  description,
  snapshot,
  trackerOverride,
  sourceHealthOverride,
  summaryChips,
  availabilityMessage,
  children
}: PageShellProps) {
  const tracker = trackerOverride ?? snapshot?.tracker ?? null;
  const sourceHealth = sourceHealthOverride ?? snapshot?.sourceHealth ?? [];
  const liveSourceHealth = sourceHealth.filter(isLiveSource);
  const healthSummary = snapshot
    ? sourceHealthSummary(sourceHealth, tracker ?? snapshot.tracker)
    : tracker
      ? sourceHealthSummary(sourceHealth, tracker)
    : "Live source health unavailable";

  function formatTrackerValue(value: string | null) {
    if (!tracker) {
      return "unavailable";
    }
    if (!hasConfiguredLiveSources(tracker)) {
      return "not configured";
    }
    return formatTimestamp(value);
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">JF</div>
          <div>
            <h1>Job Focus</h1>
            <p>Automation workspace for sourcing, scoring, packet prep, and applications.</p>
          </div>
        </div>

        <Navigation activePath={activePath} />

        <section className="sidebar-panel" aria-labelledby="tracker-panel-title">
          <div>
            <p className="eyebrow">Worker Tracker</p>
            <h3 id="tracker-panel-title">Freshness snapshot</h3>
          </div>

          <div className="detail-list">
            <div className="detail-row">
              <span>Ingest</span>
              <span className="tracker-note">{formatTrackerValue(tracker?.lastIngestAt ?? null)}</span>
            </div>
            <div className="detail-row">
              <span>Score</span>
              <span className="tracker-note">{formatTrackerValue(tracker?.lastScoreAt ?? null)}</span>
            </div>
            <div className="detail-row">
              <span>Packets</span>
              <span className="tracker-note">{formatTrackerValue(tracker?.lastPacketAt ?? null)}</span>
            </div>
            <div className="detail-row">
              <span>Apply</span>
              <span className="tracker-note">{formatTrackerValue(tracker?.lastApplyAt ?? null)}</span>
            </div>
          </div>

          <p className="sidebar-footnote">
            {!tracker
              ? "Tracker unavailable until the API responds."
              : !hasConfiguredLiveSources(tracker)
                ? "No live sources configured yet."
                : !hasWorkerActivity(tracker)
                  ? "No worker activity has been recorded yet."
                  : `Redis status: ${tracker.redisConnected ? "connected" : "unavailable"}.`}
          </p>
        </section>

        <section className="sidebar-panel" aria-labelledby="source-panel-title">
          <div>
            <p className="eyebrow">Source Health</p>
            <h3 id="source-panel-title">{healthSummary}</h3>
          </div>
          {liveSourceHealth.length > 0 ? (
            <div className="sidebar-health-list">
              {sourceHealth.map((source) => (
                <div key={source.id} className="sidebar-health-item">
                  <span>{source.displayName}</span>
                  <StatusBadge
                    label={formatLabel(source.status)}
                    tone={toneForSourceHealth(source.status)}
                  />
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">
              {tracker && !hasConfiguredLiveSources(tracker)
                ? "No live sources are configured yet."
                : "Live sources are configured, but no source health has been recorded yet."}
            </p>
          )}
        </section>
      </aside>

      <main className="content">
        <section className="hero">
          <div className="eyebrow">{eyebrow}</div>
          <h2>{title}</h2>
          <p>{description}</p>
          {summaryChips ? (
            <div className="hero-band">{summaryChips}</div>
          ) : snapshot ? (
            <div className="hero-band">
              <span className="chip mono">{snapshot.profile.email}</span>
              <span className="chip">{snapshot.profile.location}</span>
              <span className="chip">{snapshot.profile.targetRoles[0] ?? "No target role set"}</span>
              <span className="chip">
                {snapshot.tracker.configuredLiveSourceCount} live source
                {snapshot.tracker.configuredLiveSourceCount === 1 ? "" : "s"} configured
              </span>
              <span className="chip">
                Auto-apply {snapshot.preferences.autoApplyEnabled ? "on" : "off"}
              </span>
            </div>
          ) : (
            <>
              <div className="hero-band">
                <span className="chip">Live API unavailable</span>
                <span className="chip">No demo fallback</span>
              </div>
              {availabilityMessage ? <p className="feedback error">{availabilityMessage}</p> : null}
            </>
          )}
        </section>

        {children}
      </main>
    </div>
  );
}
