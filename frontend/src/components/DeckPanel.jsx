import React, { useState } from "react";
import { useDeck } from "../DeckContext";
import { useDroppable } from "@dnd-kit/core";
import CardModal from "./CardModal";
import "./DeckPanel.css";
import DraggableCard from "./DraggableCard";

export default function DeckPanel({ activeDragId = null }) {
    const {
        sortedDeckView,
        toggleFavorite,
        runSimForCard,
        runSimForState,
        loading,
        probabilities,
        favorites,
        applyZoneEffects,
        setApplyZoneEffects
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

                <label style={{ display: "flex", alignItems: "center", gap: 6, marginLeft: 8, fontSize: 12 }} title="Include oracle effects from cards currently in zones (hand, battlefield, graveyard, top/bottom)">
                    <input
                        type="checkbox"
                        checked={!!applyZoneEffects}
                        onChange={(e) => setApplyZoneEffects(e.target.checked)}
                    />
                    Include zone effects
                </label>
            </div>

            {probabilities?.lastResp && (() => {
                const cat = String(probabilities.lastResp.category || "").toLowerCase();
                const needsArticle = cat && !["specific_cards"].includes(cat);
                const article = /^[aeiou]/.test(cat) ? "an" : "a";
                const title = needsArticle ? `Chance to draw ${article} ${cat}` : "Draw probability";
                const pct = (probabilities.lastResp.probability * 100).toFixed(2);
                return (
                    <div className="deck-summary">
                        <div className="summary-title">{title}</div>
                        <div className="summary-grid">
                            <div>
                                Probability: <strong>{pct}%</strong>
                            </div>
                            <div>
                                Hits: <strong>{probabilities.lastResp.hits}</strong>
                            </div>
                            <div>
                                Runs: <strong>{probabilities.lastResp.simulations_run}</strong>
                            </div>
                        </div>
                    </div>
                );
            })()}

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
                            activeDragId={activeDragId}
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
