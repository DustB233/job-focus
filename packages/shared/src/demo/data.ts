import type { DashboardSnapshotDTO } from "../dto";

export const demoDashboardSnapshot: DashboardSnapshotDTO = {
  profile: {
    id: "11cd0216-bf2e-4cf1-b7c4-4b735c2f03f9",
    email: "demo@jobfocus.dev",
    fullName: "Avery Collins",
    headline: "Senior Product Operations Manager moving into AI platform roles.",
    location: "Seattle, WA",
    targetRoles: ["Product Operations", "Program Manager", "AI Platform Operations"],
    yearsExperience: 8,
    seniorityLevel: "senior",
    authorizationRegions: ["US"],
    createdAt: "2026-04-12T09:00:00.000Z"
  },
  preferences: {
    id: "f0915f25-d23c-4743-b585-a21e0d450e46",
    userId: "11cd0216-bf2e-4cf1-b7c4-4b735c2f03f9",
    preferredLocations: ["Remote - US", "Seattle, WA"],
    preferredWorkModes: ["remote", "hybrid"],
    preferredEmploymentTypes: ["full_time"],
    desiredSalaryMin: 150000,
    desiredSalaryMax: 190000,
    autoApplyEnabled: false,
    autoApplyMinScore: 88,
    updatedAt: "2026-04-12T09:00:00.000Z"
  },
  resume: {
    id: "8d926335-6bbf-4fe0-9021-b0a2769038d6",
    userId: "11cd0216-bf2e-4cf1-b7c4-4b735c2f03f9",
    version: 1,
    title: "Avery Collins - Product Ops Resume",
    fileName: "avery-collins-resume.pdf",
    summary:
      "Scaled hiring operations, workflow automation, and GTM reporting across venture-backed SaaS teams.",
    skills: ["SQL", "Python", "Notion", "Automation", "Stakeholder Management", "Hiring Ops"],
    isDefault: true,
    updatedAt: "2026-04-12T09:30:00.000Z"
  },
  jobs: [
    {
      id: "c2b7d44e-c26c-418e-a8fe-a23810e51e26",
      externalJobId: "northstar-ai-program-manager",
      company: "Northstar Labs",
      title: "AI Program Manager",
      location: "Remote - US",
      workMode: "remote",
      employmentType: "full_time",
      source: "greenhouse",
      salaryMin: 155000,
      salaryMax: 185000,
      description: "Lead cross-functional delivery for AI product launches and process automation.",
      applicationUrl: "https://boards.greenhouse.io/northstar/jobs/12345",
      seniorityLevel: "senior",
      authorizationRequirement: "US work authorization required",
      postedAt: "2026-04-11T18:00:00.000Z"
    },
    {
      id: "c46f8d95-d508-4efa-b0f2-8ae0c640d95d",
      externalJobId: "relay-ops-systems-lead",
      company: "Relay Commerce",
      title: "Operations Systems Lead",
      location: "San Francisco, CA",
      workMode: "hybrid",
      employmentType: "full_time",
      source: "lever",
      salaryMin: 145000,
      salaryMax: 172000,
      description: "Own business systems, recruiting workflows, and operational analytics.",
      applicationUrl: "https://jobs.lever.co/relay/abc123",
      seniorityLevel: "lead",
      authorizationRequirement: "US work authorization required",
      postedAt: "2026-04-10T14:00:00.000Z"
    },
    {
      id: "ff193830-6d3f-492e-89ab-a94ef7511f9a",
      externalJobId: "meridian-platform-ops-manager",
      company: "Meridian AI",
      title: "Platform Operations Manager",
      location: "New York, NY",
      workMode: "remote",
      employmentType: "full_time",
      source: "ashby",
      salaryMin: 160000,
      salaryMax: 195000,
      description: "Build playbooks, scorecards, and launch systems for AI customer operations.",
      applicationUrl: "https://jobs.ashbyhq.com/meridian/xyz987",
      seniorityLevel: "senior",
      authorizationRequirement: "US work authorization required",
      postedAt: "2026-04-09T16:30:00.000Z"
    }
  ],
  matches: [
    {
      id: "d826f1d9-f9be-4705-90c3-2bcf2d0a5be1",
      userId: "11cd0216-bf2e-4cf1-b7c4-4b735c2f03f9",
      jobId: "c2b7d44e-c26c-418e-a8fe-a23810e51e26",
      score: 91,
      strength: "high",
      rationale: "Role lines up with AI operations, stakeholder leadership, and remote-first preference.",
      whyMatched: {
        totalScore: 91,
        strengths: ["Strong title overlap", "Remote preference aligned", "Skills overlap: Automation, Python"]
      },
      createdAt: "2026-04-12T10:00:00.000Z"
    },
    {
      id: "d5650b28-07ef-4fa4-8fb9-f588d3d85c3e",
      userId: "11cd0216-bf2e-4cf1-b7c4-4b735c2f03f9",
      jobId: "c46f8d95-d508-4efa-b0f2-8ae0c640d95d",
      score: 78,
      strength: "medium",
      rationale: "Strong systems overlap, slightly lower fit because of hybrid location constraints.",
      whyMatched: {
        totalScore: 78,
        concerns: ["Location fit is weaker than remote-first roles"]
      },
      createdAt: "2026-04-12T10:05:00.000Z"
    }
  ],
  applications: [
    {
      id: "9985d07f-a74e-42c1-9d0e-2d0b13c34074",
      userId: "11cd0216-bf2e-4cf1-b7c4-4b735c2f03f9",
      jobId: "c2b7d44e-c26c-418e-a8fe-a23810e51e26",
      status: "waiting_review",
      packetId: "7806e446-54d9-45fa-9f26-6432143af6f3",
      packetStatus: "waiting_review",
      notes: "Resume is tailored. Cover note still needs a final pass.",
      submittedAt: null,
      lastError: null,
      blockingReason: null,
      latestErrorCode: null,
      confirmationDetails: null,
      job: {
        id: "c2b7d44e-c26c-418e-a8fe-a23810e51e26",
        externalJobId: "northstar-ai-program-manager",
        company: "Northstar Labs",
        title: "AI Program Manager",
        location: "Remote - US",
        workMode: "remote",
        employmentType: "full_time",
        source: "greenhouse",
        salaryMin: 155000,
        salaryMax: 185000,
        description: "Lead cross-functional delivery for AI product launches and process automation.",
        applicationUrl: "https://boards.greenhouse.io/northstar/jobs/12345",
        seniorityLevel: "senior",
        authorizationRequirement: "US work authorization required",
        postedAt: "2026-04-11T18:00:00.000Z"
      },
      matchScore: 91,
      matchStrength: "high",
      packet: {
        id: "7806e446-54d9-45fa-9f26-6432143af6f3",
        userId: "11cd0216-bf2e-4cf1-b7c4-4b735c2f03f9",
        jobId: "c2b7d44e-c26c-418e-a8fe-a23810e51e26",
        resumeId: "8d926335-6bbf-4fe0-9021-b0a2769038d6",
        status: "waiting_review",
        selectedResumeVersion: 1,
        tailoredResumeSummary:
          "Targeted for cross-functional AI launch operations and workflow automation programs.",
        coverNote:
          "I have led cross-functional operating cadences and automation rollouts in fast-growing SaaS teams.",
        screeningAnswers: {
          work_authorization: "Authorized to work in the United States.",
          years_experience: "8 years of relevant experience.",
          location_flexibility: "Based in Seattle, WA and open to Remote - US, Seattle, WA opportunities.",
          work_mode_preference: "Preferred work modes: remote, hybrid."
        },
        missingFields: [],
        updatedAt: "2026-04-12T10:45:00.000Z"
      },
      events: [
        {
          id: "c3a35af7-86ea-4ae8-b7d7-4e55de6184dc",
          applicationId: "9985d07f-a74e-42c1-9d0e-2d0b13c34074",
          fromStatus: null,
          toStatus: "discovered",
          eventType: "created",
          actor: "seed",
          note: "Discovered from inbound job match.",
          payload: {},
          createdAt: "2026-04-12T10:40:00.000Z"
        },
        {
          id: "3b65b7e0-3db3-45c9-82d7-7c45df784e56",
          applicationId: "9985d07f-a74e-42c1-9d0e-2d0b13c34074",
          fromStatus: "discovered",
          toStatus: "shortlisted",
          eventType: "status_changed",
          actor: "seed",
          note: "Shortlisted because the match score crossed the review threshold.",
          payload: { matchScore: 91 },
          createdAt: "2026-04-12T10:42:00.000Z"
        },
        {
          id: "a05508ab-e43a-40e3-927f-84c9ed9151bf",
          applicationId: "9985d07f-a74e-42c1-9d0e-2d0b13c34074",
          fromStatus: "shortlisted",
          toStatus: "waiting_review",
          eventType: "status_changed",
          actor: "seed",
          note: "Packet prepared and queued for final review.",
          payload: { packetId: "7806e446-54d9-45fa-9f26-6432143af6f3" },
          createdAt: "2026-04-12T10:50:00.000Z"
        }
      ],
      createdAt: "2026-04-12T11:00:00.000Z",
      updatedAt: "2026-04-12T11:00:00.000Z"
    },
    {
      id: "eae6b6f3-c7e4-4b64-a96b-cb5c80eb8571",
      userId: "11cd0216-bf2e-4cf1-b7c4-4b735c2f03f9",
      jobId: "c46f8d95-d508-4efa-b0f2-8ae0c640d95d",
      status: "failed",
      packetId: "38bf8cb7-9890-4fd0-82c0-77d92354ca34",
      packetStatus: "finalized",
      notes: "Lever rejected the submission because a required field was missing.",
      submittedAt: null,
      lastError: "required_phone_missing",
      blockingReason: null,
      latestErrorCode: "required_phone_missing",
      confirmationDetails: null,
      job: {
        id: "c46f8d95-d508-4efa-b0f2-8ae0c640d95d",
        externalJobId: "relay-ops-systems-lead",
        company: "Relay Commerce",
        title: "Operations Systems Lead",
        location: "San Francisco, CA",
        workMode: "hybrid",
        employmentType: "full_time",
        source: "lever",
        salaryMin: 145000,
        salaryMax: 172000,
        description: "Own business systems, recruiting workflows, and operational analytics.",
        applicationUrl: "https://jobs.lever.co/relay/abc123",
        seniorityLevel: "lead",
        authorizationRequirement: "US work authorization required",
        postedAt: "2026-04-10T14:00:00.000Z"
      },
      matchScore: 78,
      matchStrength: "medium",
      packet: {
        id: "38bf8cb7-9890-4fd0-82c0-77d92354ca34",
        userId: "11cd0216-bf2e-4cf1-b7c4-4b735c2f03f9",
        jobId: "c46f8d95-d508-4efa-b0f2-8ae0c640d95d",
        resumeId: "8d926335-6bbf-4fe0-9021-b0a2769038d6",
        status: "finalized",
        selectedResumeVersion: 1,
        tailoredResumeSummary: "Positioned around systems ownership, analytics, and automation delivery.",
        coverNote: "I have owned systems programs and recruiting workflow improvements across SaaS operations teams.",
        screeningAnswers: {
          work_authorization: "Authorized to work in the United States.",
          years_experience: "8 years of relevant experience."
        },
        missingFields: [],
        updatedAt: "2026-04-12T12:00:00.000Z"
      },
      events: [
        {
          id: "f2051180-f4b9-4408-a236-fbf2e8a97acc",
          applicationId: "eae6b6f3-c7e4-4b64-a96b-cb5c80eb8571",
          fromStatus: null,
          toStatus: "discovered",
          eventType: "created",
          actor: "seed",
          note: "Created from seeded failure scenario.",
          payload: {},
          createdAt: "2026-04-12T11:40:00.000Z"
        },
        {
          id: "4206cc14-529f-4a1a-b523-53d78f8325e5",
          applicationId: "eae6b6f3-c7e4-4b64-a96b-cb5c80eb8571",
          fromStatus: "waiting_review",
          toStatus: "failed",
          eventType: "apply_failed",
          actor: "worker",
          note: "Missing required phone number for Lever submission.",
          payload: { errorCode: "required_phone_missing", provider: "lever" },
          createdAt: "2026-04-12T12:15:00.000Z"
        }
      ],
      createdAt: "2026-04-12T11:30:00.000Z",
      updatedAt: "2026-04-12T12:15:00.000Z"
    },
    {
      id: "9a0d54b6-c112-48f0-86c9-16687e7ca44f",
      userId: "11cd0216-bf2e-4cf1-b7c4-4b735c2f03f9",
      jobId: "ff193830-6d3f-492e-89ab-a94ef7511f9a",
      status: "submitted",
      packetId: "735d57a1-a7a8-4caf-b97d-bf7e32e4585b",
      packetStatus: "finalized",
      notes: "Submitted successfully through the ATS adapter.",
      submittedAt: "2026-04-12T13:20:00.000Z",
      lastError: null,
      blockingReason: null,
      latestErrorCode: null,
      confirmationDetails: {
        confirmationNumber: "ASHBY-20481",
        submittedAt: "2026-04-12T13:20:00.000Z"
      },
      job: {
        id: "ff193830-6d3f-492e-89ab-a94ef7511f9a",
        externalJobId: "meridian-platform-ops-manager",
        company: "Meridian AI",
        title: "Platform Operations Manager",
        location: "New York, NY",
        workMode: "remote",
        employmentType: "full_time",
        source: "ashby",
        salaryMin: 160000,
        salaryMax: 195000,
        description: "Build playbooks, scorecards, and launch systems for AI customer operations.",
        applicationUrl: "https://jobs.ashbyhq.com/meridian/xyz987",
        seniorityLevel: "senior",
        authorizationRequirement: "US work authorization required",
        postedAt: "2026-04-09T16:30:00.000Z"
      },
      matchScore: null,
      matchStrength: null,
      packet: {
        id: "735d57a1-a7a8-4caf-b97d-bf7e32e4585b",
        userId: "11cd0216-bf2e-4cf1-b7c4-4b735c2f03f9",
        jobId: "ff193830-6d3f-492e-89ab-a94ef7511f9a",
        resumeId: "8d926335-6bbf-4fe0-9021-b0a2769038d6",
        status: "finalized",
        selectedResumeVersion: 1,
        tailoredResumeSummary: "Framed for AI customer operations systems and launch playbooks.",
        coverNote: "I’m excited to bring operational rigor to AI customer programs and scale repeatable systems.",
        screeningAnswers: {
          work_authorization: "Authorized to work in the United States.",
          years_experience: "8 years of relevant experience."
        },
        missingFields: [],
        updatedAt: "2026-04-12T13:00:00.000Z"
      },
      events: [
        {
          id: "f0fbef82-c3b7-4f3a-a589-1c4f2f78ca1b",
          applicationId: "9a0d54b6-c112-48f0-86c9-16687e7ca44f",
          fromStatus: "submitting",
          toStatus: "submitted",
          eventType: "apply_succeeded",
          actor: "worker",
          note: "Ashby submission confirmed.",
          payload: {
            confirmationNumber: "ASHBY-20481",
            submittedAt: "2026-04-12T13:20:00.000Z"
          },
          createdAt: "2026-04-12T13:20:00.000Z"
        }
      ],
      createdAt: "2026-04-12T12:45:00.000Z",
      updatedAt: "2026-04-12T13:20:00.000Z"
    }
  ],
  sourceHealth: [
    {
      source: "greenhouse",
      displayName: "Greenhouse",
      status: "healthy",
      isActive: true,
      jobCount: 1,
      lastSeenAt: "2026-04-12T08:45:00.000Z",
      lastPostedAt: "2026-04-11T18:00:00.000Z",
      note: "Fresh ingest and recent postings are flowing."
    },
    {
      source: "lever",
      displayName: "Lever",
      status: "healthy",
      isActive: true,
      jobCount: 1,
      lastSeenAt: "2026-04-12T08:45:00.000Z",
      lastPostedAt: "2026-04-10T14:00:00.000Z",
      note: "Latest sync succeeded and the source is producing jobs."
    },
    {
      source: "ashby",
      displayName: "Ashby",
      status: "warning",
      isActive: true,
      jobCount: 1,
      lastSeenAt: "2026-04-10T09:00:00.000Z",
      lastPostedAt: "2026-04-09T16:30:00.000Z",
      note: "Source is active, but it looks less fresh than the supported ATS feeds."
    },
    {
      source: "manual",
      displayName: "Manual Link",
      status: "inactive",
      isActive: false,
      jobCount: 0,
      lastSeenAt: null,
      lastPostedAt: null,
      note: "Manual intake only. Automated discovery is intentionally disabled."
    }
  ],
  tracker: {
    userCount: 1,
    jobCount: 3,
    matchCount: 2,
    applicationCount: 3,
    configuredLiveSourceCount: 2,
    lastIngestAt: "2026-04-12T08:45:00.000Z",
    lastScoreAt: "2026-04-12T09:15:00.000Z",
    lastPacketAt: "2026-04-12T09:30:00.000Z",
    lastApplyAt: "2026-04-12T09:40:00.000Z",
    redisConnected: true
  }
};

export const demoUser = demoDashboardSnapshot.profile;
export const demoPreferences = demoDashboardSnapshot.preferences;
export const demoResume = demoDashboardSnapshot.resume;
export const demoJobs = demoDashboardSnapshot.jobs;
export const demoMatches = demoDashboardSnapshot.matches;
export const demoApplications = demoDashboardSnapshot.applications;
export const demoSourceHealth = demoDashboardSnapshot.sourceHealth;
export const demoTracker = demoDashboardSnapshot.tracker;
