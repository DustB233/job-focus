type BadgeTone = "neutral" | "success" | "warning" | "accent" | "danger";

export function StatusBadge({
  label,
  tone = "neutral"
}: {
  label: string;
  tone?: BadgeTone;
}) {
  return <span className={`badge ${tone}`}>{label}</span>;
}
