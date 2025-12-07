// frontend/src/components/ListCardItem.jsx
import React from "react";
import "./CardItem.css";

export default function ListCardItem({
    card,
    probability = null,
    onDoubleClick,
    onStarClick,
    starred = false,
    count = null,
}) {
    const art =
        card.image_uris &&
        (card.image_uris.art_crop ||
            card.image_uris.normal ||
            card.image_uris.small ||
            card.image_uris.large);

    const backgroundStyle = art
        ? { backgroundImage: `url(${art})` }
        : { backgroundColor: "#111" };

    return (
        <div
            className="list-card"
            style={backgroundStyle}
            onDoubleClick={() => onDoubleClick?.(card)}
        >
            <div className="list-card-content">
                <button
                    type="button"
                    className={`list-card-star${starred ? " active" : ""}`}
                    onPointerDown={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                    }}
                    onMouseDown={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                    }}
                    onTouchStart={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                    }}
                    onClick={(e) => {
                        e.stopPropagation();
                        onStarClick?.(card);
                    }}
                    title={starred ? "Unfavorite" : "Favorite"}
                >
                    ★
                </button>

                <div className="list-card-main">
                    <div className="list-card-name">{card.name}</div>
                    {card.type_line && (
                        <div className="list-card-type">{card.type_line}</div>
                    )}
                </div>

                <div className="list-card-meta">
                    {typeof count === "number" && count > 0 && (
                        <span className="list-card-count">x{count}</span>
                    )}
                    {probability !== null && (
                        <span className="list-card-prob">
                            {(probability * 100).toFixed(2)}%
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}
