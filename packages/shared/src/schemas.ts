import { z } from "zod";

import {
  applicationStatuses,
  employmentTypes,
  jobSources,
  matchStrengths,
  packetStatuses,
  reviewActions,
  sourceHealthStatuses,
  workModes
} from "./enums";

export const userProfileSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  fullName: z.string().min(1),
  headline: z.string().min(1),
  location: z.string().min(1),
  targetRoles: z.array(z.string().min(1)).min(1),
  yearsExperience: z.number().int().min(0),
  seniorityLevel: z.string().min(1).nullable(),
  authorizationRegions: z.array(z.string().min(1)),
  createdAt: z.string().datetime()
});

export const profileUpdateSchema = userProfileSchema.omit({
  id: true,
  email: true,
  createdAt: true
});

export const resumeSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  version: z.number().int().positive(),
  title: z.string().min(1),
  fileName: z.string().min(1),
  summary: z.string().min(1),
  skills: z.array(z.string().min(1)).min(1),
  isDefault: z.boolean(),
  updatedAt: z.string().datetime()
});

export const userPreferenceSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  preferredLocations: z.array(z.string().min(1)),
  preferredWorkModes: z.array(z.enum(workModes)),
  preferredEmploymentTypes: z.array(z.enum(employmentTypes)),
  desiredSalaryMin: z.number().int().nonnegative().nullable(),
  desiredSalaryMax: z.number().int().nonnegative().nullable(),
  autoApplyEnabled: z.boolean(),
  autoApplyMinScore: z.number().int().min(0).max(100),
  updatedAt: z.string().datetime()
});

export const userPreferenceUpdateSchema = userPreferenceSchema.omit({
  id: true,
  userId: true,
  updatedAt: true
});

export const jobSchema = z.object({
  id: z.string().uuid(),
  sourceId: z.string().uuid(),
  externalJobId: z.string().min(1),
  company: z.string().min(1),
  title: z.string().min(1),
  location: z.string().min(1),
  workMode: z.enum(workModes),
  employmentType: z.enum(employmentTypes),
  source: z.enum(jobSources),
  sourceDisplayName: z.string().min(1),
  sourceExternalIdentifier: z.string().min(1).nullable(),
  salaryMin: z.number().int().nonnegative(),
  salaryMax: z.number().int().nonnegative(),
  description: z.string().min(1),
  applicationUrl: z.string().url().nullable(),
  seniorityLevel: z.string().min(1).nullable(),
  authorizationRequirement: z.string().min(1).nullable(),
  postedAt: z.string().datetime()
});

export const discoveredJobSchema = z.object({
  source: z.enum(jobSources),
  externalJobId: z.string().min(1),
  company: z.string().min(1),
  title: z.string().min(1),
  location: z.string().min(1),
  workMode: z.enum(workModes),
  employmentType: z.enum(employmentTypes),
  salaryMin: z.number().int().nonnegative(),
  salaryMax: z.number().int().nonnegative(),
  description: z.string().min(1),
  applicationUrl: z.string().url().nullable(),
  seniorityLevel: z.string().min(1).nullable(),
  authorizationRequirement: z.string().min(1).nullable(),
  postedAt: z.string().datetime(),
  rawPayload: z.record(z.unknown())
});

export const matchSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  jobId: z.string().uuid(),
  score: z.number().int().min(0).max(100),
  strength: z.enum(matchStrengths),
  rationale: z.string().min(1),
  whyMatched: z.record(z.unknown()),
  createdAt: z.string().datetime()
});

export const applicationPacketSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  jobId: z.string().uuid(),
  resumeId: z.string().uuid().nullable(),
  status: z.enum(packetStatuses),
  selectedResumeVersion: z.number().int().positive().nullable(),
  tailoredResumeSummary: z.string().nullable(),
  coverNote: z.string().nullable(),
  screeningAnswers: z.record(z.string()),
  missingFields: z.array(z.string()),
  updatedAt: z.string().datetime()
});

export const applicationEventSchema = z.object({
  id: z.string().uuid(),
  applicationId: z.string().uuid(),
  fromStatus: z.enum(applicationStatuses).nullable(),
  toStatus: z.enum(applicationStatuses),
  eventType: z.string().min(1),
  actor: z.string().min(1),
  note: z.string().nullable(),
  payload: z.record(z.unknown()),
  createdAt: z.string().datetime()
});

