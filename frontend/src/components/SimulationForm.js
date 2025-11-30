import { useState } from "react";

export default function SimulationForm() {
    const [lands, setLands] = useState(); //24 being number of lands
    const [nonlands, setNonLands] = useState(); //36 being number of nonlands
    const [sim, setSims] = useState(); //1000 simulations
    const [result, setResult] = useState(null);

    const runSim = async () => {
        const res = await fetch('/simulate/lands=${lands}&non_lands=$nonLands}&num_simulations={sims}');
        const data = await res.json();
        setResult(data);
    }

    return (
        <div>
            <h2>Land probability Simulator</h2>
            <input type="number" value={lands} onchange={e => setLands(e.target.values)} /> lands
            <input type="number" value={nonlands} onchange={e => setNonLands(e.target.values)} /> nonlands
            <button onlick={runSim}>Run Simulation</button>

            {result && <p>probability: {(result.probability * 100).toFixed(2)}%</p>}
        </div>
    );

}
