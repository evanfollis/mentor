"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const USER_ID = 1;

interface GateResult {
  passed: boolean;
  overall_score: number;
  question_scores: Record<string, { score: number; feedback: string }>;
  feedback: string;
  attempt_number: number;
}

interface WeekDetail {
  week_number: number;
  title: string;
  gate_questions: { questions: string[] };
  phase_name: string;
}

export default function GateReviewPage() {
  const searchParams = useSearchParams();
  const weekParam = searchParams.get("week");

  const [weekNumber, setWeekNumber] = useState(weekParam ? parseInt(weekParam) : 1);
  const [week, setWeek] = useState<WeekDetail | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<GateResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/api/curriculum/weeks/${weekNumber}`)
      .then((r) => r.json())
      .then((data) => {
        setWeek(data);
        setResult(null);
        setAnswers({});
      })
      .catch(() => setError("Could not load week data."));
  }, [weekNumber]);

  const submitGate = async () => {
    if (!week) return;
    setSubmitting(true);
    setError("");

    try {
      const res = await fetch(`${API}/api/gates/attempt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: USER_ID,
          week_number: weekNumber,
          answers,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        setError(errData.detail || "Gate submission failed. Make sure you've started this week first.");
        return;
      }

      setResult(await res.json());
    } catch {
      setError("Could not reach the backend.");
    } finally {
      setSubmitting(false);
    }
  };

  const questions = week?.gate_questions?.questions || [];

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <h1>Gate Review</h1>
        <Link href="/progress" style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
          Back to Progress
        </Link>
      </div>

      {/* Week selector */}
      <div style={{ marginBottom: "2rem", display: "flex", alignItems: "center", gap: "1rem" }}>
        <label style={{ color: "var(--text-secondary)" }}>Week:</label>
        <select
          value={weekNumber}
          onChange={(e) => setWeekNumber(parseInt(e.target.value))}
          style={{
            padding: "0.4rem 0.8rem",
            background: "var(--bg-card)",
            color: "var(--text-primary)",
            border: "1px solid var(--border)",
            borderRadius: "4px",
          }}
        >
          {Array.from({ length: 16 }, (_, i) => (
            <option key={i + 1} value={i + 1}>Week {i + 1}</option>
          ))}
        </select>
        {week && (
          <span style={{ color: "var(--text-secondary)" }}>
            {week.title}
          </span>
        )}
      </div>

      {/* Result banner */}
      {result && (
        <div style={{
          padding: "1.5rem",
          marginBottom: "2rem",
          borderRadius: "8px",
          background: result.passed ? "rgba(34, 197, 94, 0.1)" : "rgba(239, 68, 68, 0.1)",
          border: `1px solid ${result.passed ? "var(--success)" : "var(--danger)"}`,
        }}>
          <div style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "0.5rem" }}>
            {result.passed ? "Gate Passed!" : "Not Yet — Keep Going"}
          </div>
          <div style={{ marginBottom: "0.5rem" }}>
            Score: <strong>{(result.overall_score * 100).toFixed(0)}%</strong> (need 75% to pass) | Attempt #{result.attempt_number}
          </div>
          <div style={{ whiteSpace: "pre-wrap", color: "var(--text-secondary)" }}>
            {result.feedback}
          </div>
        </div>
      )}

      {error && (
        <div style={{ padding: "1rem", marginBottom: "1rem", color: "var(--danger)", background: "rgba(239, 68, 68, 0.1)", borderRadius: "6px" }}>
          {error}
        </div>
      )}

      {/* Gate questions */}
      {questions.map((q, i) => {
        const qResult = result?.question_scores?.[q];
        return (
          <div
            key={i}
            style={{
              marginBottom: "1.5rem",
              padding: "1.2rem",
              background: "var(--bg-card)",
              border: `1px solid ${qResult ? (qResult.score >= 0.75 ? "var(--success)" : "var(--danger)") : "var(--border)"}`,
              borderRadius: "8px",
            }}
          >
            <div style={{ marginBottom: "0.8rem", fontWeight: 500 }}>
              Q{i + 1}: {q}
            </div>

            <textarea
              value={answers[q] || ""}
              onChange={(e) => setAnswers((prev) => ({ ...prev, [q]: e.target.value }))}
              placeholder="Write your answer here... Be specific and reference your build experience."
              rows={5}
              style={{
                width: "100%",
                padding: "0.8rem",
                background: "var(--bg-primary)",
                color: "var(--text-primary)",
                border: "1px solid var(--border)",
                borderRadius: "4px",
                fontSize: "0.9rem",
                resize: "vertical",
              }}
            />

            {qResult && (
              <div style={{
                marginTop: "0.8rem",
                padding: "0.8rem",
                background: "var(--bg-primary)",
                borderRadius: "4px",
                fontSize: "0.85rem",
              }}>
                <strong>Score: {(qResult.score * 100).toFixed(0)}%</strong>
                <div style={{ color: "var(--text-secondary)", marginTop: "0.3rem", whiteSpace: "pre-wrap" }}>
                  {qResult.feedback}
                </div>
              </div>
            )}
          </div>
        );
      })}

      {questions.length > 0 && !result?.passed && (
        <button
          onClick={submitGate}
          disabled={submitting || questions.some((q) => !answers[q]?.trim())}
          style={{
            padding: "0.8rem 2rem",
            background: "var(--accent)",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: submitting ? "wait" : "pointer",
            opacity: submitting || questions.some((q) => !answers[q]?.trim()) ? 0.5 : 1,
            fontSize: "1rem",
          }}
        >
          {submitting ? "Evaluating..." : "Submit Gate Review"}
        </button>
      )}
    </div>
  );
}
