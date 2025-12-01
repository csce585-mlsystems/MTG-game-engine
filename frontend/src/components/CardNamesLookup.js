import { useState } from "react";

export default function CardNamesLookup({ apiUrl }) {
  const API_URL = apiUrl || process.env.REACT_APP_API_URL || "http://localhost:8000";
  const [namesRaw, setNamesRaw] = useState("");
  const [cards, setCards] = useState(null);
  const [error, setError] = useState(null);

  const onLookup = async () => {
    setError(null);
    setCards(null);
    const names = namesRaw.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
    if (!names.length) {
      setError("Enter at least one name");
      return;
    }
    try {
      const res = await fetch(`${API_URL}/cards/names`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ names })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setCards(await res.json());
    } catch (e) {
      setError("Lookup failed");
      // eslint-disable-next-line no-console
      console.error(e);
    }
  };

  return (
    <div style={{ marginBottom: 24 }}>
      <h2>Lookup Cards by Names</h2>
      <textarea rows={4} placeholder="names (newline separated)" value={namesRaw} onChange={(e) => setNamesRaw(e.target.value)} style={{ width: 400 }} />
      <div>
        <button onClick={onLookup}>Lookup</button>
      </div>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {cards && (
        <ul>
          {cards.map((c) => <li key={c.id}>{c.name} — {c.set_name} ({c.set_code})</li>)}
        </ul>
      )}
    </div>
  );
}


