import React from "react";
import "./App.css";
import { DeckProvider, useDeck } from "./DeckContext";
import DeckPanel from "./components/DeckPanel";
import Zones from "./components/Zones";
import { DndContext, DragOverlay, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import { snapCenterToCursor } from "@dnd-kit/modifiers";
import CardItem from "./components/CardItem";
import DeckUploadResolve from "./components/DeckUploadResolve.jsx";
import ZoneCardModal from "./components/ZoneCardModal.jsx";

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

  const [activeDragCard, setActiveDragCard] = React.useState(null);
  const [zoneModalCard, setZoneModalCard] = React.useState(null);

  function getCardByDragId(id) {
    let card = decklist.find(c => c.id === id);
    if (card) return card;
    const match = c => (c.instanceId || c.id) === id;
    card = hand.find(match) || battlefield.find(match) || graveyard.find(match) || top.find(match) || bottom.find(match);
    return card || null;
  }

  function handleDragStart(event) {
    const id = event.active?.id;
    if (!id) return;
    const card = getCardByDragId(id);
    if (card) setActiveDragCard(card);
  }

  function handleDragEnd(event) {
    const activeId = event.active?.id;
    const overId = event.over?.id;

    setActiveDragCard(null);

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

  function handleDragCancel() {
    setActiveDragCard(null);
  }

  function handleZoneCardDoubleClick(card) {
    if (!card) return;
    setZoneModalCard(card);
  }

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        delay: 100,
        tolerance: 3
      }
    })
  );

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
      modifiers={[snapCenterToCursor]}
    >
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
            <Zones
              activeDragId={activeDragCard ? (activeDragCard.instanceId || activeDragCard.id) : null}
              onCardDoubleClick={handleZoneCardDoubleClick}
            />
          </div>
          <aside>
            <DeckPanel activeDragId={activeDragCard ? (activeDragCard.instanceId || activeDragCard.id) : null} />
          </aside>
        </div>
      )}
      <DragOverlay zIndex={3000}>
        {activeDragCard ? (
          <div
            style={{
              width: 150,
              pointerEvents: "none",
              transform: "scale(1.12)",
              transformOrigin: "center center",
              filter: "drop-shadow(0 6px 16px rgba(0,0,0,0.5))"
            }}
          >
            <CardItem card={activeDragCard} viewMode="zone" />
          </div>
        ) : null}
      </DragOverlay>

      {zoneModalCard && (
        <ZoneCardModal
          card={zoneModalCard}
          onClose={() => setZoneModalCard(null)}
        />
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