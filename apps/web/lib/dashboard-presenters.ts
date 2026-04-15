import type {
  ApplicationDTO,
  ApplicationStatus,
  MatchStrength,
  SourceHealthDTO,
  SourceHealthStatus,
  TrackerOverviewDTO
} from "@job-focus/shared";

type BadgeTone = "neutral" | "success" | "warning" | "accent" | "danger";

export function toneForApplicationStatus(status: ApplicationStatus): BadgeTone {
  switch (status) {
    case "submitted":
      return "success";
    case "waiting_review":
    case "draft_ready":
      return "warning";
    case "failed":
    case "blocked":
      return "danger";
    case "submitting":
      return "accent";
    default:
      return "neutral";
  }
}

export function toneForMatchStrength(strength: MatchStrength | null): BadgeTone {
  switch (strength) {
    case "high":
      return "success";
    case "medium":
      return "warning";
    case "low":
      return "neutral";
    default:
      return "neutral";
  }
}

export function toneForSourceHealth(status: SourceHealthStatus): BadgeTone {
  switch (status) {
    case "healthy":
      return "success";
    case "warning":
      return "warning";
    case "inactive":
      return "neutral";
    default:
      return "neutral";
  }
}

export function getLatestEventNote(application: ApplicationDTO) {
  return application.events.at(-1)?.note ?? application.notes;
}

export function hasReviewAction(application: ApplicationDTO) {
  return application.status === "waiting_review" || application.status === "needs_user_input";
}

export function hasConfiguredLiveSources(tracker: TrackerOverviewDTO) {
  return tracker.configuredLiveSourceCount > 0;
}

export function hasWorkerActivity(tracker: TrackerOverviewDTO) {
  return Boolean(
    tracker.lastIngestAt ||
      tracker.lastScoreAt ||
      tracker.lastPacketAt ||
      tracker.lastApplyAt
  );
}

export function isLiveSource(source: Pick<SourceHealthDTO, "source" | "isActive">) {
  return source.isActive && (source.source === "greenhouse" || source.source === "lever");
}

export function sourceHealthSummary(
  sourceHealth: SourceHealthDTO[],
  tracker: TrackerOverviewDTO
) {
  if (!hasConfiguredLiveSources(tracker)) {
    return "No live sources configured";
  }

  const liveSources = sourceHealth.filter(isLiveSource);
  if (liveSources.length === 0) {
    return "Awaiting first live source sync";
  }

  const healthy = liveSources.filter((source) => source.status === "healthy").length;
  const warning = liveSources.filter((source) => source.status === "warning").length;

  return `${healthy} healthy${warning ? `, ${warning} watching` : ""}`;
}
