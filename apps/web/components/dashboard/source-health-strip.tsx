import type { SourceHealthDTO, TrackerOverviewDTO } from "@job-focus/shared";

import { formatDate, formatLabel } from "@/lib/dashboard-data";
import {
  hasConfiguredLiveSources,
  isLiveSource,
  toneForSourceHealth
} from "@/lib/dashboard-presenters";

import { StatusBadge } from "../status-badge";

export function SourceHealthStrip({
  sourceHealth,
  tracker
}: {
  sourceHealth: SourceHealthDTO[];
  tracker: TrackerOverviewDTO;
}) {
  const liveSources = sourceHealth.filter(isLiveSource);

  if (!hasConfiguredLiveSources(tracker)) {
    return (
      <section className="card section-stack">
        <div>
          <p className="eyebrow">Source Health</p>
          <h3>No live sources configured yet</h3>
        </div>
        <p className="muted">
          Add Greenhouse or Lever sources from the source registry before the dashboard can ingest
          live jobs. LinkedIn and Handshake remain manual-only.
        </p>
      </section>
    );
  }

  if (liveSources.length === 0) {
    return (
      <section className="card section-stack">
        <div>
          <p className="eyebrow">Source Health</p>
          <h3>No live source data yet</h3>
        </div>
        <p className="muted">
          Live sources are configured, but the worker has not recorded any source health yet.
        </p>
      </section>
    );
  }

  return (
    <div className="health-grid">
      {liveSources.map((source) => (
        <article key={source.id} className="health-card">
          <div className="health-card-head">
            <div>
              <p className="eyebrow">{source.displayName}</p>
              <h3>{source.jobCount} tracked job{source.jobCount === 1 ? "" : "s"}</h3>
            </div>
            <StatusBadge
              label={formatLabel(source.status)}
              tone={toneForSourceHealth(source.status)}
            />
          </div>
          <p className="muted">{source.note}</p>
          <div className="detail-list compact">
            <div className="detail-row">
              <span>Last seen</span>
              <strong>{formatDate(source.lastSeenAt)}</strong>
            </div>
            <div className="detail-row">
              <span>Latest posting</span>
              <strong>{formatDate(source.lastPostedAt)}</strong>
            </div>
            <div className="detail-row">
              <span>Last sync</span>
              <strong>{formatDate(source.lastSyncCompletedAt)}</strong>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}
