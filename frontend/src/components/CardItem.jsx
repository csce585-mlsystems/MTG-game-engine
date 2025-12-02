import React from "react";
import "./CardItem.css";

export default function CardItem({
    card,
    probability = null,
    onDoubleClick,
    onStarClick,
    starred = false,
    count = null,
    viewMode = "grid" // "grid" | "list" | "zone"
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
                </>
            )}

            {/* LIST MODE (wide art_crop banner) */}
            {viewMode === "list" && (
                <div
                    className="list-art"
                    style={{ backgroundImage: `url(${imgArt})` }}
                >
                    <div className="list-name">
                        {count !== null && count > 1 && (
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
