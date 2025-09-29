import random
import time
from typing import Optional, List
import matplotlib.pyplot as plt
import numpy as np

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

def analyze_iterations_vs_accuracy(game_state: GameState, 
                                  max_simulations: int = 1000000,
                                  num_data_points: int = 20) -> dict:
    """
    Analyze the relationship between number of iterations and accuracy.
    
    Args:
        game_state: Game state to analyze
        max_simulations: Maximum number of simulations to test
        num_data_points: Number of data points to collect
        
    Returns:
        Dictionary with analysis results for plotting
    """
    # Create logarithmic spacing for simulation counts
    simulation_counts = np.logspace(2, np.log10(max_simulations), num_data_points, dtype=int)
    
    results = {
        'simulation_counts': [],
        'error_percentages': [],
        'execution_times': [],
        'simulations_per_second': []
    }
    
    theoretical_prob = game_state.land_probability()
    
    print(f"Analyzing {game_state} with theoretical probability: {theoretical_prob:.6f}")
    print("Running analysis...")
    
    for i, sim_count in enumerate(simulation_counts):
        print(f"Progress: {i+1}/{len(simulation_counts)} - {sim_count:,} simulations", end='\r')
        
        # Run multiple trials to get average performance
        trials = 5 if sim_count <= 10000 else 3 if sim_count <= 100000 else 1
        
        trial_errors = []
        trial_times = []
        trial_speeds = []
        
        for _ in range(trials):
            result = monte_carlo_land_probability(game_state, num_simulations=sim_count)
            trial_errors.append(result['error_percentage'])
            trial_times.append(result['execution_time_seconds'])
            trial_speeds.append(result['simulations_per_second'])
        
        # Average the results
        results['simulation_counts'].append(sim_count)
        results['error_percentages'].append(np.mean(trial_errors))
        results['execution_times'].append(np.mean(trial_times))
        results['simulations_per_second'].append(np.mean(trial_speeds))
    
    print("\nAnalysis complete!")
    return results

