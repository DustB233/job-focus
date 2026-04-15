"use client";

import { useDeferredValue, useState } from "react";
import type {
  ApplicationDTO,
  JobDTO,
  MatchDTO,
  SourceHealthDTO,
  TrackerOverviewDTO
} from "@job-focus/shared";

import { formatDate, formatLabel, formatSalary } from "@/lib/dashboard-data";
import { toneForApplicationStatus, toneForMatchStrength } from "@/lib/dashboard-presenters";

import { StatusBadge } from "../status-badge";
import { SourceHealthStrip } from "./source-health-strip";

type JobsBoardProps = {
  applications: ApplicationDTO[];
  jobs: JobDTO[];
  matches: MatchDTO[];
  sourceHealth: SourceHealthDTO[];
  tracker: TrackerOverviewDTO;
};

export function JobsBoard({
  applications,
  jobs,
  matches,
  sourceHealth,
  tracker
}: JobsBoardProps) {
  const [sourceFilter, setSourceFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [scoreFilter, setScoreFilter] = useState("all");
  const [companyFilter, setCompanyFilter] = useState("");
  const deferredCompany = useDeferredValue(companyFilter.trim().toLowerCase());

  const rows = jobs.map((job) => {
    const match = matches.find((candidate) => candidate.jobId === job.id) ?? null;
    const application = applications.find((candidate) => candidate.jobId === job.id) ?? null;
    const pipelineStatus = application?.status ?? "open";

    return {
      job,
      match,
      application,
      pipelineStatus
    };
  });

  const statusOptions = Array.from(new Set(rows.map((row) => row.pipelineStatus))).sort();
  const filteredRows = rows.filter((row) => {
    const matchesSource = sourceFilter === "all" || row.job.source === sourceFilter;
    const matchesStatus = statusFilter === "all" || row.pipelineStatus === statusFilter;
    const matchesCompany =
      deferredCompany.length === 0 || row.job.company.toLowerCase().includes(deferredCompany);
    const matchesScore =
      scoreFilter === "all" || (row.match?.score ?? -1) >= Number(scoreFilter);

    return matchesSource && matchesStatus && matchesCompany && matchesScore;
  });

  return (
    <div className="section-stack">
      <SourceHealthStrip sourceHealth={sourceHealth} tracker={tracker} />

      <section className="card section-stack">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Jobs Discovered</p>
            <h3>{filteredRows.length} roles visible</h3>
          </div>
        </div>

        <div className="filter-bar">
          <label className="filter">
            <span>Source</span>
            <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)}>
              <option value="all">All sources</option>
              {Array.from(new Set(jobs.map((job) => job.source))).map((source) => (
                <option key={source} value={source}>
                  {formatLabel(source)}
                </option>
              ))}
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
                <th>Score</th>
                <th>Status</th>
                <th>Salary</th>
                <th>Posted</th>
              </tr>
            </thead>
            <tbody>
              {filteredRows.map((row) => (
                <tr key={row.job.id}>
                  <td>
                    <div className="table-primary">
                      <strong>{row.job.title}</strong>
                      <span className="muted">{row.job.company}</span>
                    </div>
                  </td>
                  <td>
                    <div className="table-primary">
                      <span>{formatLabel(row.job.source)}</span>
                      <span className="muted">{row.job.location}</span>
                    </div>
                  </td>
                  <td>
                    {row.match ? (
                      <StatusBadge
                        label={`${row.match.score}`}
                        tone={toneForMatchStrength(row.match.strength)}
                      />
                    ) : (
                      <span className="muted">Not scored</span>
                    )}
                  </td>
                  <td>
                    {row.application ? (
                      <StatusBadge
                        label={formatLabel(row.application.status)}
                        tone={toneForApplicationStatus(row.application.status)}
                      />
                    ) : (
                      <span className="muted">Open</span>
                    )}
                  </td>
                  <td className="mono">{formatSalary(row.job)}</td>
                  <td>{formatDate(row.job.postedAt)}</td>
                </tr>
              ))}
              {filteredRows.length === 0 ? (
                <tr>
                  <td className="empty-row" colSpan={6}>
                    No jobs match the current filters.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
