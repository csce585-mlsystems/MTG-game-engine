"""
FastAPI endpoints for MTG land simulation
"""
from fastapi import FastAPI, HTTPException, Request, Response, Query #Added Response, Query
import time
import logging
from typing import Callable, List, Optional #Added List, Optional
import json

from .models import SimulationRequest, SimulationResponse, HealthResponse
from .simulation import GameState, monte_carlo_probability
from datetime import datetime #Added Datetime
import sqlite3
from pydantic import BaseModel
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os

#Database Path from Environment Variable or Default
DB_PATH = os.environ.get("SCRYFALL_DB_PATH", "data/scryfall.db")
executor = ThreadPoolExecutor(max_workers = 4)
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

#Pydantic Response Models
class CardBase(BaseModel):
    id: str
    oracle_id: Optional[str] = None
    name: Optional[str] = None
    set_code: Optional[str] = None
    set_name: Optional[str] = None
    collector_number: Optional[str] = None
    rarity: Optional[str] = None
    mana_cost: Optional[str] = None
    cmc: Optional[float] = None
    type_line: Optional[str] = None
    oracle_text: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    colors: Optional[dict] = None
    color_identity: Optional[dict] = None
    image_uris: Optional[dict] = None

class CardListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    results: List[CardBase]

#DB Helpers

def _open_conn():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"DB not found at {DB_PATH}. Run Importer First")
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # Use named access for rows to match usage elsewhere (row["id"], row.keys(), etc.)
    conn.row_factory = sqlite3.Row
    return conn
def _row_to_card(row: sqlite3.Row) -> CardBase:
    def _maybe_load(val):
        if val is None:
            return None
        try:
            return json.loads(val)
        except Exception:
            return val
    return CardBase(
        id = row["id"],
        oracle_id = row["oracle_id"],
        name = row["name"],
        set_code = row["set_code"],
        set_name = row["set_name"],
        collector_number = row["collector_number"],
        rarity = row["rarity"],
        mana_cost = row["mana_cost"],
        cmc = row["cmc"],
        type_line = row["type_line"],
        oracle_text = row["oracle_text"],
        power = row["power"],
        toughness = row["toughness"],
        colors = _maybe_load(row["colors"]) if "colors" in row.keys() else None,
        color_identity = _maybe_load(row["color_identity"]) if "color_identity" in row.keys() else None,
        image_uris = _maybe_load(row["image_uris"])if "image_uris" in row.keys() else None,                        
    )

async def run_db(fn, *args, **kwargs):
    loop = asyncio.get_event_loop()
def _count_cards(where_clause: str = "", params: tuple = ()):
    conn = _open_conn()
    sql = "SELECT COUNT(*) as count FROM cards" + where_clause
    cur = conn.execute(sql, params)
    return cur.fetchone()["count"]
def _query_cards(offset: int, limit:int, where_clause: str = "", params: tuple = (), order_by: str = "name"):
    conn = _open_conn()
    try:
        # Whitelist acceptable columns for ordering to avoid SQL injection
        ALLOWED_ORDER_COLUMNS = {"name", "set_name", "set_code", "collector_number", "rarity", "cmc"}
        if order_by not in ALLOWED_ORDER_COLUMNS:
            order_by = "name"

        sql = f"""
            SELECT id, oracle_id, name, set_code, set_name, collector_number,
            rarity, mana_cost, cmc, type_line, oracle_text, power, toughness,
            colors, color_identity, image_uris
            FROM cards
            {where_clause}
            ORDER BY {order_by} COLLATE NOCASE
            LIMIT ? OFFSET ?
            """
        cur = conn.execute(sql, params + (limit, offset))
        rows = cur.fetchall()
        return [_row_to_card(r) for r in rows]
    finally:
        conn.close()
def _get_card_by_id(card_id: str):
    conn = _open_conn()
    try:
        sql = """
        SELECT id, oracle_id, name, set_code, set_name, collector_number,
        rarity, mana_cost, cmc, type_line, oracle_text, power, toughness,
        colors, color_identity, image_uris
        FROM cards
        WHERE id = ?
        """
        cur = conn.execute(sql, (card_id,))
        row = cur.fetchone()
        if not row:
            return None
        return _row_to_card(row)
    finally:
        conn.close()
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

@app.get("/health")
async def health():
    return {"status": "ok", "db_path": DB_PATH}

@app.get("/cards", response_model = CardListResponse)
async def list_cards(
    q: Optional[str] = Query(None, description = "Search query for card name or text"),
    set_code: Optional[str] = Query(None, description = "Filter by set code"),
    rarity: Optional[str] = Query(None, description = "Filter by card rarity"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=250),
):
    where_clauses = []
    params = []
    if q:
        where_clauses.append("name LIKE ?")
        params.append(f"%{q}%")
    if set_code:
        where_clauses.append("LOWER(set_code) = LOWER(?)")
        params.append(set_code)
    if rarity:
        where_clauses.append("LOWER(rarity) = LOWER(?)")
        params.append(rarity)
        where_sql = ("WHERE" + " AND ".join(where_clauses)) if where_clauses else ""
        offset = (page -1) *per_page

        total = await run_db(_count_cards, where_sql, tuple(params))
        results = await run_db(_query_cards, offset, per_page, where_sql, tuple(params))
    return CardListResponse(
        total=total,
        page=page,
        per_page=per_page,
        results=results
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
            random_seed=request.random_seed
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
