"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional


class DeckConfiguration(BaseModel):
    """Deck configuration for simulation"""
    total_cards: int = Field(default=60, ge=1, le=250, description="Total number of cards in deck")
    lands_in_deck: int = Field(default=24, ge=0, description="Number of lands in deck")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_cards": 60,
                "lands_in_deck": 24
            }
        }


class SimulationRequest(BaseModel):
    """Request model for land probability simulation"""
    deck: DeckConfiguration
    num_simulations: int = Field(default=10000, ge=100, le=1000000, description="Number of Monte Carlo simulations to run")
    random_seed: Optional[int] = Field(default=None, description="Optional random seed for reproducible results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "deck": {
                    "total_cards": 60,
                    "lands_in_deck": 24
                },
                "num_simulations": 10000,
                "random_seed": 42
            }
        }


class SimulationResponse(BaseModel):
    """Response model for simulation results"""
    land_probability: float = Field(description="Simulated probability of drawing a land")
    theoretical_probability: float = Field(description="Theoretical probability of drawing a land")
    absolute_error: float = Field(description="Absolute difference between simulated and theoretical")
    error_percentage: float = Field(description="Error as percentage of theoretical probability")
    simulations_run: int = Field(description="Number of simulations executed")
    land_draws: int = Field(description="Number of times a land was drawn in simulation")
    execution_time_seconds: float = Field(description="Time taken to run the simulation")
    simulations_per_second: float = Field(description="Performance metric: simulations per second")
    game_state: str = Field(description="String representation of the game state")
    
    class Config:
        json_schema_extra = {
            "example": {
                "land_probability": 0.4012,
                "theoretical_probability": 0.4,
                "absolute_error": 0.0012,
                "error_percentage": 0.3,
                "simulations_run": 10000,
                "land_draws": 4012,
                "execution_time_seconds": 0.0045,
                "simulations_per_second": 2222222.22,
                "game_state": "GameState(24 lands / 60 total cards)"
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: float
    version: str
