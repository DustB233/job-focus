import type {
  ApplicationStatus,
  EmploymentType,
  JobSource,
  MatchStrength,
  PacketStatus,
  ReviewAction,
  SourceHealthStatus,
  WorkMode
} from "./enums";

export type UserProfileDTO = {
  id: string;
  email: string;
  fullName: string;
  headline: string;
  location: string;
  targetRoles: string[];
  yearsExperience: number;
  seniorityLevel: string | null;
  authorizationRegions: string[];
  createdAt: string;
};

export type ProfileUpdateDTO = {
  fullName: string;
  headline: string;
  location: string;
  targetRoles: string[];
  yearsExperience: number;
  seniorityLevel: string | null;
  authorizationRegions: string[];
};

export type ResumeDTO = {
  id: string;
  userId: string;
  version: number;
  title: string;
  fileName: string;
  summary: string;
  skills: string[];
  isDefault: boolean;
  updatedAt: string;
};

export type UserPreferenceDTO = {
  id: string;
  userId: string;
  preferredLocations: string[];
  preferredWorkModes: WorkMode[];
  preferredEmploymentTypes: EmploymentType[];
  desiredSalaryMin: number | null;
  desiredSalaryMax: number | null;
  autoApplyEnabled: boolean;
  autoApplyMinScore: number;
  updatedAt: string;
};

export type UserPreferenceUpdateDTO = {
  preferredLocations: string[];
  preferredWorkModes: WorkMode[];
  preferredEmploymentTypes: EmploymentType[];
  desiredSalaryMin: number | null;
  desiredSalaryMax: number | null;
  autoApplyEnabled: boolean;
  autoApplyMinScore: number;
};

export type JobDTO = {
  id: string;
  sourceId: string;
  externalJobId: string;
  company: string;
  title: string;
  location: string;
  workMode: WorkMode;
  employmentType: EmploymentType;
  source: JobSource;
  sourceDisplayName: string;
  sourceExternalIdentifier: string | null;
  salaryMin: number;
  salaryMax: number;
  description: string;
  applicationUrl: string | null;
  seniorityLevel: string | null;
  authorizationRequirement: string | null;
  postedAt: string;
};

export type DiscoveredJobDTO = {
  source: JobSource;
  externalJobId: string;
  company: string;
  title: string;
  location: string;
  workMode: WorkMode;
  employmentType: EmploymentType;
  salaryMin: number;
  salaryMax: number;
  description: string;
  applicationUrl: string | null;
  seniorityLevel: string | null;
  authorizationRequirement: string | null;
  postedAt: string;
  rawPayload: Record<string, unknown>;
};

export type MatchDTO = {
  id: string;
  userId: string;
  jobId: string;
  score: number;
  strength: MatchStrength;
  rationale: string;
  whyMatched: Record<string, unknown>;
  createdAt: string;
};

export type ApplicationPacketDTO = {
  id: string;
  userId: string;
  jobId: string;
  resumeId: string | null;
  status: PacketStatus;
  selectedResumeVersion: number | null;
  tailoredResumeSummary: string | null;
  coverNote: string | null;
  screeningAnswers: Record<string, string>;
  missingFields: string[];
  updatedAt: string;
};

export type ApplicationEventDTO = {
  id: string;
  applicationId: string;
  fromStatus: ApplicationStatus | null;
  toStatus: ApplicationStatus;
  eventType: string;
  actor: string;
  note: string | null;
  payload: Record<string, unknown>;
  createdAt: string;
};

export type ApplicationDTO = {
  id: string;
  userId: string;
  jobId: string;
  status: ApplicationStatus;
  packetId: string | null;
  packetStatus: PacketStatus | null;
  notes: string;
  submittedAt: string | null;
  lastError: string | null;
  blockingReason: string | null;
  latestErrorCode: string | null;
  confirmationDetails: Record<string, unknown> | null;
  job: JobDTO;
  matchScore: number | null;
  matchStrength: MatchStrength | null;
  packet: ApplicationPacketDTO | null;
  events: ApplicationEventDTO[];
  createdAt: string;
  updatedAt: string;
};

export type ApplicationReviewRequestDTO = {
  action: ReviewAction;
  note: string | null;
};

export type SourceHealthDTO = {
  id: string;
  source: JobSource;
  displayName: string;
  externalIdentifier: string | null;
  baseUrl: string | null;
  status: SourceHealthStatus;
  isActive: boolean;
  jobCount: number;
  lastSeenAt: string | null;
  lastPostedAt: string | null;
  lastSyncRequestedAt: string | null;
  lastSyncStartedAt: string | null;
  lastSyncCompletedAt: string | null;
  lastSuccessfulSyncAt: string | null;
  lastError: string | null;
  lastErrorAt: string | null;
  lastFetchedJobCount: number;
  lastCreatedJobCount: number;
  lastUpdatedJobCount: number;
  note: string;
};

export type SourceRegistryDTO = {
  id: string;
  source: JobSource;
  displayName: string;
  externalIdentifier: string | null;
  baseUrl: string | null;
  isActive: boolean;
  trackedJobCount: number;
  status: SourceHealthStatus;
  lastSyncRequestedAt: string | null;
  lastSyncStartedAt: string | null;
  lastSyncCompletedAt: string | null;
  lastSuccessfulSyncAt: string | null;
  lastError: string | null;
  lastErrorAt: string | null;
  lastFetchedJobCount: number;
  lastCreatedJobCount: number;
  lastUpdatedJobCount: number;
  note: string;
};

export type SourceCreateDTO = {
  source: JobSource;
  externalIdentifier: string;
  displayName: string | null;
  isActive: boolean;
};

export type TrackerOverviewDTO = {
  userCount: number;
  jobCount: number;
  matchCount: number;
  applicationCount: number;
  configuredLiveSourceCount: number;
  lastIngestAt: string | null;
  lastScoreAt: string | null;
  lastPacketAt: string | null;
  lastApplyAt: string | null;
  redisConnected: boolean;
};

export type LoginRequestDTO = {
  email: string;
  password: string;
};

export type AuthSessionDTO = {
  accessToken: string;
  tokenType: string;
  user: UserProfileDTO;
};

export type DashboardSnapshotDTO = {
  profile: UserProfileDTO;
  preferences: UserPreferenceDTO;
  resume: ResumeDTO;
  jobs: JobDTO[];
  matches: MatchDTO[];
  applications: ApplicationDTO[];
  sourceHealth: SourceHealthDTO[];
  tracker: TrackerOverviewDTO;
};
