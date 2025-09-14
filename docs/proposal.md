## Problem

We will investigate estimating the probability of drawing a specific card (or combination of cards) from a shuffled Magic: The Gathering (MTG) deck as the game state evolves. Unlike static, one-shot draw calculators, real MTG games involve actions that change the deck and draw process (e.g., mulligans, scry, tutors/fetches, cantrips, and continuous effects). This makes the probability dynamic and state‑dependent.

Why this is interesting:
- Strategic Advantage: Accurate draw probabilities inform in‑game decisions and risk management.
- Scientific Contribution: Modeling a high‑variance, rule‑rich system pushes probabilistic simulation and evaluation techniques beyond simple analytical cases.

## Background Reading

- Quinn, T. (2021). “Monte Carlo & Magic: the Gathering.” [Blog post](https://thquinn.github.io/blog.html?post=6).
- Jagajanian, V., et al. (2021). “Monte Carlo Tree Search Variations.” [Course notes](https://www.cs.hmc.edu/jagajanian/cs151/).
- Esche, A. (2018). “Mathematical programming and Magic: The Gathering.” [Thesis](https://huskiecommons.lib.niu.edu/allgraduate-thesesdissertations/3903/).

These sources provide context on Monte Carlo methods applied to MTG and related search/optimization ideas. We will also use standard analytical probability for baseline checks (e.g., hypergeometric distribution in static cases).

## Data

- Primary data: Synthetic datasets generated from Monte Carlo simulations of MTG scenarios.
- Representation: A unified, explicit schema for decks, card effects, and transient game state to drive reproducible simulations.
- Reproducibility: Fixed random seeds and configuration snapshots for each scenario; results and any aggregated statistics will be saved under the project’s data directory.

No external datasets are required; scenarios are specified and simulated to produce the necessary traces and outcome counts.

## Method/Algorithm

- Core approach: Monte Carlo simulation to estimate probabilities of drawing target card(s) across evolving game states.
- Modeled actions: Mulligans, scry, tutors/fetches, cantrips, and effects that modify draws and deck composition, executed according to scenario definitions.
- Estimation: Frequencies of success across independent trials, with reported confidence intervals.
- Baseline/validation: Compare against analytical hypergeometric results in static settings to verify correctness.

Use of existing implementations: We extend prior MTG draw‑probability calculators conceptually by explicitly modeling dynamic, stateful actions rather than only static, one‑draw cases.

Potential improvements (within scope): expanded action library to cover additional common MTG interactions.

## Evaluation Plan

Qualitative outputs (expected):
- Line/curve plots of draw probability vs. turn or action sequence length.
- Histograms of estimated probabilities across deck variants or mulligan strategies.
- Scenario summaries highlighting the impact of scry, tutors, and cantrips on success rates.

Quantitative analysis (expected):
- Accuracy vs. analytical baselines in static cases (e.g., mean absolute error).
- Precision of estimates via 95% confidence intervals for Bernoulli proportions across runs.
- Convergence diagnostics: probability estimate vs. number of simulations; time per effective sample.

Success criteria:
- Matches analytical baselines within confidence bounds on static scenarios.
- Stable, reproducible estimates with well‑calibrated intervals on dynamic scenarios.
- Clear, interpretable plots and tables enabling strategy comparison across actions and deck choices.
