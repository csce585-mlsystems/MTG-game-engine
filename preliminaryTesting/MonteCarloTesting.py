import random
import time
from typing import Optional, List
import matplotlib.pyplot as plt
import numpy as np
import psutil
import platform
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

class GameState:
    """Track deck composition with multiple card categories (lands, creatures, spells, etc.)."""

    def __init__(self, card_counts: dict[str, int]):
        """Initialize game state
            Args: card_counts: Dictionary mapping category → count
                    e.g. {"land": 24, "creature": 20, "spell": 16}"""
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
    Monte Carlo simulation to predict probability of drawing a given category, such as lands.
    
    Args:
        category: e.g. "land", "creature", "spell", "<GIVEN-CARD-NAME>, etc"

    Returns:
        dictionary of simulation results and statistics.
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

    #Run simulations
    for _ in range(num_simulations):
        #
        if random.random() < base_probability:
            hits += 1

    #Calculate detailed statistics
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

def analyze_iterations_vs_accuracy(game_state: GameState, 
                                  max_simulations: int = 1000000,
                                  num_data_points: int = 20,
                                  num_trials: int = 10) -> dict:
    """
    Analyze the relationship between number of iterations and accuracy with multiple trials.
    
    Args:
        game_state: Game state to analyze
        max_simulations: Maximum number of simulations to test
        num_data_points: Number of data points to collect
        num_trials: Number of independent trials to run at each iteration count
        
    Returns:
        Dictionary with analysis results including means and standard deviations
    """
    # Create logarithmic spacing for simulation counts
    simulation_counts = np.logspace(2, np.log10(max_simulations), num_data_points, dtype=int)
    
    results = {
        'simulation_counts': [],
        'error_percentages_mean': [],
        'error_percentages_std': [],
        'error_percentages_all': [],
        'execution_times_mean': [],
        'execution_times_std': [],
        'simulations_per_second_mean': [],
        'simulations_per_second_std': [],
        'land_probabilities_mean': [],
        'land_probabilities_std': []
    }
    
    #Changing land_probability to probability to reflect changes in GameState
    theoretical_prob = game_state.probability("land")
    
    print(f"Analyzing {game_state} with theoretical probability: {theoretical_prob:.6f}")
    print(f"Running {num_trials} trials at each of {num_data_points} iteration counts...")
    
    total_runs = len(simulation_counts) * num_trials
    current_run = 0
    
    for i, sim_count in enumerate(simulation_counts):
        print(f"Progress: {i+1}/{len(simulation_counts)} iteration counts - {sim_count:,} simulations")
        
        trial_errors = []
        trial_times = []
        trial_speeds = []
        trial_probabilities = []
        
        for _ in range(num_trials):
            result = monte_carlo_probability(game_state, "land", num_simulations=sim_count)
            trial_errors.append(result['error_percentage'])
            trial_times.append(result['execution_time_seconds'])
            trial_speeds.append(result['simulations_per_second'])
            trial_probabilities.append(result['land_probability'])
        
        # Calculate statistics across trials
        results['simulation_counts'].append(sim_count)
        results['error_percentages_mean'].append(np.mean(trial_errors))
        results['error_percentages_std'].append(np.std(trial_errors))
        results['error_percentages_all'].append(trial_errors.copy())
        results['execution_times_mean'].append(np.mean(trial_times))
        results['execution_times_std'].append(np.std(trial_times))
        results['simulations_per_second_mean'].append(np.mean(trial_speeds))
        results['simulations_per_second_std'].append(np.std(trial_speeds))
        results['land_probabilities_mean'].append(np.mean(trial_probabilities))
        results['land_probabilities_std'].append(np.std(trial_probabilities))
        
        print(f"  {sim_count:,} sims: {np.mean(trial_errors):.4f}±{np.std(trial_errors):.4f}% error")
    
    print("\nAnalysis complete!")
    return results

