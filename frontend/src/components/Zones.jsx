import React from "react";
import { useDeck } from "../DeckContext";
import { useDroppable } from "@dnd-kit/core";
import DraggableCard from "./DraggableCard";
import "./Zones.css";

function DroppableZone({ zoneId, title, cards }) {
    const { setNodeRef, isOver } = useDroppable({ id: zoneId });

    return (
        <div
            ref={setNodeRef}
            className="zone-box"
            style={{
                background: isOver ? "rgba(255,255,255,0.12)" : "rgba(255,255,255,0.15)"
            }}
        >
            <div className="zone-title">{title}</div>

            <div className="zone-cards">
                {cards.map(card => (
                    <DraggableCard
                        key={card.instanceId || card.id}
                        card={card}
                        probability={null}
                        starred={false}
                        viewMode="grid"
                    />
                ))}
            </div>
        </div>
    );
}

export default function Zones() {
    const {
        hand,
        battlefield,
        graveyard,
        top,
        bottom
    } = useDeck();

    return (
        <div className="zones-layout">
            <DroppableZone
                zoneId="graveyard"
                title="Graveyard"
                cards={graveyard}
            />

            <DroppableZone
                zoneId="battlefield"
                title="Battlefield"
                cards={battlefield}
            />

            <DroppableZone
                zoneId="hand"
                title="Hand"
                cards={hand}
            />

            <div className="middle-zones">
                <DroppableZone
                    zoneId="bottom"
                    title="Bottom of Library"
                    cards={bottom}
                />
                <div className="deck-placeholder">
                    DECK
                    <small>Unknown</small>
                </div>
                <DroppableZone
                    zoneId="top"
                    title="Top of Library"
                    cards={top}
                />
            </div>
        </div>
    );
}
