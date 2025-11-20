"""
FastAPI endpoints for MTG land simulation
"""
from fastapi import FastAPI, HTTPException, Request, Response, Query #Added Response, Query
import time
import logging
from typing import Optional, List

from .models import SimulationRequest, SimulationResponse, HealthResponse, CardListResponse, CardSearchRequest, CardNamesRequest, CardBase, ResolveDeckRequest, ResolveDeckResponse, SimulationByNamesRequest, SimulationByCardRequest
from .simulation import GameState, monte_carlo_probability, monte_carlo_probability_for_successes
from datetime import datetime #Added Datetime
from .repository import run_db, count_cards, query_cards, get_cards_by_names, DB_PATH
from .deck_service import resolve_deck

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def now_iso_utc() -> str: #Used for DB Timestamps
    """Return current UTC time in ISO 8601 format with Z suffix. Used for DB"""
    return datetime.utcnow().isoformat(timespec = "milliseconds") + "Z"

# Initialize FastAPI app
app = FastAPI(
    title="MTG Card Simulation API",
    description="Monte Carlo simulation for Magic: The Gathering card probability calculations with support for multiple card categories",
    version="2.0.0"
)

# API endpoints only below

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
        version="1.0.0",
        db_path=DB_PATH
    )

@app.post("/cards", response_model = CardListResponse)
async def list_cards(request: CardSearchRequest):
    where_clauses = []
    params = []
    if request.q:
        where_clauses.append("name LIKE ? COLLATE NOCASE")
        params.append(f"%{request.q}%")
    if request.set_code:
        where_clauses.append("LOWER(set_code) = LOWER(?)")
        params.append(request.set_code)
    if request.rarity:
        where_clauses.append("LOWER(rarity) = LOWER(?)")
        params.append(request.rarity)
    if request.names:
        placeholders = ",".join(["?"] * len(request.names))
        where_clauses.append(f"name COLLATE NOCASE IN ({placeholders})")
        params.extend(request.names)
    where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    offset = (request.page - 1) * request.per_page

    total = await run_db(count_cards, where_sql, tuple(params))
    results = await run_db(query_cards, offset, request.per_page, where_sql, tuple(params))
    return CardListResponse(
        total=total,
        page=request.page,
        per_page=request.per_page,
        results=results
    )


@app.post("/cards/names", response_model=List[CardBase])
async def get_cards_by_names_endpoint(request: CardNamesRequest):
    results = await run_db(get_cards_by_names, request.names)
    return results


@app.post("/cards/resolve-deck", response_model=ResolveDeckResponse)
async def resolve_deck_endpoint(request: ResolveDeckRequest):
    # CPU-bound but light; run sync in thread for consistency
    result = await run_db(resolve_deck, request.deck)
    return result


@app.post("/simulate/by-names", response_model=SimulationResponse)
async def simulate_by_names(request: SimulationByNamesRequest):
    # Resolve deck and derive counts
    resolved = await run_db(resolve_deck, request.deck)
    game_state = GameState(card_counts=resolved.derived_counts)

    # Collect oracle texts for selected names (if provided)
    oracle_texts = None
    if request.oracle_names:
        lower = {n.lower() for n in request.oracle_names}
        oracle_texts = [
            rc.card.oracle_text for rc in resolved.resolved
            if rc.card.name and rc.card.name.lower() in lower and rc.card.oracle_text
        ]

    result = monte_carlo_probability(
        game_state=game_state,
        category=request.category,
        num_simulations=request.num_simulations,
        random_seed=request.random_seed,
        oracle_texts=oracle_texts
    )
    return SimulationResponse(**result)


