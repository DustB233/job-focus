import { SectionCard } from "./section-card";

type LiveDataEmptyStateCardProps = {
  title: string;
  description: string;
  hint?: string | null;
};

export function LiveDataEmptyStateCard({
  title,
  description,
  hint
}: LiveDataEmptyStateCardProps) {
  return (
    <SectionCard title={title} subtitle="This page only shows live backend state.">
      <div className="empty-state">
        <p className="muted">{description}</p>
        {hint ? <p className="muted">{hint}</p> : null}
      </div>
    </SectionCard>
  );
}
