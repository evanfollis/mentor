"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { getArtifactStatus, getWeek, reviewArtifact, submitArtifact } from "@/lib/api";

const USER_ID = 1; // TODO: proper auth

interface WeekDetail {
  week_number: number;
  title: string;
  artifact_spec: { description?: string; deliverables?: string[] } | null;
}

interface ArtifactState {
  artifact_status: string;
  artifact_url: string | null;
  artifact_feedback: { review?: string; reviewed_at?: string };
}

export default function ArtifactPage() {
  const searchParams = useSearchParams();
  const weekParam = searchParams.get("week");
  const weekNumber = weekParam ? parseInt(weekParam) : 1;

  const [week, setWeek] = useState<WeekDetail | null>(null);
  const [artifact, setArtifact] = useState<ArtifactState | null>(null);
  const [url, setUrl] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      getWeek(weekNumber) as Promise<WeekDetail>,
      getArtifactStatus(USER_ID, weekNumber) as Promise<ArtifactState>,
    ])
      .then(([w, a]) => {
        setWeek(w);
        setArtifact(a);
        if (a.artifact_url) setUrl(a.artifact_url);
      })
      .catch(() => setError("Could not load data."));
  }, [weekNumber]);

  const handleSubmit = async () => {
    if (!url.trim()) return;
    setSubmitting(true);
    setError("");
    try {
      await submitArtifact(USER_ID, weekNumber, { url: url.trim(), description });
      setArtifact((prev) => prev ? { ...prev, artifact_status: "submitted", artifact_url: url.trim() } : prev);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleReview = async () => {
    setReviewing(true);
    setError("");
    try {
      const result = await reviewArtifact(USER_ID, weekNumber);
      setArtifact((prev) => prev ? {
        ...prev,
        artifact_status: "reviewed",
        artifact_feedback: { review: result.feedback, reviewed_at: new Date().toISOString() },
      } : prev);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Review failed");
    } finally {
      setReviewing(false);
    }
  };

  const status = artifact?.artifact_status || "not_started";
  const spec = week?.artifact_spec;

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <h1>Artifact — Week {weekNumber}</h1>
        <Link href="/progress" style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
          Back to Progress
        </Link>
      </div>

      {week && (
        <div style={{ color: "var(--text-secondary)", marginBottom: "1.5rem" }}>
          {week.title}
        </div>
      )}

      {error && (
        <div style={{ padding: "1rem", marginBottom: "1rem", color: "var(--danger)", background: "rgba(239, 68, 68, 0.1)", borderRadius: "6px" }}>
          {error}
        </div>
      )}

      {/* Artifact spec */}
      {spec && (
        <div style={{
          padding: "1.2rem",
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          marginBottom: "1.5rem",
        }}>
          <div style={{ fontSize: "0.8rem", color: "var(--accent)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.8rem" }}>
            What to Build
          </div>
          {spec.description && (
            <p style={{ marginBottom: "0.8rem", lineHeight: 1.6 }}>{spec.description}</p>
          )}
          {spec.deliverables && spec.deliverables.length > 0 && (
            <ul style={{ paddingLeft: "1.2rem", lineHeight: 1.8 }}>
              {spec.deliverables.map((d, i) => (
                <li key={i} style={{ color: "var(--text-secondary)" }}>{d}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Submission form */}
      {(status === "not_started" || status === "reviewed") && (
        <div style={{
          padding: "1.2rem",
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          marginBottom: "1.5rem",
        }}>
          <div style={{ fontSize: "0.9rem", fontWeight: 500, marginBottom: "1rem" }}>
            {status === "reviewed" ? "Resubmit Artifact" : "Submit Artifact"}
          </div>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="GitHub repo URL, Notion link, etc."
            style={{
              width: "100%",
              padding: "0.7rem",
              background: "var(--bg-primary)",
              color: "var(--text-primary)",
              border: "1px solid var(--border)",
              borderRadius: "4px",
              marginBottom: "0.8rem",
              fontSize: "0.9rem",
            }}
          />
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what you built and key decisions you made (optional but recommended)..."
            rows={3}
            style={{
              width: "100%",
              padding: "0.7rem",
              background: "var(--bg-primary)",
              color: "var(--text-primary)",
              border: "1px solid var(--border)",
              borderRadius: "4px",
              marginBottom: "1rem",
              fontSize: "0.9rem",
              resize: "vertical",
            }}
          />
          <button
            onClick={handleSubmit}
            disabled={submitting || !url.trim()}
            style={{
              padding: "0.7rem 1.5rem",
              background: "var(--accent)",
              color: "white",
              border: "none",
              borderRadius: "6px",
              cursor: submitting || !url.trim() ? "default" : "pointer",
              opacity: submitting || !url.trim() ? 0.5 : 1,
              fontSize: "0.9rem",
            }}
          >
            {submitting ? "Submitting..." : "Submit"}
          </button>
        </div>
      )}

      {/* Submitted, awaiting review */}
      {status === "submitted" && (
        <div style={{
          padding: "1.2rem",
          background: "var(--bg-card)",
          border: "1px solid var(--accent)",
          borderRadius: "8px",
          marginBottom: "1.5rem",
        }}>
          <div style={{ marginBottom: "0.8rem" }}>
            Submitted: <a href={artifact?.artifact_url || "#"} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent)" }}>{artifact?.artifact_url}</a>
          </div>
          <button
            onClick={handleReview}
            disabled={reviewing}
            style={{
              padding: "0.7rem 1.5rem",
              background: "var(--accent)",
              color: "white",
              border: "none",
              borderRadius: "6px",
              cursor: reviewing ? "wait" : "pointer",
              opacity: reviewing ? 0.5 : 1,
              fontSize: "0.9rem",
            }}
          >
            {reviewing ? "Reviewing... (this may take a moment)" : "Request AI Review"}
          </button>
        </div>
      )}

      {/* Review feedback */}
      {status === "reviewed" && artifact?.artifact_feedback?.review && (
        <div style={{
          padding: "1.5rem",
          background: "var(--bg-card)",
          border: "1px solid var(--success)",
          borderRadius: "8px",
        }}>
          <div style={{ fontSize: "0.8rem", color: "var(--success)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "1rem" }}>
            AI Review
          </div>
          <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.7 }}>
            {artifact.artifact_feedback.review}
          </div>
        </div>
      )}
    </div>
  );
}
