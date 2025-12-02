import { useState } from "react";
import { useDeck } from "../DeckContext";

// Parse decklist lines with emphasis on "N Card Name" where names may contain commas.
// Supported (in priority order):
// - "4 Enduring Curiosity"                -> count then full name
// - "Kaito, Bane of Nightmares 3"         -> name then trailing count
// - "Kaito, Bane of Nightmares x3"        -> name then 'xN'
// - "Kaito, Bane of Nightmares, 3"        -> name then comma then N (only if last token is integer)
function parseDeckText(text) {
  const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  const deck = [];
  for (const line of lines) {
    let name = "";
    let count = 1;

    // number at start: "4 Card Name"
    let m = line.match(/^\s*(\d+)\s+(.+?)\s*$/);
    if (m) {
      count = Number(m[1]);
      name = m[2].trim();
    } else {
      // name then ' xN' suffix
      m = line.match(/^(.+?)\s*[xX]\s*(\d+)\s*$/);
      if (m) {
        name = m[1].trim();
        count = Number(m[2]);
      } else {
        // name then trailing integer count: "Name ... 3"
        m = line.match(/^(.+?)\s+(\d+)\s*$/);
        if (m) {
          name = m[1].trim();
          count = Number(m[2]);
        } else {
          // name, N format but allow commas inside name: take last comma only if after it is integer
          const lastComma = line.lastIndexOf(",");
          if (lastComma !== -1) {
            const left = line.slice(0, lastComma).trim();
            const right = line.slice(lastComma + 1).trim();
            if (/^\d+$/.test(right)) {
              name = left;
              count = Number(right);
            } else {
              name = line.trim();
            }
          } else {
            name = line.trim();
          }
        }
      }
    }

    if (name) {
      const n = Number.isFinite(count) && count > 0 ? count : 1;
      deck.push({ name, count: n });
    }
  }
  return deck;
}

export default function DeckUploadResolve({ apiUrl }) {
  const API_URL = apiUrl || process.env.REACT_APP_API_URL || "http://localhost:8000";
  const { setDecklist, runSimForState } = useDeck();
  const [fileName, setFileName] = useState("");
  const [text, setText] = useState("");
  const [parsed, setParsed] = useState([]);
  const [resp, setResp] = useState(null);
  const [error, setError] = useState(null);
  const [unresolvedEdits, setUnresolvedEdits] = useState({});
  const [loading, setLoading] = useState(false);

  const onFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    const content = await file.text();
    setText(content);
    setParsed(parseDeckText(content));
  };

  const onParse = () => {
    setParsed(parseDeckText(text));
  };

  const resolve = async (deck) => {
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/cards/resolve-deck`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ deck })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResp(data);
      // Seed unresolved edits with current unresolved names
      const edits = {};
      for (const u of data.unresolved || []) {
        edits[u] = u;
      }
      setUnresolvedEdits(edits);

      // If fully resolved, immediately take over the deck in DeckContext and compute probabilities
      if ((data.unresolved?.length || 0) === 0 && Array.isArray(data.resolved)) {
        const cards = data.resolved.map(rc => ({
          id: rc.card.id || rc.card.name,
          ...rc.card,
          count: rc.count || 1
        }));
        setDecklist(cards);
        // fire-and-forget; DeckContext will update UI
        runSimForState(cards, "land");
      }
    } catch (e) {
      setError("Resolve failed");
      // eslint-disable-next-line no-console
      console.error(e);
    }
    setLoading(false);
  };

  const onResolveClick = () => resolve(parsed);

  const onReResolve = () => {
    // Build new deck by replacing unresolved names with edits, counts preserved
    const unresolvedSet = new Set(Object.keys(unresolvedEdits));
    const updated = parsed.map(entry => {
      if (unresolvedSet.has(entry.name)) {
        const newName = (unresolvedEdits[entry.name] || entry.name).trim();
        return { name: newName, count: entry.count };
      }
      return entry;
    });
    setParsed(updated);
    resolve(updated);
  };

  return (
    <div style={{ marginBottom: 24 }}>
      <h2>Upload / Paste Decklist → Resolve</h2>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
        <input type="file" accept=".txt" onChange={onFileChange} />
        {fileName && <span>{fileName}</span>}
        <button onClick={onParse}>Parse Text</button>
        <button onClick={onResolveClick} disabled={!parsed.length || loading}>
          {loading ? "Resolving..." : "Resolve Deck"}
        </button>
      </div>
      <textarea
        rows={8}
        placeholder="Paste decklist here (e.g., '4 Lightning Bolt' or 'Lightning Bolt,4')"
        value={text}
        onChange={(e) => setText(e.target.value)}
        style={{ width: 500 }}
      />

      {error && <p style={{ color: "red" }}>{error}</p>}

      {parsed.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <p>Parsed entries: {parsed.length}</p>
          <ul>
            {parsed.map((d, idx) => (
              <li key={idx}>{d.name} — {d.count}</li>
            ))}
          </ul>
        </div>
      )}

      {resp && (
        <div style={{ marginTop: 12 }}>
          <h3>Derived Counts</h3>
          <pre style={{ background: "#f6f8fa", padding: 8 }}>{JSON.stringify(resp.derived_counts, null, 2)}</pre>

          <h3>Unresolved</h3>
          {resp.unresolved && resp.unresolved.length > 0 ? (
            <div style={{ display: "grid", gap: 6, maxWidth: 500 }}>
              {resp.unresolved.map((name) => (
                <div key={name} style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span style={{ minWidth: 120 }}>Original:</span>
                  <code style={{ background: "#eee", padding: "2px 6px" }}>{name}</code>
                  <span>→</span>
                  <input
                    value={unresolvedEdits[name] || ""}
                    onChange={(e) => setUnresolvedEdits({ ...unresolvedEdits, [name]: e.target.value })}
                    placeholder="Corrected name"
                    style={{ flex: 1 }}
                  />
                </div>
              ))}
              <button onClick={onReResolve}>Re-resolve</button>
            </div>
          ) : (
            <p>None</p>
          )}

          <h3>Resolved Cards</h3>
          <ul>
            {resp.resolved?.map((rc) => (
              <li key={rc.card.id}>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                  {rc.card.image_uris?.small && (
                    <img src={rc.card.image_uris.small} alt={rc.card.name} style={{ width: 36, height: "auto", borderRadius: 4 }} />
                  )}
                  <span>{rc.card.name} — count {rc.count}</span>
                </span>
                {rc.effects && rc.effects.length > 0 && (
                  <ul>
                    {rc.effects.map((e, i) => (
                      <li key={i}>{e.type}{e.target ? `(${e.target})` : ""}{typeof e.count === "number" ? ` x${e.count}` : ""}</li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}



