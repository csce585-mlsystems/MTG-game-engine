import { useState } from "react";
import { useDeck } from "../DeckContext";

export default function CardModal({ card, onClose, runSimForCard, runSimForState }) {
  const [applyOracle, setApplyOracle] = useState(true);
  const [applyFavorites, setApplyFavorites] = useState(false);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const large = card?.image_uris?.large || card?.image_uris?.normal || card?.image_uris?.small;
  const { favorites, decklist } = useDeck();

  function buildOracleNames(includeThis) {
    const names = new Set();
    if (applyFavorites && favorites && decklist) {
      for (const c of decklist) {
        if (favorites.has(c.id) && c.name) names.add(c.name);
      }
    }
    if (includeThis && applyOracle && card?.name) names.add(card.name);
    return names.size > 0 ? Array.from(names) : undefined;
  }

  async function simulateCard() {
    setRunning(true);
    setResult(null);
    try {
      const oracleNames = buildOracleNames(true);
      const resp = await runSimForCard(card, oracleNames);
      setResult(resp);
    } finally {
      setRunning(false);
    }
  }

  async function simulateCategory() {
    setRunning(true);
    setResult(null);
    try {
      // derive simple category from type_line
      const t = (card.type_line || "").toLowerCase();
      let cat = "artifact";
      if (t.includes("land")) cat = "land";
      else if (t.includes("creature")) cat = "creature";
      else if (t.includes("instant")) cat = "instant";
      else if (t.includes("sorcery")) cat = "sorcery";
      else if (t.includes("enchantment")) cat = "enchantment";
      else if (t.includes("planeswalker")) cat = "planeswalker";
      const oracleNames = buildOracleNames(true);
      const resp = await runSimForState(null, cat, oracleNames);
      setResult(resp);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000
    }}
      onClick={onClose}
    >
      <div style={{
        background: "#111", color: "#fff", width: 820, maxWidth: "95vw",
        borderRadius: 8, overflow: "hidden", boxShadow: "0 4px 16px rgba(0,0,0,0.5)"
      }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: "grid", gridTemplateColumns: "340px 1fr" }}>
          <div style={{ background: "#000" }}>
            {large ? <img src={large} alt={card.name} style={{ width: "100%", display: "block" }} /> : null}
          </div>
          <div style={{ padding: 16, display: "grid", gap: 12 }}>
            <div>
              <div style={{ fontSize: 20, fontWeight: 700 }}>{card.name}</div>
              <div style={{ opacity: 0.8, fontSize: 12, marginTop: 2 }}>{card.type_line}</div>
            </div>
            <pre style={{ whiteSpace: "pre-wrap", background: "#181818", padding: 8, borderRadius: 6, maxHeight: 220, overflow: "auto" }}>
{card.oracle_text || "(No oracle text)"}
            </pre>
            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input type="checkbox" checked={applyOracle} onChange={(e) => setApplyOracle(e.target.checked)} />
              Apply this card's oracle effects in simulation
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input type="checkbox" checked={applyFavorites} onChange={(e) => setApplyFavorites(e.target.checked)} />
              Apply starred cards' oracle effects
            </label>
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={simulateCard} disabled={running} style={{ padding: "8px 12px" }}>
                {running ? "Simulating..." : "Simulate: draw this card"}
              </button>
              <button onClick={simulateCategory} disabled={running} style={{ padding: "8px 12px" }}>
                {running ? "Simulating..." : "Simulate: draw this card's type"}
              </button>
              <div style={{ flex: 1 }} />
              <button onClick={onClose} style={{ padding: "8px 12px" }}>Close</button>
            </div>
            {result && (
              <div style={{ marginTop: 8, background: "#181818", borderRadius: 6, padding: 10 }}>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>Simulation Result</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, fontSize: 13 }}>
                  <div>Category: <strong>{result.category}</strong></div>
                  <div>Probability: <strong>{(result.probability * 100).toFixed(2)}%</strong></div>
                  <div>Hits: <strong>{result.hits}</strong></div>
                  <div>Runs: <strong>{result.simulations_run}</strong></div>
                  <div>Sim/sec: <strong>{Math.round(result.simulations_per_second).toLocaleString()}</strong></div>
                  <div>Time: <strong>{result.execution_time_seconds.toFixed(3)}s</strong></div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


