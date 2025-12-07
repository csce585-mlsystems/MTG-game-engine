# MTG-game-engine  

## Group Info
cyrusnj@email.sc.edu, jmr40@email.sc.edu, grimesjp@email.sc.edu 

## Project Summary/Abstract  
### This project aims to explore machine learning (ML) applications in complex scenarios by developing a Magic: The Gathering (MTG) game engine. The core of the project is to create a tool that can accurately predict the probability of a player drawing a specific card from their deck. This engine will leverage data from various simulated game states, helping them optimize their strategies. Ultimately, the goal is to demonstrate the power of ML in predicting outcomes within highly non-deterministic variable systems, using MTG as a compelling case study.

## Problem Description  
The problem is to calculate the probability of drawing a specific card or combination of cards from a shuffled Magic: The Gathering deck. This can be complex due to factors like deck size, shuffling, and cards that alter deck composition or allow for card selection. The core challenge is modeling and predicting these probabilities accurately across various game states.  
- Motivation  
  - Strategic Advantage: Understanding card draw probabilities gives players a higher chance at winning. It allows them to make more informed decisions about when to take risks and what cards to play.
  - Deck Optimization: A predictive engine can help players create and tune their decks. By simulating thousands of games, the tool can identify cards that are either over or underperforming.
  - Scientific and Technical Contribution: The development of a sophisticated MTG game engine with ML-driven prediction capabilities is a valuable research contribution. It pushes the boundaries of ML in modeling complex, non-deterministic systems with a large state space. The project could yield insights applicable to other areas requiring probabilistic modeling, such as financial markets, logistics, or other complex strategy games  
- Challenges  
  - Game State Complexity: The probability of drawing a card changes with every action taken in a game. A model must account for the state of the board and any effects that might modify the deck, making it a highly dynamic problem.  
  - Data Formatting: While there is a vast amount of MTG data online, it's often not in a format that's easy to use for a predictive model. Building a comprehensive data format that includes all game states and actions would take lots of work to accurately hold the game state.  
  - Card Interactions: Many MTG cards have unique and complex interactions with one another. A robust model must be able to accurately represent these interactions, including keywords, triggered abilities, and continuous effects, which can drastically change card probabilities. 

## Contribution  
- [`Extension of existing work`], [`Novel contribution`]  
We extend prior MTG draw‑probability calculators by modeling dynamic game states and card interactions, using Monte Carlo simulations to estimate probabilities under realistic play patterns. Our main contributions are:  
- Monte Carlo simulation engine for MTG card-draw probabilities across evolving game states (e.g., mulligans, scry, tutors/fetches, cantrips, and effects that modify draws).  
- Unified, explicit schema for representing decks, card effects, and transient game state to drive simulations consistently.  

## References  
Quinn, T. (2021). Monte Carlo & Magic: the Gathering. https://thquinn.github.io/blog.html?post=6. https://thquinn.github.io/blog.html?post=6
 
Jagajanian, V., & others. (2021). Monte Carlo Tree Search Variations. https://www.cs.hmc.edu/ jagajanian/cs151/. https://www.cs.hmc.edu/ jagajanian/cs151/

Esche, A. (2018). Mathematical programming and Magic: The Gathering [Northern Illinois University]. https://huskiecommons.lib.niu.edu/allgraduate-thesesdissertations/3903/

## Dependencies  
### Runtime and tooling needed to run this project end-to-end:
- **Docker** (Desktop or Engine) with **Docker Compose v2**
- **Python 3.11** (only required if you want to run the backend directly without Docker)
- Stable internet connection (first run downloads Scryfall bulk data and, optionally, calls OpenAI)
- Optional: OpenAI API key (for LLM-based effects enrichment)

