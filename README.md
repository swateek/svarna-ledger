# SvarṇaLedger (svarna-ledger)

SvarṇaLedger is a transparent, append-only tracker of daily gold prices in India. It scrapes official jeweller websites once a day via GitHub Actions and publishes searchable tables and historical charts using a static GitHub Pages site — no backend, no ads, no noise.

**Live Application:** [https://swateek.github.io/svarna-ledger/](https://swateek.github.io/svarna-ledger/)

## Features

- **Daily Gold Rates**: Automatically scrapes 24K gold prices from Tanishq and Malabar Gold & Diamonds.
- **Append-only Ledger**: Historical data is stored in `docs/data/gold_prices.json`.
- **Static Website**: A responsive, searchable table built with Vanilla JS and DataTables.
- **Automated Workflows**: Powered by GitHub Actions for daily updates.

## Technical Architecture

1.  **Scraper (Python)**: A robust script using `requests` and `BeautifulSoup` to fetch prices.
2.  **Data Storage**: Data is version-controlled in the repository as a JSON file.
3.  **Frontend**: A simple HTML/JS application hosted on GitHub Pages that consumes the JSON data.
4.  **Automation**: GitHub Actions runs the scraper daily and commits the updated data.

## For Developers

### Local Development

#### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (Package manager)

#### Setup

1.  Clone the repository:
    ```bash
    git clone https://github.com/swateek/svarna-ledger.git
    cd svarna-ledger
    ```

2.  Install dependencies:
    ```bash
    uv sync
    ```

#### Running the Scraper

To manually fetch the latest gold prices and update the local data file:

```bash
uv run scraper/scrape_gold.py
```

#### Running the Frontend Locally

Since the frontend is a static site, you can serve it using any local web server. For example, using Python's built-in server:

```bash
python3 -m http.server -d docs 8000
```
Then visit `http://localhost:8000` in your browser.

## Project Structure

- `.github/workflows/`: GitHub Action definitions for daily scraping.
- `scraper/`: Python source code for data extraction.
- `docs/`: Frontend code and historical data (deployed to GitHub Pages).
- `docs/data/gold_prices.json`: The source of truth for gold prices.
- `pyproject.toml`: Project metadata and dependencies managed by `uv`.

## License

This project is open-source. See the repository for details.
