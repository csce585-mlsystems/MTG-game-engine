"""
FastAPI endpoints for MTG land simulation
"""
from fastapi import FastAPI, HTTPException
import time

from .models import SimulationRequest, SimulationResponse, HealthResponse
from .simulation import GameState, monte_carlo_probability


# Initialize FastAPI app
app = FastAPI(
    title="MTG Card Simulation API",
    description="Monte Carlo simulation for Magic: The Gathering card probability calculations with support for multiple card categories",
    version="2.0.0"
)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "MTG Card Simulation API",
        "description": "Monte Carlo simulation for Magic: The Gathering card probability calculations with support for multiple card categories",
        "version": "2.0.0",
        "endpoints": {
            "/simulate": "POST - Run category-specific probability simulation",
            "/simulate/land": "GET - Quick land probability simulation",
            "/health": "GET - Health check",
            "/docs": "GET - Interactive API documentation",
            "/redoc": "GET - Alternative API documentation"
        },
        "features": [
            "Multi-category card simulation (lands, creatures, spells, etc.)",
            "Flexible deck configuration",
            "High-performance Monte Carlo algorithms",
            "Detailed statistical analysis",
            "Reproducible results with random seeds"
        ]
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
async def simulate_card_probability(request: SimulationRequest):
    """
    Run Monte Carlo simulation to calculate card category draw probability
    
    This endpoint accepts a deck configuration with multiple card categories and 
    simulation parameters, then runs a Monte Carlo simulation to estimate the 
    probability of drawing a specific card category from the deck.
    
    Args:
        request: Simulation request containing deck configuration and parameters
        
    Returns:
        Detailed simulation results including probabilities, errors, and performance metrics
        
    Raises:
        HTTPException: If deck configuration is invalid or simulation fails
    """
    try:
        # Validate deck configuration
        if not request.deck.card_counts:
            raise HTTPException(
                status_code=400,
                detail="Card counts cannot be empty"
            )
        
        # Validate all counts are positive
        for category, count in request.deck.card_counts.items():
            if count < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Card count for '{category}' cannot be negative: {count}"
                )
        
        # Validate category exists in deck
        if request.category not in request.deck.card_counts:
            available_categories = list(request.deck.card_counts.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Category '{request.category}' not found in deck. Available categories: {available_categories}"
            )
        
        # Create game state
        game_state = GameState(card_counts=request.deck.card_counts)
        
        # Run simulation
        result = monte_carlo_probability(
            game_state=game_state,
            category=request.category,
            num_simulations=request.num_simulations,
            random_seed=request.random_seed
        )
        
        # Return structured response
        return SimulationResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@app.get("/simulate/land", response_model=SimulationResponse)
async def quick_land_simulation(
    lands: int = 24,
    non_lands: int = 36,
    num_simulations: int = 1000
):
    """
    Quick land simulation endpoint with query parameters
    
    Convenient endpoint for simple land probability simulations without JSON payload.
    
    Args:
        lands: Number of lands in deck (default: 24)
        non_lands: Number of non-land cards in deck (default: 36)
        num_simulations: Number of simulations to run (default: 1000)
        
    Returns:
        Land simulation results
    """
    try:
        # Validate parameters
        if lands < 0 or non_lands < 0:
            raise HTTPException(
                status_code=400,
                detail="Card counts cannot be negative"
            )
        
        total_cards = lands + non_lands
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
        card_counts = {"land": lands, "non_land": non_lands}
        game_state = GameState(card_counts=card_counts)
        result = monte_carlo_probability(
            game_state=game_state, 
            category="land", 
            num_simulations=num_simulations
        )
        
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
