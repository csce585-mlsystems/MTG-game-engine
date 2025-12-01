import { useState } from "react";

export default function SimulateByNamesForm({ apiUrl }) {
  const API_URL = apiUrl || process.env.REACT_APP_API_URL || "http://localhost:8000";
  const [deckRaw, setDeckRaw] = useState("Tinker,1\nBrainstorm,4\nPonder,4\nIsland,24");
  const [category, setCategory] = useState("artifact");
  const [oracleRaw, setOracleRaw] = useState("Tinker");
  const [sims, setSims] = useState(10000);
  const [seed, setSeed] = useState(42);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const parseDeck = () => deckRaw.split(/\r?\n/).map(l => l.trim()).filter(Boolean).map(l => {
    const [name, count] = l.split(",").map(s => s.trim());
    return { name, count: Number(count || 1) };
  });
  const parseOracle = () => oracleRaw.split(/\r?\n/).map(s => s.trim()).filter(Boolean);

  const run = async () => {
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/simulate/by-names`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          deck: parseDeck(),
          category,
          num_simulations: Number(sims),
          random_seed: Number(seed),
          oracle_names: parseOracle()
        })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResult(await res.json());
    } catch (e) {
      setError("Simulation failed");
      // eslint-disable-next-line no-console
      console.error(e);
    }
  };

  return (
    <div style={{ marginBottom: 24 }}>
      <h2>Simulate by Names (Category)</h2>
      <textarea rows={6} value={deckRaw} onChange={(e) => setDeckRaw(e.target.value)} style={{ width: 400 }} />
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <input placeholder="category (e.g., artifact)" value={category} onChange={(e) => setCategory(e.target.value)} />
        <input type="number" placeholder="simulations" value={sims} onChange={(e) => setSims(e.target.value)} />
        <input type="number" placeholder="seed" value={seed} onChange={(e) => setSeed(e.target.value)} />
      </div>
      <textarea rows={2} placeholder="oracle_names (newline separated)" value={oracleRaw} onChange={(e) => setOracleRaw(e.target.value)} style={{ width: 400, marginTop: 8 }} />
      <div>
        <button onClick={run}>Run</button>
      </div>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {result && (
        <pre style={{ background: "#f6f8fa", padding: 8 }}>{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
}