def create_optimization_plots(analysis_results: dict, game_state: GameState):
    """Create comprehensive plots for iterations vs accuracy optimization with error bars."""
    
    sim_counts = analysis_results['simulation_counts']
    errors_mean = analysis_results['error_percentages_mean']
    errors_std = analysis_results['error_percentages_std']
    times_mean = analysis_results['execution_times_mean']
    times_std = analysis_results['execution_times_std']
    speeds_mean = analysis_results['simulations_per_second_mean']
    speeds_std = analysis_results['simulations_per_second_std']
    probs_mean = analysis_results['land_probabilities_mean']
    probs_std = analysis_results['land_probabilities_std']
    
    # Create figure with subplots
    fig_width = 18
    base_fig_width = 14
    scale_factor = fig_width / base_fig_width
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(fig_width, 14 * scale_factor))
    fig.suptitle(f'Monte Carlo Optimization Analysis\n{game_state}', fontsize=16 * scale_factor, fontweight='bold')
    plt.subplots_adjust(top=0.90)
    
    # Plot 1: Error vs Simulations (log-log)
    ax1.loglog(sim_counts, errors, 'bo-', linewidth=2, markersize=6 * scale_factor)
    ax1.set_xlabel('Number of Simulations', fontsize=12 * scale_factor)
    ax1.set_ylabel('Error Percentage (%)', fontsize=12 * scale_factor)
    ax1.set_title('Accuracy vs Iterations', fontweight='bold', fontsize=14 * scale_factor)
    ax1.grid(True, alpha=0.3)
    
    theoretical_errors = errors[0] * np.sqrt(sim_counts[0] / np.array(sim_counts))
    ax1.loglog(sim_counts, theoretical_errors, 'r--', alpha=0.7, label='Theoretical 1/√n')
    ax1.legend(fontsize=10 * scale_factor)
    
    # Plot 2: Execution Time vs Simulations
    ax2.loglog(sim_counts, times, 'go-', linewidth=2, markersize=6 * scale_factor)
    ax2.set_xlabel('Number of Simulations', fontsize=12 * scale_factor)
    ax2.set_ylabel('Execution Time (seconds)', fontsize=12 * scale_factor)
    ax2.set_title('Performance vs Iterations', fontweight='bold', fontsize=14 * scale_factor)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Efficiency (Simulations per Second)
    ax3.semilogx(sim_counts, np.array(speeds) / 1e6, 'mo-', linewidth=2, markersize=6 * scale_factor)
    ax3.set_xlabel('Number of Simulations', fontsize=12 * scale_factor)
    ax3.set_ylabel('Simulations per Second (Millions)', fontsize=12 * scale_factor)
    ax3.set_title('Computational Efficiency', fontweight='bold', fontsize=14 * scale_factor)
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # Plot 4: Accuracy per Time (Optimization metric)
    accuracy_per_time = 1 / (np.array(errors) * np.array(times))  # Higher is better
    ax4.loglog(sim_counts, accuracy_per_time, 'co-', linewidth=2, markersize=6 * scale_factor)
    ax4.set_xlabel('Number of Simulations', fontsize=12 * scale_factor)
    ax4.set_ylabel('Accuracy per Second (1 / (Error% × Time))', fontsize=12 * scale_factor)
    ax4.set_title('Overall Efficiency (Higher = Better)', fontweight='bold', fontsize=14 * scale_factor)
    ax4.grid(True, alpha=0.3)
    
    # Find optimal point (minimum coefficient of variation for reasonable accuracy)
    # Filter to reasonable accuracy first (< 1% error)
    reasonable_mask = np.array(errors_mean) < 1.0
    if np.any(reasonable_mask):
        reasonable_cv = cv_error[reasonable_mask]
        reasonable_sims = np.array(sim_counts)[reasonable_mask]
        optimal_idx = np.argmin(reasonable_cv)
        optimal_sims = reasonable_sims[optimal_idx]
        ax4.axvline(x=optimal_sims, color='red', linestyle='--', alpha=0.8)
        ax4.text(optimal_sims, max(cv_error) * 0.8, 
                 f'Most Consistent: {optimal_sims:,}', rotation=90, ha='right', 
                 color='red', fontweight='bold')
    else:
        optimal_sims = sim_counts[-1]  # Default to highest if none meet criteria
    
    plt.tight_layout(pad=5.0 * scale_factor)
    plt.savefig('monte_carlo_optimization.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return optimal_sims

def create_detailed_error_analysis(analysis_results: dict, game_state: GameState):
    """Create detailed error analysis plots showing individual trial results."""
    
    sim_counts = analysis_results['simulation_counts']
    all_errors = analysis_results['error_percentages_all']
    
    # Create figure for detailed error analysis
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle(f'Detailed Error Analysis - Multiple Trials\n{game_state}', 
                 fontsize=14, fontweight='bold')
    
    # Plot 1: Box plot of errors at each iteration count
    positions = range(len(sim_counts))
    bp = ax1.boxplot(all_errors, positions=positions, patch_artist=True, 
                     labels=[f'{count:,}' for count in sim_counts])
    
    # Color the boxes
    colors = plt.cm.viridis(np.linspace(0, 1, len(bp['boxes'])))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax1.set_xlabel('Number of Simulations')
    ax1.set_ylabel('Error Percentage (%)')
    ax1.set_title('Error Distribution at Each Iteration Count')
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3)
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
    
    # Plot 2: Individual trial trajectories
    colors = plt.cm.tab10(np.linspace(0, 1, len(all_errors[0])))
    for trial_idx in range(len(all_errors[0])):
        trial_errors = [errors[trial_idx] for errors in all_errors]
        ax2.loglog(sim_counts, trial_errors, 'o-', alpha=0.6, linewidth=1, 
                   markersize=4, color=colors[trial_idx])
    
    # Add mean line
    means = [np.mean(errors) for errors in all_errors]
    ax2.loglog(sim_counts, means, 'ko-', linewidth=3, markersize=8, 
               label='Mean', alpha=0.8)
    
    ax2.set_xlabel('Number of Simulations')
    ax2.set_ylabel('Error Percentage (%)')
    ax2.set_title('Individual Trial Trajectories')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig('monte_carlo_detailed_error_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def find_optimal_simulation_count(analysis_results: dict, 
                                 target_error: float = 0.1,
                                 max_time: float = 1.0) -> dict:
    """
    Find optimal simulation count based on constraints using multi-trial data.
    
    Args:
        analysis_results: Results from analyze_iterations_vs_accuracy
        target_error: Maximum acceptable error percentage (mean)
        max_time: Maximum acceptable execution time in seconds (mean)
        
    Returns:
        Dictionary with optimization recommendations
    """
    sim_counts = np.array(analysis_results['simulation_counts'])
    errors_mean = np.array(analysis_results['error_percentages_mean'])
    times_mean = np.array(analysis_results['execution_times_mean'])
    
    # Find points that meet error constraint
    error_mask = errors_mean <= target_error
    valid_error_sims = sim_counts[error_mask]
    valid_error_times = times_mean[error_mask]
    
    # Find points that meet time constraint
    time_mask = times_mean <= max_time
    valid_time_sims = sim_counts[time_mask]
    valid_time_errors = errors_mean[time_mask]
    
    # Find intersection (meets both constraints)
    both_mask = error_mask & time_mask
    optimal_sims = sim_counts[both_mask]
    optimal_errors = errors_mean[both_mask]
    optimal_times = times_mean[both_mask]
    
    recommendations = {
        'target_error_percent': target_error,
        'max_time_seconds': max_time,
        'min_sims_for_error': min(valid_error_sims) if len(valid_error_sims) > 0 else None,
        'max_sims_for_time': max(valid_time_sims) if len(valid_time_sims) > 0 else None,
        'optimal_range': (min(optimal_sims), max(optimal_sims)) if len(optimal_sims) > 0 else None,
        'recommended_sims': min(optimal_sims) if len(optimal_sims) > 0 else None
    }
    
    return recommendations

