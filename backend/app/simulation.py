"""
Monte Carlo simulation logic for MTG land probability calculations
Enhanced version supporting multiple card categories
"""
import random
import time
import re
import math
from typing import Optional, Dict, List


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

    # Generic "draw <X> cards?" including "draw a card"
    for m in re.finditer(r"draw (a|an|\d+|\w+) cards?", text):
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
                                          target_categories: Optional[List[str]] = None) -> dict:
    start_time = time.time()
    if random_seed is not None:
        random.seed(random_seed)

    eff_p = effective_probability_for_successes(
        total_cards=total_cards,
        successes=successes,
        oracle_texts=oracle_texts,
        target_categories=target_categories
    )

    hits = 0
    for _ in range(num_simulations):
        if random.random() < eff_p:
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
                            oracle_texts: Optional[List[str]] = None) -> dict:
    """
    Monte Carlo simulation to predict probability of drawing a given category.
    
    Args:
        game_state: Current game state to simulate from
        category: Card category to simulate (e.g. "land", "creature", "spell")
        num_simulations: Number of Monte Carlo trials to run
        random_seed: Optional seed for reproducible results
        
    Returns:
        Dictionary containing simulation results and detailed statistics
    """
    start_time = time.time()
    
    if random_seed is not None:
        random.seed(random_seed)
    
    if game_state.total_cards == 0:
        return {
            'probability': 0.0,
            'simulations_run': num_simulations,
            'execution_time_seconds': time.time() - start_time,
            'game_state': str(game_state),
            'category': category
        }
    
    hits = 0
    effective_probability = _effective_probability_with_oracle(game_state, category, oracle_texts)
    
    # Run simulations
    for _ in range(num_simulations):
        if random.random() < effective_probability:
            hits += 1
    
    # Calculate detailed statistics
    simulated_probability = hits / num_simulations
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
