"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Union


class DeckConfiguration(BaseModel):
    """Deck configuration for simulation with multiple card categories"""
    card_counts: Dict[str, int] = Field(description="Dictionary mapping card categories to counts")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "description": "Standard MTG deck",
                    "card_counts": {
                        "land": 24,
                        "creature": 20,
                        "spell": 16
                    }
                },
                {
                    "description": "Commander deck",
                    "card_counts": {
                        "land": 37,
                        "creature": 30,
                        "instant": 15,
                        "sorcery": 10,
                        "artifact": 4,
                        "enchantment": 3
                    }
                },
                {
                    "description": "Limited deck",
                    "card_counts": {
                        "land": 17,
                        "creature": 15,
                        "spell": 8
                    }
                }
            ]
        }


class SimulationRequest(BaseModel):
    """Request model for category-specific probability simulation"""
    deck: DeckConfiguration
    category: str = Field(description="Card category to simulate (e.g., 'land', 'creature', 'spell')")
    num_simulations: int = Field(default=10000, ge=100, le=1000000, description="Number of Monte Carlo simulations to run")
    random_seed: Optional[int] = Field(default=None, description="Optional random seed for reproducible results")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "description": "Land probability simulation",
                    "deck": {
                        "card_counts": {
                            "land": 24,
                            "creature": 20,
                            "spell": 16
                        }
                    },
                    "category": "land",
                    "num_simulations": 10000,
                    "random_seed": 42
                },
                {
                    "description": "Creature probability simulation",
                    "deck": {
                        "card_counts": {
                            "land": 24,
                            "creature": 20,
                            "spell": 16
                        }
                    },
                    "category": "creature",
                    "num_simulations": 10000,
                    "random_seed": 42
                }
            ]
        }


class SimulationResponse(BaseModel):
    """Response model for simulation results"""
    probability: float = Field(description="Simulated probability of drawing the specified category")
    theoretical_probability: float = Field(description="Theoretical probability of drawing the category")
    absolute_error: float = Field(description="Absolute difference between simulated and theoretical")
    error_percentage: float = Field(description="Error as percentage of theoretical probability")
    simulations_run: int = Field(description="Number of simulations executed")
    hits: int = Field(description="Number of times the category was drawn in simulation")
    execution_time_seconds: float = Field(description="Time taken to run the simulation")
    simulations_per_second: float = Field(description="Performance metric: simulations per second")
    game_state: str = Field(description="String representation of the game state")
    category: str = Field(description="Card category that was simulated")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "description": "Land simulation result",
                    "probability": 0.4012,
                    "theoretical_probability": 0.4,
                    "absolute_error": 0.0012,
                    "error_percentage": 0.3,
                    "simulations_run": 10000,
                    "hits": 4012,
                    "execution_time_seconds": 0.0045,
                    "simulations_per_second": 2222222.22,
                    "game_state": "GameState(land: 24, creature: 20, spell: 16, total=60)",
                    "category": "land"
                },
                {
                    "description": "Creature simulation result",
                    "probability": 0.3312,
                    "theoretical_probability": 0.3333,
                    "absolute_error": 0.0021,
                    "error_percentage": 0.63,
                    "simulations_run": 10000,
                    "hits": 3312,
                    "execution_time_seconds": 0.0045,
                    "simulations_per_second": 2222222.22,
                    "game_state": "GameState(land: 24, creature: 20, spell: 16, total=60)",
                    "category": "creature"
                }
            ]
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: float
    version: str
