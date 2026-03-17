import logging
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TARGET_URL = "https://www.cashheatingoil.com/vernon_rockville_ct_oil_prices/06066"
HTTPX_TIMEOUT = 10.0



def fetch_oil_price():
    """
    Fetches the HTML and parses out the current price.
    Returns: float price or None if failed.
    """
    logger.info(f"Fetching oil price from {TARGET_URL}")

    try:
        with httpx.Client(timeout=HTTPX_TIMEOUT, follow_redirects=True) as client:
            response = client.get(TARGET_URL)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        price_tags = soup.find_all(string=lambda t: "$" in t)
        found_prices = []
        for tag in price_tags:
            clean_price = tag.strip().replace("$", "").replace(",", "")
            try:
                price = float(clean_price)
                if price > 1.0:
                    found_prices.append(price)
            except ValueError:
                continue

        if found_prices:
            lowest_price = min(found_prices)
            logger.info(f"Filtered results. Lowest valid price: ${lowest_price}")
            return lowest_price

        logger.warning("No valid oil prices (> $1.00) found on page.")
        return None

    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return None