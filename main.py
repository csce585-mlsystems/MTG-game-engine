from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn
from MonteCarloTesting import GameState, monte_carlo_land_probability
import time

# Initialize FastAPI app
app = FastAPI(
    title="MTG Land Simulation API",
    description="Monte Carlo simulation for Magic: The Gathering land probability calculations",
    version="1.0.0"
)

# Pydantic models for request/response validation
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

# API Endpoints
@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "MTG Land Simulation API",
        "description": "Monte Carlo simulation for Magic: The Gathering land probability calculations",
        "version": "1.0.0",
        "endpoints": {
            "/simulate": "POST - Run land probability simulation",
            "/health": "GET - Health check",
            "/docs": "GET - Interactive API documentation",
            "/redoc": "GET - Alternative API documentation"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version="1.0.0"
    )

@app.post("/simulate", response_model=SimulationResponse)
async def simulate_land_probability(request: SimulationRequest):
    """
    Run Monte Carlo simulation to calculate land draw probability
    
    This endpoint accepts a deck configuration and simulation parameters,
    then runs a Monte Carlo simulation to estimate the probability of
    drawing a land from the deck.
    
    Args:
        request: Simulation request containing deck configuration and parameters
        
    Returns:
        Detailed simulation results including probabilities, errors, and performance metrics
        
    Raises:
        HTTPException: If deck configuration is invalid or simulation fails
    """
    try:
        # Validate deck configuration
        if request.deck.lands_in_deck > request.deck.total_cards:
            raise HTTPException(
                status_code=400,
                detail=f"Number of lands ({request.deck.lands_in_deck}) cannot exceed total cards ({request.deck.total_cards})"
            )
        
        # Create game state
        game_state = GameState(
            total_cards=request.deck.total_cards,
            lands_in_deck=request.deck.lands_in_deck
        )
        
        # Run simulation
        result = monte_carlo_land_probability(
            game_state=game_state,
            num_simulations=request.num_simulations,
            random_seed=request.random_seed
        )
        
        # Return structured response
        return SimulationResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@app.get("/simulate/quick", response_model=SimulationResponse)
async def quick_simulation(
    total_cards: int = 60,
    lands_in_deck: int = 24,
    num_simulations: int = 1000
):
    """
    Quick simulation endpoint with query parameters
    
    Convenient endpoint for simple simulations without JSON payload.
    
    Args:
        total_cards: Total number of cards in deck (default: 60)
        lands_in_deck: Number of lands in deck (default: 24)
        num_simulations: Number of simulations to run (default: 1000)
        
    Returns:
        Simulation results
    """
    try:
        # Validate parameters
        if lands_in_deck > total_cards:
            raise HTTPException(
                status_code=400,
                detail=f"Number of lands ({lands_in_deck}) cannot exceed total cards ({total_cards})"
            )
        
        if not (1 <= total_cards <= 250):
            raise HTTPException(
                status_code=400,
                detail="Total cards must be between 1 and 250"
            )
        
        if not (100 <= num_simulations <= 1000000):
            raise HTTPException(
                status_code=400,
                detail="Number of simulations must be between 100 and 1,000,000"
            )
        
        # Create game state and run simulation
        game_state = GameState(total_cards=total_cards, lands_in_deck=lands_in_deck)
        result = monte_carlo_land_probability(game_state, num_simulations=num_simulations)
        
        return SimulationResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

# Add CORS middleware for web frontend access
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
