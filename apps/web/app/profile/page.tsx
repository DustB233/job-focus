import { LiveDataUnavailableCard } from "@/components/live-data-unavailable-card";
import { ProfileSetupForm } from "@/components/dashboard/profile-setup-form";
import { PageShell } from "@/components/page-shell";
import { loadDashboardSnapshot } from "@/lib/dashboard-data";

export default async function ProfilePage() {
  const result = await loadDashboardSnapshot();
  const snapshot = result.status === "ready" ? result.snapshot : null;
  const availabilityMessage =
    result.status === "unavailable" ? result.message : "Live profile data is unavailable.";

  return (
    <PageShell
      activePath="/profile"
      eyebrow="Profile Setup"
      title="Keep candidate data structured before automation touches it."
      description="This page owns the approved profile fields used by matching, packet generation, and ATS submission adapters."
      snapshot={snapshot}
      availabilityMessage={result.status === "unavailable" ? result.message : null}
    >
      {snapshot ? (
        <ProfileSetupForm profile={snapshot.profile} resume={snapshot.resume} />
      ) : (
        <LiveDataUnavailableCard
          title="Profile unavailable"
          message={availabilityMessage}
        />
      )}
    </PageShell>
  );
}
