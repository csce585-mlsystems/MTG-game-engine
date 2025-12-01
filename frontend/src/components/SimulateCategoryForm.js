import { useState } from "react";

export default function SimulateCategoryForm({ apiUrl }) {
  const API_URL = apiUrl || process.env.REACT_APP_API_URL || "http://localhost:8000";
  const [countsRaw, setCountsRaw] = useState('{"land":24,"creature":20,"spell":16}');
  const [category, setCategory] = useState("land");
  const [sims, setSims] = useState(10000);
  const [seed, setSeed] = useState(42);
  const [oracleTexts, setOracleTexts] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const run = async () => {
    setError(null);
    setResult(null);
    try {
      const card_counts = JSON.parse(countsRaw);
      const res = await fetch(`${API_URL}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          deck: { card_counts },
          category,
          num_simulations: Number(sims),
          random_seed: Number(seed),
          oracle_texts: oracleTexts
            ? oracleTexts.split(/\r?\n/).map((s) => s.trim()).filter(Boolean)
            : undefined
        })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResult(await res.json());
    } catch (e) {
      setError("Simulation failed (check JSON for counts)");
      // eslint-disable-next-line no-console
      console.error(e);
    }
  };

  return (
    <div style={{ marginBottom: 24 }}>
      <h2>Simulate Category (Counts)</h2>
      <textarea rows={4} value={countsRaw} onChange={(e) => setCountsRaw(e.target.value)} style={{ width: 400 }} />
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <input placeholder="category" value={category} onChange={(e) => setCategory(e.target.value)} />
        <input type="number" placeholder="simulations" value={sims} onChange={(e) => setSims(e.target.value)} />
        <input type="number" placeholder="seed" value={seed} onChange={(e) => setSeed(e.target.value)} />
      </div>
      <textarea rows={2} placeholder="oracle_texts (newline separated, optional)" value={oracleTexts} onChange={(e) => setOracleTexts(e.target.value)} style={{ width: 400, marginTop: 8 }} />
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