@app.post("/simulate/by-card", response_model=SimulationResponse)
async def simulate_by_card(request: SimulationByCardRequest):
    # Resolve deck and compute successes (sum counts for target names)
    resolved = await run_db(resolve_deck, request.deck)
    total_cards = sum(resolved.derived_counts.values())
    target_set = {n.lower() for n in request.target_names}
    successes = sum(rc.count for rc in resolved.resolved if rc.card.name and rc.card.name.lower() in target_set)

    # Determine categories of target cards for tutor matching
    from .deck_service import pick_category
    target_categories = list({pick_category(rc.card.type_line or "") for rc in resolved.resolved if rc.card.name and rc.card.name.lower() in target_set})

    # Collect oracle texts for selected names (if provided)
    oracle_texts = None
    if request.oracle_names:
        lower = {n.lower() for n in request.oracle_names}
        oracle_texts = [
            rc.card.oracle_text for rc in resolved.resolved
            if rc.card.name and rc.card.name.lower() in lower and rc.card.oracle_text
        ]

    result = monte_carlo_probability_for_successes(
        total_cards=total_cards,
        successes=successes,
        num_simulations=request.num_simulations,
        random_seed=request.random_seed,
        oracle_texts=oracle_texts,
        target_categories=target_categories
    )

    # Adapt to SimulationResponse schema
    result.update({
        'game_state': str(GameState(card_counts=resolved.derived_counts)),
        'category': 'specific_cards'
    })
    return SimulationResponse(**result)

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
    endpoint_start = time.time()
    
    # Log request start
    total_cards = sum(request.deck.card_counts.values())
    logger.info(f"SIMULATION REQUEST: category='{request.category}', deck_size={total_cards}, simulations={request.num_simulations:,}, deck={dict(request.deck.card_counts)}")
    
    try:
        # Validate deck configuration
        if not request.deck.card_counts:
            logger.error(f"VALIDATION ERROR: Empty card counts - duration={time.time() - endpoint_start:.4f}s")
            raise HTTPException(
                status_code=400,
                detail="Card counts cannot be empty"
            )
        
        # Validate all counts are positive
        for category, count in request.deck.card_counts.items():
            if count < 0:
                logger.error(f"VALIDATION ERROR: Negative count for '{category}': {count} - duration={time.time() - endpoint_start:.4f}s")
                raise HTTPException(
                    status_code=400,
                    detail=f"Card count for '{category}' cannot be negative: {count}"
                )
        
        # Validate category exists in deck
        if request.category not in request.deck.card_counts:
            available_categories = list(request.deck.card_counts.keys())
            logger.error(f"VALIDATION ERROR: Category '{request.category}' not in deck, available={available_categories} - duration={time.time() - endpoint_start:.4f}s")
            raise HTTPException(
                status_code=400,
                detail=f"Category '{request.category}' not found in deck. Available categories: {available_categories}"
            )
        
        # Create game state and run simulation
        game_state = GameState(card_counts=request.deck.card_counts)
        theoretical_prob = game_state.probability(request.category)
        
        sim_start = time.time()
        result = monte_carlo_probability(
            game_state=game_state,
            category=request.category,
            num_simulations=request.num_simulations,
            random_seed=request.random_seed,
            oracle_texts=request.oracle_texts
        )
        sim_duration = time.time() - sim_start
        endpoint_duration = time.time() - endpoint_start
        
        # Log complete results in single statement
        logger.info(f"SIMULATION COMPLETE: result={result['probability']:.4f} ({result['probability']*100:.2f}%), theoretical={theoretical_prob:.4f} ({theoretical_prob*100:.2f}%), error={result['error_percentage']:.3f}%, hits={result['hits']:,}/{request.num_simulations:,}, performance={result['simulations_per_second']:,.0f} sims/sec, timing=sim:{sim_duration:.4f}s total:{endpoint_duration:.4f}s, status=200")
        
        # Return structured response
        return SimulationResponse(**result)
        
    except HTTPException as e:
        endpoint_duration = time.time() - endpoint_start
        logger.error(f"REQUEST FAILED: status={e.status_code}, error='{e.detail}', duration={endpoint_duration:.4f}s")
        raise e
    except ValueError as e:
        endpoint_duration = time.time() - endpoint_start
        logger.error(f"VALUE ERROR: error='{str(e)}', duration={endpoint_duration:.4f}s")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        endpoint_duration = time.time() - endpoint_start
        logger.error(f"INTERNAL ERROR: error='{str(e)}', duration={endpoint_duration:.4f}s")
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
    endpoint_start = time.time()
    
    # Log request start
    total_cards = lands + non_lands
    logger.info(f"QUICK LAND SIMULATION: lands={lands}, non_lands={non_lands}, total={total_cards}, ratio={lands/total_cards:.3f}, simulations={num_simulations:,}")
    
    try:
        # Validate parameters
        if lands < 0 or non_lands < 0:
            logger.error(f"VALIDATION ERROR: Negative card counts lands={lands} non_lands={non_lands} - duration={time.time() - endpoint_start:.4f}s")
            raise HTTPException(
                status_code=400,
                detail="Card counts cannot be negative"
            )
        
        if not (1 <= total_cards <= 250):
            logger.error(f"VALIDATION ERROR: Invalid total cards {total_cards} (must be 1-250) - duration={time.time() - endpoint_start:.4f}s")
            raise HTTPException(
                status_code=400,
                detail="Total cards must be between 1 and 250"
            )
        
        if not (100 <= num_simulations <= 1000000):
            logger.error(f"VALIDATION ERROR: Invalid simulation count {num_simulations} (must be 100-1,000,000) - duration={time.time() - endpoint_start:.4f}s")
            raise HTTPException(
                status_code=400,
                detail="Number of simulations must be between 100 and 1,000,000"
            )
        
        # Create game state and run simulation
        card_counts = {"land": lands, "non_land": non_lands}
        game_state = GameState(card_counts=card_counts)
        theoretical_prob = game_state.probability("land")
        
        sim_start = time.time()
        result = monte_carlo_probability(
            game_state=game_state, 
            category="land", 
            num_simulations=num_simulations
        )
        sim_duration = time.time() - sim_start
        endpoint_duration = time.time() - endpoint_start
        
        # Log complete results in single statement
        logger.info(f"QUICK SIMULATION COMPLETE: result={result['probability']:.4f} ({result['probability']*100:.2f}%), theoretical={theoretical_prob:.4f} ({theoretical_prob*100:.2f}%), error={result['error_percentage']:.3f}%, hits={result['hits']:,}/{num_simulations:,}, performance={result['simulations_per_second']:,.0f} sims/sec, timing=sim:{sim_duration:.4f}s total:{endpoint_duration:.4f}s, status=200")
        
        return SimulationResponse(**result)
        
    except HTTPException as e:
        endpoint_duration = time.time() - endpoint_start
        logger.error(f"QUICK SIMULATION FAILED: status={e.status_code}, error='{e.detail}', duration={endpoint_duration:.4f}s")
        raise e
    except ValueError as e:
        endpoint_duration = time.time() - endpoint_start
        logger.error(f"VALUE ERROR: error='{str(e)}', duration={endpoint_duration:.4f}s")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        endpoint_duration = time.time() - endpoint_start
        logger.error(f"INTERNAL ERROR: error='{str(e)}', duration={endpoint_duration:.4f}s")
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
