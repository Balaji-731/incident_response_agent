const API_BASE_URL = "http://127.0.0.1:8000/api";

export async function fetchHealth() {
  const res = await fetch(`${API_BASE_URL}/health`);
  return res.json();
}

export async function parseRawLog(raw_log) {
  const res = await fetch(`${API_BASE_URL}/incidents/parse-log`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_log })
  });
  return res.json();
}

export async function createIncident(incidentData) {
  const res = await fetch(`${API_BASE_URL}/incidents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(incidentData)
  });
  return res.json();
}

export async function listIncidents() {
  const res = await fetch(`${API_BASE_URL}/incidents`);
  return res.json();
}

export async function analyzeIncident(incidentId) {
  const res = await fetch(`${API_BASE_URL}/incidents/${incidentId}/analyze`, {
    method: "POST"
  });
  return res.json();
}

export async function resolveIncident(incidentId, resolutionData) {
  const res = await fetch(`${API_BASE_URL}/incidents/${incidentId}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(resolutionData)
  });
  return res.json();
}

export async function searchMemories(query, top_k = 5) {
  const res = await fetch(`${API_BASE_URL}/memories/search?q=${encodeURIComponent(query)}&top_k=${top_k}`);
  return res.json();
}

export async function resetSystem() {
  const res = await fetch(`${API_BASE_URL}/incidents/reset`, {
    method: "DELETE"
  });
  return res.json();
}