import logo from './logo.svg';
import './App.css';
import { useEffect, useState } from "react";

function App() {
  const [data, setData] = useState(null);

  // Get API URL from environment variable, fallback to localhost for development
  const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

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
    <div>
      <h1>MTG Land Simulator</h1>
      <p>{data ? data.message : "Loading..."}</p>
    </div>
  );
}

export default App;
