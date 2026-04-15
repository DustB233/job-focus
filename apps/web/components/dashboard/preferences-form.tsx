"use client";

import { useState, useTransition } from "react";
import type {
  EmploymentType,
  UserPreferenceDTO,
  WorkMode
} from "@job-focus/shared";
import { useRouter } from "next/navigation";

import { fetchJson } from "@/lib/client-api";
import { formatLabel } from "@/lib/dashboard-data";

const workModeOptions: WorkMode[] = ["remote", "hybrid", "onsite"];
const employmentTypeOptions: EmploymentType[] = ["full_time", "contract", "internship"];

function serializeList(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function toggleItem<T extends string>(items: T[], value: T) {
  return items.includes(value) ? items.filter((item) => item !== value) : [...items, value];
}

export function PreferencesForm({ preferences }: { preferences: UserPreferenceDTO }) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [preferredLocations, setPreferredLocations] = useState(
    preferences.preferredLocations.join(", ")
  );
  const [preferredWorkModes, setPreferredWorkModes] = useState<WorkMode[]>(
    preferences.preferredWorkModes
  );
  const [preferredEmploymentTypes, setPreferredEmploymentTypes] = useState<EmploymentType[]>(
    preferences.preferredEmploymentTypes
  );
  const [desiredSalaryMin, setDesiredSalaryMin] = useState(
    preferences.desiredSalaryMin?.toString() ?? ""
  );
  const [desiredSalaryMax, setDesiredSalaryMax] = useState(
    preferences.desiredSalaryMax?.toString() ?? ""
  );
  const [autoApplyEnabled, setAutoApplyEnabled] = useState(preferences.autoApplyEnabled);
  const [autoApplyMinScore, setAutoApplyMinScore] = useState(
    String(preferences.autoApplyMinScore)
  );

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setNotice(null);

    startTransition(async () => {
      try {
        await fetchJson<UserPreferenceDTO>("/api/profile/me/preferences", {
          method: "PUT",
          body: {
            preferredLocations: serializeList(preferredLocations),
            preferredWorkModes,
            preferredEmploymentTypes,
            desiredSalaryMin: desiredSalaryMin ? Number(desiredSalaryMin) : null,
            desiredSalaryMax: desiredSalaryMax ? Number(desiredSalaryMax) : null,
            autoApplyEnabled,
            autoApplyMinScore: Number(autoApplyMinScore) || 0
          }
        });
        setNotice("Preferences saved.");
        router.refresh();
      } catch (submissionError) {
        setError(
          submissionError instanceof Error
            ? submissionError.message
            : "Unable to save preferences."
        );
      }
    });
  }

  return (
    <section className="split-grid">
      <form className="card section-stack" onSubmit={onSubmit}>
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Target Preferences</p>
            <h3>Guardrails for matching and auto-apply</h3>
          </div>
          <button className="button button-primary" disabled={isPending} type="submit">
            {isPending ? "Saving..." : "Save preferences"}
          </button>
        </div>

        <div className="form-grid">
          <label className="field field-span">
            <span>Preferred locations</span>
            <input
              value={preferredLocations}
              onChange={(event) => setPreferredLocations(event.target.value)}
              placeholder="Remote - US, Seattle, WA"
            />
          </label>

          <div className="field field-span">
            <span>Preferred work modes</span>
            <div className="choice-row">
              {workModeOptions.map((option) => {
                const active = preferredWorkModes.includes(option);

                return (
                  <button
                    key={option}
                    className={`button button-chip${active ? " is-active" : ""}`}
                    type="button"
                    onClick={() => setPreferredWorkModes(toggleItem(preferredWorkModes, option))}
                  >
                    {formatLabel(option)}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="field field-span">
            <span>Preferred employment types</span>
            <div className="choice-row">
              {employmentTypeOptions.map((option) => {
                const active = preferredEmploymentTypes.includes(option);

                return (
                  <button
                    key={option}
                    className={`button button-chip${active ? " is-active" : ""}`}
                    type="button"
                    onClick={() =>
                      setPreferredEmploymentTypes(toggleItem(preferredEmploymentTypes, option))
                    }
                  >
                    {formatLabel(option)}
                  </button>
                );
              })}
            </div>
          </div>

          <label className="field">
            <span>Desired salary min</span>
            <input
              inputMode="numeric"
              value={desiredSalaryMin}
              onChange={(event) => setDesiredSalaryMin(event.target.value)}
              placeholder="150000"
            />
          </label>
          <label className="field">
            <span>Desired salary max</span>
            <input
              inputMode="numeric"
              value={desiredSalaryMax}
              onChange={(event) => setDesiredSalaryMax(event.target.value)}
              placeholder="190000"
            />
          </label>
          <label className="field">
            <span>Auto-apply min score</span>
            <input
              max={100}
              min={0}
              type="number"
              value={autoApplyMinScore}
              onChange={(event) => setAutoApplyMinScore(event.target.value)}
            />
          </label>
          <label className="toggle-field">
            <span>Auto-apply enabled</span>
            <button
              aria-pressed={autoApplyEnabled}
              className={`toggle${autoApplyEnabled ? " is-on" : ""}`}
              type="button"
              onClick={() => setAutoApplyEnabled((current) => !current)}
            >
              <span />
            </button>
          </label>
        </div>

        {error ? <p className="feedback error">{error}</p> : null}
        {notice ? <p className="feedback success">{notice}</p> : null}
      </form>

      <aside className="card section-stack">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Scoring Inputs</p>
            <h3>What the engine is using right now</h3>
          </div>
        </div>

        <div className="detail-list">
          <div className="detail-row">
            <span>Preferred locations</span>
            <strong>{preferences.preferredLocations.length}</strong>
          </div>
          <div className="detail-row">
            <span>Work mode filters</span>
            <strong>{preferences.preferredWorkModes.length}</strong>
          </div>
          <div className="detail-row">
            <span>Employment filters</span>
            <strong>{preferences.preferredEmploymentTypes.length}</strong>
          </div>
          <div className="detail-row">
            <span>Auto-apply threshold</span>
            <strong>{preferences.autoApplyMinScore}</strong>
          </div>
        </div>

        <p className="muted">
          The matching engine scores title, location, seniority, skills, authorization, salary,
          and these preference signals before a job enters the queue.
        </p>
      </aside>
    </section>
  );
}
