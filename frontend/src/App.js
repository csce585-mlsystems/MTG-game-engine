import './App.css';
import { useEffect, useState } from "react";

function App() {
  const [data, setData] = useState(null);

  // Get API URL from environment variable, fallback to localhost for development
  const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

  const [deckSize, setDeckSize] = useState(60);
  const [landCount, setLandCount] = useState(24);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = async () => {
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/simulate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },

        // send POST JSON 
        body: JSON.stringify({
          total_cards: Number(deckSize),
          successes: Number(landCount),
          num_simulations: 10000,
        }),
      });

      const json = await response.json();
      setResult(json);
    } catch (err) {
      console.error("Simulation error:", err);
      setResult({ error: "Failed to reach backend" });
    }

    setLoading(false);
  };

  useEffect(() => {
    fetch(`${API_URL}/`)
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch((error) => {
        console.error("Error fetching data:", error);
        setData({ message: "Error connecting to API" });
      });
  }, [API_URL]);

  return (
    <div style={{ padding: "20px" }}>
      <h1>MTG Probability Simulator</h1>

      {/* Deck size input */}
      <div style={{ marginBottom: "16px" }}>
        <label>Deck Size: </label>
        <input
          type="number"
          value={deckSize}
          onChange={(e) => setDeckSize(e.target.value)}
        />
      </div>

      {/* Land count input */}
      <div style={{ marginBottom: "16px" }}>
        <label>Number of Lands: </label>
        <input
          type="number"
          value={landCount}
          onChange={(e) => setLandCount(e.target.value)}
        />
      </div>

      {/* Simulate button */}
      <button onClick={runSimulation} disabled={loading}>
        {loading ? "Simulating..." : "Run Simulation"}
      </button>

      <hr />

      {result && (
        <div style={{ marginTop: "16px" }}>
          {result.error && <p style={{ color: "red" }}>{result.error}</p>}

          {result.probability !== undefined && (
            <>
              <p><strong>Simulated Probability:</strong> {result.probability}</p>
              <p><strong>Theoretical Probability:</strong> {result.theoretical_probability}</p>
              <p><strong>Simulations:</strong> {result.simulations_run}</p>
              <p><strong>Execution Time:</strong> {result.execution_time_seconds.toFixed(4)} sec</p>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
