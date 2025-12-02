import React, { useState } from "react";
import { useDeck } from "../DeckContext";
import CardItem from "./CardItem";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import CardModal from "./CardModal";
import "./DeckPanel.css";

function DraggableCard({
    card,
    probability,
    onDoubleClick,
    onStarClick,
    starred,
    viewMode
}) {
    const dragId = card.id;
    const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: dragId });

    return (
        <div
            ref={setNodeRef}
            {...listeners}
            {...attributes}
            style={{
                transform: transform
                    ? `translate3d(${transform.x}px, ${transform.y}px, 0)`
                    : undefined,
                cursor: "grab"
            }}
        >
            <CardItem
                card={card}
                probability={probability}
                onDoubleClick={onDoubleClick}
                onStarClick={onStarClick}
                starred={starred}
                count={card.count}
                viewMode={viewMode}
            />
        </div>
    );
}

export default function DeckPanel() {
    const {
        sortedDeckView,
        toggleFavorite,
        runSimForCard,
        runSimForState,
        loading,
        probabilities,
        favorites
    } = useDeck();

    const [modalCard, setModalCard] = useState(null);
    const [viewMode, setViewMode] = useState("list");

    const { setNodeRef: setDeckDroppableRef } = useDroppable({ id: "decklist" });

    function handleDouble(card) {
        setModalCard(card);
    }

    function handleStar(card) {
        toggleFavorite(card.id);
    }

    function toggleView() {
        setViewMode((v) => (v === "list" ? "grid" : "list"));
    }

    return (
        <div className="deck-panel">
            <div className="deck-header">
                <h3 style={{ margin: 0 }}>Deck</h3>

                <button className="toggle-btn" onClick={toggleView}>
                    {viewMode === "list" ? "Grid View" : "List View"}
                </button>
            </div>

            {probabilities?.lastResp && (
                <div className="deck-summary">
                    <div className="summary-title">Last Simulation</div>

                    <div className="summary-grid">
                        <div>
                            Category: <strong>{probabilities.lastResp.category}</strong>
                        </div>
                        <div>
                            Probability:{" "}
                            <strong>
                                {(probabilities.lastResp.probability * 100).toFixed(2)}%
                            </strong>
                        </div>
                        <div>
                            Hits: <strong>{probabilities.lastResp.hits}</strong>
                        </div>
                        <div>
                            Runs: <strong>{probabilities.lastResp.simulations_run}</strong>
                        </div>
                    </div>
                </div>
            )}

            <div
                ref={setDeckDroppableRef}
                className={viewMode === "list" ? "deck-list-view" : "deck-grid-view"}
            >
                {sortedDeckView.map(card => {
                    const starred = favorites?.has(card.id);
                    const probability =
                        probabilities?.lastResp?.per_card?.[card.name?.toLowerCase()] ??
                        null;

                    return (
                        <DraggableCard
                            key={card.id}
                            card={card}
                            onDoubleClick={handleDouble}
                            onStarClick={handleStar}
                            starred={starred}
                            probability={probability}
                            viewMode={viewMode}
                        />
                    );
                })}
            </div>

            {loading && <div className="loading-msg">Updating probabilities...</div>}

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
