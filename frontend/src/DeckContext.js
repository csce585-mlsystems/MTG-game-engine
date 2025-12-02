import React, { createContext, useContext, useMemo, useState } from "react";
import { resolveDeck, simulateByNames, simulateByCard } from "./api";

const DeckContext = createContext(null);
export function useDeck() { return useContext(DeckContext); }

function alphabetical(a, b) {
    return (a.name || "").localeCompare(b.name || "");
}

export function DeckProvider({ children }) {
    const [decklist, setDecklist] = useState([]);
    const [hand, setHand] = useState([]);
    const [battlefield, setBattlefield] = useState([]);
    const [graveyard, setGraveyard] = useState([]);
    const [top, setTop] = useState([]);
    const [bottom, setBottom] = useState([]);

    const [favorites, setFavorites] = useState(new Set());
    const [loading, setLoading] = useState(false);
    const [probabilities, setProbabilities] = useState({});

    // Sort decklist display
    const sortedDeckView = useMemo(() => {
        const v = decklist.filter(c => (c.count || 0) > 0);
        const fav = v.filter(c => favorites.has(c.id)).sort(alphabetical);
        const rest = v.filter(c => !favorites.has(c.id)).sort(alphabetical);
        return [...fav, ...rest];
    }, [decklist, favorites]);

    // Build backend deck payload
    function deckPayload(list = decklist) {
        const map = new Map();
        for (const c of list) {
            const count = c.count ?? 1;
            if (count <= 0) continue;
            map.set(c.name, (map.get(c.name) || 0) + count);
        }
        return Array.from(map.entries()).map(([name, count]) => ({ name, count }));
    }

    async function loadResolvedDeck(nameCountList) {
        setLoading(true);
        try {
            const res = await resolveDeck({ deck: nameCountList });
            const cards = res.resolved.map(rc => ({
                id: rc.card.id || rc.card.name,
                ...rc.card,
                count: rc.count || 1
            }));
            setDecklist(cards);

            await runSimForState(cards);
        } finally {
            setLoading(false);
        }
    }

    async function runSimForState(list = null, category = "land", oracleNames = undefined) {
        setLoading(true);
        try {
            const payload = deckPayload(list || decklist);
            const res = await simulateByNames({
                deck: payload,
                category,
                num_simulations: 20000,
                oracle_names: oracleNames
            });
            setProbabilities(prev => ({
                ...prev,
                lastResp: res,
                per_card: res.per_card || {}
            }));
            return res;
        } finally {
            setLoading(false);
        }
    }

    async function runSimForCard(card, oracleNames = undefined) {
        setLoading(true);
        try {
            const res = await simulateByCard({
                deck: deckPayload(decklist),
                target_names: [card.name],
                num_simulations: 20000,
                oracle_names: oracleNames
            });
            return res;
        } finally {
            setLoading(false);
        }
    }

    async function simulateActualDeckState() {
        const deckCounts = {};

        const apply = (arr, type) => {
            for (const c of arr) {
                const name = c.name;
                deckCounts[name] = deckCounts[name] || { top: 0, bottom: 0, in_hand: 0, in_gy: 0 };
                deckCounts[name][type]++;
            }
        };

        apply(top, "top");
        apply(bottom, "bottom");
        apply(hand, "in_hand");
        apply(graveyard, "in_gy");

        const payload = {
            deck: deckPayload(),
            zones: deckCounts,
            num_simulations: 20000
        };

        return await simulateByNames(payload);
    }

    function toggleFavorite(id) {
        setFavorites(prev => {
            const s = new Set(prev);
            s.has(id) ? s.delete(id) : s.add(id);
            return s;
        });
    }

    // Moving cards between zones
    function moveCard({ cardId, fromZone, toZone }) {
        if (fromZone === toZone) return;

        const removeOne = (arr, match) => {
            const idx = arr.findIndex(c => c.instanceId === match || c.id === match);
            if (idx === -1) return [arr, null];
            const copy = arr.slice();
            const [item] = copy.splice(idx, 1);
            return [copy, item];
        };

        let movedCard = null;

        // Decklist → zone (decrement count)
        if (fromZone === "decklist") {
            const idx = decklist.findIndex(c => c.id === cardId);
            if (idx !== -1 && decklist[idx].count > 0) {
                const src = decklist[idx];
                const newDL = decklist.slice();
                newDL[idx] = { ...src, count: src.count - 1 };
                setDecklist(newDL);

                movedCard = {
                    ...src,
                    instanceId: "inst_" + Math.random().toString(36).slice(2)
                };
            }
        }

        // Normal zones → zone
        else {
            const zoneMap = {
                hand: [hand, setHand],
                battlefield: [battlefield, setBattlefield],
                graveyard: [graveyard, setGraveyard],
                top: [top, setTop],
                bottom: [bottom, setBottom]
            };

            const [arr, setter] = zoneMap[fromZone] || [];
            if (arr) {
                const [newArr, item] = removeOne(arr, cardId);
                setter(newArr);
                movedCard = item;
            }
        }

        if (!movedCard) return;

        // Add to destination
        const zoneAdd = {
            hand: setHand,
            battlefield: setBattlefield,
            graveyard: setGraveyard,
            top: setTop,
            bottom: setBottom,
            decklist: setDecklist
        };

        if (toZone === "decklist") {
            setDecklist(d => {
                const idx = d.findIndex(c => c.id === movedCard.id);
                if (idx >= 0) {
                    const copy = d.slice();
                    copy[idx] = { ...copy[idx], count: copy[idx].count + 1 };
                    return copy;
                }
                return [...d, { ...movedCard, count: 1 }];
            });
        } else {
            zoneAdd[toZone](z => [...z, movedCard]);
        }

        // Auto-update sim
        runSimForState();
    }

    return (
        <DeckContext.Provider value={{
            decklist,
            hand,
            battlefield,
            graveyard,
            top,
            bottom,
            favorites,
            loading,
            probabilities,
            sortedDeckView,

            // functions exposed:
            loadResolvedDeck,
            runSimForState,
            runSimForCard,
            simulateActualDeckState,
            toggleFavorite,
            moveCard,
            setDecklist,
            setHand,
            setBattlefield,
            setGraveyard,
            setTop,
            setBottom
        }}>
            {children}
        </DeckContext.Provider>
    );
}
