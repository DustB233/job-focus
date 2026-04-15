import { SectionCard } from "./section-card";

type LiveDataUnavailableCardProps = {
  title: string;
  message: string;
};

export function LiveDataUnavailableCard({
  title,
  message
}: LiveDataUnavailableCardProps) {
  return (
    <SectionCard
      title={title}
      subtitle="This page only renders live API-backed data."
    >
      <div className="empty-state">
        <p className="muted">
          The backend response required for this page is unavailable right now, so no demo or
          static data is being shown.
        </p>
        <p className="feedback error">{message}</p>
      </div>
    </SectionCard>
  );
}
