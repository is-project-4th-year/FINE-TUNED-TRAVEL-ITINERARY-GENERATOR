// frontend/lib/api.ts

export type GenParams = {
  text: string;
  days?: number;
  start_date?: string;
  end_date?: string;
  travelers?: number;
  budget?: number;
};

// Always use direct FastAPI connection via SSH tunnel
const API_BASE = "http://localhost:8000";

console.log("🔥 API BASE:", API_BASE);

// Generic fetch wrapper
async function apiFetch(path: string, init: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, init);

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `HTTP ${res.status}`);
  }

  return res.json();
}

// Exported function used by the form
export async function generateItinerary(payload: GenParams) {
  return apiFetch("/itinerary", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// --- Itinerary Job API Integration ---
export async function submitItineraryJob(payload: GenParams) {
  const res = await fetch(`${API_BASE}/itinerary/job`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to submit job");
  return await res.json(); // { job_id, status }
}

export async function pollItineraryJob(jobId: string) {
  const res = await fetch(`${API_BASE}/itinerary/job/${jobId}`);
  if (!res.ok) throw new Error("Failed to poll job status");
  return await res.json(); // { job_id, status, result }
}

export async function getItineraryWithPolling(
  payload: GenParams,
  pollInterval = 3000,
  maxWait = 600000
) {
  const { job_id } = await submitItineraryJob(payload);
  const start = Date.now();
  while (true) {
    const job = await pollItineraryJob(job_id);
    if (job.status === "done") {
      return job.result;
    }
    if (job.status === "error") {
      throw new Error(job.result?.error || "Job failed");
    }
    if (Date.now() - start > maxWait) {
      throw new Error("Job polling timed out");
    }
    await new Promise((r) => setTimeout(r, pollInterval));
  }
}
