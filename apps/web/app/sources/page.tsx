import { SourcesAdmin } from "@/components/dashboard/sources-admin";
import { LiveDataUnavailableCard } from "@/components/live-data-unavailable-card";
import { PageShell } from "@/components/page-shell";
import { formatTimestamp } from "@/lib/dashboard-data";
import { loadSourceRegistryPageData } from "@/lib/source-registry-data";

export default async function SourcesPage() {
  const result = await loadSourceRegistryPageData();

  if (result.status !== "ready") {
    return (
      <PageShell
        activePath="/sources"
        eyebrow="Sources"
        title="Manage the live source registry."
        description="Register Greenhouse boards and Lever sites, inspect their health, and queue syncs without touching environment variables."
        availabilityMessage={result.message}
      >
        <LiveDataUnavailableCard title="Source registry unavailable" message={result.message} />
      </PageShell>
    );
  }

  const { sourceHealth, sources, tracker } = result;

  return (
    <PageShell
      activePath="/sources"
      eyebrow="Sources"
      title="Manage the live source registry."
      description="Register Greenhouse boards and Lever sites, inspect their health, and queue syncs without touching environment variables."
      trackerOverride={tracker}
      sourceHealthOverride={sourceHealth}
      summaryChips={
        <>
          <span className="chip">
            {tracker.configuredLiveSourceCount} live source
            {tracker.configuredLiveSourceCount === 1 ? "" : "s"} configured
          </span>
          <span className="chip">{sources.length} total registry records</span>
          <span className="chip">
            Last ingest {formatTimestamp(tracker.lastIngestAt)}
          </span>
          <span className="chip">Redis {tracker.redisConnected ? "connected" : "unavailable"}</span>
        </>
      }
    >
      <SourcesAdmin initialSources={sources} />
    </PageShell>
  );
}
