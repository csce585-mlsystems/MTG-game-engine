import React from "react";
import { useDraggable } from "@dnd-kit/core";
import CardItem from "./CardItem";

export default function DraggableCard({
  card,
  probability = null,
  starred = false,
  onDoubleClick,
  onStarClick,
  viewMode = "grid",
  activeDragId = null,
  effectEnabled = false,
  onEffectToggle,
}) {
  const dragId = card.instanceId || card.id;
  const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: dragId });

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      style={{
        transform: transform ? `translate3d(${transform.x}px,${transform.y}px,0)` : undefined,
        cursor: "grab",
        opacity: activeDragId === dragId ? 0 : 1,
        pointerEvents: activeDragId === dragId ? "none" : "auto",
      }}
    >
      <CardItem
        card={card}
        probability={probability}
        onDoubleClick={onDoubleClick}
        onStarClick={onStarClick}
        starred={starred}
        count={card?.count ?? null}
        viewMode={viewMode}
        effectEnabled={effectEnabled}
        onEffectToggle={onEffectToggle}
      />
    </div>
  );
}


