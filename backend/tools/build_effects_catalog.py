#!/usr/bin/env python
"""
Generate entries for backend/data/effects.json using the OpenAI Responses API.

Usage:
    python backend/tools/build_effects_catalog.py --cards-file data/cards_for_effects.json

The cards file should be JSON containing a list of objects with at least:
    [{"name": "Brainstorm", "oracle_text": "Draw three cards..."}]

The script appends/updates entries in effects.json without overwriting existing ones.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Dict, Iterable, List

from dotenv import load_dotenv
from openai import OpenAI


PROMPT_TEMPLATE = """You are helping build a deterministic simulation for Magic: The Gathering.
For the card below, emit a JSON array describing the card's effects using only the allowed actions.
Return ONLY JSON (no prose), following this structure:

[
  {"action": "draw", "count": 3},
  {"action": "topdeck_from_hand", "count": 2}
]

Allowed actions (all lowercase):
- draw:    {"action": "draw", "count": N}
- mill:    {"action": "mill", "count": N}
- shuffle: {"action": "shuffle"}
- scry:    {"action": "scry", "count": N, "strategy": "keep_lands|keep_nonlands|default"}
- tutor:   {"action": "tutor", "target": "any|land|artifact|...","shuffle": true/false}
- topdeck_from_hand: {"action": "topdeck_from_hand", "count": N}
- choice/modal effects:
    {"action": "choice", "options": [[{...}], [{...}]], "strategy": "prefer_draw|prefer_mill"}
- sequence helpers:
    {"action": "sequence", "steps": [{...}, {...}]}

Card name: "{name}"
Oracle text:
{oracle_text}

Output JSON array now:
"""


def load_cards_from_file(path: Path) -> List[Dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list of card objects")
    for entry in data:
        if "name" not in entry or "oracle_text" not in entry:
            raise ValueError("Each card entry must include 'name' and 'oracle_text'")
    return data


def extract_text(response) -> str:
    """
    OpenAI Responses API wrapper: extract the first text output chunk.
    The SDK returns nested structures; this normalizes them.
    """
    for item in response.output:
        if hasattr(item, "content"):
            for block in item.content:
                if getattr(block, "type", None) == "output_text":
                    return block.text
    raise ValueError("No text content returned by model")


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate backend/data/effects.json using OpenAI.")
    parser.add_argument(
        "--cards-file",
        required=True,
        type=Path,
        help="JSON file containing [{'name': ..., 'oracle_text': ...}, ...]",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model name (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        help="Seconds to sleep between requests (default: 1.0)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate entries even if the card already exists in effects.json",
    )
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY missing. Add it to your .env or environment.")

    cards = load_cards_from_file(args.cards_file)
    effects_path = Path("backend/data/effects.json")
    effects_path.parent.mkdir(parents=True, exist_ok=True)
    catalog: Dict[str, List[dict]] = {}
    if effects_path.exists():
        catalog = json.loads(effects_path.read_text(encoding="utf-8"))

    client = OpenAI(api_key=api_key)
    updated = False
    for card in cards:
        key = card["name"]
        if not args.overwrite and key in catalog:
            print(f"Skipping {key} (already present)")
            continue

        prompt = PROMPT_TEMPLATE.format(**card)
        print(f"Requesting effects for {key}...")
        response = client.responses.create(
            model=args.model,
            input=prompt,
            temperature=0.2,
        )
        text = extract_text(response)
        try:
            actions = json.loads(text)
        except json.JSONDecodeError as exc:
            print(f"Failed to parse JSON for {key}: {exc}")
            continue
        catalog[key] = actions
        updated = True
        time.sleep(args.sleep)

    if updated:
        effects_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
        print(f"Wrote {effects_path}")
    else:
        print("No changes made.")


if __name__ == "__main__":
    main()

