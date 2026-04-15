"use client";

import { useMemo, useState, useTransition } from "react";
import type { JobSource, SourceCreateDTO, SourceRegistryDTO } from "@job-focus/shared";
import { useRouter } from "next/navigation";

import { fetchJson } from "@/lib/client-api";
import { formatLabel, formatTimestamp } from "@/lib/dashboard-data";
import { toneForSourceHealth } from "@/lib/dashboard-presenters";

import { StatusBadge } from "../status-badge";

type SourcesAdminProps = {
  initialSources: SourceRegistryDTO[];
};

type SourceFormState = {
  source: Extract<JobSource, "greenhouse" | "lever">;
  externalIdentifier: string;
  displayName: string;
};

function sortSources(sources: SourceRegistryDTO[]) {
  return sources
    .slice()
    .sort((left, right) => left.displayName.localeCompare(right.displayName));
}

export function SourcesAdmin({ initialSources }: SourcesAdminProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [sources, setSources] = useState(() => sortSources(initialSources));
  const [form, setForm] = useState<SourceFormState>({
    source: "greenhouse",
    externalIdentifier: "",
    displayName: ""
  });
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const liveSourceCount = useMemo(
    () => sources.filter((source) => source.isActive && source.externalIdentifier).length,
    [sources]
  );

  function mergeSource(updatedSource: SourceRegistryDTO) {
    setSources((current) => {
      const next = current.some((source) => source.id === updatedSource.id)
        ? current.map((source) => (source.id === updatedSource.id ? updatedSource : source))
        : [...current, updatedSource];
      return sortSources(next);
    });
  }

  async function handleCreateSource() {
    setFeedback(null);
    setError(null);

    startTransition(async () => {
      try {
        const createdSource = await fetchJson<SourceRegistryDTO>("/api/sources", {
          method: "POST",
          body: {
            source: form.source,
            externalIdentifier: form.externalIdentifier.trim(),
            displayName: form.displayName.trim() || null,
            isActive: true
          } satisfies SourceCreateDTO
        });
        mergeSource(createdSource);
        setForm((current) => ({
          ...current,
          externalIdentifier: "",
          displayName: ""
        }));
        setFeedback(`Added ${createdSource.displayName}.`);
        router.refresh();
      } catch (submissionError) {
        setError(
          submissionError instanceof Error
            ? submissionError.message
            : "Unable to create source."
        );
      }
    });
  }

  function handleRowAction(
    sourceId: string,
    action: "enable" | "disable" | "sync",
    successMessage: string
  ) {
    setFeedback(null);
    setError(null);

    startTransition(async () => {
      try {
        const updatedSource = await fetchJson<SourceRegistryDTO>(`/api/sources/${sourceId}/${action}`, {
          method: "POST",
          body: null
        });
        mergeSource(updatedSource);
        setFeedback(successMessage.replace("{name}", updatedSource.displayName));
        router.refresh();
      } catch (submissionError) {
        setError(
          submissionError instanceof Error
            ? submissionError.message
            : "Unable to update source."
        );
      }
    });
  }

  return (
    <div className="section-stack">
      <section className="card section-stack">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Source Registry</p>
            <h3>{liveSourceCount} live source{liveSourceCount === 1 ? "" : "s"} active</h3>
          </div>
        </div>

        <div className="form-grid">
          <label className="field">
            <span>Provider</span>
            <select
              value={form.source}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  source: event.target.value as SourceFormState["source"]
                }))
              }
            >
              <option value="greenhouse">Greenhouse</option>
              <option value="lever">Lever</option>
            </select>
          </label>
          <label className="field">
            <span>External identifier</span>
            <input
              placeholder={form.source === "greenhouse" ? "northstar" : "relay"}
              value={form.externalIdentifier}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  externalIdentifier: event.target.value
                }))
              }
            />
          </label>
          <label className="field field-span">
            <span>Display name</span>
            <input
              placeholder="Optional friendly label shown in the dashboard"
              value={form.displayName}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  displayName: event.target.value
                }))
              }
            />
          </label>
        </div>

        <div className="drawer-actions">
          <button
            className="button button-primary"
            disabled={isPending || form.externalIdentifier.trim().length === 0}
            type="button"
            onClick={() => void handleCreateSource()}
          >
            {isPending ? "Saving..." : "Create source"}
          </button>
          <p className="muted">
            Use the Greenhouse board token or Lever site name. LinkedIn and Handshake stay
            manual-only.
          </p>
        </div>

        {feedback ? <p className="feedback success">{feedback}</p> : null}
        {error ? <p className="feedback error">{error}</p> : null}
      </section>

      <section className="card section-stack">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Registered Sources</p>
            <h3>{sources.length} source record{sources.length === 1 ? "" : "s"}</h3>
          </div>
          <p className="muted">Sync requests are picked up by the worker on the next ingest run.</p>
        </div>

        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Status</th>
                <th>Jobs</th>
                <th>Last sync</th>
                <th>Latest result</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((source) => (
                <tr key={source.id}>
                  <td>
                    <div className="table-primary">
                      <strong>{source.displayName}</strong>
                      <span className="muted">
                        {formatLabel(source.source)}
                        {source.externalIdentifier ? ` - ${source.externalIdentifier}` : ""}
                      </span>
                    </div>
                  </td>
                  <td>
                    <StatusBadge
                      label={formatLabel(source.status)}
                      tone={toneForSourceHealth(source.status)}
                    />
                  </td>
                  <td>
                    <div className="table-primary">
                      <span>{source.trackedJobCount} tracked</span>
                      <span className="muted">
                        {source.lastFetchedJobCount} fetched - {source.lastCreatedJobCount} new -{" "}
                        {source.lastUpdatedJobCount} updated
                      </span>
                    </div>
                  </td>
                  <td>
                    <div className="table-primary">
                      <span>{formatTimestamp(source.lastSyncCompletedAt)}</span>
                      <span className="muted">
                        Requested {formatTimestamp(source.lastSyncRequestedAt)}
                      </span>
                    </div>
                  </td>
                  <td className="cell-long">
                    <span>{source.note}</span>
                    {source.lastError ? (
                      <div className="muted mono">Error: {source.lastError}</div>
                    ) : null}
                  </td>
                  <td>
                    <div className="hero-band">
                      <button
                        className="button button-secondary"
                        disabled={isPending}
                        type="button"
                        onClick={() =>
                          handleRowAction(
                            source.id,
                            source.isActive ? "disable" : "enable",
                            source.isActive ? "Disabled {name}." : "Enabled {name}."
                          )
                        }
                      >
                        {source.isActive ? "Disable" : "Enable"}
                      </button>
                      <button
                        className="button button-primary"
                        disabled={
                          isPending ||
                          !source.isActive ||
                          (source.source !== "greenhouse" && source.source !== "lever")
                        }
                        type="button"
                        onClick={() =>
                          handleRowAction(source.id, "sync", "Queued a sync for {name}.")
                        }
                      >
                        Sync now
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {sources.length === 0 ? (
                <tr>
                  <td className="empty-row" colSpan={6}>
                    No sources have been registered yet.
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