def get_system_info():
    """Get comprehensive system information for benchmarking."""
    cpu_info = {
        'processor': platform.processor(),
        'machine': platform.machine(),
        'cores_physical': psutil.cpu_count(logical=False),
        'cores_logical': psutil.cpu_count(logical=True),
        'cpu_freq_max': psutil.cpu_freq().max if psutil.cpu_freq() else 'Unknown',
        'cpu_freq_current': psutil.cpu_freq().current if psutil.cpu_freq() else 'Unknown'
    }
    
    memory_info = {
        'total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
        'used_percent': psutil.virtual_memory().percent
    }
    
    system_info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu': cpu_info,
        'memory': memory_info
    }
    
    return system_info

def benchmark_single_thread(game_state: GameState, simulation_counts: List[int]) -> dict:
    """Benchmark single-threaded performance."""
    results = {
        'simulation_counts': [],
        'execution_times': [],
        'simulations_per_second': [],
        'cpu_usage': [],
        'memory_usage': []
    }
    
    for sim_count in simulation_counts:
        # Monitor system resources
        cpu_before = psutil.cpu_percent(interval=None)
        memory_before = psutil.virtual_memory().percent
        
        # Run simulation
        result = monte_carlo_land_probability(game_state, num_simulations=sim_count)
        
        # Monitor system resources after
        cpu_after = psutil.cpu_percent(interval=0.1)
        memory_after = psutil.virtual_memory().percent
        
        results['simulation_counts'].append(sim_count)
        results['execution_times'].append(result['execution_time_seconds'])
        results['simulations_per_second'].append(result['simulations_per_second'])
        results['cpu_usage'].append(max(cpu_before, cpu_after))
        results['memory_usage'].append(max(memory_before, memory_after))
    
    return results

