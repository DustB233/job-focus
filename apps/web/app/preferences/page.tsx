import { LiveDataUnavailableCard } from "@/components/live-data-unavailable-card";
import { PreferencesForm } from "@/components/dashboard/preferences-form";
import { PageShell } from "@/components/page-shell";
import { loadDashboardSnapshot } from "@/lib/dashboard-data";

export default async function PreferencesPage() {
  const result = await loadDashboardSnapshot();
  const snapshot = result.status === "ready" ? result.snapshot : null;
  const availabilityMessage =
    result.status === "unavailable" ? result.message : "Live preferences data is unavailable.";

  return (
    <PageShell
      activePath="/preferences"
      eyebrow="Target Preferences"
      title="Tune what gets scored, queued, and auto-applied."
      description="Preferred locations, work modes, employment types, and salary bounds all feed the matching engine and the review queue."
      snapshot={snapshot}
      availabilityMessage={result.status === "unavailable" ? result.message : null}
    >
      {snapshot ? (
        <PreferencesForm preferences={snapshot.preferences} />
      ) : (
        <LiveDataUnavailableCard
          title="Preferences unavailable"
          message={availabilityMessage}
        />
      )}
    </PageShell>
  );
}
