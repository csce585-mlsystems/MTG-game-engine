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


function InnerApp() {
  const { decklist, hand, battlefield, graveyard, moveCard } = useDeck();

  // onDragEnd will receive event.active.id (dragged) and event.over?.id (dropped target)
  function handleDragEnd(event) {
    const activeId = event.active?.id;
    const overId = event.over?.id;

    if (!activeId || !overId) return;

    // Our convention: droppable id matches zone: "decklist", "hand", "battlefield", "graveyard"
    // But if overId is a card id inside deckpanel, we still want to compute zone by parent. For simplicity
    // we'll use overId as zone if it equals zones; else if it matches a card id we consider its current zone.
    const zones = ["decklist", "hand", "battlefield", "graveyard"];
    let toZone = zones.includes(overId) ? overId : "decklist";
    function findZoneOfCard(id) {
      if (decklist.some(c => c.id === id)) return "decklist";
      if (hand.some(c => c.id === id)) return "hand";
      if (battlefield.some(c => c.id === id)) return "battlefield";
      if (graveyard.some(c => c.id === id)) return "graveyard";
      return null;
    }
    const fromZone = findZoneOfCard(activeId);
    if (fromZone && toZone && fromZone !== toZone) {
      moveCard({ cardId: activeId, fromZone, toZone });
    }
  }

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 12, padding: 12 }}>
        <div>
          <Zones />
        </div>
        <aside>
          <DeckPanel />
        </aside>
      </div>
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