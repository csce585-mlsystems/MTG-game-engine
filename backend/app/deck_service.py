from typing import List, Dict, Tuple

from .models import DeckNameCount, ResolveDeckResponse, ResolvedCard, CardEffectHint, CardBase
from .repository import get_cards_by_names_map, get_cards_by_names_map_relaxed, DB_PATH
from .effects import extract_effect_hints, ensure_effects_for_cards

# Optional: import Scryfall search inserter for fallback resolution
try:
    from .scryfall_import import search_and_insert 
except Exception:  
    search_and_insert = None


def pick_category(type_line: str) -> str:
    tl = (type_line or "").lower()
    # Priority order
    if "land" in tl:
        return "land"
    if "creature" in tl:
        return "creature"
    if "artifact" in tl:
        return "artifact"
    if "instant" in tl:
        return "instant"
    if "sorcery" in tl:
        return "sorcery"
    if "enchantment" in tl:
        return "enchantment"
    if "planeswalker" in tl:
        return "planeswalker"
    return "other"


def derive_counts(resolved: List[ResolvedCard]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for rc in resolved:
        category = pick_category(rc.card.type_line or "")
        counts[category] = counts.get(category, 0) + rc.count
    return counts


def resolve_deck(deck: List[DeckNameCount], auto_fetch: bool = True) -> ResolveDeckResponse:
    names = [d.name for d in deck]
    name_to_card = get_cards_by_names_map(names)
    # Best-effort: enrich effects catalog for any of these cards using the LLM
    try:
        ensure_effects_for_cards(list(name_to_card.values()))
    except Exception:
        pass

    resolved: List[ResolvedCard] = []
    unresolved: List[str] = []

    for entry in deck:
        key = entry.name.lower()
        card = name_to_card.get(key)
        if not card:
            unresolved.append(entry.name)
            continue
        effects: List[CardEffectHint] = extract_effect_hints(card.oracle_text, card.name)
        resolved.append(ResolvedCard(card=card, count=entry.count, effects=effects))

    # If we failed to resolve some names, try to fetch them via Scryfall and re-resolve once
    if auto_fetch and unresolved and search_and_insert is not None:
        # Batch unresolved names into fewer Scryfall queries to reduce latency
        def quote(n: str) -> str:
            safe = n.replace('"', '\\"')
            return f'name:"{safe}"'
        chunks: List[List[str]] = []
        chunk: List[str] = []
        # Simple chunking to keep URLs reasonable (Scryfall q length limits)
        for name in unresolved:
            chunk.append(quote(name))
            if len(chunk) >= 8:  # up to 8 names per chunk
                chunks.append(chunk)
                chunk = []
        if chunk:
            chunks.append(chunk)

        for group in chunks:
            q = " OR ".join(group)
            try:
                search_and_insert(DB_PATH, q, max_pages=2)
            except Exception:
                # Best-effort; continue with others
                pass
        # Recompute mapping after attempted inserts (relaxed matching to account for punctuation)
        name_to_card = get_cards_by_names_map_relaxed(names)
        resolved_after: List[ResolvedCard] = []
        unresolved_after: List[str] = []
        for entry in deck:
            key = entry.name.lower()
            card = name_to_card.get(key)
            if not card:
                unresolved_after.append(entry.name)
                continue
            effects: List[CardEffectHint] = extract_effect_hints(card.oracle_text, card.name)
            resolved_after.append(ResolvedCard(card=card, count=entry.count, effects=effects))
        derived = derive_counts(resolved_after)
        return ResolveDeckResponse(resolved=resolved_after, unresolved=unresolved_after, derived_counts=derived)

    derived = derive_counts(resolved)
    return ResolveDeckResponse(resolved=resolved, unresolved=unresolved, derived_counts=derived)


