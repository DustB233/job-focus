import { afterEach, describe, expect, it, vi } from "vitest";

import type { DashboardSnapshotDTO } from "@job-focus/shared";

import {
  buildJobLookup,
  buildOverviewMetrics,
  formatSalary,
  loadDashboardSnapshot
} from "../lib/dashboard-data";

const testDashboardSnapshot: DashboardSnapshotDTO = {
  profile: {
    id: "user-1",
    email: "candidate@example.com",
    fullName: "Avery Collins",
    headline: "Operations leader",
    location: "Seattle, WA",
    targetRoles: ["Program Manager"],
    yearsExperience: 8,
    seniorityLevel: "senior",
    authorizationRegions: ["US"],
    createdAt: "2026-04-12T09:00:00.000Z"
  },
  preferences: {
    id: "pref-1",
    userId: "user-1",
    preferredLocations: ["Remote - US"],
    preferredWorkModes: ["remote"],
    preferredEmploymentTypes: ["full_time"],
    desiredSalaryMin: 150000,
    desiredSalaryMax: 190000,
    autoApplyEnabled: false,
    autoApplyMinScore: 88,
    updatedAt: "2026-04-12T09:00:00.000Z"
  },
  resume: {
    id: "resume-1",
    userId: "user-1",
    version: 1,
    title: "Avery Collins Resume",
    fileName: "avery-collins-resume.pdf",
    summary: "Structured summary.",
    skills: ["Python", "Automation"],
    isDefault: true,
    updatedAt: "2026-04-12T09:30:00.000Z"
  },
  jobs: [
    {
      id: "job-1",
      externalJobId: "northstar-ai-program-manager",
      company: "Northstar Labs",
      title: "AI Program Manager",
      location: "Remote - US",
      workMode: "remote",
      employmentType: "full_time",
      source: "greenhouse",
      salaryMin: 155000,
      salaryMax: 185000,
      description: "Lead AI launches.",
      applicationUrl: "https://boards.greenhouse.io/northstar/jobs/12345",
      seniorityLevel: "senior",
      authorizationRequirement: "US work authorization required",
      postedAt: "2026-04-11T18:00:00.000Z"
    },
    {
      id: "job-2",
      externalJobId: "relay-ops-systems-lead",
      company: "Relay Commerce",
      title: "Operations Systems Lead",
      location: "San Francisco, CA",
      workMode: "hybrid",
      employmentType: "full_time",
      source: "lever",
      salaryMin: 145000,
      salaryMax: 172000,
      description: "Own systems.",
      applicationUrl: "https://jobs.lever.co/relay/abc123",
      seniorityLevel: "lead",
      authorizationRequirement: "US work authorization required",
      postedAt: "2026-04-10T14:00:00.000Z"
    },
    {
      id: "job-3",
      externalJobId: "meridian-platform-ops-manager",
      company: "Meridian AI",
      title: "Platform Operations Manager",
      location: "New York, NY",
      workMode: "remote",
      employmentType: "full_time",
      source: "manual",
      salaryMin: 160000,
      salaryMax: 195000,
      description: "Build playbooks.",
      applicationUrl: "https://example.com/apply",
      seniorityLevel: "senior",
      authorizationRequirement: "US work authorization required",
      postedAt: "2026-04-09T16:30:00.000Z"
    }
  ],
  matches: [
    {
      id: "match-1",
      userId: "user-1",
      jobId: "job-1",
      score: 91,
      strength: "high",
      rationale: "Strong overlap.",
      whyMatched: {
        strengths: ["Strong title overlap", "Remote preference aligned"]
      },
      createdAt: "2026-04-12T10:00:00.000Z"
    },
    {
      id: "match-2",
      userId: "user-1",
      jobId: "job-2",
      score: 78,
      strength: "medium",
      rationale: "Good systems fit.",
      whyMatched: {
        strengths: ["Good title overlap"]
      },
      createdAt: "2026-04-12T10:05:00.000Z"
    }
  ],
  applications: [
    {
      id: "application-1",
      userId: "user-1",
      jobId: "job-1",
      status: "waiting_review",
      packetId: "packet-1",
      packetStatus: "waiting_review",
      notes: "Packet ready.",
      submittedAt: null,
      lastError: null,
      blockingReason: null,
      latestErrorCode: null,
      confirmationDetails: null,
      job: {
        id: "job-1",
        externalJobId: "northstar-ai-program-manager",
        company: "Northstar Labs",
        title: "AI Program Manager",
        location: "Remote - US",
        workMode: "remote",
        employmentType: "full_time",
        source: "greenhouse",
        salaryMin: 155000,
        salaryMax: 185000,
        description: "Lead AI launches.",
        applicationUrl: "https://boards.greenhouse.io/northstar/jobs/12345",
        seniorityLevel: "senior",
        authorizationRequirement: "US work authorization required",
        postedAt: "2026-04-11T18:00:00.000Z"
      },
      matchScore: 91,
      matchStrength: "high",
      packet: {
        id: "packet-1",
        userId: "user-1",
        jobId: "job-1",
        resumeId: "resume-1",
        status: "waiting_review",
        selectedResumeVersion: 1,
        tailoredResumeSummary: "Tailored summary",
        coverNote: "Cover note",
        screeningAnswers: {
          work_authorization: "Authorized to work in the United States."
        },
        missingFields: [],
        updatedAt: "2026-04-12T10:45:00.000Z"
      },
      events: [],
      createdAt: "2026-04-12T11:00:00.000Z",
      updatedAt: "2026-04-12T11:00:00.000Z"
    },
    {
      id: "application-2",
      userId: "user-1",
      jobId: "job-2",
      status: "submitted",
      packetId: "packet-2",
      packetStatus: "finalized",
      notes: "Submitted.",
      submittedAt: "2026-04-12T13:20:00.000Z",
      lastError: null,
      blockingReason: null,
      latestErrorCode: null,
      confirmationDetails: {
        confirmationId: "lv-456"
      },
      job: {
        id: "job-2",
        externalJobId: "relay-ops-systems-lead",
        company: "Relay Commerce",
        title: "Operations Systems Lead",
        location: "San Francisco, CA",
        workMode: "hybrid",
        employmentType: "full_time",
        source: "lever",
        salaryMin: 145000,
        salaryMax: 172000,
        description: "Own systems.",
        applicationUrl: "https://jobs.lever.co/relay/abc123",
        seniorityLevel: "lead",
        authorizationRequirement: "US work authorization required",
        postedAt: "2026-04-10T14:00:00.000Z"
      },
      matchScore: 78,
      matchStrength: "medium",
      packet: null,
      events: [],
      createdAt: "2026-04-12T12:45:00.000Z",
      updatedAt: "2026-04-12T13:20:00.000Z"
    },
    {
      id: "application-3",
      userId: "user-1",
      jobId: "job-3",
      status: "failed",
      packetId: null,
      packetStatus: null,
      notes: "Failed submission.",
      submittedAt: null,
      lastError: "required_phone_missing",
      blockingReason: null,
      latestErrorCode: "required_phone_missing",
      confirmationDetails: null,
      job: {
        id: "job-3",
        externalJobId: "meridian-platform-ops-manager",
        company: "Meridian AI",
        title: "Platform Operations Manager",
        location: "New York, NY",
        workMode: "remote",
        employmentType: "full_time",
        source: "manual",
        salaryMin: 160000,
        salaryMax: 195000,
        description: "Build playbooks.",
        applicationUrl: "https://example.com/apply",
        seniorityLevel: "senior",
        authorizationRequirement: "US work authorization required",
        postedAt: "2026-04-09T16:30:00.000Z"
      },
      matchScore: null,
      matchStrength: null,
      packet: null,
      events: [],
      createdAt: "2026-04-12T11:30:00.000Z",
      updatedAt: "2026-04-12T12:15:00.000Z"
    }
  ],
  sourceHealth: [
    {
      source: "greenhouse",
      displayName: "Greenhouse",
      status: "healthy",
      isActive: true,
      jobCount: 1,
      lastSeenAt: "2026-04-12T10:00:00.000Z",
      lastPostedAt: "2026-04-11T18:00:00.000Z",
      note: "Healthy source."
    }
  ],
  tracker: {
    userCount: 1,
    jobCount: 3,
    matchCount: 2,
    applicationCount: 3,
    configuredLiveSourceCount: 2,
    lastIngestAt: "2026-04-12T10:00:00.000Z",
    lastScoreAt: "2026-04-12T10:05:00.000Z",
    lastPacketAt: "2026-04-12T10:45:00.000Z",
    lastApplyAt: "2026-04-12T13:20:00.000Z",
    redisConnected: true
  }
};

describe("dashboard data helpers", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("builds overview metrics from a live snapshot payload", () => {
    const metrics = buildOverviewMetrics(testDashboardSnapshot);

    expect(metrics[0]?.value).toBe(3);
    expect(metrics[1]?.value).toBe(3);
  });

  it("indexes jobs by id", () => {
    const lookup = buildJobLookup(testDashboardSnapshot);

    expect(lookup.get(testDashboardSnapshot.jobs[0]!.id)?.company).toBe("Northstar Labs");
  });

  it("formats salary ranges", () => {
    expect(formatSalary(testDashboardSnapshot.jobs[0]!)).toContain("$155,000");
  });

  it("returns an unavailable state instead of demo data when the API is down", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 503
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await loadDashboardSnapshot();

    expect(result.status).toBe("unavailable");
    expect(result.message).toContain("Failed to load");
    expect(fetchMock).toHaveBeenCalled();
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({ cache: "no-store" });
  });
});
