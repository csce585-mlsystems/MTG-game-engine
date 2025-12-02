import React from "react";
import "./App.css";
import { DeckProvider, useDeck } from "./DeckContext";
import DeckPanel from "./components/DeckPanel";
import Zones from "./components/Zones";
import { DndContext } from "@dnd-kit/core";
import DeckUploadResolve from "./components/DeckUploadResolve.jsx";

function InnerApp() {
  const {
    decklist,
    hand,
    battlefield,
    graveyard,
    top,
    bottom,
    moveCard
  } = useDeck();

  function findZoneOfCard(id) {
    // decklist: draggable id is card.id
    if (decklist.some(c => c.id === id)) return "decklist";

    const match = c => (c.instanceId || c.id) === id;

    if (hand.some(match)) return "hand";
    if (battlefield.some(match)) return "battlefield";
    if (graveyard.some(match)) return "graveyard";
    if (top.some(match)) return "top";
    if (bottom.some(match)) return "bottom";

    return null;
  }

  function handleDragEnd(event) {
    const activeId = event.active?.id;
    const overId = event.over?.id;

    if (!activeId || !overId) return;

    const zones = ["decklist", "hand", "battlefield", "graveyard", "top", "bottom"];

    let toZone = "decklist";
    if (zones.includes(overId)) {
      toZone = overId;
    } else {
      const overZone = findZoneOfCard(overId);
      if (overZone) toZone = overZone;
    }

    const fromZone = findZoneOfCard(activeId);

    if (fromZone && toZone && fromZone !== toZone) {
      moveCard({ cardId: activeId, fromZone, toZone });
    }
  }

  return (
    <DndContext onDragEnd={handleDragEnd}>
      {decklist.length === 0 ? (
        <div style={{ padding: 24 }}>
          <DeckUploadResolve />
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 380px",
            gap: 12,
            padding: 12
          }}
        >
          <div>
            <Zones />
          </div>
          <aside>
            <DeckPanel />
          </aside>
        </div>
      )}
    </DndContext>
  );
}

export default function App() {
  return (
    <DeckProvider>
      <InnerApp />
    </DeckProvider>
  );
}