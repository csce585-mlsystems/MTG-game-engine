import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { simulateByNames, simulateByCard, resolveDeck } from "./api";

/*
 DeckContext responsibilities:
 - hold master decklist (array of card objects from DB)
 - hold zones: decklist (right panel), hand, battlefield, graveyard
 - favorites toggling
 - functions: moveCard(zoneFrom, zoneTo, cardId), toggleFavorite(cardId), doubleClickSim(card)
 - runSimForState() to call backend /simulate/by-names
*/

const DeckContext = createContext(null);

export function useDeck() {
    return useContext(DeckContext);
}

function typeIncludes(type_line, term) {
    return !!(type_line || "").toLowerCase().includes(term.toLowerCase());
}

function bucketFor(card) {
    const t = (card.type_line || "").toLowerCase();
    if (typeIncludes(t, "land")) return "lands";
    if (typeIncludes(t, "creature")) return "creatures";
    if (typeIncludes(t, "planeswalker")) return "planeswalkers";
    if (typeIncludes(t, "artifact") && !typeIncludes(t, "creature")) return "artifacts";
    if (typeIncludes(t, "enchantment")) return "enchantments";
    if (typeIncludes(t, "battle")) return "battles";
    if (typeIncludes(t, "sorcery")) return "sorceries";
    if (typeIncludes(t, "instant")) return "instants";
    return "others";
}

function alphabetical(a, b) {
    return (a.name || "").localeCompare(b.name || "");
}

