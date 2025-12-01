import { useState } from "react";

export default function CardSearchForm({ apiUrl }) {
  const API_URL = apiUrl || process.env.REACT_APP_API_URL || "http://localhost:8000";
  const [q, setQ] = useState("");
  const [setCode, setSetCode] = useState("");
  const [rarity, setRarity] = useState("");
  const [namesRaw, setNamesRaw] = useState("");
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [resp, setResp] = useState(null);
  const [error, setError] = useState(null);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResp(null);
    let names = undefined;
    if (namesRaw.trim()) {
      names = namesRaw.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
    }
    try {
      const res = await fetch(`${API_URL}/cards`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          q: q || undefined,
          set_code: setCode || undefined,
          rarity: rarity || undefined,
          names,
          page: Number(page),
          per_page: Number(perPage)
        })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResp(await res.json());
    } catch (e2) {
      setError("Search failed");
      // eslint-disable-next-line no-console
      console.error(e2);
    }
  };

  return (
    <div style={{ marginBottom: 24 }}>
      <h2>Search Cards</h2>
      <form onSubmit={onSubmit} style={{ display: "grid", gap: 8, maxWidth: 640 }}>
        <input placeholder="q (name/text substring)" value={q} onChange={(e) => setQ(e.target.value)} />
        <input placeholder="set_code (e.g., mh2)" value={setCode} onChange={(e) => setSetCode(e.target.value)} />
        <input placeholder="rarity (e.g., rare)" value={rarity} onChange={(e) => setRarity(e.target.value)} />
        <textarea rows={4} placeholder="names (newline separated, optional exact matches)" value={namesRaw} onChange={(e) => setNamesRaw(e.target.value)} />
        <div style={{ display: "flex", gap: 8 }}>
          <input type="number" value={page} onChange={(e) => setPage(e.target.value)} style={{ width: 100 }} />
          <input type="number" value={perPage} onChange={(e) => setPerPage(e.target.value)} style={{ width: 100 }} />
          <button type="submit">Search</button>
        </div>
      </form>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {resp && (
        <div style={{ marginTop: 8 }}>
          <p>Total: {resp.total} | Page {resp.page} / {Math.ceil(resp.total / resp.per_page || 1)}</p>
          <ul>
            {resp.results?.map((c) => (
              <li key={c.id}>{c.name} — {c.set_name} ({c.set_code})</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}


