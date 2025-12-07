"""
Monte Carlo simulation logic for MTG land probability calculations
Enhanced version supporting multiple card categories
"""
import json
import math
import os
import random
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

# Inside backend container, /app is backend root; default effects file is data/effects.json
EFFECTS_CATALOG_PATH = Path(os.environ.get("EFFECTS_CATALOG_PATH", "data/effects.json"))
_EFFECTS_CACHE: Optional[Dict[str, List[dict]]] = None


def _coerce_actions(value) -> List[dict]:
    """
    Normalise raw catalog values into a list of action dicts.
    Supports both:
      - {"Card Name": [ {...}, {...} ]}
      - {"Card Name": {"actions": [ {...}, {...} ]}}
    """
    actions: List[dict] = []
    if isinstance(value, list):
        actions = [a for a in value if isinstance(a, dict)]
    elif isinstance(value, dict):
        inner = value.get("actions")
        if isinstance(inner, list):
            actions = [a for a in inner if isinstance(a, dict)]
    return actions


@dataclass
class EffectModifiers:
    extra_draws: float = 0.0
    self_mill: int = 0
    tutor_any: bool = False
    tutor_categories: Set[str] = field(default_factory=set)
    shuffle: bool = False


def _load_effects_catalog() -> Dict[str, List[dict]]:
    global _EFFECTS_CACHE
    if _EFFECTS_CACHE is None:
        try:
            raw = json.loads(EFFECTS_CATALOG_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            raw = {}
        _EFFECTS_CACHE = {k.lower(): _coerce_actions(v) for k, v in raw.items()}
    return _EFFECTS_CACHE


def _estimate_scry_draws(count: int, strategy: Optional[str], category: Optional[str], target_categories: Optional[Set[str]]) -> float:
    if count <= 0:
        return 0.0
    strategy = (strategy or "default").lower()
    cat = (category or "").lower()
    targets = {t.lower() for t in (target_categories or set()) if t}
    if strategy == "keep_lands":
        relevant = cat == "land" or "land" in targets
        return float(count if relevant else min(count * 0.5, count))
    if strategy == "keep_nonlands":
        relevant = cat != "land"
        return float(count if relevant else min(count * 0.5, count))
    return float(min(count, 2))


def _pick_choice_index(strategy: Optional[str], options: List[List[dict]]) -> int:
    if not options:
        return -1
    strategy = (strategy or "").lower()
    if strategy.startswith("prefer_draw"):
        for idx, steps in enumerate(options):
            if any(step.get("action") == "draw" for step in steps):
                return idx
    if strategy.startswith("prefer_mill"):
        for idx, steps in enumerate(options):
            if any(step.get("action") == "mill" for step in steps):
                return idx
    return 0


def _apply_effect_actions(actions: List[dict], modifiers: EffectModifiers, category: Optional[str], target_categories: Optional[Set[str]]) -> None:
    for action in actions or []:
        if not isinstance(action, dict):
            continue
        kind = (action.get("action") or "").lower()
        if kind == "draw":
            modifiers.extra_draws += max(0, int(action.get("count", 1)))
        elif kind == "mill":
            modifiers.self_mill += max(0, int(action.get("count", 1)))
        elif kind == "shuffle":
            modifiers.shuffle = True
        elif kind == "scry":
            count = max(0, int(action.get("count", 1)))
            strategy = action.get("strategy")
            modifiers.extra_draws += _estimate_scry_draws(count, strategy, category, target_categories)
        elif kind == "tutor":
            target = (action.get("target") or "any").lower()
            if target in ("any", "library"):
                modifiers.tutor_any = True
            else:
                modifiers.tutor_categories.add(target)
            if action.get("shuffle"):
                modifiers.shuffle = True
        elif kind == "topdeck_from_hand":
            count = max(0, int(action.get("count", 1)))
            modifiers.extra_draws = max(0.0, modifiers.extra_draws - min(count, modifiers.extra_draws))
        elif kind == "sequence":
            _apply_effect_actions(action.get("steps", []), modifiers, category, target_categories)
        elif kind == "choice":
            options = action.get("options", [])
            idx = _pick_choice_index(action.get("strategy"), options)
            if 0 <= idx < len(options):
                _apply_effect_actions(options[idx], modifiers, category, target_categories)


def aggregate_effect_modifiers(card_names: Optional[List[str]], category: Optional[str] = None, target_categories: Optional[List[str]] = None) -> EffectModifiers:
    modifiers = EffectModifiers()
    if not card_names:
        return modifiers
    catalog = _load_effects_catalog()
    cat = (category or "").lower()
    targets = {t.lower() for t in (target_categories or []) if t}
    seen: Set[str] = set()
    for name in card_names:
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        actions = catalog.get(key)
        if not actions:
            continue
        _apply_effect_actions(actions, modifiers, cat, targets)
    return modifiers

class GameState:
    """Track deck composition with multiple card categories (lands, creatures, spells, etc.)."""
    
    def __init__(self, card_counts: Dict[str, int]):
        """
        Initialize game state with card category support.
        
        Args:
            card_counts: Dictionary mapping category → count (e.g. {"land": 24, "creature": 20, "spell": 16})
        """
        self.card_counts = card_counts
        self.total_cards = sum(card_counts.values())
    
    def probability(self, category: str) -> float:
        """Return probability of drawing a card of the given category."""
        if self.total_cards == 0 or category not in self.card_counts:
            return 0.0
        return self.card_counts[category] / self.total_cards
    
    def __str__(self) -> str:
        breakdown = ", ".join(f"{k}: {v}" for k, v in self.card_counts.items())
        return f"GameState({breakdown}, total={self.total_cards})"


def _effective_probability_with_oracle(game_state: GameState, category: str, oracle_texts: Optional[List[str]]) -> float:
    """
    Compute an effective probability after applying simple oracle-text-driven effects.
    Currently recognizes simple tutor effects like 'Search your library for an <type> card'.
    """
    base_probability = game_state.probability(category)
    if not oracle_texts:
        return base_probability

    # Simple pattern match for tutor-by-type effects
    normalized_texts = " ".join(oracle_texts).lower()
    # Map categories to searchable keywords expected in oracle text
    category_to_keyword = {
        "artifact": "search your library for an artifact card",
        "creature": "search your library for a creature card",
        "land": "search your library for a land card",
        "instant": "search your library for an instant card",
        "sorcery": "search your library for a sorcery card",
        "enchantment": "search your library for an enchantment card",
        "planeswalker": "search your library for a planeswalker card",
    }
    key = category_to_keyword.get(category.lower())
    if key and key in normalized_texts:
        # Treat tutor effect as guaranteeing access to the category
        return 1.0

    # Parse other common effects that influence draw odds
    extra_draws, self_mill = _parse_draw_and_mill_effects(normalized_texts)
    if extra_draws <= 0 and self_mill <= 0:
        return base_probability

    # Hypergeometric approximation for at-least-one success in k draws without replacement
    total_cards = game_state.total_cards
    successes = game_state.card_counts.get(category, 0)

    # Apply milling to our own library as expected values (approximation)
    mill = min(max(self_mill, 0), max(total_cards - 1, 0))
    remaining_total = max(total_cards - mill, 1)
    # Expected remaining successes after random mill
    expected_successes = successes * (remaining_total / total_cards) if total_cards > 0 else 0.0

    # Total number of draws considered: base one draw plus extra draws
    k_draws = 1 + max(extra_draws, 0)
    k_draws = min(k_draws, remaining_total)

    if expected_successes <= 0 or k_draws <= 0:
        return 0.0

    # Use continuous expected successes in comb; clamp to valid ints by rounding
    K = int(round(expected_successes))
    N = int(remaining_total)
    k = int(k_draws)
    K = max(0, min(K, N))
    k = max(0, min(k, N))
    if K == 0 or k == 0:
        return 0.0
    if K >= N or k >= N:
        return 1.0

    # P(at least 1) = 1 - C(N-K, k) / C(N, k)
    try:
        no_success = math.comb(N - K, k) / math.comb(N, k)
        return 1.0 - no_success
    except Exception:
        # Fallback to independence approximation if comb overflows unexpectedly
        p = expected_successes / N
        return 1.0 - (1.0 - p) ** k


def _parse_draw_and_mill_effects(text: str) -> (int, int):
    """
    Very simple heuristics to extract extra draws and self-mill counts from oracle text.
    Assumptions:
      - 'each player draws a card' => +1 extra draw for us
      - 'target player draws a card' => +1 (assume we target ourselves)
      - 'draw X cards' => +X extra draws (X may be numerals or words: one, two, three, etc.)
      - 'mills X cards' or 'mill X cards' => +X self mill (assume applies to us if unspecified)
    """
    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
        "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
        "nineteen": 19, "twenty": 20
    }

    extra_draws = 0
    self_mill = 0

    # Each player draws a card => count as +1 for us
    if "each player draws a card" in text:
        extra_draws += 1
    # Target player draws a card => assume we target ourselves for probability calc
    if "target player draws a card" in text:
        extra_draws += 1

    # Generic "draw/draws <X> cards?" including "draw a card" / "draws two cards"
    for m in re.finditer(r"draws? (a|an|\d+|\w+) cards?", text):
        token = m.group(1)
        if token in ("a", "an"):
            extra_draws += 1
        elif token.isdigit():
            extra_draws += int(token)
        else:
            extra_draws += word_to_num.get(token, 0)

    # Mill patterns: "mill X cards" or "mills X cards"
    for m in re.finditer(r"mill[s]? (\d+|\w+) cards?", text):
        token = m.group(1)
        if token.isdigit():
            self_mill += int(token)
        else:
            self_mill += word_to_num.get(token, 0)

    return extra_draws, self_mill


