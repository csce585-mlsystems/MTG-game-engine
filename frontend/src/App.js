import logo from './logo.svg';
import './App.css';
import { useEffect, useState } from "react";

function App() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch("http://0.0.0.0:8000/")
      .then((res) => res.json())
      .then((json) => setData(json));
  }, []);

  return (
    <div>
      <h1>MTG Land Simulator</h1>
      <p>{data ? data.message : "Loading..."}</p>
    </div>
  );
}

export default App;
