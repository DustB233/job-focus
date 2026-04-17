import { afterEach, describe, expect, it, vi } from "vitest";

import type { SourceHealthDTO, SourceRegistryDTO, TrackerOverviewDTO } from "@job-focus/shared";

import { loadSourceRegistryPageData } from "../lib/source-registry-data";

const sources: SourceRegistryDTO[] = [
  {
    id: "source-1",
    source: "greenhouse",
    displayName: "Greenhouse / Production Source",
    externalIdentifier: "production-source",
    baseUrl: "https://boards-api.greenhouse.io/v1/boards/production-source",
    isActive: true,
    trackedJobCount: 42,
    status: "healthy",
    lastSyncRequestedAt: null,
    lastSyncStartedAt: "2026-04-16T08:00:00.000Z",
    lastSyncCompletedAt: "2026-04-16T08:01:00.000Z",
    lastSuccessfulSyncAt: "2026-04-16T08:01:00.000Z",
    lastError: null,
    lastErrorAt: null,
    lastFetchedJobCount: 42,
    lastCreatedJobCount: 40,
    lastUpdatedJobCount: 2,
    note: "Latest sync succeeded and the source is producing jobs."
  }
];

const sourceHealth: SourceHealthDTO[] = [
  {
    id: "source-1",
    source: "greenhouse",
    displayName: "Greenhouse / Production Source",
    externalIdentifier: "production-source",
    baseUrl: "https://boards-api.greenhouse.io/v1/boards/production-source",
    status: "healthy",
    isActive: true,
    jobCount: 42,
    lastSeenAt: "2026-04-16T08:01:00.000Z",
    lastPostedAt: "2026-04-16T07:30:00.000Z",
    lastSyncRequestedAt: null,
    lastSyncStartedAt: "2026-04-16T08:00:00.000Z",
    lastSyncCompletedAt: "2026-04-16T08:01:00.000Z",
    lastSuccessfulSyncAt: "2026-04-16T08:01:00.000Z",
    lastError: null,
    lastErrorAt: null,
    lastFetchedJobCount: 42,
    lastCreatedJobCount: 40,
    lastUpdatedJobCount: 2,
    note: "Latest sync succeeded and the source is producing jobs."
  }
];

const tracker: TrackerOverviewDTO = {
  userCount: 1,
  jobCount: 42,
  matchCount: 42,
  applicationCount: 0,
  configuredLiveSourceCount: 1,
  lastIngestAt: "2026-04-16T08:01:00.000Z",
  lastScoreAt: "2026-04-16T08:02:00.000Z",
  lastPacketAt: null,
  lastApplyAt: null,
  redisConnected: true
};

describe("source registry page data", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("loads live source registry, health, and tracker data", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/sources")) {
        return { ok: true, json: async () => sources };
      }
      if (url.endsWith("/api/tracker/sources")) {
        return { ok: true, json: async () => sourceHealth };
      }
      if (url.endsWith("/api/tracker/overview")) {
        return { ok: true, json: async () => tracker };
      }
      return { ok: false, status: 404, json: async () => ({}) };
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await loadSourceRegistryPageData();

    expect(result.status).toBe("ready");
    if (result.status !== "ready") {
      throw new Error("Expected source registry data to load.");
    }
    expect(result.sources).toHaveLength(1);
    expect(result.sources[0]?.trackedJobCount).toBe(42);
    expect(result.sourceHealth[0]?.jobCount).toBe(42);
    expect(result.tracker.configuredLiveSourceCount).toBe(1);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({ cache: "no-store" });
  });
});