def effective_probability_for_successes(total_cards: int,
                                        successes: int,
                                        oracle_texts: Optional[List[str]] = None,
                                        target_categories: Optional[List[str]] = None) -> float:
    """
    Generalized effective probability of drawing at least one success given effects.
    - successes: number of successful cards in deck (e.g., count of target names)
    - target_categories: categories of the target cards for tutor matching
    """
    if total_cards <= 0:
        return 0.0
    base_probability = successes / total_cards
    if not oracle_texts:
        return base_probability

    normalized_texts = " ".join(oracle_texts).lower()

    # Tutor handling: if any oracle text tutors for any of the target categories, guarantee success
    category_to_keyword = {
        "artifact": "search your library for an artifact card",
        "creature": "search your library for a creature card",
        "land": "search your library for a land card",
        "instant": "search your library for an instant card",
        "sorcery": "search your library for a sorcery card",
        "enchantment": "search your library for an enchantment card",
        "planeswalker": "search your library for a planeswalker card",
    }
    if target_categories:
        for cat in target_categories:
            key = category_to_keyword.get(cat.lower())
            if key and key in normalized_texts:
                return 1.0

    # Draw and mill handling via hypergeometric approximation
    extra_draws, self_mill = _parse_draw_and_mill_effects(normalized_texts)
    if extra_draws <= 0 and self_mill <= 0:
        return base_probability

    import math

    mill = min(max(self_mill, 0), max(total_cards - 1, 0))
    remaining_total = max(total_cards - mill, 1)
    expected_successes = successes * (remaining_total / total_cards)

    k_draws = 1 + max(extra_draws, 0)
    k_draws = min(k_draws, remaining_total)

    if expected_successes <= 0 or k_draws <= 0:
        return 0.0

    K = int(round(expected_successes))
    N = int(remaining_total)
    k = int(k_draws)
    K = max(0, min(K, N))
    k = max(0, min(k, N))
    if K == 0 or k == 0:
        return 0.0
    if K >= N or k >= N:
        return 1.0

    try:
        no_success = math.comb(N - K, k) / math.comb(N, k)
        return 1.0 - no_success
    except Exception:
        p = expected_successes / N
        return 1.0 - (1.0 - p) ** k


