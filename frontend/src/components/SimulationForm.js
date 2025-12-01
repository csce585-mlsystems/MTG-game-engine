import { useState } from "react";

export default function SimulationForm({ apiUrl }) {
    const API_URL = apiUrl || process.env.REACT_APP_API_URL || "http://localhost:8000";

    const [lands, setLands] = useState(24);
    const [nonlands, setNonLands] = useState(36);
    const [sims, setSims] = useState(1000);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const runSim = async () => {
        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const res = await fetch(`${API_URL}/simulate/land?lands=${Number(lands)}&non_lands=${Number(nonlands)}&num_simulations=${Number(sims)}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            setResult(data);
        } catch (e) {
            setError("Failed to run simulation");
            // eslint-disable-next-line no-console
            console.error(e);
        }
        setLoading(false);
    };

    return (
        <div>
            <h2>Land Probability Simulator</h2>
            <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12 }}>
                <label>
                    Lands:
                    <input type="number" value={lands} onChange={e => setLands(e.target.value)} style={{ marginLeft: 6, width: 80 }} />
                </label>
                <label>
                    Non-lands:
                    <input type="number" value={nonlands} onChange={e => setNonLands(e.target.value)} style={{ marginLeft: 6, width: 80 }} />
                </label>
                <label>
                    Simulations:
                    <input type="number" value={sims} onChange={e => setSims(e.target.value)} style={{ marginLeft: 6, width: 100 }} />
                </label>
                <button onClick={runSim} disabled={loading}>
                    {loading ? "Running..." : "Run Simulation"}
                </button>
            </div>

            {error && <p style={{ color: "red" }}>{error}</p>}
            {result && result.probability !== undefined && (
                <p>Probability: {(result.probability * 100).toFixed(2)}%</p>
            )}
        </div>
    );
}
