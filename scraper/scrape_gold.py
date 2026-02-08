# Scraper script to fetch gold prices from Tanishq and Malabar Gold & Diamonds

import json
import os
import re
from datetime import datetime, timedelta, timezone

import requests


def _parse_google_gold_price(text):
    """Parse the Google gold price card text and return (price, grams)."""
    normalized = " ".join(text.split())

    patterns = [
        (
            r"10g of 24k gold.*?(Bengaluru|Bangalore).*?([0-9,]+(?:\.\d+)?)\s*Indian Rupee",
            10,
        ),
        (
            r"1g of 24k gold.*?(Bengaluru|Bangalore).*?([0-9,]+(?:\.\d+)?)\s*Indian Rupee",
            1,
        ),
    ]

    for pattern, grams in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            value = float(match.group(2).replace(",", ""))
            return value, grams

    idx = normalized.lower().find("24k gold")
    if idx != -1:
        window = normalized[idx : idx + 300]
        match = re.search(r"([0-9,]+(?:\.\d+)?)\s*Indian Rupee", window)
        if match:
            value = float(match.group(1).replace(",", ""))
            grams = 10 if value > 50000 else 1
            return value, grams

    match = re.search(r"([0-9,]+(?:\.\d+)?)\s*Indian Rupee", normalized)
    if match:
        value = float(match.group(1).replace(",", ""))
        grams = 10 if value > 50000 else 1
        return value, grams

    return None, None


def _parse_google_date(text):
    """Parse the date shown on Google card (e.g., '4 Feb, 4:12 pm IST')."""
    match = re.search(
        r"(\d{1,2})\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None

    day = int(match.group(1))
    month_str = match.group(2).title()
    month_map = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
    }
    month = month_map.get(month_str)
    if not month:
        return None

    now_tz = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    try:
        return datetime(now_tz.year, month, day).date().isoformat()
    except ValueError:
        return None


def scrape_tanishq_gold_price():
    """Scrape gold prices from Tanishq website using requests + BeautifulSoup."""
    import random
    import time

    from bs4 import BeautifulSoup

    url = "https://www.tanishq.co.in/gold-rate.html?lang=en_IN"

    # More comprehensive headers to bypass anti-bot
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }

    results = {"source": "Tanishq", "success": False, "rates": {}, "error": None}

    try:
        # Create a session to handle cookies
        session = requests.Session()

        # Add a small random delay before starting
        time.sleep(random.uniform(1, 3))

        # First visit home page to get necessary cookies, mimicking a user coming from Google
        session.get("https://www.tanishq.co.in/", headers=headers, timeout=20)

        # Update referer for the actual page request
        headers["Referer"] = "https://www.tanishq.co.in/"
        headers["Sec-Fetch-Site"] = "same-origin"

        # Wait a bit more before fetching the gold rate page
        time.sleep(random.uniform(1, 2))

        # Fetch the gold rate page
        response = session.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        # Parse the page
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the first span with gold rate data attributes
        # The gold rates are embedded as data attributes in span.goldpurity-rate elements
        # The first occurrence contains today's rates
        rate_span = soup.find("span", class_="goldpurity-rate")

        if rate_span:
            # Extract prices from data attributes (values are per gram in INR)
            gold_22k = rate_span.get("data-goldrate22kt", "Not found")
            gold_24k = rate_span.get("data-goldrate24kt", "Not found")
            gold_18k = rate_span.get("data-goldrate18kt", "Not found")

            results["rates"] = {"22K": gold_22k, "24K": gold_24k, "18K": gold_18k}
            results["success"] = True

            # Extract date from page (format: DD-MM-YYYY)
            date_match = re.search(r"(\d{2})-(\d{2})-(\d{4})", response.text)
            if date_match:
                d, m, y = date_match.groups()
                results["date"] = f"{y}-{m}-{d}"
        else:
            results["error"] = "Could not find gold rate element on page"

    except requests.RequestException as e:
        results["error"] = f"Request failed: {str(e)}"
    except Exception as e:
        results["error"] = str(e)

    return results


