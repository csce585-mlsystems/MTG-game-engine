import React from "react";
import "./CardItem.css";

export default function CardItem({
    card,
    probability = null,
    onDoubleClick,
    onStarClick,
    starred = false,
    count = null,
    viewMode = "grid", // "grid" | "list" | "zone"
    effectEnabled = false,
    onEffectToggle
}) {
    const imgFull =
        card.image_uris?.normal ||
        card.image_uris?.large ||
        card.image_uris?.small;

    const imgArt = card.image_uris?.art_crop || imgFull;

    return (
        <div
            className={`card-item ${viewMode}`}
            onDoubleClick={() => onDoubleClick?.(card)}
        >

            {/* ZONE MODE (mini–card like old LittleCard) */}
            {viewMode === "zone" && (
                <>
                    <img src={imgFull} alt={card.name} className="zone-img" />
                    <button
                        className={`effect-toggle ${effectEnabled ? "active" : ""}`}
                        title={effectEnabled ? "Included in zone effects" : "Include in zone effects"}
                        onPointerDown={(e) => { e.stopPropagation(); e.preventDefault(); }}
                        onClick={(e) => { e.stopPropagation(); onEffectToggle?.(card); }}
                    >
                        fx
                    </button>
                </>
            )}

            {/* LIST MODE (wide art_crop banner) */}
            {viewMode === "list" && (
                <div
                    className="list-art"
                    style={{ backgroundImage: `url(${imgArt})` }}
                >
                    <div className="list-name">
                        {count !== null && count > 0 && (
                            <span className="list-count">{count}</span>
                        )}
                        {card.name}
                        {probability !== null && (
                            <span className="list-prob">
                                {(probability * 100).toFixed(2)}%
                            </span>
                        )}
                    </div>
                </div>
            )}

            {viewMode === "grid" && (
                <>
                    <img src={imgFull} alt={card.name} className="grid-img" />
                    {count !== null && count > 0 && (
                        <div className="grid-count" title={`${count} copies remaining`}>
                            {count}
                        </div>
                    )}
                    {probability !== null && (
                        <div className="prob-overlay">
                            {(probability * 100).toFixed(2)}%
                        </div>
                    )}
                </>
            )}

            {viewMode !== "zone" && (
                <button
                    className={`card-star ${starred ? "active" : ""}`}
                    onClick={(e) => {
                        e.stopPropagation();
                        onStarClick?.(card);
                    }}
                >
                    ★
                </button>
            )}
        </div>
    );
}
