const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// Auth
export function registerUser(data: { name: string; email: string; timezone?: string }) {
  return fetchAPI("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getUser(userId: number) {
  return fetchAPI(`/api/auth/me/${userId}`);
}

// Curriculum
export function getPhases() {
  return fetchAPI("/api/curriculum/phases");
}

export function getWeek(weekNumber: number) {
  return fetchAPI(`/api/curriculum/weeks/${weekNumber}`);
}

// Progress
export function getLearnerState(userId: number) {
  return fetchAPI(`/api/progress/${userId}/state`);
}

export function getWeekProgress(userId: number) {
  return fetchAPI(`/api/progress/${userId}/weeks`);
}

export function startWeek(userId: number, weekNumber: number) {
  return fetchAPI(`/api/progress/${userId}/weeks/${weekNumber}/start`, {
    method: "POST",
  });
}

// Chat
export function sendMessage(data: {
  user_id: number;
  message: string;
  conversation_id?: number;
  mode?: string;
}) {
  return fetchAPI("/api/chat/send", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Quiz
export function generateQuiz(data: { user_id: number; week_number?: number }) {
  return fetchAPI("/api/quiz/generate", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function evaluateQuiz(data: {
  user_id: number;
  week_number: number;
  question: string;
  answer: string;
}) {
  return fetchAPI("/api/quiz/evaluate", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Cards (Spaced Repetition)
export function getDueCards(userId: number, limit = 10) {
  return fetchAPI<{ cards: { id: number; concept: string; question: string }[]; total_due: number }>(
    `/api/cards/${userId}/due?limit=${limit}`
  );
}

export function reviewCard(userId: number, data: { card_id: number; self_score: number }) {
  return fetchAPI<{ ideal_answer: string; next_review_at: string; interval_days: number; ease_factor: number }>(
    `/api/cards/${userId}/review`,
    { method: "POST", body: JSON.stringify(data) }
  );
}

// Artifacts
export function submitArtifact(userId: number, weekNumber: number, data: { url: string; description?: string }) {
  return fetchAPI(`/api/progress/${userId}/weeks/${weekNumber}/artifact`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function reviewArtifact(userId: number, weekNumber: number) {
  return fetchAPI<{ feedback: string; artifact_status: string }>(
    `/api/progress/${userId}/weeks/${weekNumber}/artifact/review`,
    { method: "POST" }
  );
}

export function getArtifactStatus(userId: number, weekNumber: number) {
  return fetchAPI<{ artifact_status: string; artifact_url: string | null; artifact_feedback: Record<string, unknown> }>(
    `/api/progress/${userId}/weeks/${weekNumber}/artifact`
  );
}

// Study Time
export function logStudyTime(userId: number, minutes: number) {
  return fetchAPI(`/api/progress/${userId}/log-time?minutes=${minutes}`, {
    method: "POST",
  });
}

// Gates
export function getGateQuestions(userId: number, weekNumber: number) {
  return fetchAPI(`/api/gates/${userId}/${weekNumber}/questions`);
}

export function attemptGate(data: {
  user_id: number;
  week_number: number;
  answers: Record<string, string>;
}) {
  return fetchAPI("/api/gates/attempt", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
