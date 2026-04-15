"use client";

import { useState, useTransition } from "react";
import type { ResumeDTO, UserProfileDTO } from "@job-focus/shared";
import { useRouter } from "next/navigation";

import { fetchJson } from "@/lib/client-api";
import { formatTimestamp } from "@/lib/dashboard-data";

type ProfileSetupFormProps = {
  profile: UserProfileDTO;
  resume: ResumeDTO;
};

function serializeList(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function ProfileSetupForm({ profile, resume }: ProfileSetupFormProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [fullName, setFullName] = useState(profile.fullName);
  const [headline, setHeadline] = useState(profile.headline);
  const [location, setLocation] = useState(profile.location);
  const [targetRoles, setTargetRoles] = useState(profile.targetRoles.join(", "));
  const [yearsExperience, setYearsExperience] = useState(String(profile.yearsExperience));
  const [seniorityLevel, setSeniorityLevel] = useState(profile.seniorityLevel ?? "");
  const [authorizationRegions, setAuthorizationRegions] = useState(
    profile.authorizationRegions.join(", ")
  );

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setNotice(null);

    startTransition(async () => {
      try {
        await fetchJson<UserProfileDTO>("/api/profile/me", {
          method: "PUT",
          body: {
            fullName,
            headline,
            location,
            targetRoles: serializeList(targetRoles),
            yearsExperience: Number(yearsExperience) || 0,
            seniorityLevel: seniorityLevel.trim() || null,
            authorizationRegions: serializeList(authorizationRegions)
          }
        });
        setNotice("Profile saved.");
        router.refresh();
      } catch (submissionError) {
        setError(
          submissionError instanceof Error ? submissionError.message : "Unable to save profile."
        );
      }
    });
  }

  return (
    <section className="split-grid">
      <form className="card section-stack" onSubmit={onSubmit}>
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Profile Setup</p>
            <h3>Candidate identity and targeting signals</h3>
          </div>
          <button className="button button-primary" disabled={isPending} type="submit">
            {isPending ? "Saving..." : "Save profile"}
          </button>
        </div>

        <div className="form-grid">
          <label className="field">
            <span>Full name</span>
            <input value={fullName} onChange={(event) => setFullName(event.target.value)} />
          </label>
          <label className="field">
            <span>Location</span>
            <input value={location} onChange={(event) => setLocation(event.target.value)} />
          </label>
          <label className="field field-span">
            <span>Headline</span>
            <textarea
              rows={3}
              value={headline}
              onChange={(event) => setHeadline(event.target.value)}
            />
          </label>
          <label className="field field-span">
            <span>Target roles</span>
            <input
              value={targetRoles}
              onChange={(event) => setTargetRoles(event.target.value)}
              placeholder="Product Operations, Program Manager"
            />
          </label>
          <label className="field">
            <span>Years of experience</span>
            <input
              min={0}
              type="number"
              value={yearsExperience}
              onChange={(event) => setYearsExperience(event.target.value)}
            />
          </label>
          <label className="field">
            <span>Seniority</span>
            <input
              value={seniorityLevel}
              onChange={(event) => setSeniorityLevel(event.target.value)}
              placeholder="senior"
            />
          </label>
          <label className="field field-span">
            <span>Authorization regions</span>
            <input
              value={authorizationRegions}
              onChange={(event) => setAuthorizationRegions(event.target.value)}
              placeholder="US, Canada"
            />
          </label>
        </div>

        {error ? <p className="feedback error">{error}</p> : null}
        {notice ? <p className="feedback success">{notice}</p> : null}
      </form>

      <aside className="card section-stack">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Resume Asset</p>
            <h3>Default packet baseline</h3>
          </div>
        </div>

        <div className="detail-list">
          <div className="detail-row">
            <span>Document</span>
            <strong>{resume.fileName}</strong>
          </div>
          <div className="detail-row">
            <span>Resume title</span>
            <strong>{resume.title}</strong>
          </div>
          <div className="detail-row">
            <span>Version</span>
            <strong>{resume.version}</strong>
          </div>
          <div className="detail-row">
            <span>Updated</span>
            <strong>{formatTimestamp(resume.updatedAt)}</strong>
          </div>
        </div>

        <p className="muted">{resume.summary}</p>
        <div className="tag-cloud">
          {resume.skills.map((skill) => (
            <span key={skill} className="token">
              {skill}
            </span>
          ))}
        </div>
      </aside>
    </section>
  );
}
