"use client";

import { useState, useRef, useEffect } from "react";
import { logStudyTime } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const USER_ID = 1;

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ConversationSummary {
  id: number;
  mode: string;
  preview: string;
  message_count: number;
  last_message_at: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("freeform");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load conversation list on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Track study time — log every 5 minutes and on unmount
  useEffect(() => {
    let lastLogged = Date.now();

    const interval = setInterval(() => {
      const minutes = Math.round((Date.now() - lastLogged) / 60000);
      if (minutes >= 5) {
        logStudyTime(USER_ID, minutes).catch(() => {});
        lastLogged = Date.now();
      }
    }, 60000); // check every minute

    return () => {
      clearInterval(interval);
      const minutes = Math.round((Date.now() - lastLogged) / 60000);
      if (minutes >= 1) {
        logStudyTime(USER_ID, minutes).catch(() => {});
      }
    };
  }, []);

  const loadConversations = async () => {
    try {
      const res = await fetch(`${API}/api/chat/${USER_ID}/conversations`);
      if (res.ok) setConversations(await res.json());
    } catch {}
  };

  const loadConversation = async (id: number) => {
    try {
      const res = await fetch(`${API}/api/chat/conversation/${id}`);
      if (res.ok) {
        const data = await res.json();
        setConversationId(data.id);
        setMode(data.mode);
        setMessages(data.messages);
      }
    } catch {}
  };

  const newConversation = () => {
    setConversationId(null);
    setMessages([]);
  };

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
      loadConversations(); // refresh sidebar
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Error: Could not reach the mentor. Is the backend running?",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const modeLabels: Record<string, string> = {
    freeform: "Freeform",
    socratic: "Socratic",
    explain: "Explain",
    quiz: "Quiz Me",
  };

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      {/* Sidebar */}
      <div
        style={{
          width: sidebarOpen ? 280 : 0,
          overflow: "hidden",
          borderRight: sidebarOpen ? "1px solid var(--border)" : "none",
          background: "var(--bg-secondary)",
          transition: "width 0.2s",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            padding: "1rem",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>
            Conversations
          </span>
          <button
            onClick={newConversation}
            style={{
              padding: "0.3rem 0.6rem",
              background: "var(--accent)",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "0.8rem",
            }}
          >
            + New
          </button>
        </div>
        <div style={{ flex: 1, overflow: "auto" }}>
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => loadConversation(conv.id)}
              style={{
                padding: "0.7rem 1rem",
                cursor: "pointer",
                borderBottom: "1px solid var(--border)",
                background:
                  conv.id === conversationId
                    ? "var(--bg-card)"
                    : "transparent",
              }}
            >
              <div
                style={{
                  fontSize: "0.75rem",
                  color: "var(--accent)",
                  marginBottom: "0.2rem",
                }}
              >
                {modeLabels[conv.mode] || conv.mode}
              </div>
              <div
                style={{
                  fontSize: "0.85rem",
                  color: "var(--text-primary)",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {conv.preview || "Empty conversation"}
              </div>
              <div
                style={{
                  fontSize: "0.7rem",
                  color: "var(--text-secondary)",
                  marginTop: "0.2rem",
                }}
              >
                {conv.message_count} messages
              </div>
            </div>
          ))}
          {conversations.length === 0 && (
            <div
              style={{
                padding: "2rem 1rem",
                color: "var(--text-secondary)",
                textAlign: "center",
                fontSize: "0.85rem",
              }}
            >
              No conversations yet.
              <br />
              Start one below!
            </div>
          )}
        </div>
      </div>

      {/* Main chat area */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          padding: "1rem",
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
          <div style={{ display: "flex", alignItems: "center", gap: "0.8rem" }}>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              style={{
                background: "none",
                border: "1px solid var(--border)",
                color: "var(--text-secondary)",
                cursor: "pointer",
                padding: "0.3rem 0.5rem",
                borderRadius: "4px",
                fontSize: "0.9rem",
              }}
            >
              {sidebarOpen ? "\u25C0" : "\u25B6"}
            </button>
            <h1 style={{ fontSize: "1.3rem" }}>Chat with Mentor</h1>
          </div>
          <select
            value={mode}
            onChange={(e) => {
              setMode(e.target.value);
              if (!conversationId) {
                // Only reset if starting a new conversation
                setMessages([]);
              }
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
    </div>
  );
}