export function DeckProvider({ children }) {
    const [decklist, setDecklist] = useState([]); // full list from resolveDeck or initial load
    const [hand, setHand] = useState([]);
    const [battlefield, setBattlefield] = useState([]);
    const [graveyard, setGraveyard] = useState([]);
    const [favorites, setFavorites] = useState(new Set());
    const [probabilities, setProbabilities] = useState({}); // map card.name -> probability
    const [loading, setLoading] = useState(false);

    const sortedDeckView = useMemo(() => {

        // utilizing buckets to order remaining cards with favorites at the top
        const favs = decklist.filter(c => favorites.has(c.id)).sort(alphabetical);

        const nonFav = decklist.filter(c => !favorites.has(c.id));
        const lands = nonFav.filter(c => bucketFor(c) === "lands").sort(alphabetical);
        const creatures = nonFav.filter(c => bucketFor(c) === "creatures").sort(alphabetical);
        const planeswalkers = nonFav.filter(c => bucketFor(c) === "planeswalkers").sort(alphabetical);
        const artifacts = nonFav.filter(c => bucketFor(c) === "artifacts").sort(alphabetical);
        const enchantments = nonFav.filter(c => bucketFor(c) === "enchantments").sort(alphabetical);
        const battles = nonFav.filter(c => bucketFor(c) === "battles").sort(alphabetical);
        const sorceries = nonFav.filter(c => bucketFor(c) === "sorceries").sort(alphabetical);
        const instants = nonFav.filter(c => bucketFor(c) === "instants").sort(alphabetical);
        const others = nonFav.filter(c => bucketFor(c) === "others").sort(alphabetical);

        return [
            ...favs,
            ...lands,
            ...creatures,
            ...planeswalkers,
            ...artifacts,
            ...enchantments,
            ...battles,
            ...sorceries,
            ...instants,
            ...others
        ];
    }, [decklist, favorites]);

    // helper to build the deck payload expected by backend
    function deckPayloadFromList(list) {
        // backend ResolveDeck expects [{name, count}] , aggregate by name
        const map = new Map();
        for (const c of list) {
            const key = c.name;
            map.set(key, (map.get(key) || 0) + (c.count || 1));
        }
        const arr = [];
        for (const [name, count] of map.entries()) arr.push({ name, count });
        return arr;
    }

    // API interactions
    // load initial deck via resolveDeck (call backend)
    async function loadResolvedDeck(nameCountList) {
        setLoading(true);
        try {
            const res = await resolveDeck({ deck: nameCountList });
            // resolved.resolved is list of ResolvedCard { card, count, effects }
            const cards = res.resolved.map(rc => ({
                id: rc.card.id || rc.card.name,
                ...rc.card,
                count: rc.count || 1
            }));
            setDecklist(cards);
            // derive initial probabilities via simulate/by-names for 'land' maybe or overall
            await runSimForState(cards, null);
        } catch (e) {
            console.error("resolveDeck failed", e);
        } finally {
            setLoading(false);
        }
    }

    // run simulation for current deck (or provided deck)
    async function runSimForState(currentDeck = null, category = "land") {
        setLoading(true);
        try {
            const deckToUse = currentDeck || decklist;
            // convert deck to resolve format [{name,count}]
            const payloadDeck = deckPayloadFromList(deckToUse);
            // call simulate/by-names — returns SimulationResponse
            const resp = await simulateByNames({ deck: payloadDeck, category, num_simulations: 20000 });
            setProbabilities(prev => ({ ...prev, _categoryProb: resp.probability, lastResp: resp }));
            return resp;
        } catch (e) {
            console.error("runSimForState failed", e);
            throw e;
        } finally {
            setLoading(false);
        }
    }

    // run simulation for a specific card (on double-click) - calls /simulate/by-card
    async function runSimForCard(card) {
        setLoading(true);
        try {
            // Build deck payload
            const payloadDeck = deckPayloadFromList(decklist);
            // resp contains probability for target_names union, to display the before-after probability comparison
            const resp = await simulateByCard({ deck: payloadDeck, target_names: [card.name], num_simulations: 20000 });
            return resp;
        } catch (e) {
            console.error("runSimForCard failed", e);
            throw e;
        } finally {
            setLoading(false);
        }
    }

    function toggleFavorite(cardId) {
        setFavorites(prev => {
            const copy = new Set(prev);
            if (copy.has(cardId)) copy.delete(cardId);
            else copy.add(cardId);
            return copy;
        });
    }

    // moveCard: move a card object from its current zone into the target zone
    function moveCard({ cardId, fromZone, toZone }) {
        // helper for removal
        const popFrom = (arr, id) => {
            const idx = arr.findIndex(c => c.id === id);
            if (idx === -1) return [arr, null];
            const copy = arr.slice();
            const [item] = copy.splice(idx, 1);
            return [copy, item];
        };

        if (fromZone === toZone) return;

        let movedItem = null;
        if (fromZone === "decklist") {
            const [newDecklist, item] = popFrom(decklist, cardId);
            if (item) {
                setDecklist(newDecklist);
                movedItem = item;
            }
        } else if (fromZone === "hand") {
            const [newHand, item] = popFrom(hand, cardId);
            if (item) {
                setHand(newHand);
                movedItem = item;
            }
        } else if (fromZone === "battlefield") {
            const [nb, item] = popFrom(battlefield, cardId);
            if (item) {
                setBattlefield(nb);
                movedItem = item;
            }
        } else if (fromZone === "graveyard") {
            const [ng, item] = popFrom(graveyard, cardId);
            if (item) {
                setGraveyard(ng);
                movedItem = item;
            }
        }

        if (!movedItem) return;

        if (toZone === "decklist") setDecklist(d => [...d, movedItem]);
        else if (toZone === "hand") setHand(d => [...d, movedItem]);
        else if (toZone === "battlefield") setBattlefield(d => [...d, movedItem]);
        else if (toZone === "graveyard") setGraveyard(d => [...d, movedItem]);

        // After state change, run simulation, update probabilities for decklist, then call backend for updated stats
        runSimForState();
    }

    return (
        <DeckContext.Provider value={{
            decklist,
            hand,
            battlefield,
            graveyard,
            favorites,
            loading,
            probabilities,
            sortedDeckView,
            loadResolvedDeck,
            runSimForCard,
            runSimForState,
            toggleFavorite,
            moveCard,
            setDecklist, setHand, setBattlefield, setGraveyard
        }}>
            {children}
        </DeckContext.Provider>
    );
}