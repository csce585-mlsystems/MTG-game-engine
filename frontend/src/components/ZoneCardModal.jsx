import React from "react";

export default function ZoneCardModal({ card, onClose }) {
  if (!card) return null;

  const large =
    card?.image_uris?.large ||
    card?.image_uris?.normal ||
    card?.image_uris?.small;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.6)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          position: "relative",
          background: "#111",
          color: "#fff",
          width: 820,
          maxWidth: "95vw",
          borderRadius: 8,
          overflow: "hidden",
          boxShadow: "0 4px 16px rgba(0,0,0,0.5)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          aria-label="Close"
          onClick={(e) => {
            e.stopPropagation();
            onClose();
          }}
          style={{
            position: "absolute",
            top: 8,
            right: 8,
            width: 28,
            height: 28,
            borderRadius: "999px",
            border: "1px solid #555",
            background: "rgba(0,0,0,0.8)",
            color: "#fff",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 16,
            lineHeight: 1,
          }}
        >
          ×
        </button>
        <div style={{ display: "grid", gridTemplateColumns: "340px 1fr" }}>
          <div style={{ background: "#000" }}>
            {large ? (
              <img
                src={large}
                alt={card.name}
                style={{ width: "100%", display: "block" }}
              />
            ) : null}
          </div>
          <div
            style={{
              padding: 16,
              display: "grid",
              gap: 12,
            }}
          >
            <div>
              <div style={{ fontSize: 20, fontWeight: 700 }}>{card.name}</div>
              <div
                style={{
                  opacity: 0.8,
                  fontSize: 12,
                  marginTop: 2,
                }}
              >
                {card.type_line}
              </div>
            </div>
            <pre
              style={{
                whiteSpace: "pre-wrap",
                background: "#181818",
                padding: 8,
                borderRadius: 6,
                maxHeight: 260,
                overflow: "auto",
              }}
            >
{card.oracle_text || "(No oracle text)"}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}


