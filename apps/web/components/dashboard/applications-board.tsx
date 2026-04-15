"use client";

import { useDeferredValue, useState, useTransition } from "react";
import type { ApplicationDTO, ReviewAction } from "@job-focus/shared";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { fetchJson } from "@/lib/client-api";
import { formatDate, formatLabel, formatSalary, formatTimestamp } from "@/lib/dashboard-data";
import {
  getLatestEventNote,
  hasReviewAction,
  toneForApplicationStatus,
  toneForMatchStrength
} from "@/lib/dashboard-presenters";

import { StatusBadge } from "../status-badge";

type ApplicationsBoardMode = "all" | "review" | "failed";

type ApplicationsBoardProps = {
  applications: ApplicationDTO[];
  mode?: ApplicationsBoardMode;
};

function getModeApplications(applications: ApplicationDTO[], mode: ApplicationsBoardMode) {
  switch (mode) {
    case "review":
      return applications.filter(
        (application) =>
          application.status === "waiting_review" || application.status === "needs_user_input"
      );
    case "failed":
      return applications.filter((application) => application.status === "failed");
    default:
      return applications;
  }
}

function getStatusOptions(applications: ApplicationDTO[]) {
  return Array.from(new Set(applications.map((application) => application.status))).sort();
}

export function ApplicationsBoard({
  applications,
  mode = "all"
}: ApplicationsBoardProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [sourceFilter, setSourceFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [scoreFilter, setScoreFilter] = useState("all");
  const [companyFilter, setCompanyFilter] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(applications[0]?.id ?? null);
  const [actionError, setActionError] = useState<string | null>(null);
  const deferredCompany = useDeferredValue(companyFilter.trim().toLowerCase());

  const modeApplications = getModeApplications(applications, mode);
  const statusOptions = getStatusOptions(modeApplications);
  const filteredApplications = modeApplications.filter((application) => {
    const matchesSource =
      sourceFilter === "all" || application.job.sourceDisplayName === sourceFilter;
    const matchesStatus =
      statusFilter === "all" || application.status === statusFilter;
    const matchesCompany =
      deferredCompany.length === 0 ||
      application.job.company.toLowerCase().includes(deferredCompany);
    const score = application.matchScore ?? -1;
    const matchesScore =
      scoreFilter === "all" || score >= Number(scoreFilter);

    return matchesSource && matchesStatus && matchesCompany && matchesScore;
  });

  const selectedApplication =
    filteredApplications.find((application) => application.id === selectedId) ??
    filteredApplications[0] ??
    null;

  async function handleReviewAction(action: ReviewAction) {
    if (!selectedApplication) {
      return;
    }

    setActionError(null);

    startTransition(async () => {
      try {
        await fetchJson<ApplicationDTO>(`/api/applications/${selectedApplication.id}/review`, {
          method: "POST",
          body: {
            action,
            note:
              action === "approve"
                ? "Approved from the review queue in the web dashboard."
                : "Rejected from the review queue in the web dashboard."
          }
        });
        router.refresh();
      } catch (submissionError) {
        setActionError(
          submissionError instanceof Error
            ? submissionError.message
            : "Unable to update application."
        );
      }
    });
  }

  return (
    <section className="drawer-shell">
      <div className="card section-stack">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Pipeline Table</p>
            <h3>
              {filteredApplications.length} visible application
              {filteredApplications.length === 1 ? "" : "s"}
            </h3>
          </div>
        </div>

        <div className="filter-bar">
          <label className="filter">
            <span>Source</span>
            <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)}>
              <option value="all">All sources</option>
              {Array.from(
                new Set(modeApplications.map((application) => application.job.sourceDisplayName))
              ).map(
                (source) => (
                  <option key={source} value={source}>
                    {source}
                  </option>
                )
              )}
            </select>
          </label>
          <label className="filter">
            <span>Status</span>
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="all">All statuses</option>
              {statusOptions.map((status) => (
                <option key={status} value={status}>
                  {formatLabel(status)}
                </option>
              ))}
            </select>
          </label>
          <label className="filter">
            <span>Score</span>
            <select value={scoreFilter} onChange={(event) => setScoreFilter(event.target.value)}>
              <option value="all">All scores</option>
              <option value="70">70+</option>
              <option value="80">80+</option>
              <option value="90">90+</option>
            </select>
          </label>
          <label className="filter filter-wide">
            <span>Company</span>
            <input
              placeholder="Filter company"
              value={companyFilter}
              onChange={(event) => setCompanyFilter(event.target.value)}
            />
          </label>
        </div>

        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Role</th>
                <th>Source</th>
                <th>Status</th>
                <th>Score</th>
                <th>{mode === "failed" ? "Error" : "Packet"}</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {filteredApplications.map((application) => (
                <tr
                  key={application.id}
                  className={selectedApplication?.id === application.id ? "is-selected" : ""}
                >
                  <td>
                    <button
                      className="row-select"
                      type="button"
                      onClick={() => setSelectedId(application.id)}
                    >
                      <strong>{application.job.title}</strong>
                      <span className="muted">{application.job.company}</span>
                    </button>
                  </td>
                  <td>
                    <div className="table-primary">
                      <span>{application.job.sourceDisplayName}</span>
                      <span className="muted">
                        {formatLabel(application.job.source)} · {application.job.location}
                      </span>
                    </div>
                  </td>
                  <td>
                    <StatusBadge
                      label={formatLabel(application.status)}
                      tone={toneForApplicationStatus(application.status)}
                    />
                  </td>
                  <td>
                    {application.matchScore !== null ? (
                      <StatusBadge
                        label={`${application.matchScore}`}
                        tone={toneForMatchStrength(application.matchStrength)}
                      />
                    ) : (
                      <span className="muted">No score</span>
                    )}
                  </td>
                  <td>
                    {mode === "failed" ? (
                      <span className="mono muted">{application.latestErrorCode ?? "unknown"}</span>
                    ) : (
                      <span className="muted">
                        {application.packetStatus ? formatLabel(application.packetStatus) : "No packet"}
                      </span>
                    )}
                  </td>
                  <td>{formatTimestamp(application.updatedAt)}</td>
                </tr>
              ))}
              {filteredApplications.length === 0 ? (
                <tr>
                  <td className="empty-row" colSpan={6}>
                    No applications match the current filters.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <aside className="card drawer-panel">
        {selectedApplication ? (
          <>
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Application Detail</p>
                <h3>{selectedApplication.job.title}</h3>
              </div>
              <StatusBadge
                label={formatLabel(selectedApplication.status)}
                tone={toneForApplicationStatus(selectedApplication.status)}
              />
            </div>

            <div className="detail-list">
              <div className="detail-row">
                <span>Company</span>
                <strong>{selectedApplication.job.company}</strong>
              </div>
              <div className="detail-row">
                <span>Source</span>
                <strong>{selectedApplication.job.sourceDisplayName}</strong>
              </div>
              <div className="detail-row">
                <span>Compensation</span>
                <strong>{formatSalary(selectedApplication.job)}</strong>
              </div>
              <div className="detail-row">
                <span>Latest note</span>
                <strong>{getLatestEventNote(selectedApplication)}</strong>
              </div>
              {selectedApplication.confirmationDetails ? (
                <div className="detail-row">
                  <span>Confirmation</span>
                  <strong className="mono">
                    {JSON.stringify(selectedApplication.confirmationDetails)}
                  </strong>
                </div>
              ) : null}
              {selectedApplication.latestErrorCode ? (
                <div className="detail-row">
                  <span>Error code</span>
                  <strong className="mono">{selectedApplication.latestErrorCode}</strong>
                </div>
              ) : null}
            </div>

            <div className="drawer-section">
              <div className="panel-heading">
                <h4>Packet</h4>
                <span className="muted">
                  {selectedApplication.packet?.selectedResumeVersion
                    ? `Resume v${selectedApplication.packet.selectedResumeVersion}`
                    : "No resume attached"}
                </span>
              </div>
              <p className="muted">
                {selectedApplication.packet?.tailoredResumeSummary ?? "No tailored summary yet."}
              </p>
              <p className="muted">
                {selectedApplication.packet?.coverNote ?? "No cover note drafted yet."}
              </p>
              {selectedApplication.packet?.missingFields.length ? (
                <div className="tag-cloud">
                  {selectedApplication.packet.missingFields.map((field) => (
                    <span key={field} className="token token-warning">
                      Missing: {field}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>

            <div className="drawer-section">
              <div className="panel-heading">
                <h4>Screening answers</h4>
              </div>
              <div className="answer-list">
                {Object.entries(selectedApplication.packet?.screeningAnswers ?? {}).map(
                  ([key, value]) => (
                    <div key={key} className="answer-row">
                      <span className="muted">{formatLabel(key)}</span>
                      <strong>{value}</strong>
                    </div>
                  )
                )}
                {Object.keys(selectedApplication.packet?.screeningAnswers ?? {}).length === 0 ? (
                  <p className="muted">No screening answers are attached to this packet yet.</p>
                ) : null}
              </div>
            </div>

            <div className="drawer-section">
              <div className="panel-heading">
                <h4>Event log</h4>
                {selectedApplication.job.applicationUrl ? (
                  <Link
                    className="link-inline"
                    href={selectedApplication.job.applicationUrl}
                    rel="noreferrer"
                    target="_blank"
                  >
                    Open posting
                  </Link>
                ) : null}
              </div>
              <div className="timeline">
                {selectedApplication.events.map((event) => (
                  <article key={event.id} className="timeline-item">
                    <div className="timeline-head">
                      <strong>{formatLabel(event.eventType)}</strong>
                      <span className="muted">{formatTimestamp(event.createdAt)}</span>
                    </div>
                    <p className="muted">
                      {event.note ??
                        `${formatLabel(event.fromStatus ?? "queued")} to ${formatLabel(event.toStatus)}.`}
                    </p>
                    {Object.keys(event.payload).length ? (
                      <pre className="code-block">
                        {JSON.stringify(event.payload, null, 2)}
                      </pre>
                    ) : null}
                  </article>
                ))}
              </div>
            </div>

            {hasReviewAction(selectedApplication) ? (
              <div className="drawer-actions">
                <button
                  className="button button-primary"
                  disabled={isPending || selectedApplication.status !== "waiting_review"}
                  type="button"
                  onClick={() => handleReviewAction("approve")}
                >
                  {isPending ? "Saving..." : "Approve"}
                </button>
                <button
                  className="button button-secondary"
                  disabled={isPending}
                  type="button"
                  onClick={() => handleReviewAction("reject")}
                >
                  Reject
                </button>
              </div>
            ) : null}
            {actionError ? <p className="feedback error">{actionError}</p> : null}
            {selectedApplication.submittedAt ? (
              <p className="muted">Submitted {formatDate(selectedApplication.submittedAt)}.</p>
            ) : null}
          </>
        ) : (
          <div className="empty-state">
            <p className="eyebrow">Application Detail</p>
            <h3>No application selected</h3>
            <p className="muted">Choose an application from the table to inspect its packet and log.</p>
          </div>
        )}
      </aside>
    </section>
  );
}
