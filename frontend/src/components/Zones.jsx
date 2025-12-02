import React from "react";
import { useDeck } from "../DeckContext";
import CardItem from "./CardItem";
import { useDraggable, useDroppable } from "@dnd-kit/core";

function DraggableCard({ card }) {
    const dragId = card.instanceId || card.id;
    const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: dragId });
    return (
        <div
            ref={setNodeRef}
            {...listeners}
            {...attributes}
            style={{
                transform: transform ? `translate3d(${transform.x}px,${transform.y}px,0)` : undefined,
                cursor: "grab"
            }}
        >
            <CardItem card={card} />
        </div>
    );
}

function DroppableZone({ zoneId, title, cards, onDrop }) {
    const { isOver, setNodeRef } = useDroppable({ id: zoneId });
    return (
        <div
            ref={setNodeRef}
            style={{
                minHeight: 180,
                border: isOver ? "2px solid #3182ce" : "2px dashed #999",
                padding: 8,
                background: isOver ? "rgba(49,130,206,0.08)" : "transparent",
                borderRadius: 8,
                transition: "border-color 120ms ease, background 120ms ease"
            }}
        >
            <h4>{title}</h4>
            <div className="zone-grid">
                {cards.map(c => <DraggableCard key={c.instanceId || c.id} card={c} />)}
            </div>
        </div>
    );
}

export default function Zones() {
    const { hand, battlefield, graveyard } = useDeck();

    return (
        <div style={{ display: "grid", gap: 12 }}>
            <DroppableZone zoneId="hand" title="Hand" cards={hand} />
            <DroppableZone zoneId="battlefield" title="Battlefield" cards={battlefield} />
            <DroppableZone zoneId="graveyard" title="Graveyard" cards={graveyard} />
        </div>
    );
}