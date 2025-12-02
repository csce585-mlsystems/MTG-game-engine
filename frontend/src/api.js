const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

async function postJson(path, body) {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${text}`);
  }
  return res.json();
}

export async function resolveDeck(payload) {
  // payload: { deck: [{ name, count }, ...] }
  return postJson("/cards/resolve-deck", payload);
}

export async function simulateByNames(payload) {
  // payload: { deck: [{ name, count }], category, num_simulations, random_seed?, oracle_names? }
  return postJson("/simulate/by-names", payload);
}

export async function simulateByCard(payload) {
  // payload: { deck: [{ name, count }], target_names: [..], num_simulations, random_seed?, oracle_names? }
  return postJson("/simulate/by-card", payload);
}

export async function simulateFullState(payload) {
  // payload: { deck: [{ name, count }], top_zone: [names], bottom_zone: [names], num_simulations, random_seed? }
  return postJson("/simulate/full-state", payload);
}

// Optional helpers for other UI panels
export async function cardSearch(payload) {
  return postJson("/cards", payload);
}

export async function cardsByNames(names) {
  return postJson("/cards/names", { names });
}

export default {
  resolveDeck,
  simulateByNames,
  simulateByCard,
  simulateFullState,
  cardSearch,
  cardsByNames,
};

