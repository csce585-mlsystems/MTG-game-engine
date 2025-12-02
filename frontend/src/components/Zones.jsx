import React from "react";
import { useDeck } from "../DeckContext";
import { useDroppable } from "@dnd-kit/core";
import DraggableCard from "./DraggableCard";
import "./Zones.css";

function DroppableZone({
    zoneId,
    title,
    cards,
    variant,
    activeDragId = null,
    onClear,
    isEffectEnabled,
    onToggleEffect,
    onCardDoubleClick,
}) {
    const { setNodeRef, isOver } = useDroppable({ id: zoneId });

    return (
        <div
            ref={setNodeRef}
            className={`zone-box ${variant || ""} ${isOver ? "over" : ""}`}
        >
            <div className="zone-header">
                <div className="zone-title">{title}</div>
                <div className="zone-actions">
                    {cards.length > 0 && onClear && (
                        <button className="zone-clear-btn" onClick={() => onClear(zoneId)}>
                            Clear all
                        </button>
                    )}
                </div>
            </div>

            <div className="zone-cards">
                {cards.map(card => (
                    <DraggableCard
                        key={card.instanceId || card.id}
                        card={card}
                        probability={null}
                        starred={false}
                        viewMode="zone"
                        activeDragId={activeDragId}
                        effectEnabled={isEffectEnabled ? isEffectEnabled(card) : false}
                        onEffectToggle={onToggleEffect ? () => onToggleEffect(card) : undefined}
                        onDoubleClick={onCardDoubleClick}
                    />
                ))}
            </div>
        </div>
    );
}

export default function Zones({ activeDragId = null, onCardDoubleClick = null }) {
    const {
        hand,
        battlefield,
        graveyard,
        top,
        bottom,
        clearZone,
        zoneEffectIds,
        toggleZoneEffect
    } = useDeck();

    return (
        <div className="zones-layout">
            <DroppableZone
                zoneId="graveyard"
                title="Graveyard"
                cards={graveyard}
                variant="graveyard"
                activeDragId={activeDragId}
                onClear={clearZone}
                isEffectEnabled={(c) => !!(c?.instanceId && zoneEffectIds.has(c.instanceId))}
                onToggleEffect={(c) => c?.instanceId && toggleZoneEffect(c.instanceId)}
                    onCardDoubleClick={onCardDoubleClick}
            />

            <DroppableZone
                zoneId="battlefield"
                title="Battlefield"
                cards={battlefield}
                variant="battlefield"
                activeDragId={activeDragId}
                onClear={clearZone}
                isEffectEnabled={(c) => !!(c?.instanceId && zoneEffectIds.has(c.instanceId))}
                onToggleEffect={(c) => c?.instanceId && toggleZoneEffect(c.instanceId)}
                    onCardDoubleClick={onCardDoubleClick}
            />

            <DroppableZone
                zoneId="hand"
                title="Hand"
                cards={hand}
                variant="hand"
                activeDragId={activeDragId}
                onClear={clearZone}
                isEffectEnabled={(c) => !!(c?.instanceId && zoneEffectIds.has(c.instanceId))}
                onToggleEffect={(c) => c?.instanceId && toggleZoneEffect(c.instanceId)}
                    onCardDoubleClick={onCardDoubleClick}
            />

            <div className="middle-zones">
                <DroppableZone
                    zoneId="bottom"
                    title="Bottom of Library"
                    cards={bottom}
                    variant="bottom"
                    activeDragId={activeDragId}
                    onClear={clearZone}
                    isEffectEnabled={(c) => !!(c?.instanceId && zoneEffectIds.has(c.instanceId))}
                    onToggleEffect={(c) => c?.instanceId && toggleZoneEffect(c.instanceId)}
                    onCardDoubleClick={onCardDoubleClick}
                />
                <div className="deck-placeholder" title="Deck">
                    <div className="deck-badge" aria-label="DECK Unknown">
                        <span className="deck-word">DECK</span>
                        <span className="unknown-word">Unknown</span>
                    </div>
                </div>
                <DroppableZone
                    zoneId="top"
                    title="Top of Library"
                    cards={top}
                    variant="top"
                    activeDragId={activeDragId}
                    onClear={clearZone}
                    isEffectEnabled={(c) => !!(c?.instanceId && zoneEffectIds.has(c.instanceId))}
                    onToggleEffect={(c) => c?.instanceId && toggleZoneEffect(c.instanceId)}
                    onCardDoubleClick={onCardDoubleClick}
                />
            </div>
        </div>
    );
}
