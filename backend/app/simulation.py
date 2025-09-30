"""
Monte Carlo simulation logic for MTG land probability calculations
Enhanced version supporting multiple card categories
"""
import random
import time
from typing import Optional, Dict


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


def monte_carlo_probability(game_state: GameState, 
                           category: str,
                           num_simulations: int = 10000,
                           random_seed: Optional[int] = None) -> dict:
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
    base_probability = game_state.probability(category)
    
    # Run simulations
    for _ in range(num_simulations):
        if random.random() < base_probability:
            hits += 1
    
    # Calculate detailed statistics
    simulated_probability = hits / num_simulations
    theoretical_probability = base_probability
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


# Remove the legacy wrapper function - we'll use monte_carlo_probability directly