def monte_carlo_probability_for_successes(total_cards: int,
                                          successes: int,
                                          num_simulations: int = 10000,
                                          random_seed: Optional[int] = None,
                                          oracle_texts: Optional[List[str]] = None,
                                          target_categories: Optional[List[str]] = None,
                                          oracle_card_names: Optional[List[str]] = None) -> dict:
    start_time = time.time()
    if random_seed is not None:
        random.seed(random_seed)

    # Normalize inputs
    total_cards = max(int(total_cards), 0)
    successes = max(int(successes), 0)
    num_simulations = max(int(num_simulations), 0)

    if total_cards <= 0 or successes <= 0 or num_simulations <= 0:
        return {
            'probability': 0.0,
            'theoretical_probability': (successes / total_cards) if total_cards > 0 else 0.0,
            'absolute_error': 0.0,
            'error_percentage': 0.0,
            'simulations_run': num_simulations,
            'hits': 0,
            'execution_time_seconds': 0.0,
            'simulations_per_second': 0.0,
        }

    # Aggregate oracle effects
    extra_draws = 0
    self_mill = 0
    tutor_guarantee = False

    # 1) Prefer structured catalog actions when available for the named cards
    modifiers = aggregate_effect_modifiers(oracle_card_names, target_categories=target_categories)
    extra_draws += modifiers.extra_draws
    self_mill += modifiers.self_mill
    target_lower = {t.lower() for t in (target_categories or []) if t}
    if modifiers.tutor_any or (target_lower and modifiers.tutor_categories.intersection(target_lower)):
        tutor_guarantee = True

    # 2) Fallback to simple oracle-text heuristics only if no structured actions exist
    if (modifiers.extra_draws == 0 and modifiers.self_mill == 0
            and not modifiers.tutor_any and not modifiers.tutor_categories
            and oracle_texts):
        normalized_texts = " ".join(oracle_texts).lower()
        ed, sm = _parse_draw_and_mill_effects(normalized_texts)
        extra_draws += max(ed, 0)
        self_mill += max(sm, 0)
        category_to_keyword = {
            "artifact": "search your library for an artifact card",
            "creature": "search your library for a creature card",
            "land": "search your library for a land card",
            "instant": "search your library for an instant card",
            "sorcery": "search your library for a sorcery card",
            "enchantment": "search your library for an enchantment card",
            "planeswalker": "search your library for a planeswalker card",
        }
        if target_categories:
            for cat in target_categories:
                key = category_to_keyword.get(str(cat).lower())
                if key and key in normalized_texts:
                    tutor_guarantee = True
                    break

    if tutor_guarantee:
        simulated_probability = 1.0
        theoretical_probability = successes / total_cards if total_cards > 0 else 0.0
        sim_time = time.time() - start_time
        return {
            'probability': simulated_probability,
            'theoretical_probability': theoretical_probability,
            'absolute_error': abs(simulated_probability - theoretical_probability),
            'error_percentage': ((abs(simulated_probability - theoretical_probability) / theoretical_probability) * 100) if theoretical_probability > 0 else 0.0,
            'simulations_run': num_simulations,
            'hits': num_simulations,
            'execution_time_seconds': sim_time,
            'simulations_per_second': (num_simulations / sim_time) if sim_time > 0 else float('inf'),
        }

    # Cap to feasible ranges
    self_mill = min(int(round(self_mill)), max(total_cards - 1, 0))
    draws = min(1 + max(int(round(extra_draws)), 0), total_cards)

    hits = 0
    for _ in range(num_simulations):
        remaining_total = total_cards
        remaining_success = successes

        # Mill cards uniformly without replacement
        mill = min(self_mill, remaining_total)
        for _mm in range(mill):
            if remaining_total <= 0 or remaining_success <= 0:
                break
            if random.random() < (remaining_success / remaining_total):
                remaining_success -= 1
            remaining_total -= 1

        trial_hit = False
        if remaining_total > 0 and remaining_success > 0:
            d = min(draws, remaining_total)
            for _d in range(d):
                if remaining_total <= 0:
                    break
                if remaining_success > 0 and random.random() < (remaining_success / remaining_total):
                    trial_hit = True
                    remaining_success -= 1
                remaining_total -= 1
        if trial_hit:
            hits += 1

    simulated_probability = hits / num_simulations if num_simulations > 0 else 0.0
    theoretical_probability = successes / total_cards if total_cards > 0 else 0.0
    error = abs(simulated_probability - theoretical_probability)
    error_percentage = (error / theoretical_probability * 100) if theoretical_probability > 0 else 0
    sim_time = time.time() - start_time
    sims_per_sec = num_simulations / sim_time if sim_time > 0 else 0

    return {
        'probability': simulated_probability,
        'theoretical_probability': theoretical_probability,
        'absolute_error': error,
        'error_percentage': error_percentage,
        'simulations_run': num_simulations,
        'hits': hits,
        'execution_time_seconds': sim_time,
        'simulations_per_second': sims_per_sec,
    }


