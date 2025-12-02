import React from "react";
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

import { DeckProvider, useDeck } from "./DeckContext";
import DeckPanel from "./components/DeckPanel";
import Zones from "./components/Zones";
import { DndContext } from "@dnd-kit/core";
import DeckUploadResolve from "./components/DeckUploadResolve.jsx";


function InnerApp() {
  const { decklist, hand, battlefield, graveyard, moveCard } = useDeck();

  // onDragEnd will receive event.active.id (dragged) and event.over?.id (dropped target)
  function handleDragEnd(event) {
    const activeId = event.active?.id;
    const overId = event.over?.id;

    if (!activeId || !overId) return;

    // Our convention: droppable id matches zone: "decklist", "hand", "battlefield", "graveyard"
    // If overId is a card id inside any zone, resolve its parent zone.
    const zones = ["decklist", "hand", "battlefield", "graveyard"];
    let toZone = "decklist";
    if (zones.includes(overId)) {
      toZone = overId;
    } else {
      // Determine which zone the over card currently belongs to
      function findZoneOfCard(id) {
        // For decklist, dragId = card.id, for other zones dragId = instanceId
        if (decklist.some(c => c.id === id)) return "decklist";
        const match = (c) => (c.instanceId || c.id) === id;
        if (hand.some(match)) return "hand";
        if (battlefield.some(match)) return "battlefield";
        if (graveyard.some(match)) return "graveyard";
        return null;
      }
      const overZone = findZoneOfCard(overId);
      if (overZone) toZone = overZone;
    }
    // Reuse same resolver to determine from-zone by active drag id
    function findZoneOfCard(id) {
      if (decklist.some(c => c.id === id)) return "decklist";
      const match = (c) => (c.instanceId || c.id) === id;
      if (hand.some(match)) return "hand";
      if (battlefield.some(match)) return "battlefield";
      if (graveyard.some(match)) return "graveyard";
      return null;
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
          {/* When no deck is loaded, only show the deck upload/resolve flow */}
          <DeckUploadResolve />
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 12, padding: 12 }}>
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