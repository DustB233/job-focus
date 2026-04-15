import type {
  ApplicationDTO,
  DashboardSnapshotDTO,
  JobDTO,
  MatchDTO,
  ResumeDTO,
  SourceHealthDTO,
  TrackerOverviewDTO,
  UserPreferenceDTO,
  UserProfileDTO
} from "@job-focus/shared";

import { apiBaseUrl } from "./client-api";

export type DashboardLoadResult =
  | {
      status: "ready";
      snapshot: DashboardSnapshotDTO;
    }
  | {
      status: "unavailable";
      message: string;
    };

async function fetchFromApi<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function loadDashboardSnapshot(): Promise<DashboardLoadResult> {
  try {
    const [profile, preferences, resume, jobs, matches, applications, sourceHealth, tracker] =
      await Promise.all([
        fetchFromApi<UserProfileDTO>("/api/profile/me"),
        fetchFromApi<UserPreferenceDTO>("/api/profile/me/preferences"),
        fetchFromApi<ResumeDTO>("/api/profile/me/resume"),
        fetchFromApi<JobDTO[]>("/api/jobs"),
        fetchFromApi<MatchDTO[]>("/api/matches"),
        fetchFromApi<ApplicationDTO[]>("/api/applications"),
        fetchFromApi<SourceHealthDTO[]>("/api/tracker/sources"),
        fetchFromApi<TrackerOverviewDTO>("/api/tracker/overview")
      ]);

    return {
      status: "ready",
      snapshot: {
        profile,
        preferences,
        resume,
        jobs,
        matches,
        applications,
        sourceHealth,
        tracker
      }
    };
  } catch (error) {
    return {
      status: "unavailable",
      message:
        error instanceof Error ? error.message : "Unable to load live dashboard data from the API."
    };
  }
}

export function buildOverviewMetrics(snapshot: DashboardSnapshotDTO) {
  const readyPackets = snapshot.applications.filter(
    (application) =>
      application.packetStatus !== null && application.packetStatus !== "needs_user_input"
  ).length;
  const submittedApplications = snapshot.applications.filter(
    (application) => application.status === "submitted"
  ).length;
  const highMatches = snapshot.matches.filter((match) => match.score >= 85).length;
  const reviewQueue = snapshot.applications.filter(
    (application) => application.status === "waiting_review"
  ).length;

  return [
    {
      label: "Open jobs",
      value: snapshot.jobs.length,
      detail: `${highMatches} high-signal matches`
    },
    {
      label: "Applications",
      value: snapshot.applications.length,
      detail: `${submittedApplications} submitted, ${reviewQueue} waiting review`
    },
    {
      label: "Ready packets",
      value: readyPackets,
      detail: "Resume summaries and answers are staged"
    },
    {
      label: "Healthy sources",
      value: snapshot.sourceHealth.filter((source) => source.status === "healthy").length,
      detail:
        snapshot.tracker.configuredLiveSourceCount > 0
          ? `${snapshot.tracker.configuredLiveSourceCount} live connectors configured`
          : "No live sources configured"
    }
  ];
}

export function buildJobLookup(snapshot: DashboardSnapshotDTO) {
  return new Map(snapshot.jobs.map((job) => [job.id, job]));
}

export function buildMatchLookup(snapshot: DashboardSnapshotDTO) {
  return new Map(snapshot.matches.map((match) => [match.jobId, match]));
}

export function formatSalary(job: JobDTO) {
  const dollars = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  });

  return `${dollars.format(job.salaryMin)} - ${dollars.format(job.salaryMax)}`;
}

export function formatTimestamp(value: string | null) {
  if (!value) {
    return "pending";
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function formatDate(value: string | null) {
  if (!value) {
    return "pending";
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium"
  }).format(new Date(value));
}

export function formatLabel(value: string) {
  return value
    .split(/[_-]/g)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}
