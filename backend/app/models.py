"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Union, List, Any


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
    oracle_texts: Optional[List[str]] = Field(default=None, description="Optional list of oracle texts whose effects should be applied during simulation")
    

# Effects and deck resolution (defined early to avoid forward-ref issues)
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
    colors: Optional[List[str]] = None
    color_identity: Optional[List[str]] = None
    image_uris: Optional[Dict[str, Any]] = None


class CardEffectHint(BaseModel):
    type: str  # e.g., "tutor", "draw", "mill"
    target: Optional[str] = None  # e.g., "artifact" for tutor
    count: Optional[int] = None   # e.g., draws=2, mill=20


class DeckNameCount(BaseModel):
    name: str
    count: int = Field(ge=1)


class ResolveDeckRequest(BaseModel):
    deck: List[DeckNameCount]


class ResolvedCard(BaseModel):
    card: CardBase
    count: int
    effects: List[CardEffectHint] = []


class ResolveDeckResponse(BaseModel):
    resolved: List[ResolvedCard]
    unresolved: List[str]
    derived_counts: Dict[str, int]


class SimulationByNamesRequest(BaseModel):
    """Simulate by passing a decklist of names; server resolves counts and effects."""
    deck: List['DeckNameCount']
    category: str
    num_simulations: int = Field(default=10000, ge=100, le=1000000)
    random_seed: Optional[int] = None
    oracle_names: Optional[List[str]] = None  # names of cards whose oracle effects to apply


class SimulationByCardRequest(BaseModel):
    """Simulate probability of drawing specific card(s) by name from a decklist of names."""
    deck: List['DeckNameCount']
    target_names: List[str] = Field(min_items=1)
    num_simulations: int = Field(default=10000, ge=100, le=1000000)
    random_seed: Optional[int] = None
    oracle_names: Optional[List[str]] = None

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
    db_path: str


class CardListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    results: List[CardBase]


class CardSearchRequest(BaseModel):
    """Request body for card search endpoint"""
    q: Optional[str] = None
    set_code: Optional[str] = None
    rarity: Optional[str] = None
    names: Optional[List[str]] = None  # exact name filter (case-insensitive)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=25, ge=1, le=250)


class CardNamesRequest(BaseModel):
    """Request body to fetch cards by exact names (case-insensitive). No pagination."""
    names: List[str] = Field(min_items=1, description="List of card names to fetch")



