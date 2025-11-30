from typing import List, Dict, Tuple

from .models import DeckNameCount, ResolveDeckResponse, ResolvedCard, CardEffectHint, CardBase
from .repository import get_cards_by_names_map
from .effects import extract_effect_hints


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


def resolve_deck(deck: List[DeckNameCount]) -> ResolveDeckResponse:
    names = [d.name for d in deck]
    name_to_card = get_cards_by_names_map(names)

    resolved: List[ResolvedCard] = []
    unresolved: List[str] = []

    for entry in deck:
        key = entry.name.lower()
        card = name_to_card.get(key)
        if not card:
            unresolved.append(entry.name)
            continue
        effects: List[CardEffectHint] = extract_effect_hints(card.oracle_text)
        resolved.append(ResolvedCard(card=card, count=entry.count, effects=effects))

    derived = derive_counts(resolved)
    return ResolveDeckResponse(resolved=resolved, unresolved=unresolved, derived_counts=derived)