export const applicationSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  jobId: z.string().uuid(),
  status: z.enum(applicationStatuses),
  packetId: z.string().uuid().nullable(),
  packetStatus: z.enum(packetStatuses).nullable(),
  notes: z.string(),
  submittedAt: z.string().datetime().nullable(),
  lastError: z.string().nullable(),
  blockingReason: z.string().nullable(),
  latestErrorCode: z.string().nullable(),
  confirmationDetails: z.record(z.unknown()).nullable(),
  job: jobSchema,
  matchScore: z.number().int().min(0).max(100).nullable(),
  matchStrength: z.enum(matchStrengths).nullable(),
  packet: applicationPacketSchema.nullable(),
  events: z.array(applicationEventSchema),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime()
});

export const applicationReviewRequestSchema = z.object({
  action: z.enum(reviewActions),
  note: z.string().nullable()
});

export const sourceHealthSchema = z.object({
  id: z.string().uuid(),
  source: z.enum(jobSources),
  displayName: z.string().min(1),
  externalIdentifier: z.string().min(1).nullable(),
  baseUrl: z.string().url().nullable(),
  status: z.enum(sourceHealthStatuses),
  isActive: z.boolean(),
  jobCount: z.number().int().nonnegative(),
  lastSeenAt: z.string().datetime().nullable(),
  lastPostedAt: z.string().datetime().nullable(),
  lastSyncRequestedAt: z.string().datetime().nullable(),
  lastSyncStartedAt: z.string().datetime().nullable(),
  lastSyncCompletedAt: z.string().datetime().nullable(),
  lastSuccessfulSyncAt: z.string().datetime().nullable(),
  lastError: z.string().nullable(),
  lastErrorAt: z.string().datetime().nullable(),
  lastFetchedJobCount: z.number().int().nonnegative(),
  lastCreatedJobCount: z.number().int().nonnegative(),
  lastUpdatedJobCount: z.number().int().nonnegative(),
  note: z.string().min(1)
});

export const sourceRegistrySchema = z.object({
  id: z.string().uuid(),
  source: z.enum(jobSources),
  displayName: z.string().min(1),
  externalIdentifier: z.string().min(1).nullable(),
  baseUrl: z.string().url().nullable(),
  isActive: z.boolean(),
  trackedJobCount: z.number().int().nonnegative(),
  status: z.enum(sourceHealthStatuses),
  lastSyncRequestedAt: z.string().datetime().nullable(),
  lastSyncStartedAt: z.string().datetime().nullable(),
  lastSyncCompletedAt: z.string().datetime().nullable(),
  lastSuccessfulSyncAt: z.string().datetime().nullable(),
  lastError: z.string().nullable(),
  lastErrorAt: z.string().datetime().nullable(),
  lastFetchedJobCount: z.number().int().nonnegative(),
  lastCreatedJobCount: z.number().int().nonnegative(),
  lastUpdatedJobCount: z.number().int().nonnegative(),
  note: z.string().min(1)
});

export const sourceCreateSchema = z.object({
  source: z.enum(jobSources),
  externalIdentifier: z.string().min(1),
  displayName: z.string().min(1).nullable(),
  isActive: z.boolean()
});

export const trackerOverviewSchema = z.object({
  userCount: z.number().int().nonnegative(),
  jobCount: z.number().int().nonnegative(),
  matchCount: z.number().int().nonnegative(),
  applicationCount: z.number().int().nonnegative(),
  configuredLiveSourceCount: z.number().int().nonnegative(),
  lastIngestAt: z.string().datetime().nullable(),
  lastScoreAt: z.string().datetime().nullable(),
  lastPacketAt: z.string().datetime().nullable(),
  lastApplyAt: z.string().datetime().nullable(),
  redisConnected: z.boolean()
});

export const loginRequestSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
});

export const authSessionSchema = z.object({
  accessToken: z.string().min(1),
  tokenType: z.string().min(1),
  user: userProfileSchema
});

export const dashboardSnapshotSchema = z.object({
  profile: userProfileSchema,
  preferences: userPreferenceSchema,
  resume: resumeSchema,
  jobs: z.array(jobSchema),
  matches: z.array(matchSchema),
  applications: z.array(applicationSchema),
  sourceHealth: z.array(sourceHealthSchema),
  tracker: trackerOverviewSchema
});