def scrape_google_gold_price():
    """Scrape gold prices from Google search card using Selenium."""
    results = {"source": "Google", "success": False, "rates": {}, "error": None}

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        def build_driver(user_agent, headless_arg, window_size):
            options = Options()
            options.add_argument(headless_arg)
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"--window-size={window_size}")
            options.add_argument("--lang=en-IN")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--user-data-dir=/tmp/chrome-google-scrape")
            options.add_argument(f"--user-agent={user_agent}")
            options.add_experimental_option(
                "excludeSwitches", ["enable-automation", "enable-logging"]
            )
            options.add_experimental_option("useAutomationExtension", False)

            chrome_bin = os.environ.get("CHROME_BIN")
            if chrome_bin:
                options.binary_location = chrome_bin

            return webdriver.Chrome(options=options)

        user_agent_profiles = [
            (
                "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "412,915",
            ),
            (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "1280,720",
            ),
            (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "1280,720",
            ),
        ]
        headless_modes = ["--headless=new", "--headless=old"]

        last_error = None

        for headless_arg in headless_modes:
            for user_agent, window_size in user_agent_profiles:
                try:
                    driver = build_driver(user_agent, headless_arg, window_size)
                except Exception as e:
                    last_error = f"Chrome start failed ({headless_arg}): {str(e)}"
                    continue

                try:
                    driver.execute_script(
                        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                    )
                    driver.execute_cdp_cmd(
                        "Network.setUserAgentOverride",
                        {
                            "userAgent": user_agent,
                            "platform": "Linux x86_64",
                            "acceptLanguage": "en-IN,en;q=0.9",
                        },
                    )

                    url = "https://www.google.com/search?q=gold+price+india+bangalore&hl=en&gl=IN"
                    driver.get(url)

                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )

                    page_source = driver.page_source.lower()
                    if "unusual traffic" in page_source or "recaptcha" in page_source:
                        last_error = "Blocked by Google captcha"
                        continue

                    # Try targeted extraction first
                    candidate_texts = []
                    for el in driver.find_elements(
                        By.XPATH,
                        "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '24k gold')]",
                    ):
                        text = el.text.strip()
                        if text:
                            candidate_texts.append(text)

                    body_text = driver.find_element(By.TAG_NAME, "body").text
                    candidate_texts.append(body_text)

                    price = None
                    grams = None
                    for text in candidate_texts:
                        price, grams = _parse_google_gold_price(text)
                        if price is not None:
                            break

                    if price is None:
                        last_error = "Could not parse price from Google card"
                        continue

                    price_per_gram_24k = int(round(price / grams))
                    price_per_gram_22k = int(round(price_per_gram_24k * 22 / 24))
                    price_per_gram_18k = int(round(price_per_gram_24k * 18 / 24))

                    results["rates"] = {
                        "24K": str(price_per_gram_24k),
                        "22K": str(price_per_gram_22k),
                        "18K": str(price_per_gram_18k),
                    }
                    results["success"] = True

                    scraped_date = _parse_google_date(body_text)
                    if scraped_date:
                        results["date"] = scraped_date

                    return results
                finally:
                    driver.quit()

        results["error"] = last_error or "Could not fetch Google results"

    except Exception as e:
        results["error"] = str(e)

    return results


def scrape_malabar_gold_price():
    """Scrape gold prices from Malabar Gold & Diamonds website."""
    results = {
        "source": "Malabar Gold & Diamonds",
        "success": False,
        "rates": {},
        "error": None,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.malabargoldanddiamonds.com/",
    }

    try:
        # Create a session to handle cookies
        session = requests.Session()

        # First visit the main page to get cookies
        session.get("https://www.malabargoldanddiamonds.com/", headers=headers)

        # Fetch the gold rate panel (contains 22K, 18K, 14K rates)
        panel_url = (
            "https://www.malabargoldanddiamonds.com/malabarprice/index/currentGoldRate/"
        )
        panel_response = session.get(panel_url, headers=headers)
        panel_response.raise_for_status()
        panel_data = panel_response.json()

        # Parse the HTML in the response to extract rates
        if "data" in panel_data:
            html_content = panel_data["data"]
            # Extract rates using string parsing (format: "22 KT(916) - </td><td>₹  12650/g")

            # Pattern to match karat and price
            pattern = r"(\d+)\s*KT\([^)]+\)\s*-\s*</td><td>[^0-9]*(\d+)/g"
            matches = re.findall(pattern, html_content)

            for karat, price in matches:
                results["rates"][f"{karat}K"] = price

        # Also fetch the getrates API for 24K rate (may not be in panel)
        rates_url = "https://www.malabargoldanddiamonds.com/malabarprice/index/getrates/?country=IN&state=Karnataka"
        rates_response = session.get(rates_url, headers=headers)
        rates_response.raise_for_status()
        rates_data = rates_response.json()

        # Extract 24kt if available and not already present
        if "24kt" in rates_data and "24K" not in results["rates"]:
            # Parse the price (format: "13,800.00 INR")
            price_24k = rates_data["24kt"].replace(",", "").split(".")[0]
            results["rates"]["24K"] = price_24k

        # Update 22K from getrates if not already present (as backup)
        if "22kt" in rates_data and "22K" not in results["rates"]:
            price_22k = rates_data["22kt"].replace(",", "").split(".")[0]
            results["rates"]["22K"] = price_22k

        # Extract date from getrates updated_time (format: "DD/MM/YYYY HH:MM AM/PM")
        updated_time = rates_data.get("updated_time", "")
        date_match = re.search(r"(\d{2})/(\d{2})/(\d{4})", updated_time)
        if date_match:
            d, m, y = date_match.groups()
            results["date"] = f"{y}-{m}-{d}"

        if results["rates"]:
            results["success"] = True
        else:
            results["error"] = "No rates found in API response"

    except requests.RequestException as e:
        results["error"] = f"Request failed: {str(e)}"
    except Exception as e:
        results["error"] = str(e)

    return results


