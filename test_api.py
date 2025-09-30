#!/usr/bin/env python3
"""
Test script for the MTG Land Simulation API
Demonstrates various ways to use the API endpoints
"""

import requests
import json
import time

# API base URL (change this to your deployed URL)
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_quick_simulation():
    """Test the quick simulation endpoint"""
    print("=== Testing Quick Simulation ===")
    
    # Test with default standard deck
    response = requests.get(f"{BASE_URL}/simulate/quick")
    print(f"Default deck - Status: {response.status_code}")
    result = response.json()
    print(f"Land probability: {result['land_probability']:.4f}")
    print(f"Theoretical: {result['theoretical_probability']:.4f}")
    print(f"Error: {result['error_percentage']:.2f}%")
    print()
    
    # Test with custom parameters
    params = {
        "total_cards": 40,
        "lands_in_deck": 16,
        "num_simulations": 5000
    }
    response = requests.get(f"{BASE_URL}/simulate/quick", params=params)
    print(f"Custom deck (40 cards, 16 lands) - Status: {response.status_code}")
    result = response.json()
    print(f"Land probability: {result['land_probability']:.4f}")
    print(f"Execution time: {result['execution_time_seconds']:.4f}s")
    print()

def test_detailed_simulation():
    """Test the detailed simulation endpoint"""
    print("=== Testing Detailed Simulation ===")
    
    # Test with various deck configurations
    test_cases = [
        {"name": "Standard MTG Deck", "total_cards": 60, "lands_in_deck": 24},
        {"name": "Limited Deck", "total_cards": 40, "lands_in_deck": 17},
        {"name": "Commander Deck", "total_cards": 99, "lands_in_deck": 37},
        {"name": "High Land Count", "total_cards": 60, "lands_in_deck": 30},
        {"name": "Low Land Count", "total_cards": 60, "lands_in_deck": 18},
    ]
    
    for test_case in test_cases:
        payload = {
            "deck": {
                "total_cards": test_case["total_cards"],
                "lands_in_deck": test_case["lands_in_deck"]
            },
            "num_simulations": 20000,
            "random_seed": 42  # For reproducible results
        }
        
        response = requests.post(f"{BASE_URL}/simulate", json=payload)
        print(f"{test_case['name']} - Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Deck: {result['game_state']}")
            print(f"  Simulated probability: {result['land_probability']:.4f}")
            print(f"  Theoretical probability: {result['theoretical_probability']:.4f}")
            print(f"  Accuracy: {result['error_percentage']:.3f}% error")
            print(f"  Performance: {result['simulations_per_second']:,.0f} sims/sec")
        else:
            print(f"  Error: {response.text}")
        print()

def test_performance_comparison():
    """Test performance with different simulation counts"""
    print("=== Performance Comparison ===")
    
    simulation_counts = [1000, 10000, 50000, 100000]
    deck_config = {"total_cards": 60, "lands_in_deck": 24}
    
    print(f"Testing deck: {deck_config}")
    print("Simulations | Land Prob | Error % | Time (s) | Speed (sims/s)")
    print("-" * 65)
    
    for sim_count in simulation_counts:
        payload = {
            "deck": deck_config,
            "num_simulations": sim_count,
            "random_seed": 123
        }
        
        response = requests.post(f"{BASE_URL}/simulate", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"{sim_count:>11,} | {result['land_probability']:>9.4f} | "
                  f"{result['error_percentage']:>6.2f} | {result['execution_time_seconds']:>7.4f} | "
                  f"{result['simulations_per_second']:>12,.0f}")
        else:
            print(f"{sim_count:>11,} | ERROR: {response.status_code}")
    print()

def test_error_cases():
    """Test various error conditions"""
    print("=== Testing Error Cases ===")
    
    error_cases = [
        {
            "name": "More lands than cards",
            "payload": {
                "deck": {"total_cards": 60, "lands_in_deck": 70},
                "num_simulations": 1000
            }
        },
        {
            "name": "Too many simulations",
            "payload": {
                "deck": {"total_cards": 60, "lands_in_deck": 24},
                "num_simulations": 2000000  # Over the limit
            }
        },
        {
            "name": "Negative lands",
            "payload": {
                "deck": {"total_cards": 60, "lands_in_deck": -5},
                "num_simulations": 1000
            }
        },
        {
            "name": "Zero cards",
            "payload": {
                "deck": {"total_cards": 0, "lands_in_deck": 0},
                "num_simulations": 1000
            }
        }
    ]
    
    for case in error_cases:
        print(f"Testing: {case['name']}")
        response = requests.post(f"{BASE_URL}/simulate", json=case['payload'])
        print(f"  Status: {response.status_code}")
        if response.status_code != 200:
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"  Error: {error_detail}")
        print()

def main():
    """Run all tests"""
    print("MTG Land Simulation API Test Suite")
    print("=" * 50)
    print()
    
    try:
        test_health_check()
        test_quick_simulation()
        test_detailed_simulation()
        test_performance_comparison()
        test_error_cases()
        
        print("=== Test Summary ===")
        print("All tests completed successfully!")
        print(f"API Documentation available at: {BASE_URL}/docs")
        print(f"Alternative docs at: {BASE_URL}/redoc")
        
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to API at {BASE_URL}")
        print("Make sure the server is running with: python3 main.py")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()
