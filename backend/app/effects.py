import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from openai import OpenAI

from .models import CardEffectHint, CardBase


logger = logging.getLogger(__name__)

# Inside the backend container, /app is the backend root, so effects live under data/effects.json
_EFFECTS_PATH = Path(os.environ.get("EFFECTS_CATALOG_PATH", "data/effects.json"))
_LLM_DEBUG_DIR = Path(os.environ.get("LLM_DEBUG_DIR", "data/llm_debug"))
_EFFECTS_CACHE: Optional[Dict[str, List[dict]]] = None
_OPENAI_CLIENT: Optional[OpenAI] = None


def _load_effects_catalog() -> Dict[str, List[dict]]:
    """Load the LLM-generated effects catalog mapping card name -> actions list."""
    global _EFFECTS_CACHE
    if _EFFECTS_CACHE is None:
        try:
            raw = json.loads(_EFFECTS_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            raw = {}
        _EFFECTS_CACHE = {k.lower(): v for k, v in raw.items()}
        logger.info("Loaded effects catalog with %d entries from %s", len(_EFFECTS_CACHE), _EFFECTS_PATH)
    return _EFFECTS_CACHE


def _get_openai_client() -> Optional[OpenAI]:
    global _OPENAI_CLIENT
    if _OPENAI_CLIENT is not None:
        return _OPENAI_CLIENT
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.info("OPENAI_API_KEY not set; skipping LLM effects enrichment")
        return None
    try:
        _OPENAI_CLIENT = OpenAI(api_key=api_key)
        logger.info("Initialised OpenAI client for effects enrichment")
        return _OPENAI_CLIENT
    except Exception:
        logger.exception("Failed to initialise OpenAI client for effects enrichment")
        return None


_PROMPT_TEMPLATE = """You are helping build a deterministic simulation for Magic: The Gathering.
For the card below, you must emit a strict JSON object with a single key "actions" whose value is an array
describing the card's effects using only the allowed actions.

Example response format (structure only):
{
  "actions": [
    {"action": "draw", "count": 3},
    {"action": "topdeck_from_hand", "count": 2}
  ]
}

Allowed actions (all lowercase):
- draw:    {"action": "draw", "count": N}
- mill:    {"action": "mill", "count": N}
- shuffle: {"action": "shuffle"}
- scry:    {"action": "scry", "count": N, "strategy": "keep_lands|keep_nonlands|default"}
- tutor:   {"action": "tutor", "target": "any|land|artifact|...","shuffle": true/false}
- topdeck_from_hand: {"action": "topdeck_from_hand", "count": N}
- choice/modal effects:
    {"action": "choice", "options": [[{...}], [{...}]], "strategy": "prefer_draw|prefer_mill"}
- sequence helpers:
    {"action": "sequence", "steps": [{...}, {...}]}

If the card has no effects that touch the deck/hand/graveyard/library, return:
{"actions": []}

Card name: "{name}"
Oracle text:
{oracle_text}
"""


def _llm_actions_for_card(name: str, oracle_text: str) -> Optional[List[dict]]:
    client = _get_openai_client()
    if client is None or not oracle_text:
        return None
    logger.info("Requesting LLM effects for card '%s'", name)
    prompt = _PROMPT_TEMPLATE.format(name=name, oracle_text=oracle_text)
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You output ONLY JSON matching the requested schema."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
    except Exception:
        logger.exception("LLM request failed for card '%s'", name)
        return None

    # Log raw response snapshot to inspect structure.
    logger.info("LLM raw response for '%s': %s", name, repr(resp)[:800])

    # Extract JSON object from first choice.
    try:
        msg = resp.choices[0].message
    except Exception:
        logger.exception("Failed to extract message from LLM response for '%s'", name)
        return None

    content = getattr(msg, "content", None)
    logger.info("LLM content for '%s': %s", name, str(content)[:200])

    text_payload = ""
    if isinstance(content, str):
        text_payload = content
    elif isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(part.get("text") or "")
            else:
                parts.append(str(part))
        text_payload = "".join(parts)
    elif isinstance(content, dict):
        text_payload = content.get("text") or ""
    else:
        text_payload = str(content or "")

    raw = text_payload.strip()
    if raw.startswith("```"):
        chunks = raw.split("```")
        if len(chunks) >= 3:
            raw = chunks[1]
            if raw.strip().startswith("json"):
                raw = raw.strip()[4:].strip()

    # Persist last payload for inspection
    try:
        _LLM_DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "card"
        debug_path = _LLM_DEBUG_DIR / f"{slug}.json"
        debug_path.write_text(raw, encoding="utf-8")
        logger.info("Wrote LLM raw payload for '%s' to %s", name, debug_path)
    except Exception:
        logger.exception("Failed to write LLM debug payload for '%s'", name)

    if not raw:
        logger.warning("Empty LLM response for '%s'", name)
        return None

    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("LLM output for '%s' was not valid JSON object: %s", name, raw[:160])
        return None

    if not isinstance(obj, dict):
        logger.warning("LLM JSON root for '%s' is not an object: %s", name, str(obj)[:160])
        return None

    actions = obj.get("actions")
    if not isinstance(actions, list):
        logger.warning("LLM JSON for '%s' missing 'actions' array: %s", name, str(content)[:160])
        return None
    logger.info("Parsed %d actions for '%s' from LLM", len(actions), name)
    return actions


def ensure_effects_for_cards(cards: Sequence[CardBase]) -> None:
    """
    Best-effort: for any card whose name is missing from effects.json, call the LLM once to
    generate structured actions and persist them. Failures are swallowed.
    """
    try:
        raw = json.loads(_EFFECTS_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        raw = {}
    existing_lower = {k.lower() for k in raw.keys()}

    updated = False
    for card in cards:
        if not card or not getattr(card, "name", None) or not getattr(card, "oracle_text", None):
            continue
        name = str(card.name)
        key_lower = name.lower()
        if key_lower in existing_lower:
            continue
        logger.info("Enriching effects for '%s' via LLM", name)
        logger.info("Enriching effects for '%s' via LLM", name)
        actions = _llm_actions_for_card(name, str(card.oracle_text))
        # Distinguish between "no result" (None) and an empty list (valid but no deck effects)
        if actions is None:
            logger.warning("No actions returned for '%s'; skipping write", name)
            continue
        raw[name] = actions
        existing_lower.add(key_lower)
        updated = True

    if updated:
        # Ensure parent directory exists (especially in fresh containers)
        _EFFECTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _EFFECTS_PATH.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        logger.info("Updated effects catalog with %d total entries at %s", len(raw), _EFFECTS_PATH)
        # Invalidate in-process cache so future reads see new data
        global _EFFECTS_CACHE
        _EFFECTS_CACHE = None


def _hints_from_actions(actions: List[dict]) -> List[CardEffectHint]:
    """Summarise low-level actions (draw/mill/tutor) into CardEffectHint objects."""
    draw_total = 0
    mill_total = 0
    tutor_targets = set()

    for a in actions or []:
        if not isinstance(a, dict):
            continue
        kind = (a.get("action") or "").lower()
        if kind == "draw":
            draw_total += max(0, int(a.get("count", 1)))
        elif kind == "mill":
            mill_total += max(0, int(a.get("count", 1)))
        elif kind == "tutor":
            tgt = (a.get("target") or "any").lower()
            tutor_targets.add(tgt)
        elif kind == "sequence":
            nested = _hints_from_actions(a.get("steps", []))
            for h in nested:
                if h.type == "draw":
                    draw_total += h.count or 0
                elif h.type == "mill":
                    mill_total += h.count or 0
                elif h.type == "tutor" and h.target:
                    tutor_targets.add(h.target)
        elif kind == "choice":
            # For hints, merge all options conservatively
            for opt in a.get("options", []):
                nested = _hints_from_actions(opt)
                for h in nested:
                    if h.type == "draw":
                        draw_total += h.count or 0
                    elif h.type == "mill":
                        mill_total += h.count or 0
                    elif h.type == "tutor" and h.target:
                        tutor_targets.add(h.target)

    hints: List[CardEffectHint] = []
    if draw_total > 0:
        hints.append(CardEffectHint(type="draw", count=draw_total))
    if mill_total > 0:
        hints.append(CardEffectHint(type="mill", count=mill_total))
    for tgt in sorted(tutor_targets):
        hints.append(CardEffectHint(type="tutor", target=tgt))
    return hints


def extract_effect_hints(oracle_text: Optional[str], name: Optional[str] = None) -> List[CardEffectHint]:
    """
    Extract coarse effect hints for a card, preferring the LLM-generated catalog when available
    and falling back to simple regex heuristics on oracle_text.
    """
    # 1) Try catalog
    catalog = _load_effects_catalog()
    if name:
        actions = catalog.get(name.lower())
        if actions:
            return _hints_from_actions(actions)

    # 2) Fallback to regex on oracle text
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
    for m in re.finditer(r"draws? (a|an|\d+|\w+) cards?", text):
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


