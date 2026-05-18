import json
import os
from datetime import datetime


def backfill_prices():
    candidates = [
        os.path.join(os.path.dirname(__file__), "gold_prices_seed.json"),
        os.path.join(
            os.path.dirname(__file__), "..", "..", "docs", "data", "gold_prices.json"
        ),
    ]
    json_path = next(
        (os.path.abspath(p) for p in candidates if os.path.exists(p)),
        os.path.abspath(candidates[1]),
    )

    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    existing_entries = set()
    for entry in data:
        existing_entries.add((entry["source"], entry["date"], entry["purity"]))

    new_entries = []
    current_dt = datetime.now().isoformat()
    default_user = "gold-bot@users.noreply.github.com"

    for entry in data:
        if entry["purity"] == "24K":
            source = entry["source"]
            date = entry["date"]
            price_24k = entry["price_per_gm"]

            if (source, date, "22K") not in existing_entries:
                price_22k = round(price_24k * (22 / 24))
                new_entries.append(
                    {
                        "source": source,
                        "date": date,
                        "purity": "22K",
                        "price_per_gm": price_22k,
                        "created_dt": current_dt,
                        "created_by": default_user,
                        "modified_dt": None,
                        "modified_by": None,
                    }
                )
                existing_entries.add((source, date, "22K"))

            if (source, date, "18K") not in existing_entries:
                price_18k = round(price_24k * (18 / 24))
                new_entries.append(
                    {
                        "source": source,
                        "date": date,
                        "purity": "18K",
                        "price_per_gm": price_18k,
                        "created_dt": current_dt,
                        "created_by": default_user,
                        "modified_dt": None,
                        "modified_by": None,
                    }
                )
                existing_entries.add((source, date, "18K"))

            if (source, date, "9K") not in existing_entries:
                price_9k = round(price_24k * (9 / 24))
                new_entries.append(
                    {
                        "source": source,
                        "date": date,
                        "purity": "9K",
                        "price_per_gm": price_9k,
                        "created_dt": current_dt,
                        "created_by": default_user,
                        "modified_dt": None,
                        "modified_by": None,
                    }
                )
                existing_entries.add((source, date, "9K"))

    if new_entries:
        data.extend(new_entries)
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Backfilled {len(new_entries)} entries.")
    else:
        print("No missing entries found to backfill.")


if __name__ == "__main__":
    backfill_prices()
