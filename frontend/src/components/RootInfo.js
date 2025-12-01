import { useEffect, useState } from "react";

export default function RootInfo({ apiUrl }) {
  const API_URL = apiUrl || process.env.REACT_APP_API_URL || "http://localhost:8000";
  const [info, setInfo] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/`).then((r) => r.json()).then(setInfo).catch(() => setInfo(null));
  }, [API_URL]);

  return (
    <div style={{ marginBottom: 16 }}>
      <h2>API Info</h2>
      {info ? (
        <pre style={{ background: "#f6f8fa", padding: 12, overflow: "auto" }}>
{JSON.stringify(info, null, 2)}
        </pre>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}


