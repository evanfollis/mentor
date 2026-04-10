"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const USER_ID = 1;

interface LearnerState {
  current_week: number;
  current_phase: number;
  overall_mastery_score: number;
  streak_days: number;
  adaptive_difficulty: number;
  strengths: string[];
  weaknesses: string[];
}

interface WeekProgress {
  week_number: number;
  status: string;
  artifact_status: string;
  gate_score: number | null;
  gate_attempts: number;
  time_spent_minutes: number;
}

interface Phase {
  id: number;
  name: string;
  order: number;
  weeks: { week_number: number; title: string; is_high_roi: boolean; estimated_hours: number }[];
}

export default function ProgressPage() {
  const [state, setState] = useState<LearnerState | null>(null);
  const [progress, setProgress] = useState<WeekProgress[]>([]);
  const [phases, setPhases] = useState<Phase[]>([]);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/progress/${USER_ID}/state`).then((r) => r.ok ? r.json() : null),
      fetch(`${API}/api/progress/${USER_ID}/weeks`).then((r) => r.ok ? r.json() : []),
      fetch(`${API}/api/curriculum/phases`).then((r) => r.json()),
    ]).then(([s, p, ph]) => {
      setState(s);
      setProgress(p);
      setPhases(ph);
    });
  }, []);

  const getWeekProgress = (weekNum: number): WeekProgress | undefined =>
    progress.find((p) => p.week_number === weekNum);

  const statusColors: Record<string, string> = {
    completed: "var(--success)",
    in_progress: "var(--accent)",
    gate_pending: "var(--warning)",
    not_started: "var(--border)",
  };

  const startWeek = async (weekNumber: number) => {
    await fetch(`${API}/api/progress/${USER_ID}/weeks/${weekNumber}/start`, { method: "POST" });
    window.location.reload();
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <h1>Progress</h1>
        <Link href="/dashboard" style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
          Back to Dashboard
        </Link>
      </div>

      {/* Stats overview */}
      {state && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          gap: "1rem",
          marginBottom: "2.5rem",
        }}>
          <StatCard label="Current Week" value={`${state.current_week} / 16`} />
          <StatCard label="Phase" value={`${state.current_phase} / 4`} />
          <StatCard label="Mastery" value={`${state.overall_mastery_score.toFixed(0)}%`} color={state.overall_mastery_score >= 70 ? "var(--success)" : "var(--text-primary)"} />
          <StatCard label="Streak" value={`${state.streak_days}d`} />
          <StatCard label="Difficulty" value={`${(state.adaptive_difficulty * 100).toFixed(0)}%`} />
        </div>
      )}

      {/* Week-by-week breakdown */}
      {phases.map((phase) => (
        <div key={phase.id} style={{ marginBottom: "2rem" }}>
          <h2 style={{ fontSize: "1.1rem", color: "var(--accent)", marginBottom: "1rem" }}>
            Phase {phase.order}: {phase.name}
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {phase.weeks.map((week) => {
              const wp = getWeekProgress(week.week_number);
              const status = wp?.status || "not_started";
              const isCurrent = state?.current_week === week.week_number;

              return (
                <div
                  key={week.week_number}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "1rem",
                    padding: "0.8rem 1rem",
                    background: isCurrent ? "var(--bg-card)" : "transparent",
                    border: `1px solid ${isCurrent ? "var(--accent)" : "var(--border)"}`,
                    borderRadius: "6px",
                  }}
                >
                  {/* Status dot */}
                  <div style={{
                    width: 10, height: 10, borderRadius: "50%",
                    background: statusColors[status],
                    flexShrink: 0,
                  }} />

                  {/* Week info */}
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: "0.9rem" }}>
                      <strong>Week {week.week_number}</strong>: {week.title}
                      {week.is_high_roi && (
                        <span style={{ color: "var(--warning)", fontSize: "0.75rem", marginLeft: "0.5rem" }}>
                          HIGH ROI
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
                      {status === "completed" && wp
                        ? `Completed | Gate: ${((wp.gate_score || 0) * 100).toFixed(0)}% | ${wp.time_spent_minutes}min logged`
                        : status === "in_progress"
                          ? `In progress | ${wp?.time_spent_minutes || 0}min logged`
                          : status === "gate_pending"
                            ? `Gate pending | ${wp?.gate_attempts || 0} attempts`
                            : `~${week.estimated_hours}h estimated`}
                    </div>
                  </div>

                  {/* Actions */}
                  {status === "not_started" && isCurrent && (
                    <button
                      onClick={() => startWeek(week.week_number)}
                      style={{
                        padding: "0.3rem 0.8rem",
                        background: "var(--accent)",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        fontSize: "0.8rem",
                      }}
                    >
                      Start
                    </button>
                  )}
                  {(status === "in_progress" || status === "gate_pending" || status === "completed") && (
                    <Link
                      href={`/artifact?week=${week.week_number}`}
                      style={{
                        padding: "0.3rem 0.8rem",
                        background: "var(--bg-card)",
                        border: `1px solid ${wp?.artifact_status === "reviewed" ? "var(--success)" : "var(--border)"}`,
                        borderRadius: "4px",
                        fontSize: "0.8rem",
                        color: wp?.artifact_status === "reviewed" ? "var(--success)" : "var(--text-primary)",
                      }}
                    >
                      Artifact
                    </Link>
                  )}
                  {(status === "gate_pending" || (status === "in_progress" && isCurrent)) && (
                    <Link
                      href={`/gate-review?week=${week.week_number}`}
                      style={{
                        padding: "0.3rem 0.8rem",
                        background: "var(--bg-card)",
                        border: "1px solid var(--border)",
                        borderRadius: "4px",
                        fontSize: "0.8rem",
                        color: "var(--text-primary)",
                      }}
                    >
                      Gate Review
                    </Link>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{
      padding: "1rem",
      background: "var(--bg-card)",
      border: "1px solid var(--border)",
      borderRadius: "6px",
      textAlign: "center",
    }}>
      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: color || "var(--text-primary)" }}>{value}</div>
      <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{label}</div>
    </div>
  );
}
