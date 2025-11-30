import re
from typing import List, Optional

from .models import CardEffectHint


def extract_effect_hints(oracle_text: Optional[str]) -> List[CardEffectHint]:
    if not oracle_text:
        return []
    text = oracle_text.lower()
    hints: List[CardEffectHint] = []

    # Tutor by type
    type_keywords = [
        "artifact", "creature", "land", "instant", "sorcery", "enchantment", "planeswalker"
    ]
    for t in type_keywords:
        if f"search your library for an {t} card" in text or f"search your library for a {t} card" in text:
            hints.append(CardEffectHint(type="tutor", target=t))

    # Draw effects
    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
        "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
        "nineteen": 19, "twenty": 20
    }

    draws = 0
    if "each player draws a card" in text:
        draws += 1
    if "target player draws a card" in text:
        draws += 1
    for m in re.finditer(r"draw (a|an|\d+|\w+) cards?", text):
        token = m.group(1)
        if token in ("a", "an"):
            draws += 1
        elif token.isdigit():
            draws += int(token)
        else:
            draws += word_to_num.get(token, 0)
    if draws > 0:
        hints.append(CardEffectHint(type="draw", count=draws))

    # Mill effects
    mills = 0
    for m in re.finditer(r"mill[s]? (\d+|\w+) cards?", text):
        token = m.group(1)
        if token.isdigit():
            mills += int(token)
        else:
            mills += word_to_num.get(token, 0)
    if mills > 0:
        hints.append(CardEffectHint(type="mill", count=mills))

    return hints


