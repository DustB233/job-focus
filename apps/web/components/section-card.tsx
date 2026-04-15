type SectionCardProps = {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
};

export function SectionCard({ title, subtitle, children }: SectionCardProps) {
  return (
    <section className="card section-stack">
      <div>
        <h3>{title}</h3>
        {subtitle ? <p className="muted">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}
