import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

TABLE_NAME = "gold_prices"
CONFLICT_COLUMNS = "source,date,purity"

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_env() -> None:
    """Load .env from repo root or scripts/backfill-prices/ (first found wins)."""
    for path in (
        _PROJECT_ROOT / ".env",
        _PROJECT_ROOT / "scraper" / ".env",
        _PROJECT_ROOT / "scripts" / "backfill-prices" / ".env",
    ):
        if path.is_file():
            load_dotenv(path)


def get_client() -> Client:
    _load_env()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SECRET_KEY") or os.environ.get(
        "SUPABASE_SERVICE_ROLE_KEY"
    )
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SECRET_KEY must be set in the environment"
        )
    return create_client(url, key)


def upsert_gold_prices(entries: list[dict]) -> None:
    if not entries:
        return
    client = get_client()
    client.table(TABLE_NAME).upsert(entries, on_conflict=CONFLICT_COLUMNS).execute()