def monte_carlo_probability(game_state: GameState,
                            category: str,
                            num_simulations: int = 10000,
                            random_seed: Optional[int] = None,
                            oracle_texts: Optional[List[str]] = None,
                            oracle_card_names: Optional[List[str]] = None) -> dict:
    """
    Monte Carlo simulation to predict probability of drawing a given category with support
    for multiple oracle effects (extra draws, milling, tutors).
    """
    start_time = time.time()

    if random_seed is not None:
        random.seed(random_seed)

    total_cards = game_state.total_cards
    successes = int(game_state.card_counts.get(category, 0))

    if total_cards <= 0 or successes <= 0 or num_simulations <= 0:
        return {
            'probability': 0.0,
            'theoretical_probability': game_state.probability(category),
            'absolute_error': 0.0,
            'error_percentage': 0.0,
            'simulations_run': max(int(num_simulations), 0),
            'hits': 0,
            'execution_time_seconds': 0.0,
            'simulations_per_second': 0.0,
            'game_state': str(game_state),
            'category': category
        }

    # Effects
    extra_draws = 0
    self_mill = 0
    tutor_guarantee = False

    # 1) Prefer structured catalog actions when oracle_card_names are provided
    modifiers = aggregate_effect_modifiers(oracle_card_names, category=category)
    extra_draws += modifiers.extra_draws
    self_mill += modifiers.self_mill
    if modifiers.tutor_any or (category and category.lower() in modifiers.tutor_categories):
        tutor_guarantee = True

    # 2) Fallback to simple oracle-text heuristics only if no structured actions exist
    if (modifiers.extra_draws == 0 and modifiers.self_mill == 0
            and not modifiers.tutor_any and not modifiers.tutor_categories
            and oracle_texts):
        normalized_texts = " ".join(oracle_texts).lower()
        ed, sm = _parse_draw_and_mill_effects(normalized_texts)
        extra_draws += max(ed, 0)
        self_mill += max(sm, 0)
        category_to_keyword = {
            "artifact": "search your library for an artifact card",
            "creature": "search your library for a creature card",
            "land": "search your library for a land card",
            "instant": "search your library for an instant card",
            "sorcery": "search your library for a sorcery card",
            "enchantment": "search your library for an enchantment card",
            "planeswalker": "search your library for a planeswalker card",
        }
        key = category_to_keyword.get(str(category).lower())
        if key and key in normalized_texts:
            tutor_guarantee = True

    if tutor_guarantee:
        simulated_probability = 1.0
        theoretical_probability = game_state.probability(category)
        sim_time = time.time() - start_time
        return {
            'probability': simulated_probability,
            'theoretical_probability': theoretical_probability,
            'absolute_error': abs(simulated_probability - theoretical_probability),
            'error_percentage': ((abs(simulated_probability - theoretical_probability) / theoretical_probability) * 100) if theoretical_probability > 0 else 0.0,
            'simulations_run': num_simulations,
            'hits': num_simulations,
            'execution_time_seconds': sim_time,
            'simulations_per_second': (num_simulations / sim_time) if sim_time > 0 else float('inf'),
            'game_state': str(game_state),
            'category': category
        }

    # Cap ranges
    self_mill = min(int(round(self_mill)), max(total_cards - 1, 0))
    draws = min(1 + max(int(round(extra_draws)), 0), total_cards)

    hits = 0
    for _ in range(num_simulations):
        remaining_total = total_cards
        remaining_success = successes

        # Mill
        mill = min(self_mill, remaining_total)
        for _mm in range(mill):
            if remaining_total <= 0 or remaining_success <= 0:
                break
            if random.random() < (remaining_success / remaining_total):
                remaining_success -= 1
            remaining_total -= 1

        trial_hit = False
        if remaining_total > 0 and remaining_success > 0:
            d = min(draws, remaining_total)
            for _d in range(d):
                if remaining_total <= 0:
                    break
                if remaining_success > 0 and random.random() < (remaining_success / remaining_total):
                    trial_hit = True
                    remaining_success -= 1
                remaining_total -= 1
        if trial_hit:
            hits += 1

    simulated_probability = hits / num_simulations if num_simulations > 0 else 0.0
    theoretical_probability = game_state.probability(category)
    error = abs(simulated_probability - theoretical_probability)
    error_percentage = (error / theoretical_probability * 100) if theoretical_probability > 0 else 0

    sim_time = time.time() - start_time
    simulations_per_second = num_simulations / sim_time if sim_time > 0 else 0

    return {
        'probability': simulated_probability,
        'theoretical_probability': theoretical_probability,
        'absolute_error': error,
        'error_percentage': error_percentage,
        'simulations_run': num_simulations,
        'hits': hits,
        'execution_time_seconds': sim_time,
        'simulations_per_second': simulations_per_second,
        'game_state': str(game_state),
        'category': category
    }