def monte_carlo_worker(args):
    """Worker function for parallel processing."""
    game_state, num_simulations, seed = args
    return monte_carlo_land_probability(game_state, num_simulations, seed)

def benchmark_parallel_performance(game_state: GameState, total_simulations: int = 100000) -> dict:
    """Benchmark parallel vs single-threaded performance."""
    max_workers = multiprocessing.cpu_count()
    thread_counts = [1, 2, 4, max_workers] if max_workers >= 4 else [1, 2, max_workers]
    
    results = {
        'thread_counts': [],
        'execution_times': [],
        'speedup_ratios': [],
        'efficiency': [],
        'simulations_per_second': []
    }
    
    baseline_time = None
    
    for num_threads in thread_counts:
        if num_threads > max_workers:
            continue
            
        print(f"Testing {num_threads} threads...")
        
        # Divide work among threads
        sims_per_thread = total_simulations // num_threads
        remaining_sims = total_simulations % num_threads
        
        # Create work packages
        work_packages = []
        for i in range(num_threads):
            sims = sims_per_thread + (1 if i < remaining_sims else 0)
            work_packages.append((game_state, sims, i + 1))
        
        # Time parallel execution
        start_time = time.time()
        
        if num_threads == 1:
            # Single-threaded baseline
            monte_carlo_worker(work_packages[0])
        else:
            # Multi-threaded execution
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                list(executor.map(monte_carlo_worker, work_packages))
        
        execution_time = time.time() - start_time
        
        # Calculate metrics
        if baseline_time is None:
            baseline_time = execution_time
            speedup = 1.0
        else:
            speedup = baseline_time / execution_time
        
        efficiency = speedup / num_threads
        sims_per_sec = total_simulations / execution_time
        
        results['thread_counts'].append(num_threads)
        results['execution_times'].append(execution_time)
        results['speedup_ratios'].append(speedup)
        results['efficiency'].append(efficiency)
        results['simulations_per_second'].append(sims_per_sec)
    
    return results

