import React from "react";
import "./CardItem.css";

export default function CardItem({ card, probability = null, onDoubleClick, onStarClick, dragAttributes = {}, dragging = false }) {
    const imgUrl = card.image_uris && (card.image_uris.normal || card.image_uris.small || card.image_uris.large);
    const background = imgUrl ? `url(${imgUrl}) center/cover no-repeat` : "#333";

    return (
        <div
            className="card-item"
            onDoubleClick={() => onDoubleClick?.(card)}
            style={{
                background,
                opacity: dragging ? 0.6 : 1,
                display: "flex",
                alignItems: "flex-end",
                padding: "8px",
                color: "white",
                height: "80px",
                borderRadius: "6px",
                backgroundColor: "#222"
            }}
            {...dragAttributes}
        >
            <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, textShadow: "0 1px 3px rgba(0,0,0,0.7)" }}>{card.name}</div>
                <div style={{ fontSize: "0.8rem", opacity: 0.9 }}>
                    {probability !== null ? `${(probability * 100).toFixed(2)}%` : ""}
                </div>
            </div>
            <button onClick={(e) => { e.stopPropagation(); onStarClick?.(card); }} style={{
                marginLeft: 8,
                background: "transparent",
                border: "none",
                color: "gold",
                fontSize: 20,
                cursor: "pointer"
            }}>
                ★
            </button>
        </div>
    );
}