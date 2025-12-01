import { useState } from "react";

export default function SimulateByCardForm({ apiUrl }) {
  const API_URL = apiUrl || process.env.REACT_APP_API_URL || "http://localhost:8000";
  const [deckRaw, setDeckRaw] = useState("Tinker,1\nBrainstorm,4\nPonder,4\nIsland,24");
  const [targetsRaw, setTargetsRaw] = useState("Tinker");
  const [oracleRaw, setOracleRaw] = useState("Brainstorm");
  const [sims, setSims] = useState(10000);
  const [seed, setSeed] = useState(42);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const parseDeck = () => deckRaw.split(/\r?\n/).map(l => l.trim()).filter(Boolean).map(l => {
    const [name, count] = l.split(",").map(s => s.trim());
    return { name, count: Number(count || 1) };
  });
  const parseList = (text) => text.split(/\r?\n/).map(s => s.trim()).filter(Boolean);

  const run = async () => {
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/simulate/by-card`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          deck: parseDeck(),
          target_names: parseList(targetsRaw),
          num_simulations: Number(sims),
          random_seed: Number(seed),
          oracle_names: parseList(oracleRaw)
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
      <h2>Simulate by Card (Targets)</h2>
      <textarea rows={6} value={deckRaw} onChange={(e) => setDeckRaw(e.target.value)} style={{ width: 400 }} />
      <textarea rows={2} placeholder="target_names (newline separated)" value={targetsRaw} onChange={(e) => setTargetsRaw(e.target.value)} style={{ width: 400, marginTop: 8 }} />
      <textarea rows={2} placeholder="oracle_names (newline separated, optional)" value={oracleRaw} onChange={(e) => setOracleRaw(e.target.value)} style={{ width: 400, marginTop: 8 }} />
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <input type="number" placeholder="simulations" value={sims} onChange={(e) => setSims(e.target.value)} />
        <input type="number" placeholder="seed" value={seed} onChange={(e) => setSeed(e.target.value)} />
      </div>
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


