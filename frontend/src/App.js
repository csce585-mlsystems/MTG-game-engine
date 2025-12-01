import './App.css';
import SimulationForm from "./components/SimulationForm";
import RootInfo from "./components/RootInfo";
import HealthStatus from "./components/HealthStatus";
import CardSearchForm from "./components/CardSearchForm";
import CardNamesLookup from "./components/CardNamesLookup";
import ResolveDeckForm from "./components/ResolveDeckForm";
import SimulateByNamesForm from "./components/SimulateByNamesForm";
import SimulateByCardForm from "./components/SimulateByCardForm";
import SimulateCategoryForm from "./components/SimulateCategoryForm";

function App() {
  const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

  return (
    <div style={{ padding: "20px" }}>
      <h1>MTG Probability Simulator</h1>
      <RootInfo apiUrl={API_URL} />
      <HealthStatus apiUrl={API_URL} />

      <h2>Quick Land Simulation</h2>
      <SimulationForm apiUrl={API_URL} />

      <hr />
      <CardSearchForm apiUrl={API_URL} />
      <CardNamesLookup apiUrl={API_URL} />
      <ResolveDeckForm apiUrl={API_URL} />

      <hr />
      <SimulateByNamesForm apiUrl={API_URL} />
      <SimulateByCardForm apiUrl={API_URL} />
      <SimulateCategoryForm apiUrl={API_URL} />
    </div>
  );
}

export default App;
