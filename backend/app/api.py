"""
FastAPI endpoints for MTG land simulation
"""
from fastapi import FastAPI, HTTPException
import time

from .models import SimulationRequest, SimulationResponse, HealthResponse
from .simulation import GameState, monte_carlo_land_probability


# Initialize FastAPI app
app = FastAPI(
    title="MTG Land Simulation API",
    description="Monte Carlo simulation for Magic: The Gathering land probability calculations",
    version="1.0.0"
)


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
