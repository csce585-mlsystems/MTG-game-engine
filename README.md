# Project Title  
## MTG-game-engine

## Group Info
cyrusnj@email.sc.edu, jmr40@email.sc.edu,  

## Project Summary/Abstract  
### This project aims to explore machine learning (ML) applications in complex scenarios by developing a Magic: The Gathering (MTG) game engine. The core of the project is to create a tool that can accurately predict the probability of a player drawing a specific card from their deck. This engine will leverage data from various simulated game states, helping them optimize their strategies. Ultimately, the goal is to demonstrate the power of ML in predicting outcomes within highly variable systems, using MTG as a compelling case study.

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
- Empirical validation against analytical baselines (e.g., hypergeometric cases) with reported confidence intervals for estimates.  
- Reproducible scripts and seeds to run large batches of simulations and aggregate scenario-level results.  

## References  
Quinn, T. (2021). Monte Carlo & Magic: the Gathering. https://thquinn.github.io/blog.html?post=6. https://thquinn.github.io/blog.html?post=6 
Jagajanian, V., & others. (2021). Monte Carlo Tree Search Variations. https://www.cs.hmc.edu/ jagajanian/cs151/. https://www.cs.hmc.edu/ jagajanian/cs151/ 
Esche, A. (2018). Mathematical programming and Magic: The Gathering [Northern Illinois University]. https://huskiecommons.lib.niu.edu/allgraduate-thesesdissertations/3903/ 

---

# < The following is only applicable for the final project submission >  

## Dependencies  
### Include all dependencies required to run the project. Example:  
- Python 3.11  
- Ubuntu 22.04  

For Python users: Please use [uv](https://docs.astral.sh/uv/) as your package manager instead of `pip`. Your repo must include both the `uv.lock` and `pyproject.toml` files.  

## Directory Structure  
Example:  
```
|- data (mandatory)
|- src (mandatory)
|   |- model.py
|   |- example.py
|- train.py
|- run.py (mandatory)
|- result.py (mandatory)
```

⚠️ Notes:  
- All projects must include the `run.<ext>` script (extension depends on your programming language) at the project root directory. This is the script users will run to execute your project.  
- If your project computes/compares metrics such as accuracy, latency, or energy, you must include the `result.<ext>` script to plot the results.  
- Result files such as `.csv`, `.jpg`, or raw data must be saved in the `data` directory.  

## How to Run  
- Include all instructions (`commands`, `scripts`, etc.) needed to run your code.  
- Provide all other details a computer science student would need to reproduce your results.  

Example:  
- Download the [DATASET](dataset_link)
  ```bash
  wget <URL_of_file>
  ```

- To train the model, run:  
  ```bash
  python train.py
  ```  
- To plot the results, run:  
  ```bash
  python result.py
  ```  

## Demo  
- All projects must include video(s) demonstrating your project.  
- Please use annotations/explanations to clarify what is happening in the demo.  
---
