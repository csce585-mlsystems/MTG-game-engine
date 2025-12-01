import React from "react";
import { useDeck } from "../DeckContext";
import CardItem from "./CardItem";
import { DndContext, closestCenter } from "@dnd-kit/core";
import { SortableContext, arrayMove, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

function SortableCard({ id, card, onDoubleClick, onStarClick }) {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id });
    return (
        <div ref={setNodeRef} style={{
            transform: CSS.Transform.toString(transform),
            transition
        }}>
            <CardItem
                card={card}
                probability={null}
                onDoubleClick={onDoubleClick}
                onStarClick={onStarClick}
                dragAttributes={{ ...attributes, ...listeners }}
                dragging={isDragging}
            />
        </div>
    );
}

export default function DeckPanel() {
    const { sortedDeckView, toggleFavorite, runSimForCard, loading } = useDeck();
    const ids = sortedDeckView.map(c => c.id);

    // double-click handler
    async function handleDouble(card) {
        try {
            const res = await runSimForCard(card);
            // show result in alert or a nicer modal --> Need to figure out what we want to do here.
            alert(`Simulated prob: ${(res.probability * 100).toFixed(2)}% (theoretical ${(res.theoretical_probability * 100).toFixed(2)}%)`);
        } catch (e) {
            alert("Simulation failed: " + e.message);
        }
    }

    function handleStar(card) {
        toggleFavorite(card.id);
    }

    return (
        <div style={{ padding: 8 }}>
            <h3>Deck</h3>
            <DndContext collisionDetection={closestCenter}>
                <SortableContext items={ids} strategy={verticalListSortingStrategy}>
                    <div style={{ display: "grid", gap: 8 }}>
                        {sortedDeckView.map(card => (
                            <SortableCard key={card.id} id={card.id} card={card} onDoubleClick={handleDouble} onStarClick={handleStar} />
                        ))}
                    </div>
                </SortableContext>
            </DndContext>

            {loading && <div style={{ marginTop: 8 }}>Updating probabilities...</div>}
        </div>
    );
}