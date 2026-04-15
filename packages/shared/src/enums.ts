export const workModes = ["remote", "hybrid", "onsite"] as const;
export const employmentTypes = ["full_time", "contract", "internship"] as const;
export const jobSources = ["greenhouse", "lever", "ashby", "manual"] as const;
export const matchStrengths = ["high", "medium", "low"] as const;
export const sourceHealthStatuses = ["healthy", "warning", "inactive"] as const;
export const reviewActions = ["approve", "reject"] as const;
export const applicationStatuses = [
  "discovered",
  "shortlisted",
  "draft_ready",
  "needs_user_input",
  "waiting_review",
  "submitting",
  "submitted",
  "failed",
  "blocked",
  "duplicate"
] as const;
export const packetStatuses = [
  "draft_ready",
  "needs_user_input",
  "waiting_review",
  "finalized"
] as const;

export type WorkMode = (typeof workModes)[number];
export type EmploymentType = (typeof employmentTypes)[number];
export type JobSource = (typeof jobSources)[number];
export type MatchStrength = (typeof matchStrengths)[number];
export type SourceHealthStatus = (typeof sourceHealthStatuses)[number];
export type ReviewAction = (typeof reviewActions)[number];
export type ApplicationStatus = (typeof applicationStatuses)[number];
export type PacketStatus = (typeof packetStatuses)[number];
