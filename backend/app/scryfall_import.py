"""

"""

import argparse
import json
import os
import sqlite3
import time
from urllib.parse import urlparse
import requests

try:
    import ijson
    IJSON_AVAILABLE = True
except Exception:
    IJSON_AVAILABLE = False

SCRYFALL_BULK_URL = "https://api.scryfall.com/bulk-data"
"""https://data.scryfall.io/default-cards/default-cards-20251113100901.json"""

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    oracle_id TEXT,
    name TEXT,
    set_code TEXT,
    collector_number TEXT,
    mana_cost TEXT,
    cmc REAL,
    type_line TEXT,
    oracle_text TEXT,
    power TEXT,
    toughness TEXT,
    colors TEXT,
    color_identity TEXT,
    image uris TEXT,
    );
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name);
CREATE INDEX IF NOT EXISTS idx_cards_oracle ON cards(oracle_id);
"""

def get_bulk_download_url(kind="default_cards"):
    resp = requests.get(SCRYFALL_BULK_URL, timeout = 30)
    resp.raise_for_status()
    data = resp.json()
    for entry in data.get("data",[]):
        if entry.get("type") == kind:
            return entry.get("download_uri"), entry
    raise RuntimeError(f"Could not find bulk data of kind {kind}")

def stream_download_and_insert(db_path,dounwload_url):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    cur = conn.cursor()
    cur.executescript(CREATE_TABLE_SQL)
    conn.commit()

    with requests.get(dounwload_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        if IJSON_AVAILABLE:
            parser = ijson.items(r.raw,"item")
            batch = []
            BATCH_SIZE = 1000
            count = 0
            for card in parser:
                row = card_to_row(card)
                batch.append(row)
                if len(batch) >= BATCH_SIZE:
                    insert_batch(cur,batch)
                    conn.commit()
                    count += len(batch)
                    batch = []
            if batch:
                insert_batch(cur,batch)
                conn.commit()
                count += len(batch)
        else:
            text = r.content
            cards = json.loads(text)
            batch = []
            for idx, card in enumerate(cards):
                batch.append(card_to_row(card))
                if len(batch) >= 1000:
                    insert_batch(cur,batch)
                    conn.commit()
                    batch = []
            if batch:
                insert_batch(cur,batch)
def card_to_row(card):
    def j(v):
        try:
            return json.dumps(v, ensure_ascii=False)
        except Exception:
            return None
    return (
        card.get("id"),
        card.get("oracle_id"),
        card.get("name"),
        card.get("set"),               # set_code
        card.get("set_name"),         # set_name
        card.get("collector_number"),
        card.get("rarity"),
        card.get("mana_cost"),
        card.get("cmc"),
        card.get("type_line"),
        card.get("oracle_text"),
        card.get("power"),
        card.get("toughness"),
        j(card.get("colors")),
        j(card.get("color_identity")),
    )
def insert_batch(cur,batch):
    cur.executemany("""
        INSERT OR REPLACE INTO cards(
            id, oracle_id, name, set_code, set_name, collector_number, rarity, mana_cost, cmc, type_line,
            oracle_text, power, toughness, colors, color_identity, image_uris
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, batch)
def search_and_insert(db_path,query,max_pages=5):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(CREATE_TABLE_SQL)
    conn.commit()

    url = "https://api.scryfall.com/cards/search"
    page = 1
    params = {"q": query, "unique": "cards", "format": "json"}
    inserted = 0
    while url and page <= max_pages:
        resp = requests.get(url,params=params if page == 1 else None, timeout = 30)
        resp.raise_for_status()
        data = resp.json()
        for card in data.get("data",[]):
            insert_batch(cur,[card_to_row(card)])
            inserted += 1
        conn.commit()
        if data.get("has_more"):
            url = data.get("next_page")
            page +=1
        else:
            url = None
    conn.close()
    
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default = "data/scryfall.db", help = "sqlite db path (file) or sqlite:///... URL")
    ap.add_argument("--mode", choices=["bulk", "sample", "search"], default="bulk")
    ap.add_argument("--bulk-kind", default="default_cards", help="bulk-data type (default_cards, oracle_cards, all_cards)")
    ap.add_argument("--query", help="search query for search mode")
    args = ap.parse_args()
    dv_path = args.db
    if db_path.startswill("sqlite:///"):
        db_path = db_path.replace("sqlite:///","")
    if args.mode == "bulk":
        download_url, meta = get_bulk_download_url(args.bulk_kind)
        stream_download_and_insert(db_path, download_url)
    elif args.mode=="search":
        if not args.query:
            raise SystemExit("Search mode requires --query")
        search_and_insert(db_path, args.query)
    elif args.mode == "sample":
        q = args.query or 'name:"Opt"'
        search_and_insert(db_path, q, max_pages=1)
    else:
        raise SystemExit(f"Unknown mode {args.mode}")
if __name__ == "__main__":
    main()
