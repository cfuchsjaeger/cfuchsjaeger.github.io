import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

BASE_URL = "https://www.chrono24.com/search/index.htm"


async def scrape_chrono24(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    keywords: Optional[str] = None,
    max_pages: int = 2,
) -> List[Dict[str, Any]]:
    """Scrape watch listings from chrono24.com."""
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

            # Build search parameters
            params = []
            if keywords:
                params.append(f"query={keywords.replace(' ', '+')}")
            elif brand:
                params.append(f"query={brand.replace(' ', '+')}")
                if model:
                    params.append(f"query={model.replace(' ', '+')}")
            if min_price:
                params.append(f"priceFrom={int(min_price)}")
            if max_price:
                params.append(f"priceTo={int(max_price)}")
            params.append("resultview=list")
            params.append("showpage=1")

            for page_num in range(1, max_pages + 1):
                page_params = params.copy()
                if page_num > 1:
                    # Update page param
                    page_params = [p for p in page_params if not p.startswith("showpage=")]
                    page_params.append(f"showpage={page_num}")

                url = BASE_URL + "?" + "&".join(page_params)
                logger.info(f"Scraping Chrono24 page {page_num}: {url}")

                try:
                    await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)

                    # Accept cookies if present
                    try:
                        cookie_btn = page.locator(
                            "button[data-testid='cookie-modal-accept-all'], "
                            "button:has-text('Accept all'), "
                            "button:has-text('Alle akzeptieren')"
                        )
                        if await cookie_btn.count() > 0:
                            await cookie_btn.first.click()
                            await page.wait_for_timeout(1000)
                    except Exception:
                        pass

                    # Extract listings
                    listing_items = await page.query_selector_all(
                        "div[class*='article-item'], "
                        "div[data-article-id], "
                        "article.rss-article"
                    )

                    if not listing_items:
                        listing_items = await page.query_selector_all(
                            "div.js-article-item, div[class*='ResultList__item']"
                        )

                    if not listing_items:
                        logger.warning(f"No items found on Chrono24 page {page_num}")
                        break

                    for item in listing_items:
                        try:
                            listing = await _extract_chrono24_listing(item)
                            if listing:
                                listings.append(listing)
                        except Exception as e:
                            logger.error(f"Error extracting Chrono24 listing: {e}")
                            continue

                    # Check for next page
                    next_btn = await page.query_selector(
                        "a[aria-label='Next page'], "
                        "a.pagination-next, "
                        "li.next a"
                    )
                    if not next_btn:
                        logger.info("No next page found on Chrono24, stopping")
                        break

                except PlaywrightTimeoutError:
                    logger.error(f"Timeout on Chrono24 page {page_num}")
                    break
                except Exception as e:
                    logger.error(f"Error scraping Chrono24 page {page_num}: {e}")
                    break

        finally:
            await browser.close()

    logger.info(f"Chrono24 scraper found {len(listings)} listings")
    return listings


async def _extract_chrono24_listing(item) -> Optional[Dict[str, Any]]:
    """Extract data from a single Chrono24 listing element."""
    try:
        # Get article ID for external_id
        article_id = await item.get_attribute("data-article-id")

        # Title / watch name
        title_el = await item.query_selector(
            "div[class*='article-title'], span[class*='model'], h4[class*='title']"
        )
        title = await title_el.inner_text() if title_el else None

        if not title:
            title_el = await item.query_selector("h3, h4, div.text-bold")
            title = await title_el.inner_text() if title_el else None

        if not title:
            return None
        title = title.strip()

        # Brand
        brand_el = await item.query_selector(
            "div[class*='manufacturer'], span[class*='manufacturer'], "
            "div[class*='brand']"
        )
        brand = await brand_el.inner_text() if brand_el else None
        if brand:
            brand = brand.strip()

        # Model
        model_el = await item.query_selector(
            "div[class*='model-name'], span[class*='model-name']"
        )
        watch_model = await model_el.inner_text() if model_el else None
        if watch_model:
            watch_model = watch_model.strip()

        # Reference number
        ref_el = await item.query_selector(
            "span[class*='ref-number'], div[class*='ref-number']"
        )
        reference_number = await ref_el.inner_text() if ref_el else None
        if reference_number:
            reference_number = reference_number.replace("Ref.", "").strip()

        # Price
        price_el = await item.query_selector(
            "span[class*='price'], div[class*='price'], p[class*='price']"
        )
        price_text = await price_el.inner_text() if price_el else ""
        price = _parse_price(price_text)

        if price is None:
            return None

        # Condition
        condition_el = await item.query_selector(
            "span[class*='condition'], div[class*='condition']"
        )
        condition = await condition_el.inner_text() if condition_el else None
        if condition:
            condition = condition.strip()

        # Year
        year_el = await item.query_selector(
            "span[class*='year'], div[class*='year']"
        )
        year_text = await year_el.inner_text() if year_el else ""
        year = _parse_year(year_text)

        # URL
        link_el = await item.query_selector("a[href*='/watch/']")
        href = await link_el.get_attribute("href") if link_el else None
        if not href:
            link_el = await item.query_selector("a[href]")
            href = await link_el.get_attribute("href") if link_el else None

        if not href:
            return None

        if href.startswith("/"):
            url = f"https://www.chrono24.com{href}"
        else:
            url = href

        # External ID
        if article_id:
            external_id = f"chrono24_{article_id}"
        else:
            # Extract from URL
            path_part = href.split("/")[-1].split(".")[0]
            external_id = f"chrono24_{path_part}"

        # Images
        img_els = await item.query_selector_all("img[src*='chrono24'], img[data-src]")
        image_urls = []
        for img in img_els[:3]:
            src = await img.get_attribute("src") or await img.get_attribute("data-src")
            if src and src.startswith("http"):
                image_urls.append(src)

        return {
            "external_id": external_id,
            "source": "chrono24",
            "title": title,
            "brand": brand,
            "model": watch_model,
            "reference_number": reference_number,
            "price": price,
            "currency": "EUR",
            "condition": condition,
            "year": year,
            "url": url,
            "image_urls": image_urls,
            "location": None,
            "seller_name": None,
            "description": None,
        }

    except Exception as e:
        logger.error(f"Error in _extract_chrono24_listing: {e}")
        return None


def _parse_price(price_text: str) -> Optional[float]:
    """Parse price from text."""
    if not price_text:
        return None
    cleaned = re.sub(r"[€$£\s,]", "", price_text)
    cleaned = cleaned.replace(".", "")
    try:
        price = float(cleaned)
        if price <= 0:
            return None
        return price
    except ValueError:
        # Try alternative parsing
        match = re.search(r"(\d+(?:[.,]\d+)?)", price_text.replace(".", "").replace(",", ""))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None


def _parse_year(year_text: str) -> Optional[int]:
    """Parse year from text."""
    if not year_text:
        return None
    match = re.search(r"\b(19|20)\d{2}\b", year_text)
    if match:
        return int(match.group(0))
    return None
