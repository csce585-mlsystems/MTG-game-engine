import os
import sqlite3
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

from .models import CardBase

# Database configuration
DB_PATH = os.environ.get("SCRYFALL_DB_PATH", "data/scryfall.db")
executor = ThreadPoolExecutor(max_workers=4)


def _open_conn() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"DB not found at {DB_PATH}. Run Importer First")
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _maybe_load(val):
    if val is None:
        return None
    try:
        return json.loads(val)
    except Exception:
        return val


def _row_to_card(row: sqlite3.Row) -> CardBase:
    return CardBase(
        id=row["id"],
        oracle_id=row["oracle_id"],
        name=row["name"],
        set_code=row["set_code"],
        set_name=row["set_name"],
        collector_number=row["collector_number"],
        rarity=row["rarity"],
        mana_cost=row["mana_cost"],
        cmc=row["cmc"],
        type_line=row["type_line"],
        oracle_text=row["oracle_text"],
        power=row["power"],
        toughness=row["toughness"],
        colors=_maybe_load(row["colors"]) if "colors" in row.keys() else None,
        color_identity=_maybe_load(row["color_identity"]) if "color_identity" in row.keys() else None,
        image_uris=_maybe_load(row["image_uris"]) if "image_uris" in row.keys() else None,
    )


def count_cards(where_clause: str = "", params: Tuple = ()) -> int:
    conn = _open_conn()
    try:
        sql = "SELECT COUNT(*) as count FROM cards" + where_clause
        cur = conn.execute(sql, params)
        return cur.fetchone()["count"]
    finally:
        conn.close()


def query_cards(
    offset: int,
    limit: int,
    where_clause: str = "",
    params: Tuple = (),
    order_by: str = "name",
) -> List[CardBase]:
    conn = _open_conn()
    try:
        allowed = {"name", "set_name", "set_code", "collector_number", "rarity", "cmc"}
        if order_by not in allowed:
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


async def run_db(fn, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, lambda: fn(*args, **kwargs))


def get_cards_by_names(names: List[str]) -> List[CardBase]:
    if not names:
        return []
    conn = _open_conn()
    try:
        placeholders = ",".join(["?"] * len(names))
        sql = f"""
            SELECT id, oracle_id, name, set_code, set_name, collector_number,
                   rarity, mana_cost, cmc, type_line, oracle_text, power, toughness,
                   colors, color_identity, image_uris
            FROM cards
            WHERE name COLLATE NOCASE IN ({placeholders})
        """
        cur = conn.execute(sql, tuple(names))
        rows = cur.fetchall()
        return [_row_to_card(r) for r in rows]
    finally:
        conn.close()


def get_cards_by_names_map(names: List[str]) -> dict:
    """
    Return a mapping of lowercase name -> CardBase.
    If multiple printings exist, an arbitrary one is chosen.
    """
    results = get_cards_by_names(names)
    mapping = {}
    for c in results:
        if c.name:
            key = c.name.lower()
            if key not in mapping:
                mapping[key] = c
    return mapping