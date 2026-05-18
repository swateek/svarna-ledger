"""One-time migration: import gold_prices.json into Supabase."""

import json
import os
import sys

from scraper.db import upsert_gold_prices

BATCH_SIZE = 100


def migrate():
    candidates = [
        os.path.join(os.path.dirname(__file__), "gold_prices_seed.json"),
        os.path.join(
            os.path.dirname(__file__), "..", "..", "docs", "data", "gold_prices.json"
        ),
    ]
    json_path = next(
        (os.path.abspath(p) for p in candidates if os.path.exists(p)), None
    )
    if not json_path:
        json_path = os.path.abspath(candidates[0])
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for entry in data:
        rows.append(
            {
                "source": entry["source"],
                "date": entry["date"],
                "purity": entry["purity"],
                "price_per_gm": entry["price_per_gm"],
                "created_dt": entry["created_dt"],
                "created_by": entry["created_by"],
                "modified_dt": entry.get("modified_dt"),
                "modified_by": entry.get("modified_by"),
            }
        )

    total = len(rows)
    for i in range(0, total, BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        upsert_gold_prices(batch)
        print(f"Upserted {min(i + BATCH_SIZE, total)}/{total}")

    print(f"Migration complete: {total} rows upserted.")


if __name__ == "__main__":
    migrate()
