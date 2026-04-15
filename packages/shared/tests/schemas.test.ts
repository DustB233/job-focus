import { describe, expect, it } from "vitest";

import {
  applicationSchema,
  discoveredJobSchema,
  jobSchema,
  userProfileSchema
} from "../src";
import { demoApplications, demoJobs, demoUser } from "../src/demo/data";

describe("shared schemas", () => {
  it("validates the demo user profile", () => {
    expect(userProfileSchema.parse(demoUser).email).toBe("demo@jobfocus.dev");
  });

  it("validates demo jobs", () => {
    expect(jobSchema.parse(demoJobs[0]).company).toBe("Northstar Labs");
  });

  it("validates demo applications", () => {
    expect(applicationSchema.parse(demoApplications[0]).status).toBe("waiting_review");
  });

  it("validates discovered job payloads", () => {
    expect(
      discoveredJobSchema.parse({
        source: "greenhouse",
        externalJobId: "role-123",
        company: "Northstar Labs",
        title: "AI Program Manager",
        location: "Remote - US",
        workMode: "remote",
        employmentType: "full_time",
        salaryMin: 150000,
        salaryMax: 180000,
        description: "Lead AI program delivery.",
        applicationUrl: "https://boards.greenhouse.io/example/jobs/123",
        seniorityLevel: "senior",
        authorizationRequirement: "US work authorization required",
        postedAt: "2026-04-12T10:00:00.000Z",
        rawPayload: { id: 123 }
      }).source
    ).toBe("greenhouse");
  });
});
