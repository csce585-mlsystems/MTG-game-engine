import React, { createContext, useContext, useState } from "react";

const HoverContext = createContext(null);

export function useHoverCard() {
    return useContext(HoverContext);
}

export default function HoverProvider({ children }) {
    const [hoverCard, setHoverCard] = useState(null);

    const showHover = (card) => setHoverCard(card);
    const hideHover = () => setHoverCard(null);

    return (
        <HoverContext.Provider value={{ hoverCard, showHover, hideHover }}>
            {children}
        </HoverContext.Provider>
    );
}
