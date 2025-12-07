import React, { createContext, useContext, useMemo, useState } from "react";
import { resolveDeck, simulateByNames, simulateByCard, simulateFullState } from "./api";

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
    const [applyZoneEffects, setApplyZoneEffects] = useState(false);
    const [zoneEffectIds, setZoneEffectIds] = useState(new Set());

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

    // Build full-state deck payload (remaining library: decklist + top + bottom)
    function fullStateDeckPayload() {
        const map = new Map();

        const add = (name, n = 1) => {
            if (!name || n <= 0) return;
            map.set(name, (map.get(name) || 0) + n);
        };

        for (const c of decklist) {
            const count = c.count ?? 0;
            if (count > 0) add(c.name, count);
        }
        const addZone = (arr) => {
            for (const c of arr) {
                add(c.name, 1);
            }
        };
        addZone(top);
        addZone(bottom);

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

    function zoneOracleNames() {
        if (!applyZoneEffects) return undefined;
        const names = new Set();
        const push = (arr) => {
            for (const c of arr) {
                if (c?.name && c?.instanceId && zoneEffectIds.has(c.instanceId)) {
                    names.add(c.name);
                }
            }
        };
        push(hand);
        push(battlefield);
        push(graveyard);
        push(top);
        push(bottom);
        return names.size ? Array.from(names) : undefined;
    }

    function toggleZoneEffect(instanceId) {
        if (!instanceId) return;
        setZoneEffectIds(prev => {
            const next = new Set(prev);
            if (next.has(instanceId)) next.delete(instanceId);
            else next.add(instanceId);
            return next;
        });
    }

    async function runSimForState(list = null, category = "land", oracleNames = undefined) {
        setLoading(true);
        try {
            const useFullState = top.length > 0 || bottom.length > 0;

            // If we have known top/bottom positions, use the full-state endpoint so
            // probabilities respect deterministic 100%/0% outcomes.
            if (useFullState) {
                const deck = fullStateDeckPayload();
                const res = await simulateFullState({
                    deck,
                    top_zone: top.map((c) => c.name),
                    bottom_zone: bottom.map((c) => c.name),
                    num_simulations: 20000,
                });

                const categoryLower = String(category || "").toLowerCase();
                const perCard = {};
                let probNow = 0;

                // Helper: derive category from type_line similar to backend pick_category
                const pickCategory = (typeLine) => {
                    const tl = (typeLine || "").toLowerCase();
                    if (tl.includes("land")) return "land";
                    if (tl.includes("creature")) return "creature";
                    if (tl.includes("artifact")) return "artifact";
                    if (tl.includes("instant")) return "instant";
                    if (tl.includes("sorcery")) return "sorcery";
                    if (tl.includes("enchantment")) return "enchantment";
                    if (tl.includes("planeswalker")) return "planeswalker";
                    return "other";
                };

                const allCards = [...decklist, ...top, ...bottom];

                for (const entry of res.results || []) {
                    const name = entry.name;
                    const key = name.toLowerCase();
                    const pNow = entry.p_now;
                    perCard[key] = pNow;

                    const meta = allCards.find((c) => c.name === name);
                    const cat = pickCategory(meta?.type_line);
                    if (cat === categoryLower) {
                        probNow += pNow;
                    }
                }

                const simulations = res.num_simulations || 0;
                const hits = Math.round(probNow * simulations);
                const synthetic = {
                    probability: probNow,
                    theoretical_probability: probNow,
                    absolute_error: 0,
                    error_percentage: 0,
                    simulations_run: simulations,
                    hits,
                    execution_time_seconds: res.execution_time_seconds || 0,
                    simulations_per_second:
                        simulations && res.execution_time_seconds
                            ? simulations / res.execution_time_seconds
                            : 0,
                    game_state: `FullState(total_cards=${res.total_cards})`,
                    category,
                };

                setProbabilities((prev) => ({
                    ...prev,
                    lastResp: synthetic,
                    per_card: perCard,
                }));

                return synthetic;
            }

            // Fallback: original aggregate-by-category simulation without zones
            const payload = deckPayload(list || decklist);
            const z = zoneOracleNames();
            let mergedOracle = oracleNames;
            if (z) {
                const s = new Set([...(oracleNames || []), ...z]);
                mergedOracle = Array.from(s);
            }
            const res = await simulateByNames({
                deck: payload,
                category,
                num_simulations: 20000,
                oracle_names: mergedOracle
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
            const useFullState = top.length > 0 || bottom.length > 0;

            if (useFullState) {
                const deck = fullStateDeckPayload();
                const res = await simulateFullState({
                    deck,
                    top_zone: top.map((c) => c.name),
                    bottom_zone: bottom.map((c) => c.name),
                    num_simulations: 20000,
                });

                const targetName = (card?.name || "").toLowerCase();
                const entry = (res.results || []).find(
                    (r) => r.name && r.name.toLowerCase() === targetName
                );
                const pNow = entry ? entry.p_now : 0;
                const simulations = res.num_simulations || 0;
                const hits = Math.round(pNow * simulations);

                const synthetic = {
                    probability: pNow,
                    theoretical_probability: pNow,
                    absolute_error: 0,
                    error_percentage: 0,
                    simulations_run: simulations,
                    hits,
                    execution_time_seconds: res.execution_time_seconds || 0,
                    simulations_per_second:
                        simulations && res.execution_time_seconds
                            ? simulations / res.execution_time_seconds
                            : 0,
                    game_state: `FullState(total_cards=${res.total_cards})`,
                    category: "specific_cards",
                };

                return synthetic;
            }

            const z = zoneOracleNames();
            let mergedOracle = oracleNames;
            if (z) {
                const s = new Set([...(oracleNames || []), ...z]);
                mergedOracle = Array.from(s);
            }
            const res = await simulateByCard({
                deck: deckPayload(decklist),
                target_names: [card.name],
                num_simulations: 20000,
                oracle_names: mergedOracle
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
        let nextDecklist = decklist;

        // Decklist → zone (decrement count)
        if (fromZone === "decklist") {
            const idx = decklist.findIndex(c => c.id === cardId);
            if (idx !== -1 && decklist[idx].count > 0) {
                const src = decklist[idx];
                const newDL = decklist.slice();
                newDL[idx] = { ...src, count: src.count - 1 };
                nextDecklist = newDL;

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
                // If we removed a selected-effect item, unselect it
                if (item?.instanceId) {
                    setZoneEffectIds(prev => {
                        if (!prev.has(item.instanceId)) return prev;
                        const next = new Set(prev);
                        next.delete(item.instanceId);
                        return next;
                    });
                }
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
            decklist: null
        };

        if (toZone === "decklist") {
            const idx = nextDecklist.findIndex(c => c.id === movedCard.id);
            if (idx >= 0) {
                const copy = nextDecklist.slice();
                copy[idx] = { ...copy[idx], count: (copy[idx].count || 0) + 1 };
                nextDecklist = copy;
            } else {
                nextDecklist = [...nextDecklist, { ...movedCard, count: 1 }];
            }
        } else {
            zoneAdd[toZone](z => [...z, movedCard]);
        }

        // Auto-update sim
        setDecklist(nextDecklist);
        runSimForState(nextDecklist);
    }

    // Clear an entire zone back into decklist (increments counts)
    function clearZone(zoneId) {
        const zoneMap = {
            hand: [hand, setHand],
            battlefield: [battlefield, setBattlefield],
            graveyard: [graveyard, setGraveyard],
            top: [top, setTop],
            bottom: [bottom, setBottom]
        };
        const entry = zoneMap[zoneId];
        if (!entry) return;
        const [arr, setter] = entry;
        if (!arr || arr.length === 0) return;

        // Build new decklist with counts incremented for each returned card
        const idToIndex = new Map(decklist.map((c, i) => [c.id, i]));
        const newDecklist = decklist.slice();
        for (const item of arr) {
            const idx = idToIndex.get(item.id);
            if (idx !== undefined) {
                const cur = newDecklist[idx];
                newDecklist[idx] = { ...cur, count: (cur.count || 0) + 1 };
            } else {
                newDecklist.push({ ...item, count: 1 });
                idToIndex.set(item.id, newDecklist.length - 1);
            }
        }

        setDecklist(newDecklist);
        setter([]);
        // Remove all selected flags for cards cleared from this zone
        setZoneEffectIds(prev => {
            if (!arr?.length) return prev;
            const next = new Set(prev);
            for (const it of arr) {
                if (it?.instanceId) next.delete(it.instanceId);
            }
            return next;
        });
        // Re-run sims with updated deck counts
        runSimForState(newDecklist);
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
            clearZone,
            zoneEffectIds,
            toggleZoneEffect,
            setDecklist,
            setHand,
            setBattlefield,
            setGraveyard,
            setTop,
            setBottom,
            applyZoneEffects,
            setApplyZoneEffects
        }}>
            {children}
        </DeckContext.Provider>
    );
}
