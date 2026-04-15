import type { SourceHealthDTO, SourceRegistryDTO, TrackerOverviewDTO } from "@job-focus/shared";

import { apiBaseUrl } from "./client-api";

export type SourceRegistryLoadResult =
  | {
      status: "ready";
      sources: SourceRegistryDTO[];
      sourceHealth: SourceHealthDTO[];
      tracker: TrackerOverviewDTO;
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

export async function loadSourceRegistryPageData(): Promise<SourceRegistryLoadResult> {
  try {
    const [sources, sourceHealth, tracker] = await Promise.all([
      fetchFromApi<SourceRegistryDTO[]>("/api/sources"),
      fetchFromApi<SourceHealthDTO[]>("/api/tracker/sources"),
      fetchFromApi<TrackerOverviewDTO>("/api/tracker/overview")
    ]);

    return {
      status: "ready",
      sources,
      sourceHealth,
      tracker
    };
  } catch (error) {
    return {
      status: "unavailable",
      message:
        error instanceof Error ? error.message : "Unable to load live source registry data."
    };
  }
}
