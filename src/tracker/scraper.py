import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TARGET_URL = 'https://www.cashheatingoil.com/vernon_rockville_ct_oil_prices/06066'
HTTPX_TIMEOUT = 10.0
TARGET_CLASSES = {'paywithcash', 'paybycredit'}
PRICE_TYPE_LOOKUP = {
    'paywithcash': 'Cash',
    'paybycredit': 'Credit',
}


def fetch_oil_prices():
    """
    Fetches the HTML and parses out the current price.
    Returns: list of dicts.
    """
    logger.info(f'Fetching oil price from {TARGET_URL}')
    results = []

    try:
        with httpx.Client(timeout=HTTPX_TIMEOUT, follow_redirects=True) as client:
            response = client.get(TARGET_URL)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        logger.info(f'Scanning {len(tables)} tables for pricing data...')
        forms = soup.find_all('form')
        for form in forms:
            tables = form.find_all('table')
            for table in tables:
                if table.get('class'):
                    if TARGET_CLASSES.intersection(table.get('class', [])):
                        rows = table.find_all('tr')
                        for row in rows[2:]:
                            cells = row.find_all(['td'])
                            if len(cells) < 2:
                                continue
                            min_qty = cells[0].get_text(strip=True)
                            price = cells[1].get_text(strip=True)
                            results.append({
                                'supplier_id': form.find('input', {'name': 'dealerid'})['value'],
                                'type': PRICE_TYPE_LOOKUP[table.get('class')[0]],
                                'quantity': int(min_qty.split('-')[0]),
                                'price': float(price.replace('$', ''))
                            })
        unique_results = [dict(t) for t in {tuple(d.items()) for d in results}]
        logger.info(f'Extracted {len(unique_results)} unique price tiers.')
        return unique_results
    except Exception as e:
        logger.error(f'Scraping error: {e}')
        return []