def create_optimization_plots(analysis_results: dict, game_state: GameState):
    """Create comprehensive plots for iterations vs accuracy optimization."""
    
    sim_counts = analysis_results['simulation_counts']
    errors = analysis_results['error_percentages']
    times = analysis_results['execution_times']
    speeds = analysis_results['simulations_per_second']
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle(f'Monte Carlo Optimization Analysis\n{game_state}', fontsize=16, fontweight='bold')
    
    # Plot 1: Error vs Simulations (log-log)
    ax1.loglog(sim_counts, errors, 'bo-', linewidth=2, markersize=6)
    ax1.set_xlabel('Number of Simulations')
    ax1.set_ylabel('Error Percentage (%)')
    ax1.set_title('Accuracy vs Iterations')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0.001)  # Set minimum to avoid log(0)
    
    # Add theoretical 1/sqrt(n) convergence line
    theoretical_errors = errors[0] * np.sqrt(sim_counts[0] / np.array(sim_counts))
    ax1.loglog(sim_counts, theoretical_errors, 'r--', alpha=0.7, label='Theoretical 1/√n')
    ax1.legend()
    
    # Plot 2: Execution Time vs Simulations
    ax2.loglog(sim_counts, times, 'go-', linewidth=2, markersize=6)
    ax2.set_xlabel('Number of Simulations')
    ax2.set_ylabel('Execution Time (seconds)')
    ax2.set_title('Performance vs Iterations')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Efficiency (Simulations per Second)
    ax3.semilogx(sim_counts, np.array(speeds) / 1e6, 'mo-', linewidth=2, markersize=6)
    ax3.set_xlabel('Number of Simulations')
    ax3.set_ylabel('Simulations per Second (Millions)')
    ax3.set_title('Computational Efficiency')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Accuracy per Time (Optimization metric)
    accuracy_per_time = 1 / (np.array(errors) * np.array(times))  # Higher is better
    ax4.loglog(sim_counts, accuracy_per_time, 'co-', linewidth=2, markersize=6)
    ax4.set_xlabel('Number of Simulations')
    ax4.set_ylabel('Accuracy per Second (1 / (Error% × Time))')
    ax4.set_title('Overall Efficiency (Higher = Better)')
    ax4.grid(True, alpha=0.3)
    
    # Find optimal point (maximum accuracy per time)
    optimal_idx = np.argmax(accuracy_per_time)
    optimal_sims = sim_counts[optimal_idx]
    ax4.axvline(x=optimal_sims, color='red', linestyle='--', alpha=0.8)
    ax4.text(optimal_sims, max(accuracy_per_time) * 0.5, 
             f'Optimal: {optimal_sims:,}', rotation=90, ha='right', color='red', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('monte_carlo_optimization.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return optimal_sims

def find_optimal_simulation_count(analysis_results: dict, 
                                 target_error: float = 0.1,
                                 max_time: float = 1.0) -> dict:
    """
    Find optimal simulation count based on constraints.
    
    Args:
        analysis_results: Results from analyze_iterations_vs_accuracy
        target_error: Maximum acceptable error percentage
        max_time: Maximum acceptable execution time in seconds
        
    Returns:
        Dictionary with optimization recommendations
    """
    sim_counts = np.array(analysis_results['simulation_counts'])
    errors = np.array(analysis_results['error_percentages'])
    times = np.array(analysis_results['execution_times'])
    
    # Find points that meet error constraint
    error_mask = errors <= target_error
    valid_error_sims = sim_counts[error_mask]
    valid_error_times = times[error_mask]
    
    # Find points that meet time constraint
    time_mask = times <= max_time
    valid_time_sims = sim_counts[time_mask]
    valid_time_errors = errors[time_mask]
    
    # Find intersection (meets both constraints)
    both_mask = error_mask & time_mask
    optimal_sims = sim_counts[both_mask]
    optimal_errors = errors[both_mask]
    optimal_times = times[both_mask]
    
    recommendations = {
        'target_error_percent': target_error,
        'max_time_seconds': max_time,
        'min_sims_for_error': min(valid_error_sims) if len(valid_error_sims) > 0 else None,
        'max_sims_for_time': max(valid_time_sims) if len(valid_time_sims) > 0 else None,
        'optimal_range': (min(optimal_sims), max(optimal_sims)) if len(optimal_sims) > 0 else None,
        'recommended_sims': min(optimal_sims) if len(optimal_sims) > 0 else None
    }
    
    return recommendations

# Example usage and testing
if __name__ == "__main__":
    print("=== Monte Carlo Optimization Analysis ===")
    
    # Choose a standard deck for analysis
    standard_deck = GameState(60, 24)
    
    # Run comprehensive analysis
    print("Running iterations vs accuracy analysis...")
    analysis_data = analyze_iterations_vs_accuracy(
        game_state=standard_deck,
        max_simulations=1000000,
        num_data_points=15
    )
    
    # Create optimization plots
    print("\nGenerating optimization plots...")
    optimal_sims = create_optimization_plots(analysis_data, standard_deck)
    
    # Find optimal simulation counts for different constraints
    print(f"\n=== Optimization Recommendations ===")
    
    # Conservative: 0.1% error, 1 second max
    conservative = find_optimal_simulation_count(analysis_data, target_error=0.1, max_time=1.0)
    print(f"Conservative (≤0.1% error, ≤1s): {conservative['recommended_sims']:,} simulations")
    
    # Balanced: 0.5% error, 0.1 second max
    balanced = find_optimal_simulation_count(analysis_data, target_error=0.5, max_time=0.1)
    print(f"Balanced (≤0.5% error, ≤0.1s): {balanced['recommended_sims']:,} simulations")
    
    # Fast: 2% error, 0.01 second max
    fast = find_optimal_simulation_count(analysis_data, target_error=2.0, max_time=0.01)
    print(f"Fast (≤2% error, ≤0.01s): {fast['recommended_sims']:,} simulations")
    
    # Show overall optimal point
    print(f"\nOverall optimal (best accuracy/time ratio): {optimal_sims:,} simulations")
    
    # Demonstrate the recommendations
    print(f"\n=== Testing Recommendations ===")
    test_sims = [
        ("Conservative", conservative['recommended_sims']),
        ("Balanced", balanced['recommended_sims']),
        ("Fast", fast['recommended_sims']),
        ("Overall Optimal", optimal_sims)
    ]
    
    for name, sim_count in test_sims:
        if sim_count is not None:
            result = monte_carlo_land_probability(standard_deck, num_simulations=sim_count)
            print(f"{name}: {sim_count:,} sims → "
                  f"{result['error_percentage']:.3f}% error, "
                  f"{result['execution_time_seconds']:.6f}s, "
                  f"{result['simulations_per_second']:.0f} sim/sec")
    
    print(f"\nPlot saved as: monte_carlo_optimization.png")
