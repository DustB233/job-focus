import Link from "next/link";

const items = [
  { href: "/", label: "Overview", description: "System health and queue summary" },
  { href: "/profile", label: "Profile setup", description: "Identity, resume, and profile fields" },
  { href: "/preferences", label: "Target preferences", description: "Scoring and auto-apply guardrails" },
  { href: "/jobs", label: "Jobs discovered", description: "ATS ingestion and source health" },
  { href: "/sources", label: "Sources", description: "Manage live Greenhouse and Lever feeds" },
  { href: "/shortlisted", label: "Shortlisted jobs", description: "Ranked roles and why matched" },
  { href: "/applications", label: "Applications tracker", description: "Packet state and event history" },
  { href: "/review-queue", label: "Review queue", description: "Manual approve or reject decisions" },
  { href: "/logs", label: "Failure logs", description: "Normalized ATS failures and retries" }
];

export function Navigation({ activePath }: { activePath: string }) {
  return (
    <nav className="nav-list" aria-label="Primary">
      {items.map((item) => {
        const isActive = activePath === item.href;

        return (
          <Link
            key={item.href}
            className={`nav-link${isActive ? " active" : ""}`}
            href={item.href}
          >
            <span className="nav-title">{item.label}</span>
            <span className="nav-description">{item.description}</span>
          </Link>
        );
      })}
    </nav>
  );
}
