"use client";

import { useState, useRef, useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const USER_ID = 1;

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("freeform");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const res = await fetch(`${API}/api/chat/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: USER_ID,
          message: userMessage,
          conversation_id: conversationId,
          mode,
        }),
      });
      const data = await res.json();
      setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error: Could not reach the mentor. Is the backend running?" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: 800,
        margin: "0 auto",
        padding: "1rem",
        height: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
          paddingBottom: "1rem",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <h1 style={{ fontSize: "1.3rem" }}>Chat with Mentor</h1>
        <select
          value={mode}
          onChange={(e) => {
            setMode(e.target.value);
            setConversationId(null);
            setMessages([]);
          }}
          style={{
            padding: "0.4rem 0.8rem",
            background: "var(--bg-card)",
            color: "var(--text-primary)",
            border: "1px solid var(--border)",
            borderRadius: "4px",
          }}
        >
          <option value="freeform">Freeform</option>
          <option value="socratic">Socratic</option>
          <option value="explain">Explain</option>
          <option value="quiz">Quiz Me</option>
        </select>
      </div>

      <div style={{ flex: 1, overflow: "auto", marginBottom: "1rem" }}>
        {messages.length === 0 && (
          <div
            style={{
              textAlign: "center",
              color: "var(--text-secondary)",
              marginTop: "4rem",
            }}
          >
            <p style={{ fontSize: "1.1rem" }}>
              {mode === "socratic"
                ? "Socratic mode: I'll guide you through questions instead of giving answers directly."
                : mode === "explain"
                  ? "Explain mode: Ask me to explain any concept from the curriculum."
                  : mode === "quiz"
                    ? "Quiz mode: I'll generate questions calibrated to your level."
                    : "Ask me anything about AI architecture."}
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              marginBottom: "1rem",
              padding: "0.8rem 1rem",
              background:
                msg.role === "user" ? "var(--bg-card)" : "transparent",
              borderRadius: "8px",
              border:
                msg.role === "user"
                  ? "1px solid var(--border)"
                  : "1px solid transparent",
            }}
          >
            <div
              style={{
                fontSize: "0.75rem",
                color: "var(--text-secondary)",
                marginBottom: "0.3rem",
              }}
            >
              {msg.role === "user" ? "You" : "Mentor"}
            </div>
            <div style={{ whiteSpace: "pre-wrap" }}>{msg.content}</div>
          </div>
        ))}

        {loading && (
          <div style={{ color: "var(--text-secondary)", padding: "0.5rem" }}>
            Thinking...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div style={{ display: "flex", gap: "0.5rem" }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask your mentor..."
          style={{
            flex: 1,
            padding: "0.8rem 1rem",
            background: "var(--bg-card)",
            color: "var(--text-primary)",
            border: "1px solid var(--border)",
            borderRadius: "6px",
            fontSize: "1rem",
          }}
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          style={{
            padding: "0.8rem 1.5rem",
            background: "var(--accent)",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: loading ? "wait" : "pointer",
            opacity: loading ? 0.6 : 1,
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
