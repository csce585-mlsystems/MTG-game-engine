import React from "react";
import { useDeck } from "../DeckContext";
import CardItem from "./CardItem";
import { DndContext, useDraggable, useDroppable } from "@dnd-kit/core";

function DraggableCard({ card }) {
    const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: card.id });
    return (
        <div ref={setNodeRef} {...listeners} {...attributes} style={{ transform: transform ? `translate3d(${transform.x}px,${transform.y}px,0)` : undefined }}>
            <CardItem card={card} />
        </div>
    );
}

function DroppableZone({ zoneId, title, cards, onDrop }) {
    const { isOver, setNodeRef } = useDroppable({ id: zoneId });
    return (
        <div ref={setNodeRef} style={{
            minHeight: 160,
            border: "2px dashed rgba(255,255,255,0.06)",
            padding: 8,
            background: isOver ? "rgba(255,255,255,0.02)" : "transparent",
            borderRadius: 6
        }}>
            <h4>{title}</h4>
            <div style={{ display: "grid", gap: 8 }}>
                {cards.map(c => <DraggableCard key={c.id} card={c} />)}
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