## Directory Structure  
Key directories and files:
```
|- backend
|   |- app
|   |   |- api.py            # FastAPI application and HTTP endpoints
|   |   |- simulation.py     # Monte Carlo simulation engine
|   |   |- effects.py        # Card effects catalog + LLM + deterministic fallback
|   |   |- deck_service.py   # Deck resolution and effect hint aggregation
|   |   |- repository.py     # SQLite/Scryfall DB access layer
|   |   |- scryfall_import.py# Scryfall bulk/search importer for card data
|   |- data
|       |- effects.json      # Seed catalog of card effects (extended at runtime)
|       |- scryfall.db       # Populated automatically on first Docker run
|- frontend
|   |- src
|   |   |- App.js, components/*  # React UI for simulating and visualizing results
|- Dockerfile               # Backend container image definition
|- docker-compose.yml       # Orchestration for backend + frontend
|- README.md                # Project documentation (this file)
|- .env                     # Environment variables (OPENAI_API_KEY, etc.)
```

⚠️ Notes:  
- The primary entrypoint for this project is `docker compose up`, which starts both backend and frontend.

## How to Run  
End-to-end setup for a fresh clone:

1. **Clone the repository**
   ```bash
   git clone https://github.com/csce585-mlsystems/MTG-game-engine.git
   cd MTG-game-engine
   ```

2. **(Optional but recommended) Create `.env` with your OpenAI key**
   ```bash
   echo "OPENAI_API_KEY=sk-..." > .env
   ```
   - If `OPENAI_API_KEY` is not set, the engine still works using deterministic regex-based fallbacks in `effects.py`, but new cards will not get LLM-enriched effects.

3. **Start backend and frontend via Docker Compose**
   ```bash
   docker compose up --build
   ```
   - On first run, the backend will:
     - Download Scryfall bulk data and initialise `backend/data/scryfall.db`.
     - Start the FastAPI server at `http://localhost:8000`.
   - The frontend will build and start at `http://localhost:3000`.

4. **Interact with the system**
   - Backend API docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`
   - Frontend UI: `http://localhost:3000`
   - Typical workflow from the UI:
     - Search for cards and build a deck.
     - Resolve the deck (imports any missing cards via Scryfall).
     - Run simulations (by category, by specific card names, or full-state).
     - NOTE: see simulation for more details

5. **Running backend without Docker (optional)**
   ```bash
   cd backend
   pip install -r requirements.txt
   export OPENAI_API_KEY=sk-...    # optional
   uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
   ```

## User Testing
To evaluate the practical utility of our MTG game engine, we conducted a user testing session with a group of players of varying experience levels.

### Results and Observations
The newer players showed the most significant improvement in gameplay decisions. One participant, who had been playing for only 3 months, was piloting a red aggro deck with 20 lands and 40 spells. Before using the engine, they were unsure whether to mulligan a hand with only one land. After running a quick simulation showing they had a 68% chance of drawing a second land by turn 2, they confidently kept the hand and won the game by curving out perfectly.

Another newer player was struggling with understanding when to use their scry effects optimally. The engine helped them visualize how scrying to the bottom of their library affected their probability of drawing specific answers. During the actual game, they used their "Opt" spell more strategically, scrying away cards that wouldn't help in the current matchup, which directly led to them drawing their key removal spell on the turn they needed it.

The experienced players also found value in the tool, particularly for deck tuning. One veteran player discovered through simulation that their deck had a lower-than-expected probability of drawing their win condition by turn 6, which prompted them to adjust their deck composition between matches. However, the impact was less dramatic since experienced players already had strong intuitive understanding of probabilities.

### Key Findings
- **Newer players benefited most**: The engine helped bridge the knowledge gap for players who lacked the experience to intuitively assess draw probabilities. They made more informed decisions about mulligans, resource management, and when to commit to certain strategies.
- **Educational value**: Several participants reported that using the engine helped them develop better intuition about deck composition and probability assessment
- **Performance**: The engine's simulation results were fast enough to be useful during actual gameplay breaks, with most simulations completing in milliseconds.

This real-world testing validated that our engine provides tangible value to players, particularly those still learning the game, by making complex probabilistic calculations accessible and actionable during actual gameplay.

## Demo  
[Demo Video](https://youtu.be/KEDtvnTC598)
