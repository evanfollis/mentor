"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getDueCards, reviewCard } from "@/lib/api";

const USER_ID = 1; // TODO: proper auth

interface Card {
  id: number;
  concept: string;
  question: string;
}

interface ReviewResult {
  ideal_answer: string;
  next_review_at: string;
  interval_days: number;
  ease_factor: number;
}

const GRADE_BUTTONS = [
  { label: "Blackout", score: 0, color: "var(--danger)" },
  { label: "Hard", score: 3, color: "var(--warning)" },
  { label: "Good", score: 4, color: "var(--accent)" },
  { label: "Easy", score: 5, color: "var(--success)" },
];

export default function CardsPage() {
  const [cards, setCards] = useState<Card[]>([]);
  const [totalDue, setTotalDue] = useState(0);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [reviewResult, setReviewResult] = useState<ReviewResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [reviewed, setReviewed] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    getDueCards(USER_ID, 20)
      .then((data) => {
        setCards(data.cards);
        setTotalDue(data.total_due);
      })
      .catch(() => setError("Could not load cards. Is the backend running?"))
      .finally(() => setLoading(false));
  }, []);

  const handleGrade = async (score: number) => {
    const card = cards[currentIndex];
    setSubmitting(true);

    try {
      const result = await reviewCard(USER_ID, { card_id: card.id, self_score: score });
      setReviewResult(result);
      setRevealed(true);
    } catch {
      setError("Could not submit review.");
    } finally {
      setSubmitting(false);
    }
  };

  const nextCard = () => {
    setReviewed((r) => r + 1);
    setRevealed(false);
    setReviewResult(null);
    setCurrentIndex((i) => i + 1);
  };

  if (loading) {
    return (
      <div style={{ maxWidth: 700, margin: "0 auto", padding: "2rem", textAlign: "center" }}>
        <p style={{ color: "var(--text-secondary)" }}>Loading cards...</p>
      </div>
    );
  }

  // All done
  if (cards.length === 0 || currentIndex >= cards.length) {
    return (
      <div style={{ maxWidth: 700, margin: "0 auto", padding: "2rem", textAlign: "center" }}>
        <h1 style={{ marginBottom: "1rem" }}>
          {reviewed > 0 ? "Session Complete" : "All Caught Up"}
        </h1>
        {reviewed > 0 && (
          <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem" }}>
            You reviewed {reviewed} card{reviewed !== 1 ? "s" : ""}.
          </p>
        )}
        {reviewed === 0 && (
          <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem" }}>
            No cards due for review right now. Complete a gate to generate new cards.
          </p>
        )}
        <Link
          href="/dashboard"
          style={{
            padding: "0.8rem 1.5rem",
            background: "var(--accent)",
            color: "white",
            borderRadius: "6px",
          }}
        >
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const card = cards[currentIndex];

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", padding: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <h1>Review Cards</h1>
        <Link href="/dashboard" style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
          Back to Dashboard
        </Link>
      </div>

      {/* Progress indicator */}
      <div style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "1.5rem" }}>
        Card {currentIndex + 1} of {cards.length}
        {totalDue > cards.length && ` (${totalDue} total due)`}
      </div>

      {error && (
        <div style={{ padding: "1rem", marginBottom: "1rem", color: "var(--danger)", background: "rgba(239, 68, 68, 0.1)", borderRadius: "6px" }}>
          {error}
        </div>
      )}

      {/* Flashcard */}
      <div style={{
        padding: "2rem",
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "12px",
        marginBottom: "1.5rem",
        minHeight: 200,
      }}>
        <div style={{
          fontSize: "0.8rem",
          color: "var(--accent)",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          marginBottom: "1rem",
        }}>
          {card.concept}
        </div>

        <div style={{ fontSize: "1.1rem", lineHeight: 1.6, marginBottom: "1.5rem" }}>
          {card.question}
        </div>

        {/* Revealed answer */}
        {revealed && reviewResult && (
          <div style={{
            padding: "1.2rem",
            background: "var(--bg-primary)",
            borderRadius: "8px",
            borderLeft: "3px solid var(--success)",
          }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
              Ideal Answer
            </div>
            <div style={{ lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
              {reviewResult.ideal_answer}
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "1rem" }}>
              Next review in {reviewResult.interval_days} day{reviewResult.interval_days !== 1 ? "s" : ""}
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      {!revealed ? (
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", width: "100%", marginBottom: "0.25rem" }}>
            Think of your answer, then rate how well you knew it:
          </div>
          {GRADE_BUTTONS.map((btn) => (
            <button
              key={btn.score}
              onClick={() => handleGrade(btn.score)}
              disabled={submitting}
              style={{
                flex: 1,
                padding: "0.7rem 1rem",
                background: "var(--bg-card)",
                color: btn.color,
                border: `1px solid ${btn.color}`,
                borderRadius: "6px",
                cursor: submitting ? "wait" : "pointer",
                opacity: submitting ? 0.5 : 1,
                fontSize: "0.9rem",
                fontWeight: 500,
              }}
            >
              {btn.label}
            </button>
          ))}
        </div>
      ) : (
        <button
          onClick={nextCard}
          style={{
            padding: "0.8rem 2rem",
            background: "var(--accent)",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontSize: "1rem",
          }}
        >
          {currentIndex + 1 < cards.length ? "Next Card" : "Finish"}
        </button>
      )}
    </div>
  );
}
