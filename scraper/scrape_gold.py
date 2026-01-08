# Scraper script to fetch gold prices from Tanishq and Malabar Gold & Diamonds

import requests


def scrape_tanishq_gold_price():
    """Scrape gold prices from Tanishq website."""
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager

    url = "https://www.tanishq.co.in/gold-rate.html?lang=en_IN"

    # Setup Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Initialize the driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    results = {"source": "Tanishq", "success": False, "rates": {}, "error": None}

    try:
        driver.get(url)

        # Wait for the gold rate element to be present
        wait = WebDriverWait(driver, 15)
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.goldpurity-rate"))
        )

        # Parse the page source
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Find the span with gold rate data attributes
        # The prices for all karats are stored as data attributes on this element
        rate_span = soup.find("span", class_="goldpurity-rate")

        if rate_span:
            # Extract prices from data attributes (values are per gram)
            gold_22k = rate_span.get("data-goldrate22kt", "Not found")
            gold_24k = rate_span.get("data-goldrate24kt", "Not found")
            gold_18k = rate_span.get("data-goldrate18kt", "Not found")

            results["rates"] = {"22K": gold_22k, "24K": gold_24k, "18K": gold_18k}
            results["success"] = True
        else:
            results["error"] = "Could not find gold rate element on page"

    except Exception as e:
        results["error"] = str(e)

    finally:
        driver.quit()

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
            import re

            # Pattern to match karat and price
            pattern = r"(\d+)\s*KT\([^)]+\)\s*-\s*</td><td>[^0-9]*(\d+)/g"
            matches = re.findall(pattern, html_content)

            for karat, price in matches:
                results["rates"][f"{karat}K"] = price

        # Also fetch the getrates API for 24K rate (may not be in panel)
        rates_url = "https://www.malabargoldanddiamonds.com/malabarprice/index/getrates/?country=IN&state=Kerala"
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


def scrape_gold_price():
    """Main function to scrape gold prices from all sources in parallel."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Define scrapers with their names for error handling
    scrapers = [
        ("Tanishq", scrape_tanishq_gold_price),
        ("Malabar Gold & Diamonds", scrape_malabar_gold_price),
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

    return all_results


if __name__ == "__main__":
    scrape_gold_price()