def benchmark_memory_scaling(game_state: GameState) -> dict:
    """Benchmark memory usage scaling with simulation count."""
    simulation_counts = [1000, 10000, 100000, 1000000, 5000000]
    
    results = {
        'simulation_counts': [],
        'memory_before_mb': [],
        'memory_after_mb': [],
        'memory_delta_mb': [],
        'execution_times': []
    }
    
    for sim_count in simulation_counts:
        # Force garbage collection
        import gc
        gc.collect()
        
        # Measure memory before
        memory_before = psutil.virtual_memory().used / (1024**2)  # MB
        
        # Run simulation
        start_time = time.time()
        monte_carlo_land_probability(game_state, num_simulations=sim_count)
        execution_time = time.time() - start_time
        
        # Measure memory after
        memory_after = psutil.virtual_memory().used / (1024**2)  # MB
        memory_delta = memory_after - memory_before
        
        results['simulation_counts'].append(sim_count)
        results['memory_before_mb'].append(memory_before)
        results['memory_after_mb'].append(memory_after)
        results['memory_delta_mb'].append(memory_delta)
        results['execution_times'].append(execution_time)
        
        print(f"{sim_count:,} sims: {execution_time:.3f}s, {memory_delta:.1f}MB delta")
    
    return results

def create_hardware_benchmark_plots(system_info: dict, 
                                   single_thread_results: dict,
                                   parallel_results: dict,
                                   memory_results: dict):
    """Create comprehensive hardware benchmark plots."""
    
    fig = plt.figure(figsize=(20, 16))
    
    # Create a grid layout
    gs = fig.add_gridspec(4, 3, height_ratios=[0.5, 1, 1, 1], hspace=0.3, wspace=0.3)
    
    # System info text
    ax_info = fig.add_subplot(gs[0, :])
    ax_info.axis('off')
    info_text = f"""Hardware Benchmark Results
Platform: {system_info['platform']} | Python: {system_info['python_version']}
CPU: {system_info['cpu']['cores_physical']} physical cores, {system_info['cpu']['cores_logical']} logical cores
Memory: {system_info['memory']['total_gb']} GB total, {system_info['memory']['available_gb']} GB available
Processor: {system_info['cpu']['processor']}"""
    ax_info.text(0.5, 0.5, info_text, ha='center', va='center', fontsize=12, 
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
    
    # Plot 1: Single-thread performance scaling
    ax1 = fig.add_subplot(gs[1, 0])
    ax1.loglog(single_thread_results['simulation_counts'], 
               single_thread_results['execution_times'], 'bo-', linewidth=2, markersize=6)
    ax1.set_xlabel('Simulations')
    ax1.set_ylabel('Execution Time (s)')
    ax1.set_title('Single-Thread Performance')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Throughput (simulations per second)
    ax2 = fig.add_subplot(gs[1, 1])
    ax2.semilogx(single_thread_results['simulation_counts'], 
                 np.array(single_thread_results['simulations_per_second']) / 1e6, 'go-', 
                 linewidth=2, markersize=6)
    ax2.set_xlabel('Simulations')
    ax2.set_ylabel('Throughput (Million sims/s)')
    ax2.set_title('Single-Thread Throughput')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Resource usage
    ax3 = fig.add_subplot(gs[1, 2])
    ax3_twin = ax3.twinx()
    
    line1 = ax3.semilogx(single_thread_results['simulation_counts'], 
                        single_thread_results['cpu_usage'], 'ro-', 
                        linewidth=2, markersize=6, label='CPU %')
    line2 = ax3_twin.semilogx(single_thread_results['simulation_counts'], 
                             single_thread_results['memory_usage'], 'bo-', 
                             linewidth=2, markersize=6, label='Memory %')
    
    ax3.set_xlabel('Simulations')
    ax3.set_ylabel('CPU Usage (%)', color='red')
    ax3_twin.set_ylabel('Memory Usage (%)', color='blue')
    ax3.set_title('Resource Usage')
    ax3.grid(True, alpha=0.3)
    
    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax3.legend(lines, labels, loc='upper left')
    
    # Plot 4: Parallel speedup
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.plot(parallel_results['thread_counts'], parallel_results['speedup_ratios'], 
             'mo-', linewidth=2, markersize=8, label='Actual Speedup')
    ax4.plot(parallel_results['thread_counts'], parallel_results['thread_counts'], 
             'k--', alpha=0.7, label='Ideal Speedup')
    ax4.set_xlabel('Number of Threads')
    ax4.set_ylabel('Speedup Ratio')
    ax4.set_title('Parallel Speedup')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    
    # Plot 5: Parallel efficiency
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.plot(parallel_results['thread_counts'], 
             np.array(parallel_results['efficiency']) * 100, 'co-', 
             linewidth=2, markersize=8)
    ax5.axhline(y=100, color='red', linestyle='--', alpha=0.7, label='100% Efficient')
    ax5.set_xlabel('Number of Threads')
    ax5.set_ylabel('Efficiency (%)')
    ax5.set_title('Parallel Efficiency')
    ax5.grid(True, alpha=0.3)
    ax5.legend()
    
    # Plot 6: Parallel throughput
    ax6 = fig.add_subplot(gs[2, 2])
    ax6.plot(parallel_results['thread_counts'], 
             np.array(parallel_results['simulations_per_second']) / 1e6, 'yo-', 
             linewidth=2, markersize=8)
    ax6.set_xlabel('Number of Threads')
    ax6.set_ylabel('Throughput (Million sims/s)')
    ax6.set_title('Parallel Throughput')
    ax6.grid(True, alpha=0.3)
    
    # Plot 7: Memory scaling
    ax7 = fig.add_subplot(gs[3, 0])
    ax7.loglog(memory_results['simulation_counts'], 
               memory_results['memory_delta_mb'], 'ro-', linewidth=2, markersize=6)
    ax7.set_xlabel('Simulations')
    ax7.set_ylabel('Memory Delta (MB)')
    ax7.set_title('Memory Usage Scaling')
    ax7.grid(True, alpha=0.3)
    
    # Plot 8: Memory efficiency
    ax8 = fig.add_subplot(gs[3, 1])
    memory_per_sim = np.array(memory_results['memory_delta_mb']) / np.array(memory_results['simulation_counts']) * 1e6  # bytes per sim
    ax8.semilogx(memory_results['simulation_counts'], memory_per_sim, 'go-', 
                 linewidth=2, markersize=6)
    ax8.set_xlabel('Simulations')
    ax8.set_ylabel('Bytes per Simulation')
    ax8.set_title('Memory Efficiency')
    ax8.grid(True, alpha=0.3)
    
    # Plot 9: Performance vs Memory trade-off
    ax9 = fig.add_subplot(gs[3, 2])
    throughput = np.array(memory_results['simulation_counts']) / np.array(memory_results['execution_times']) / 1e6
    ax9.scatter(memory_results['memory_delta_mb'], throughput, 
                c=memory_results['simulation_counts'], cmap='viridis', s=100, alpha=0.7)
    ax9.set_xlabel('Memory Usage (MB)')
    ax9.set_ylabel('Throughput (Million sims/s)')
    ax9.set_title('Performance vs Memory')
    ax9.grid(True, alpha=0.3)
    
    # Add colorbar for the scatter plot
    cbar = plt.colorbar(ax9.collections[0], ax=ax9)
    cbar.set_label('Simulation Count')
    
    plt.suptitle('Monte Carlo Hardware Benchmark Analysis', fontsize=16, fontweight='bold')
    plt.savefig('monte_carlo_hardware_benchmark.png', dpi=300, bbox_inches='tight')
    plt.show()

# Example usage and testing
if __name__ == "__main__":
    print("=== Monte Carlo Optimization Analysis ===")
    
    # Choose a standard deck for analysis
    standard_deck = GameState({"land": 24, "creature": 18, "spell": 18})
    
    # Run comprehensive analysis with multiple trials
    print("Running iterations vs accuracy analysis with multiple trials...")
    analysis_data = analyze_iterations_vs_accuracy(
        game_state=standard_deck,
        max_simulations=500000,  # Reduced for faster execution with multiple trials
        num_data_points=12,
        num_trials=8  # 8 independent trials at each iteration count
    )
    
    # Create optimization plots with error bars
    print("\nGenerating optimization plots with error bars...")
    optimal_sims = create_optimization_plots(analysis_data, standard_deck)
    
    # Create detailed error analysis
    print("\nGenerating detailed error analysis...")
    create_detailed_error_analysis(analysis_data, standard_deck)
    
    # Find optimal simulation counts for different constraints
    print(f"\n=== Optimization Recommendations (Based on Multiple Trials) ===")
    
    # Conservative: 0.1% error, 1 second max
    conservative = find_optimal_simulation_count(analysis_data, target_error=0.1, max_time=1.0)
    print(f"Conservative (≤0.1% error, ≤1s): {conservative['recommended_sims']} simulations")
    
    # Balanced: 0.5% error, 0.1 second max
    balanced = find_optimal_simulation_count(analysis_data, target_error=0.5, max_time=0.1)
    print(f"Balanced (≤0.5% error, ≤0.1s): {balanced['recommended_sims']} simulations")
    
    # Fast: 2% error, 0.01 second max
    fast = find_optimal_simulation_count(analysis_data, target_error=2.0, max_time=0.01)
    print(f"Fast (≤2% error, ≤0.01s): {fast['recommended_sims']} simulations")
    
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
            result = monte_carlo_probability(standard_deck, "land", num_simulations=sim_count)
            print(f"{name}: {sim_count:,} sims → "
                  f"{result['error_percentage']:.3f}% error, "
                  f"{result['execution_time_seconds']:.6f}s, "
                  f"{result['simulations_per_second']:.0f} sim/sec")
    
    print(f"\nPlot saved as: monte_carlo_optimization.png")

    print(f"\nMost consistent (lowest coefficient of variation): {optimal_sims:,} simulations")
    
    # Show summary statistics
    print(f"\n=== Summary Statistics ===")
    sim_counts = analysis_data['simulation_counts']
    errors_mean = analysis_data['error_percentages_mean']
    errors_std = analysis_data['error_percentages_std']
    times_mean = analysis_data['execution_times_mean']
    
    print(f"Simulation range: {min(sim_counts):,} to {max(sim_counts):,}")
    print(f"Best mean error: {min(errors_mean):.4f}% at {sim_counts[np.argmin(errors_mean)]:,} simulations")
    print(f"Most consistent error: {min(errors_std):.4f}% std at {sim_counts[np.argmin(errors_std)]:,} simulations")
    print(f"Fastest execution: {min(times_mean):.6f}s at {sim_counts[np.argmin(times_mean)]:,} simulations")
    
    print(f"\nPlots saved as:")
    print(f"  - monte_carlo_optimization_multi_trial.png")
    print(f"  - monte_carlo_detailed_error_analysis.png")
    
    # Hardware Benchmarking Section
    print(f"\n{'='*60}")
    print("=== HARDWARE BENCHMARKING ===")
    print(f"{'='*60}")
    
    # Get system information
    print("Gathering system information...")
    system_info = get_system_info()
    
    print(f"\nSystem Information:")
    print(f"Platform: {system_info['platform']}")
    print(f"Python: {system_info['python_version']}")
    print(f"CPU: {system_info['cpu']['cores_physical']} physical cores, {system_info['cpu']['cores_logical']} logical cores")
    print(f"Memory: {system_info['memory']['total_gb']} GB total, {system_info['memory']['available_gb']} GB available")
    
    # Single-thread benchmarking
    print(f"\n--- Single-Thread Performance Benchmarking ---")
    single_thread_sim_counts = [1000, 5000, 10000, 50000, 100000, 500000]
    single_thread_results = benchmark_single_thread(standard_deck, single_thread_sim_counts)
    
    print("Single-thread results:")
    for i, sim_count in enumerate(single_thread_results['simulation_counts']):
        print(f"  {sim_count:,} sims: {single_thread_results['execution_times'][i]:.4f}s, "
              f"{single_thread_results['simulations_per_second'][i]:.0f} sim/s, "
              f"CPU: {single_thread_results['cpu_usage'][i]:.1f}%")
    
    # Parallel performance benchmarking
    print(f"\n--- Parallel Performance Benchmarking ---")
    parallel_results = benchmark_parallel_performance(standard_deck, total_simulations=200000)
    
    print("Parallel results:")
    for i, thread_count in enumerate(parallel_results['thread_counts']):
        print(f"  {thread_count} threads: {parallel_results['execution_times'][i]:.4f}s, "
              f"speedup: {parallel_results['speedup_ratios'][i]:.2f}x, "
              f"efficiency: {parallel_results['efficiency'][i]*100:.1f}%")
    
    # Memory scaling benchmarking
    print(f"\n--- Memory Scaling Benchmarking ---")
    memory_results = benchmark_memory_scaling(standard_deck)
    
    # Create comprehensive hardware benchmark plots
    print(f"\n--- Generating Hardware Benchmark Plots ---")
    create_hardware_benchmark_plots(system_info, single_thread_results, 
                                   parallel_results, memory_results)
    
    print(f"\nHardware benchmark plot saved as: monte_carlo_hardware_benchmark.png")
    
    # Performance recommendations
    print(f"\n=== HARDWARE-SPECIFIC RECOMMENDATIONS ===")
    
    # Find optimal single-thread performance point
    throughputs = single_thread_results['simulations_per_second']
    max_throughput_idx = np.argmax(throughputs)
    optimal_single_sims = single_thread_results['simulation_counts'][max_throughput_idx]
    
    print(f"Optimal single-thread simulation count: {optimal_single_sims:,}")
    print(f"Peak single-thread throughput: {max(throughputs):,.0f} simulations/second")
    
    # Find optimal parallel configuration
    parallel_throughputs = parallel_results['simulations_per_second']
    max_parallel_idx = np.argmax(parallel_throughputs)
    optimal_threads = parallel_results['thread_counts'][max_parallel_idx]
    
    print(f"Optimal thread count: {optimal_threads}")
    print(f"Peak parallel throughput: {max(parallel_throughputs):,.0f} simulations/second")
    print(f"Parallel speedup: {parallel_results['speedup_ratios'][max_parallel_idx]:.2f}x")
    
    # Memory efficiency analysis
    memory_per_sim = np.array(memory_results['memory_delta_mb']) / np.array(memory_results['simulation_counts']) * 1024 * 1024  # bytes per sim
    most_efficient_idx = np.argmin(memory_per_sim[1:]) + 1  # Skip first point which might be noisy
    efficient_sim_count = memory_results['simulation_counts'][most_efficient_idx]
    
    print(f"Most memory-efficient simulation count: {efficient_sim_count:,}")
    print(f"Memory usage: {memory_per_sim[most_efficient_idx]:.1f} bytes per simulation")
    
    print(f"\nAll benchmark plots saved!")
    print(f"Files generated:")
    print(f"  - monte_carlo_optimization_multi_trial.png")
    print(f"  - monte_carlo_detailed_error_analysis.png") 
    print(f"  - monte_carlo_hardware_benchmark.png")
