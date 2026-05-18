# SvarṇaLedger (svarna-ledger)

[![Scrape Gold Prices](https://github.com/swateek/svarna-ledger/actions/workflows/scrape.yml/badge.svg)](https://github.com/swateek/svarna-ledger/actions/workflows/scrape.yml)

SvarṇaLedger is a transparent, append-only tracker of daily gold prices in India. It scrapes jeweller and reference sources on a schedule via GitHub Actions and publishes searchable tables and historical charts using a static GitHub Pages site backed by Supabase.

**Live Application:** [https://swateek.github.io/svarna-ledger/](https://swateek.github.io/svarna-ledger/)

## Features

- **Daily Gold Rates**: Scrapes 24K, 22K, 18K, and 9K gold prices from Malabar Gold & Diamonds, GRT Jewels, and Google.
- **Append-only Ledger**: Historical data lives in Supabase (`gold_prices` table).
- **Static Website**: A responsive, searchable table built with Vanilla JS, DataTables, and Chart.js.
- **Automated Workflows**: GitHub Actions runs the scraper every 6 hours and upserts into Supabase.

## Technical Architecture

1. **Scraper (Python)**: Fetches prices via `requests`, BeautifulSoup, and Selenium; upserts to Supabase.
2. **Data Storage**: Supabase Postgres with public read-only RLS for the frontend.
3. **Frontend**: Static HTML/JS on GitHub Pages; reads data via the Supabase JS client (anon key).
4. **Automation**: GitHub Actions runs the scraper with `SUPABASE_URL` and `SUPABASE_SECRET_KEY` secrets.

## For Developers

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv)
- A Supabase project ([supabase.com](https://supabase.com))

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/swateek/svarna-ledger.git
   cd svarna-ledger
   ```

2. Install scraper dependencies:
   ```bash
   cd scraper
   uv sync
   ```

3. Create the database table — run [`scripts/backfill-prices/migrations/001_gold_prices.sql`](scripts/backfill-prices/migrations/001_gold_prices.sql) in the Supabase SQL Editor.

4. Configure environment — copy `scripts/backfill-prices/env.example` to `.env` in the repo root, `scraper/`, or `scripts/backfill-prices/` (any of these paths work). Fill in `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, and `SUPABASE_PUBLISHABLE_KEY` (from Dashboard → API: **Secret** and **Publishable** keys).

5. Configure the frontend — set `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` in [`docs/config.js`](docs/config.js).

### One-time migration (import historical data)

A seed file with historical rows is at [`scripts/backfill-prices/gold_prices_seed.json`](scripts/backfill-prices/gold_prices_seed.json). After creating the Supabase table and `.env`:

```bash
cd scripts/backfill-prices
uv sync
uv run python migrate_gold_prices_to_supabase.py
```

### Running the Scraper

Requires `.env` with Supabase credentials:

```bash
cd scraper
uv run python scrape_gold.py
```

### Running the Frontend Locally

```bash
python3 -m http.server -d docs 8000
```

Then visit `http://localhost:8000`.

### GitHub Actions secrets

Add these repository secrets (Settings → Secrets → Actions):

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`

## Project Structure

- `.github/workflows/`: Scheduled scraper workflow.
- `scraper/`: Python scrapers, Supabase client helper, and `pyproject.toml` for daily scraping.
- `scripts/backfill-prices/`: Separate `pyproject.toml` for one-time backfill/migration, seed data, and SQL schema (`migrations/`).
- `docs/`: Frontend (GitHub Pages) and `config.js` for Supabase anon key.

## License

This project is open-source. See the repository for details.