def monte_carlo_full_state(deck_counts: Dict[str, int],
                           top_zone: List[str],
                           bottom_zone: List[str],
                           num_simulations: int = 20000,
                           random_seed: Optional[int] = None) -> dict:
    """
    Full-state Monte Carlo simulation that returns per-card probabilities:
    - drawing each card on the current draw (p_now)
    - drawing each card on the next draw (p_next)
    """
    start_time = time.time()

    if random_seed is not None:
        random.seed(random_seed)

    # Normalize deck_counts: only keep positive counts and cast to int
    counts: Dict[str, int] = {}
    for name, cnt in deck_counts.items():
        c = int(cnt)
        if c > 0:
            counts[str(name)] = c

    if not counts or num_simulations <= 0:
        return {
            "total_cards": 0,
            "num_simulations": max(int(num_simulations), 0),
            "execution_time_seconds": 0.0,
            "results": {},
        }

    # Count how many card copies are in the known TOP and BOTTOM zones
    top_counts: Dict[str, int] = {}
    for n in top_zone:
        key = str(n)
        top_counts[key] = top_counts.get(key, 0) + 1

    bottom_counts: Dict[str, int] = {}
    for n in bottom_zone:
        key = str(n)
        bottom_counts[key] = bottom_counts.get(key, 0) + 1

    unknown_counts: Dict[str, int] = {}
    for name, total in counts.items():
        t = top_counts.get(name, 0)
        b = bottom_counts.get(name, 0)
        remaining = total - t - b
        if remaining < 0:
            raise ValueError(
                f"Inconsistent counts for '{name}': total={total}, "
                f"top_zone={t}, bottom_zone={b}"
            )
        if remaining > 0:
            unknown_counts[name] = remaining

    # Build the base unknown card pool
    unknown_pool_base: List[str] = []
    for name, cnt in unknown_counts.items():
        unknown_pool_base.extend([name] * cnt)

    total_cards = len(top_zone) + len(unknown_pool_base) + len(bottom_zone)

    names = list(counts.keys())
    hits_now = {name: 0 for name in names}
    hits_next = {name: 0 for name in names}

    for _ in range(num_simulations):
        # Shuffle a copy of the unknown pool
        unknown_pool = unknown_pool_base.copy()
        if len(unknown_pool) > 1:
            random.shuffle(unknown_pool)

        deck_seq: List[str] = list(top_zone) + unknown_pool + list(reversed(bottom_zone))

        if not deck_seq:
            continue

        # Current draw
        first = deck_seq[0]
        if first in hits_now:
            hits_now[first] += 1

        # Next draw
        if len(deck_seq) > 1:
            second = deck_seq[1]
            if second in hits_next:
                hits_next[second] += 1

    elapsed = time.time() - start_time

    results: Dict[str, dict] = {}
    sims = float(num_simulations)

    # Precompute helpers for deterministic overrides
    top_first_name: Optional[str] = top_zone[0] if top_zone else None

    for name in names:
        p_now = hits_now[name] / sims if sims > 0 else 0.0
        p_next = hits_next[name] / sims if sims > 0 else 0.0

        # Deterministic constraints for the current draw:
        # - If a card name is exactly the first card in the known TOP zone, it will be drawn now.
        # - If all remaining copies of a card are known to be in the BOTTOM zone, it cannot be drawn now.
        if top_first_name is not None and name == str(top_first_name):
            p_now = 1.0
        else:
            b_total = bottom_counts.get(name, 0)
            t_total = top_counts.get(name, 0)
            if b_total > 0 and t_total == 0 and b_total >= counts.get(name, 0):
                p_now = 0.0

        results[name] = {
            "copies_total": counts[name],
            "p_now": p_now,
            "p_next": p_next,
        }

    return {
        "total_cards": total_cards,
        "num_simulations": num_simulations,
        "execution_time_seconds": elapsed,
        "results": results,
    }