def display_results(results):
    """Display the scraped gold rates."""
    print(f"\n{results['source']} Gold Rates (per gram):")
    print("-" * 40)

    if results["success"]:
        # Display rates in a consistent order
        for karat in ["24K", "22K", "18K", "14K"]:
            if karat in results["rates"]:
                price = results["rates"][karat]
                print(f"  {karat}: ₹{price}")
    else:
        print(f"  Error: {results['error']}")


def scrape_grt_gold_price():
    """Scrape gold prices from GRT Jewels website."""
    results = {"source": "GRT Jewels", "success": False, "rates": {}, "error": None}

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    }

    try:
        response = requests.get(
            "https://www.grtjewels.com/", headers=headers, timeout=20
        )
        response.raise_for_status()

        # Extract gold_rate JSON from HTML
        # Note: The JSON uses escaped quotes \"key\": value
        match = re.search(r'\\"gold_rate\\":\s*(\[.*?\])', response.text)
        if match:
            # Clean the extracted string by unescaping quotes
            cleaned_json = match.group(1).replace(r"\"", '"')
            gold_rates = json.loads(cleaned_json)

            for rate in gold_rates:
                if rate.get("type") == "GOLD" and rate.get("unit") == "G":
                    purity_str = rate.get("purity")  # e.g., "22 KT", "24 KT"
                    amount = rate.get("amount")

                    if purity_str and amount:
                        # Convert "22 KT" -> "22K"
                        karat = purity_str.replace(" KT", "K").strip()
                        results["rates"][karat] = str(amount)

            if results["rates"]:
                results["success"] = True
            else:
                results["error"] = "No gold rates found in parsed JSON"
        else:
            results["error"] = "Could not find gold_rate JSON in HTML"

    except requests.RequestException as e:
        results["error"] = f"Request failed: {str(e)}"
    except json.JSONDecodeError as e:
        results["error"] = f"Failed to parse JSON: {str(e)}"
    except Exception as e:
        results["error"] = str(e)

    return results


def scrape_gold_price():
    """Main function to scrape gold prices from all sources in parallel."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Define scrapers with their names for error handling
    scrapers = [
        # ("Tanishq", scrape_tanishq_gold_price),
        ("Malabar Gold & Diamonds", scrape_malabar_gold_price),
        ("GRT Jewels", scrape_grt_gold_price),
        ("Google", scrape_google_gold_price),
    ]

    all_results = []

    print("Fetching gold rates from all sources in parallel...")

    # Run scrapers in parallel
    with ThreadPoolExecutor(max_workers=len(scrapers)) as executor:
        # Submit all scraper tasks
        future_to_source = {
            executor.submit(scraper_func): source_name
            for source_name, scraper_func in scrapers
        }

        # Collect results as they complete
        for future in as_completed(future_to_source):
            source_name = future_to_source[future]
            try:
                result = future.result()
                all_results.append(result)
            except Exception as e:
                all_results.append(
                    {
                        "source": source_name,
                        "success": False,
                        "rates": {},
                        "error": f"Unexpected error: {str(e)}",
                    }
                )

    # Display all results
    print("\n" + "=" * 50)
    print("GOLD RATES SUMMARY")
    print("=" * 50)

    for result in all_results:
        display_results(result)

    print("\n" + "=" * 50)

    # Summary of success/failure
    successful = sum(1 for r in all_results if r["success"])
    print(f"\nSuccessfully fetched rates from {successful}/{len(all_results)} sources")

    # Update or Append 24K gold prices to JSON file
    json_path = os.path.join(
        os.path.dirname(__file__), "..", "docs", "data", "gold_prices.json"
    )
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing = []

    now_tz = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    today_iso = now_tz.date().isoformat()
    now_iso = now_tz.isoformat()
    bot_email = "gold-bot@users.noreply.github.com"

    allowed_purities = ["24K", "22K", "18K"]

    for result in all_results:
        if result.get("success"):
            for purity, price_val in result.get("rates", {}).items():
                if purity not in allowed_purities:
                    continue

                source = result["source"]
                try:
                    new_price = int(str(price_val).replace(",", "").split(".")[0])
                except (ValueError, TypeError):
                    continue

                scraping_date = result.get("date", today_iso)

                # Search for existing record with same source, date, AND purity
                found = False
                for entry in existing:
                    if (
                        entry.get("source") == source
                        and entry.get("date") == scraping_date
                        and entry.get("purity") == purity
                    ):
                        # Update if price changed
                        if entry.get("price_per_gm") != new_price:
                            entry["price_per_gm"] = new_price
                            entry["modified_dt"] = now_iso
                            entry["modified_by"] = bot_email
                        found = True
                        break

                if not found:
                    # Add new record
                    entry = {
                        "source": source,
                        "date": scraping_date,
                        "purity": purity,
                        "price_per_gm": new_price,
                        "created_dt": now_iso,
                        "created_by": bot_email,
                        "modified_dt": None,
                        "modified_by": None,
                    }
                    existing.append(entry)

    # Ensure directory exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    return all_results


if __name__ == "__main__":
    scrape_gold_price()
