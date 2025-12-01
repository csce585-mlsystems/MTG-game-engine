import { useState } from "react";

export default function ResolveDeckForm({ apiUrl }) {
  const API_URL = apiUrl || process.env.REACT_APP_API_URL || "http://localhost:8000";
  const [deckRaw, setDeckRaw] = useState("Tinker,1\nBrainstorm,4\nPonder,4\nIsland,24");
  const [resp, setResp] = useState(null);
  const [error, setError] = useState(null);

  const parseDeck = () => {
    return deckRaw.split(/\r?\n/).map((line) => line.trim()).filter(Boolean).map((line) => {
      const [name, count] = line.split(",").map((s) => s.trim());
      return { name, count: Number(count || 1) };
    });
  };

  const onResolve = async () => {
    setError(null);
    setResp(null);
    try {
      const body = { deck: parseDeck() };
      const res = await fetch(`${API_URL}/cards/resolve-deck`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResp(await res.json());
    } catch (e) {
      setError("Resolve failed");
      // eslint-disable-next-line no-console
      console.error(e);
    }
  };

  return (
    <div style={{ marginBottom: 24 }}>
      <h2>Resolve Deck</h2>
      <textarea rows={6} value={deckRaw} onChange={(e) => setDeckRaw(e.target.value)} style={{ width: 400 }} />
      <div>
        <button onClick={onResolve}>Resolve</button>
      </div>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {resp && (
        <div>
          <p>Unresolved: {resp.unresolved?.join(", ") || "None"}</p>
          <p>Derived Counts:</p>
          <pre style={{ background: "#f6f8fa", padding: 8 }}>{JSON.stringify(resp.derived_counts, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}


