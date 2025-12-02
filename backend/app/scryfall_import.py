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

def log(msg: str):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    oracle_id TEXT,
    name TEXT,
    set_code TEXT,
    set_name TEXT,
    collector_number TEXT,
    rarity TEXT,
    mana_cost TEXT,
    cmc REAL,
    type_line TEXT,
    oracle_text TEXT,
    power TEXT,
    toughness TEXT,
    colors TEXT,
    color_identity TEXT,
    image_uris TEXT
);
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name);
CREATE INDEX IF NOT EXISTS idx_cards_oracle ON cards(oracle_id);
CREATE INDEX IF NOT EXISTS idx_cards_name_nocase ON cards(name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_cards_set_code_nocase ON cards(set_code COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_cards_rarity_nocase ON cards(rarity COLLATE NOCASE);
"""

def get_bulk_download_url(kind="default_cards"):
    log(f"Fetching bulk metadata from {SCRYFALL_BULK_URL} (kind={kind})")
    resp = requests.get(SCRYFALL_BULK_URL, timeout = 30)
    resp.raise_for_status()
    data = resp.json()
    for entry in data.get("data",[]):
        if entry.get("type") == kind:
            log(f"Found bulk data for kind='{kind}'")
            return entry.get("download_uri"), entry
    raise RuntimeError(f"Could not find bulk data of kind {kind}")

def stream_download_and_insert(db_path, download_url):
    log(f"Preparing database at {db_path}")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    cur = conn.cursor()
    cur.executescript(CREATE_TABLE_SQL)
    conn.commit()
    log("Schema ensured. Starting bulk stream download and insert...")

    with requests.get(download_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        if IJSON_AVAILABLE:
            log("Using streaming JSON parser (ijson).")
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
                    log(f"Inserted {count} cards...")
                    batch = []
            if batch:
                insert_batch(cur,batch)
                conn.commit()
                count += len(batch)
                log(f"Inserted {count} cards...")
        else:
            log("ijson not available; loading full JSON into memory (may be large).")
            text = r.content
            cards = json.loads(text)
            batch = []
            count = 0
            for idx, card in enumerate(cards):
                batch.append(card_to_row(card))
                if len(batch) >= 1000:
                    insert_batch(cur,batch)
                    conn.commit()
                    count += len(batch)
                    log(f"Inserted {count} cards...")
                    batch = []
            if batch:
                insert_batch(cur,batch)
                conn.commit()
                count += len(batch)
                log(f"Inserted {count} cards...")
    conn.close()
    log("Bulk import complete.")

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
        j(card.get("image_uris")),
    )

def insert_batch(cur,batch):
    cur.executemany("""
        INSERT OR REPLACE INTO cards(
            id, oracle_id, name, set_code, set_name, collector_number, rarity, mana_cost, cmc, type_line,
            oracle_text, power, toughness, colors, color_identity, image_uris
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, batch)

def search_and_insert(db_path,query,max_pages=5):
    # Ensure parent directory exists so SQLite can create the file
    parent_dir = os.path.dirname(db_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(CREATE_TABLE_SQL)
    conn.commit()
    log(f"Schema ensured. Starting search import for query='{query}', up to {max_pages} page(s).")

    url = "https://api.scryfall.com/cards/search"
    page = 1
    params = {"q": query, "unique": "cards", "format": "json"}
    inserted = 0
    while url and page <= max_pages:
        log(f"Fetching page {page} from Scryfall search API...")
        resp = requests.get(url,params=params if page == 1 else None, timeout = 30)
        resp.raise_for_status()
        data = resp.json()
        for card in data.get("data",[]):
            insert_batch(cur,[card_to_row(card)])
            inserted += 1
        conn.commit()
        log(f"Inserted {inserted} cards so far (page {page} complete).")
        if data.get("has_more"):
            url = data.get("next_page")
            page +=1
        else:
            url = None
    conn.close()
    log(f"Search import complete. Total inserted: {inserted}.")
    
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default = "data/scryfall.db", help = "sqlite db path (file) or sqlite:///... URL")
    ap.add_argument("--mode", choices=["bulk", "sample", "search"], default="bulk")
    ap.add_argument("--bulk-kind", default="default_cards", help="bulk-data type (default_cards, oracle_cards, all_cards)")
    ap.add_argument("--query", help="search query for search mode")
    args = ap.parse_args()
    db_path = args.db
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///","")
    if args.mode == "bulk":
        log(f"Mode: bulk | DB: {db_path} | kind: {args.bulk_kind}")
        download_url, meta = get_bulk_download_url(args.bulk_kind)
        stream_download_and_insert(db_path, download_url)
    elif args.mode=="search":
        log(f"Mode: search | DB: {db_path} | query: {args.query}")
        if not args.query:
            raise SystemExit("Search mode requires --query")
        search_and_insert(db_path, args.query)
    elif args.mode == "sample":
        log(f"Mode: sample | DB: {db_path}")
        q = args.query or 'name:"Opt"'
        search_and_insert(db_path, q, max_pages=1)
    else:
        raise SystemExit(f"Unknown mode {args.mode}")
        
if __name__ == "__main__":
    main()
