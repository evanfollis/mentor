"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface LearnerState {
  current_week: number;
  current_phase: number;
  overall_mastery_score: number;
  streak_days: number;
  adaptive_difficulty: number;
  strengths: string[];
  weaknesses: string[];
}

interface Phase {
  id: number;
  name: string;
  order: number;
  weeks: { week_number: number; title: string; is_high_roi: boolean }[];
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const USER_ID = 1; // TODO: proper auth

export default function DashboardPage() {
  const [state, setState] = useState<LearnerState | null>(null);
  const [phases, setPhases] = useState<Phase[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/progress/${USER_ID}/state`).then((r) => r.ok ? r.json() : null),
      fetch(`${API}/api/curriculum/phases`).then((r) => r.json()),
    ])
      .then(([s, p]) => {
        setState(s);
        setPhases(p);
      })
      .catch(() => setError("Could not connect to backend. Is docker-compose running?"));
  }, []);

  if (error) {
    return (
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem" }}>
        <h1>Dashboard</h1>
        <p style={{ color: "var(--danger)", marginTop: "1rem" }}>{error}</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem" }}>
      <h1 style={{ marginBottom: "2rem" }}>Dashboard</h1>

      {state && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
            gap: "1rem",
            marginBottom: "2rem",
          }}
        >
          <StatCard label="Current Week" value={state.current_week} />
          <StatCard label="Phase" value={state.current_phase} />
          <StatCard label="Mastery" value={`${state.overall_mastery_score}%`} />
          <StatCard label="Streak" value={`${state.streak_days} days`} />
          <StatCard label="Difficulty" value={`${(state.adaptive_difficulty * 100).toFixed(0)}%`} />
        </div>
      )}

      <h2 style={{ marginBottom: "1rem" }}>Curriculum</h2>
      {phases.map((phase) => (
        <div key={phase.id} style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ color: "var(--accent)", marginBottom: "0.5rem" }}>
            Phase {phase.order}: {phase.name}
          </h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
            {phase.weeks.map((week) => (
              <span
                key={week.week_number}
                style={{
                  padding: "0.4rem 0.8rem",
                  background:
                    state && week.week_number === state.current_week
                      ? "var(--accent)"
                      : state && week.week_number < state.current_week
                        ? "var(--success)"
                        : "var(--bg-card)",
                  border: `1px solid ${week.is_high_roi ? "var(--warning)" : "var(--border)"}`,
                  borderRadius: "4px",
                  fontSize: "0.85rem",
                  color: "var(--text-primary)",
                }}
                title={`${week.title}${week.is_high_roi ? " (High ROI)" : ""}`}
              >
                W{week.week_number}
              </span>
            ))}
          </div>
        </div>
      ))}

      <div style={{ marginTop: "2rem", display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <Link
          href="/chat"
          style={{
            padding: "0.8rem 1.5rem",
            background: "var(--accent)",
            color: "white",
            borderRadius: "6px",
            fontWeight: 500,
          }}
        >
          Start Study Session
        </Link>
        <Link
          href="/cards"
          style={{
            padding: "0.8rem 1.5rem",
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: "6px",
          }}
        >
          Review Cards
        </Link>
        <Link
          href="/gate-review"
          style={{
            padding: "0.8rem 1.5rem",
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: "6px",
          }}
        >
          Gate Review
        </Link>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div
      style={{
        padding: "1rem",
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "6px",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>{value}</div>
      <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{label}</div>
    </div>
  );
}
