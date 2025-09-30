#!/usr/bin/env python3
"""
Test script for the Enhanced MTG Card Simulation API
Demonstrates the new multi-category functionality
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_enhanced_features():
    """Test the enhanced multi-category simulation features"""
    
    print("🎯 Enhanced MTG Card Simulation API Test")
    print("=" * 50)
    
    # Test 1: Standard MTG deck with multiple categories
    print("\n📦 Test 1: Standard MTG Deck Analysis")
    standard_deck = {
        "deck": {
            "card_counts": {
                "land": 24,
                "creature": 20,
                "instant": 8,
                "sorcery": 6,
                "artifact": 2
            }
        },
        "num_simulations": 20000,
        "random_seed": 42
    }
    
    categories = ["land", "creature", "instant", "sorcery", "artifact"]
    
    for category in categories:
        payload = {**standard_deck, "category": category}
        response = requests.post(f"{BASE_URL}/simulate", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  {category.capitalize():>9}: {result['probability']:.3f} "
                  f"(theoretical: {result['theoretical_probability']:.3f}, "
                  f"error: {result['error_percentage']:.2f}%)")
        else:
            print(f"  {category.capitalize():>9}: ERROR {response.status_code}")
    
    # Test 2: Commander deck analysis
    print("\n🏰 Test 2: Commander Deck Analysis")
    commander_deck = {
        "deck": {
            "card_counts": {
                "land": 37,
                "creature": 30,
                "instant": 12,
                "sorcery": 10,
                "artifact": 6,
                "enchantment": 4
            }
        },
        "category": "land",
        "num_simulations": 15000,
        "random_seed": 123
    }
    
    response = requests.post(f"{BASE_URL}/simulate", json=commander_deck)
    if response.status_code == 200:
        result = response.json()
        print(f"  Commander land probability: {result['probability']:.3f}")
        print(f"  Deck composition: {result['game_state']}")
        print(f"  Performance: {result['simulations_per_second']:,.0f} sims/sec")
    
    # Test 3: Limited deck analysis
    print("\n🎲 Test 3: Limited Deck Analysis")
    limited_deck = {
        "deck": {
            "card_counts": {
                "land": 17,
                "creature": 15,
                "spell": 8
            }
        },
        "num_simulations": 10000
    }
    
    for category in ["land", "creature", "spell"]:
        payload = {**limited_deck, "category": category}
        response = requests.post(f"{BASE_URL}/simulate", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  {category.capitalize():>8}: {result['probability']:.3f} probability")
    
    # Test 4: Quick land simulation (backward compatibility)
    print("\n⚡ Test 4: Quick Land Simulation")
    response = requests.get(f"{BASE_URL}/simulate/land?lands=26&non_lands=34&num_simulations=5000")
    
    if response.status_code == 200:
        result = response.json()
        print(f"  High-land deck: {result['probability']:.3f} land probability")
        print(f"  Execution time: {result['execution_time_seconds']:.4f}s")
    
    # Test 5: Error handling
    print("\n❌ Test 5: Error Handling")
    
    # Test invalid category
    invalid_payload = {
        "deck": {
            "card_counts": {
                "land": 24,
                "creature": 36
            }
        },
        "category": "planeswalker",  # Not in deck
        "num_simulations": 1000
    }
    
    response = requests.post(f"{BASE_URL}/simulate", json=invalid_payload)
    if response.status_code == 400:
        error = response.json()
        print(f"  ✓ Correctly caught invalid category: {error['detail']}")
    
    print("\n🎉 All tests completed!")
    print(f"\n📚 API Documentation: {BASE_URL}/docs")

if __name__ == "__main__":
    try:
        test_enhanced_features()
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Could not connect to API at {BASE_URL}")
        print("Make sure the server is running with: cd backend && python3 main.py")
    except Exception as e:
        print(f"❌ ERROR: {e}")
