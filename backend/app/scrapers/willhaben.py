import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

BASE_URL = "https://www.willhaben.at/iad/kaufen-und-verkaufen/marktplatz/uhren-und-schmuck/uhren"


async def scrape_willhaben(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    keywords: Optional[str] = None,
    max_pages: int = 3,
) -> List[Dict[str, Any]]:
    """Scrape watch listings from willhaben.at."""
    listings = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()

            # Build search URL with parameters
            params = []
            if keywords:
                params.append(f"keyword={keywords.replace(' ', '+')}")
            elif brand:
                query = brand
                if model:
                    query += f" {model}"
                params.append(f"keyword={query.replace(' ', '+')}")
            if min_price:
                params.append(f"PRICE_FROM={int(min_price)}")
            if max_price:
                params.append(f"PRICE_TO={int(max_price)}")

            for page_num in range(1, max_pages + 1):
                page_params = params.copy()
                if page_num > 1:
                    page_params.append(f"page={page_num}")

                url = BASE_URL
                if page_params:
                    url += "?" + "&".join(page_params)

                logger.info(f"Scraping willhaben page {page_num}: {url}")

                try:
                    await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)

                    # Accept cookies if present
                    try:
                        cookie_btn = page.locator(
                            "button[data-testid='accept-all-button'], "
                            "button:has-text('Alle akzeptieren'), "
                            "#didomi-notice-agree-button"
                        )
                        if await cookie_btn.count() > 0:
                            await cookie_btn.first.click()
                            await page.wait_for_timeout(1000)
                    except Exception:
                        pass

                    # Extract listings
                    article_items = await page.query_selector_all(
                        "article[data-testid='ad-card'], div[data-testid='ad-card']"
                    )

                    if not article_items:
                        # Try alternative selectors
                        article_items = await page.query_selector_all(
                            "section[class*='ResultList'] article, "
                            "div[class*='search-result'] > div"
                        )

                    if not article_items:
                        logger.warning(f"No items found on page {page_num}")
                        break

                    for item in article_items:
                        try:
                            listing = await _extract_willhaben_listing(item, page)
                            if listing:
                                listings.append(listing)
                        except Exception as e:
                            logger.error(f"Error extracting listing: {e}")
                            continue

                    # Check if there's a next page
                    next_btn = await page.query_selector(
                        "a[data-testid='pagination-next'], "
                        "button[aria-label='Nächste Seite']"
                    )
                    if not next_btn:
                        logger.info("No next page found, stopping pagination")
                        break

                except PlaywrightTimeoutError:
                    logger.error(f"Timeout on willhaben page {page_num}")
                    break
                except Exception as e:
                    logger.error(f"Error scraping willhaben page {page_num}: {e}")
                    break

        finally:
            await browser.close()

    logger.info(f"Willhaben scraper found {len(listings)} listings")
    return listings


async def _extract_willhaben_listing(item, page) -> Optional[Dict[str, Any]]:
    """Extract data from a single willhaben listing element."""
    try:
        # Title
        title_el = await item.query_selector(
            "h3[class*='title'], a[class*='title'], span[class*='heading']"
        )
        title = await title_el.inner_text() if title_el else None

        if not title:
            title_el = await item.query_selector("h3, h4")
            title = await title_el.inner_text() if title_el else "Unknown Watch"

        title = title.strip()

        # Price
        price_el = await item.query_selector(
            "span[class*='price'], p[class*='price'], div[class*='price']"
        )
        price_text = await price_el.inner_text() if price_el else ""
        price = _parse_price(price_text)

        if price is None:
            return None  # Skip listings without price

        # URL
        link_el = await item.query_selector("a[href*='/iad/']")
        href = await link_el.get_attribute("href") if link_el else None
        if not href:
            return None

        if href.startswith("/"):
            url = f"https://www.willhaben.at{href}"
        else:
            url = href

        # Generate external ID from URL
        external_id = f"willhaben_{href.split('/')[-1].split('?')[0]}"

        # Location
        location_el = await item.query_selector(
            "span[class*='location'], div[class*='location'], p[class*='location']"
        )
        location = await location_el.inner_text() if location_el else None
        if location:
            location = location.strip()

        # Image
        img_el = await item.query_selector("img[src*='willhaben'], img[data-src]")
        image_url = None
        if img_el:
            image_url = await img_el.get_attribute("src") or await img_el.get_attribute("data-src")

        # Seller name
        seller_el = await item.query_selector(
            "span[class*='seller'], div[class*='seller']"
        )
        seller_name = await seller_el.inner_text() if seller_el else None
        if seller_name:
            seller_name = seller_name.strip()

        return {
            "external_id": external_id,
            "source": "willhaben",
            "title": title,
            "price": price,
            "currency": "EUR",
            "url": url,
            "image_urls": [image_url] if image_url else [],
            "location": location,
            "seller_name": seller_name,
            "brand": _extract_brand_from_title(title),
            "model": None,
            "condition": None,
            "year": None,
            "description": None,
        }

    except Exception as e:
        logger.error(f"Error in _extract_willhaben_listing: {e}")
        return None


def _parse_price(price_text: str) -> Optional[float]:
    """Parse price from text like '1.200 €' or '€ 1,200'."""
    if not price_text:
        return None
    # Remove currency symbols and spaces
    cleaned = re.sub(r"[€$£\s]", "", price_text)
    # Handle European number format (dot as thousands sep, comma as decimal)
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        price = float(cleaned)
        if price <= 0:
            return None
        return price
    except ValueError:
        return None


KNOWN_BRANDS = [
    "Rolex", "Omega", "Breitling", "TAG Heuer", "IWC", "Patek Philippe",
    "Audemars Piguet", "Jaeger-LeCoultre", "Cartier", "Longines", "Tissot",
    "Seiko", "Citizen", "Casio", "Swatch", "Tudor", "Zenith", "Panerai",
    "Hublot", "Richard Mille", "Vacheron Constantin", "A. Lange & Söhne",
    "Grand Seiko", "Hamilton", "Nomos", "Junghans"
]


def _extract_brand_from_title(title: str) -> Optional[str]:
    """Try to extract brand name from listing title."""
    if not title:
        return None
    title_lower = title.lower()
    for brand in KNOWN_BRANDS:
        if brand.lower() in title_lower:
            return brand
    return None
