"use client";

import { useDeferredValue, useState } from "react";
import type { ApplicationDTO, JobDTO, MatchDTO } from "@job-focus/shared";

import { formatDate, formatLabel, formatSalary } from "@/lib/dashboard-data";
import { toneForApplicationStatus, toneForMatchStrength } from "@/lib/dashboard-presenters";

import { StatusBadge } from "../status-badge";

type ShortlistBoardProps = {
  applications: ApplicationDTO[];
  jobs: JobDTO[];
  matches: MatchDTO[];
};

function summariseWhyMatched(match: MatchDTO) {
  const candidateStrengths = match.whyMatched["strengths"];
  const strengths = Array.isArray(candidateStrengths)
    ? candidateStrengths.map((item) => String(item))
    : [];
  if (strengths.length > 0) {
    return strengths.slice(0, 2).join(" • ");
  }
  return match.rationale;
}

export function ShortlistBoard({ applications, jobs, matches }: ShortlistBoardProps) {
  const [sourceFilter, setSourceFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [scoreFilter, setScoreFilter] = useState("all");
  const [companyFilter, setCompanyFilter] = useState("");
  const deferredCompany = useDeferredValue(companyFilter.trim().toLowerCase());

  const rows = matches
    .map((match) => {
      const job = jobs.find((candidate) => candidate.id === match.jobId);
      if (!job) {
        return null;
      }
      const application = applications.find((candidate) => candidate.jobId === job.id) ?? null;

      return {
        match,
        job,
        application
      };
    })
    .filter((row): row is NonNullable<typeof row> => row !== null)
    .sort((left, right) => right.match.score - left.match.score);

  const statusOptions = Array.from(
    new Set(rows.map((row) => row.application?.status ?? "unapplied"))
  ).sort();

  const filteredRows = rows.filter((row) => {
    const applicationStatus = row.application?.status ?? "unapplied";
    const matchesSource = sourceFilter === "all" || row.job.source === sourceFilter;
    const matchesStatus = statusFilter === "all" || applicationStatus === statusFilter;
    const matchesCompany =
      deferredCompany.length === 0 || row.job.company.toLowerCase().includes(deferredCompany);
    const matchesScore = scoreFilter === "all" || row.match.score >= Number(scoreFilter);

    return matchesSource && matchesStatus && matchesCompany && matchesScore;
  });

  return (
    <section className="card section-stack">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Shortlisted Jobs</p>
          <h3>{filteredRows.length} ranked opportunities</h3>
        </div>
      </div>

      <div className="filter-bar">
        <label className="filter">
          <span>Source</span>
          <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)}>
            <option value="all">All sources</option>
            {Array.from(new Set(rows.map((row) => row.job.source))).map((source) => (
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
              <th>Why matched</th>
              <th>Status</th>
              <th>Salary</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row) => (
              <tr key={row.match.id}>
                <td>
                  <div className="table-primary">
                    <strong>{row.job.title}</strong>
                    <span className="muted">{row.job.company}</span>
                  </div>
                </td>
                <td>
                  <div className="table-primary">
                    <span>{formatLabel(row.job.source)}</span>
                    <span className="muted">{formatDate(row.job.postedAt)}</span>
                  </div>
                </td>
                <td>
                  <StatusBadge
                    label={`${row.match.score}`}
                    tone={toneForMatchStrength(row.match.strength)}
                  />
                </td>
                <td className="cell-long">
                  <span>{summariseWhyMatched(row.match)}</span>
                </td>
                <td>
                  {row.application ? (
                    <StatusBadge
                      label={formatLabel(row.application.status)}
                      tone={toneForApplicationStatus(row.application.status)}
                    />
                  ) : (
                    <span className="muted">Unapplied</span>
                  )}
                </td>
                <td className="mono">{formatSalary(row.job)}</td>
              </tr>
            ))}
            {filteredRows.length === 0 ? (
              <tr>
                <td className="empty-row" colSpan={6}>
                  No shortlisted jobs match the current filters.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
