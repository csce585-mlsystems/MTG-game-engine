import { useEffect, useState } from "react";

export default function HealthStatus({ apiUrl }) {
  const API_URL = apiUrl || process.env.REACT_APP_API_URL || "http://localhost:8000";
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch((e) => {
        setError("Failed to fetch health");
        // eslint-disable-next-line no-console
        console.error(e);
      });
  }, [API_URL]);

  return (
    <div style={{ marginBottom: 16 }}>
      <h2>Health</h2>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {health && (
        <ul>
          <li>Status: {health.status}</li>
          <li>Version: {health.version}</li>
          <li>DB Path: {health.db_path}</li>
        </ul>
      )}
    </div>
  );
}


