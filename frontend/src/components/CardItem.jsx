import React from "react";
import "./CardItem.css";

export default function CardItem({ card, probability = null, onDoubleClick, onStarClick, dragAttributes = {}, dragging = false, starred = false, count = null }) {
    const imgUrl = card.image_uris && (card.image_uris.small || card.image_uris.normal || card.image_uris.large);

    return (
        <div
            className="card-item"
            onDoubleClick={() => onDoubleClick?.(card)}
            style={{ opacity: dragging ? 0.6 : 1 }}
            {...dragAttributes}
        >
            {imgUrl ? (
                <img src={imgUrl} alt={card.name} />
            ) : (
                <div style={{ width: "100%", height: "100%", background: "#222" }} />
            )}
            <div className="overlay">
                <div className="title">{card.name}</div>
                {probability !== null && <div className="prob">{(probability * 100).toFixed(2)}%</div>}
            </div>
            {typeof count === "number" && count > 1 && (
                <div className="card-count" title={`${count} copies remaining`}>{count}</div>
            )}
            <button
                className={`card-star${starred ? " active" : ""}`}
                onPointerDown={(e) => { e.stopPropagation(); e.preventDefault(); }}
                onMouseDown={(e) => { e.stopPropagation(); e.preventDefault(); }}
                onTouchStart={(e) => { e.stopPropagation(); e.preventDefault(); }}
                onClick={(e) => { e.stopPropagation(); onStarClick?.(card); }}
                title="Favorite"
                type="button"
            >
                ★
            </button>
        </div>
    );
}