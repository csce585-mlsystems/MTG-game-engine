import React, { useEffect, useState } from "react";
import { useHoverCard } from "../HoverContext";

export default function CardHoverPreview() {
    const { hoverCard } = useHoverCard();
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

    useEffect(() => {
        function move(e) {
            setMousePos({ x: e.clientX, y: e.clientY });
        }
        window.addEventListener("mousemove", move);
        return () => window.removeEventListener("mousemove", move);
    }, []);

    if (!hoverCard) return null;

    const url =
        hoverCard?.image_uris?.large ||
        hoverCard?.image_uris?.normal ||
        hoverCard?.image_uris?.small;

    if (!url) return null;

    return (
        <div
            style={{
                pointerEvents: "none",
                position: "fixed",
                left: mousePos.x + 20,
                top: mousePos.y + 20,
                zIndex: 9999,
                background: "rgba(0,0,0,0.7)",
                padding: 4,
                borderRadius: 8,
                boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
            }}
        >
            <img
                src={url}
                alt={hoverCard.name}
                style={{
                    width: 260,
                    height: "auto",
                    display: "block",
                    borderRadius: 6,
                }}
            />
        </div>
    );
}
