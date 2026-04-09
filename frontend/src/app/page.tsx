import Link from "next/link";

export default function Home() {
  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem" }}>
      <header style={{ marginBottom: "3rem" }}>
        <h1 style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>AI Mentor</h1>
        <p style={{ color: "var(--text-secondary)" }}>
          Personal AI Architecture Learning System
        </p>
      </header>

      <nav
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
          gap: "1rem",
        }}
      >
        <NavCard
          href="/dashboard"
          title="Dashboard"
          description="Overview of your progress, current week, and upcoming tasks"
        />
        <NavCard
          href="/chat"
          title="Chat with Mentor"
          description="Ask questions, get explanations, or start a Socratic session"
        />
        <NavCard
          href="/progress"
          title="Progress"
          description="Detailed progress tracking, quiz scores, and mastery analytics"
        />
        <NavCard
          href="/gate-review"
          title="Gate Review"
          description="Attempt gate questions to advance to the next week"
        />
      </nav>
    </div>
  );
}

function NavCard({
  href,
  title,
  description,
}: {
  href: string;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      style={{
        display: "block",
        padding: "1.5rem",
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "8px",
        textDecoration: "none",
        transition: "border-color 0.2s",
      }}
    >
      <h2 style={{ fontSize: "1.2rem", marginBottom: "0.5rem", color: "var(--text-primary)" }}>
        {title}
      </h2>
      <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
        {description}
      </p>
    </Link>
  );
}
