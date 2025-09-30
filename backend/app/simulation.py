"""
Monte Carlo simulation logic for MTG land probability calculations
"""
import random
import time
from typing import Optional


class GameState:
    """Minimal game state tracking total cards and lands in deck."""
    
    def __init__(self, total_cards: int = 60, lands_in_deck: int = 24):
        """
        Initialize game state.
        
        Args:
            total_cards: Total cards currently in deck
            lands_in_deck: Number of lands currently in deck
        """
        self.total_cards = total_cards
        self.lands_in_deck = lands_in_deck
    
    def land_probability(self) -> float:
        """Return probability of drawing a land from current deck."""
        if self.total_cards == 0:
            return 0.0
        return self.lands_in_deck / self.total_cards
    
    def __str__(self) -> str:
        return f"GameState({self.lands_in_deck} lands / {self.total_cards} total cards)"


def monte_carlo_land_probability(game_state: GameState, 
                                num_simulations: int = 10000,
                                random_seed: Optional[int] = None) -> dict:
    """
    Monte Carlo simulation to predict probability of drawing a land.
    
    Args:
        game_state: Current game state to simulate from
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
            'land_probability': 0.0,
            'simulations_run': num_simulations,
            'execution_time_seconds': time.time() - start_time,
            'game_state': str(game_state)
        }
    
    land_draws = 0
    base_probability = game_state.land_probability()
    
    # Run simulations
    for _ in range(num_simulations):
        # Simple draw: is it a land?
        if random.random() < base_probability:
            land_draws += 1
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Calculate detailed statistics
    simulated_probability = land_draws / num_simulations
    theoretical_probability = base_probability
    error = abs(simulated_probability - theoretical_probability)
    error_percentage = (error / theoretical_probability * 100) if theoretical_probability > 0 else 0
    
    # Performance metrics
    simulations_per_second = num_simulations / execution_time if execution_time > 0 else 0
    
    return {
        'land_probability': simulated_probability,
        'theoretical_probability': theoretical_probability,
        'absolute_error': error,
        'error_percentage': error_percentage,
        'simulations_run': num_simulations,
        'land_draws': land_draws,
        'execution_time_seconds': execution_time,
        'simulations_per_second': simulations_per_second,
        'game_state': str(game_state)
    }
