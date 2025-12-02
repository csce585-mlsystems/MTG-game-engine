import React, { useState } from "react";
import { useDeck } from "../DeckContext";
import CardItem from "./CardItem";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import CardModal from "./CardModal";

function DraggableCard({ card, onDoubleClick, onStarClick, starred }) {
    const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: card.id });
    return (
        <div
            ref={setNodeRef}
            {...listeners}
            {...attributes}
            style={{ transform: transform ? `translate3d(${transform.x}px,${transform.y}px,0)` : undefined, cursor: "grab" }}
        >
            <CardItem card={card} probability={null} onDoubleClick={onDoubleClick} onStarClick={onStarClick} starred={starred} count={card.count} />
        </div>
    );
}

export default function DeckPanel() {
    const { sortedDeckView, toggleFavorite, runSimForCard, runSimForState, loading, probabilities, favorites } = useDeck();
    const [modalCard, setModalCard] = useState(null);
    const ids = sortedDeckView.map(c => c.id);
    const { setNodeRef: setDeckDroppableRef, isOver } = useDroppable({ id: "decklist" });

    // double-click handler
    async function handleDouble(card) {
        setModalCard(card);
    }

    function handleStar(card) {
        toggleFavorite(card.id);
    }

    return (
        <div style={{ padding: 8 }}>
            <h3>Deck</h3>
            {probabilities?.lastResp && (
                <div style={{ margin: "8px 0 12px", padding: 8, border: "1px solid #333", borderRadius: 8, background: "#0f0f0f", color: "#eee" }}>
                    <div style={{ fontWeight: 600, marginBottom: 4 }}>Last Simulation</div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, fontSize: 13 }}>
                        <div>Category: <strong>{probabilities.lastResp.category}</strong></div>
                        <div>Probability: <strong>{(probabilities.lastResp.probability * 100).toFixed(2)}%</strong></div>
                        <div>Hits: <strong>{probabilities.lastResp.hits}</strong></div>
                        <div>Runs: <strong>{probabilities.lastResp.simulations_run}</strong></div>
                    </div>
                </div>
            )}
            <div
                ref={setDeckDroppableRef}
                className="card-grid"
                style={{ border: isOver ? "2px solid #3182ce" : "2px dashed #999", padding: 6, borderRadius: 8 }}
            >
                {sortedDeckView.map(card => {
                    const starred = favorites?.has(card.id);
                    return (
                        <DraggableCard key={card.id} card={card} onDoubleClick={handleDouble} onStarClick={handleStar} starred={!!starred} />
                    );
                })}
            </div>

            {loading && <div style={{ marginTop: 8 }}>Updating probabilities...</div>}
            {modalCard && (
                <CardModal
                    card={modalCard}
                    onClose={() => setModalCard(null)}
                    runSimForCard={runSimForCard}
                    runSimForState={runSimForState}
                />
            )}
        </div>
    );
}