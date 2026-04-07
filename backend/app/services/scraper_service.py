import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.listing import Listing
from ..models.deal import Deal
from ..models.alert import Alert
from ..models.price_history import PriceHistory
from ..models.search_config import SearchConfig
from ..scrapers.willhaben import scrape_willhaben
from ..scrapers.chrono24 import scrape_chrono24
from .deal_scorer import DealScorer
from .ai_analyzer import AIAnalyzer
from .telegram_notifier import TelegramNotifier
from ..config import settings

logger = logging.getLogger(__name__)


class ScraperService:
    def __init__(self):
        self.deal_scorer = DealScorer(min_deal_score=settings.MIN_DEAL_SCORE)
        self.ai_analyzer = AIAnalyzer(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.telegram = TelegramNotifier(
            bot_token=settings.TELEGRAM_BOT_TOKEN,
            chat_id=settings.TELEGRAM_CHAT_ID,
        )

    async def run_willhaben_scrape(self) -> Dict[str, Any]:
        """Run willhaben scraping for all active configs."""
        db = SessionLocal()
        stats = {"new_listings": 0, "updated_listings": 0, "new_deals": 0, "errors": 0}
        try:
            configs = (
                db.query(SearchConfig)
                .filter(
                    SearchConfig.is_active == True,
                    SearchConfig.sources.contains("willhaben"),
                )
                .all()
            )

            if not configs:
                # Run a default broad scrape
                configs_data = [{}]
            else:
                configs_data = [
                    {
                        "brand": c.brand,
                        "model": c.model,
                        "min_price": c.min_price,
                        "max_price": c.max_price,
                        "keywords": c.keywords,
                    }
                    for c in configs
                ]

            for config_data in configs_data:
                try:
                    listings_raw = await scrape_willhaben(**config_data)
                    for listing_data in listings_raw:
                        result = await self.process_listing(listing_data, "willhaben", db)
                        if result == "new":
                            stats["new_listings"] += 1
                        elif result == "updated":
                            stats["updated_listings"] += 1
                except Exception as e:
                    logger.error(f"Error in willhaben scrape for config {config_data}: {e}")
                    stats["errors"] += 1

            # Score and process deals
            new_deals = await self._process_unscored_deals(db)
            stats["new_deals"] = new_deals

        except Exception as e:
            logger.error(f"Error in run_willhaben_scrape: {e}")
        finally:
            db.close()

        return stats

    async def run_chrono24_scrape(self) -> Dict[str, Any]:
        """Run chrono24 scraping for all active configs."""
        db = SessionLocal()
        stats = {"new_listings": 0, "updated_listings": 0, "new_deals": 0, "errors": 0}
        try:
            configs = (
                db.query(SearchConfig)
                .filter(
                    SearchConfig.is_active == True,
                    SearchConfig.sources.contains("chrono24"),
                )
                .all()
            )

            if not configs:
                configs_data = [{}]
            else:
                configs_data = [
                    {
                        "brand": c.brand,
                        "model": c.model,
                        "min_price": c.min_price,
                        "max_price": c.max_price,
                        "keywords": c.keywords,
                    }
                    for c in configs
                ]

            for config_data in configs_data:
                try:
                    listings_raw = await scrape_chrono24(**config_data)
                    for listing_data in listings_raw:
                        result = await self.process_listing(listing_data, "chrono24", db)
                        if result == "new":
                            stats["new_listings"] += 1
                        elif result == "updated":
                            stats["updated_listings"] += 1
                except Exception as e:
                    logger.error(f"Error in chrono24 scrape for config {config_data}: {e}")
                    stats["errors"] += 1

            new_deals = await self._process_unscored_deals(db)
            stats["new_deals"] = new_deals

        except Exception as e:
            logger.error(f"Error in run_chrono24_scrape: {e}")
        finally:
            db.close()

        return stats

    async def process_listing(
        self,
        listing_data: Dict[str, Any],
        source: str,
        db: Session,
    ) -> str:
        """Upsert a listing and record price history. Returns 'new', 'updated', or 'skipped'."""
        try:
            external_id = listing_data.get("external_id")
            if not external_id:
                return "skipped"

            existing = db.query(Listing).filter(Listing.external_id == external_id).first()

            if existing:
                # Check if price changed
                old_price = existing.price
                new_price = listing_data.get("price", old_price)

                existing.price = new_price
                existing.title = listing_data.get("title", existing.title)
                existing.is_active = True
                existing.updated_at = datetime.utcnow()

                if old_price != new_price:
                    # Record price history
                    history = PriceHistory(
                        listing_id=existing.id,
                        price=new_price,
                        recorded_at=datetime.utcnow(),
                    )
                    db.add(history)

                db.commit()
                return "updated"
            else:
                # Create new listing
                listing = Listing(
                    external_id=external_id,
                    source=source,
                    title=listing_data.get("title", "Unknown"),
                    brand=listing_data.get("brand"),
                    model=listing_data.get("model"),
                    reference_number=listing_data.get("reference_number"),
                    price=listing_data.get("price", 0),
                    currency=listing_data.get("currency", "EUR"),
                    condition=listing_data.get("condition"),
                    year=listing_data.get("year"),
                    description=listing_data.get("description"),
                    url=listing_data.get("url", ""),
                    image_urls=listing_data.get("image_urls", []),
                    location=listing_data.get("location"),
                    seller_name=listing_data.get("seller_name"),
                    is_active=True,
                )
                db.add(listing)
                db.commit()
                db.refresh(listing)

                # Record initial price history
                history = PriceHistory(
                    listing_id=listing.id,
                    price=listing.price,
                    recorded_at=datetime.utcnow(),
                )
                db.add(history)
                db.commit()

                return "new"

        except Exception as e:
            logger.error(f"Error processing listing {listing_data.get('external_id')}: {e}")
            db.rollback()
            return "skipped"

    async def _process_unscored_deals(self, db: Session) -> int:
        """Score all listings that don't have a deal yet."""
        new_deals_count = 0

        listings_without_deals = (
            db.query(Listing)
            .filter(Listing.is_active == True)
            .outerjoin(Deal)
            .filter(Deal.id == None)
            .limit(50)
            .all()
        )

        for listing in listings_without_deals:
            try:
                market_price = self.deal_scorer.find_market_price(listing, db)
                deal = self.deal_scorer.score_deal(listing, market_price, db)

                if deal and deal.deal_score >= settings.MIN_DEAL_SCORE:
                    new_deals_count += 1

                    # Run AI analysis for high-score deals
                    if deal.deal_score >= 0.7 and self.ai_analyzer and not deal.ai_analysis:
                        await self._run_ai_analysis(deal, listing, market_price, db)

                    # Send Telegram alert for new good deals
                    if not deal.is_notified:
                        await self._send_deal_notification(deal, listing, db)

            except Exception as e:
                logger.error(f"Error processing deal for listing {listing.id}: {e}")

        return new_deals_count

    async def _run_ai_analysis(
        self,
        deal: Deal,
        listing: Listing,
        market_price,
        db: Session,
    ) -> None:
        """Run AI analysis on a deal."""
        try:
            listing_data = {
                "title": listing.title,
                "brand": listing.brand,
                "model": listing.model,
                "reference_number": listing.reference_number,
                "price": listing.price,
                "condition": listing.condition,
                "year": listing.year,
                "source": listing.source,
                "location": listing.location,
                "description": listing.description,
            }

            deal_data = {
                "deal_score": deal.deal_score,
                "price_difference": deal.price_difference,
                "price_difference_pct": deal.price_difference_pct,
            }

            market_data = None
            if market_price:
                market_data = {
                    "average_price": market_price.average_price,
                    "min_price": market_price.min_price,
                    "max_price": market_price.max_price,
                    "sample_count": market_price.sample_count,
                }

            result = await self.ai_analyzer.analyze_deal(listing_data, deal_data, market_data)

            deal.ai_analysis = result.get("analysis", "")
            deal.ai_recommendation = result.get("recommendation", "watch")
            db.commit()

        except Exception as e:
            logger.error(f"Error in AI analysis for deal {deal.id}: {e}")

    async def _send_deal_notification(
        self,
        deal: Deal,
        listing: Listing,
        db: Session,
    ) -> None:
        """Send Telegram notification for a good deal."""
        try:
            deal_data = {
                "deal_score": deal.deal_score,
                "market_price": deal.market_price,
                "price_difference": deal.price_difference,
                "price_difference_pct": deal.price_difference_pct,
                "ai_analysis": deal.ai_analysis,
                "ai_recommendation": deal.ai_recommendation or "watch",
            }

            listing_data = {
                "title": listing.title,
                "brand": listing.brand,
                "model": listing.model,
                "price": listing.price,
                "condition": listing.condition,
                "location": listing.location,
                "source": listing.source,
                "url": listing.url,
            }

            success = await self.telegram.send_deal_alert(deal_data, listing_data)

            # Record alert
            from ..models.alert import Alert as AlertModel
            alert = AlertModel(
                deal_id=deal.id,
                channel="telegram",
                message=f"Deal alert for listing {listing.id} (score: {deal.deal_score:.2f})",
                sent_at=datetime.utcnow(),
                success=success,
            )
            db.add(alert)

            deal.is_notified = True
            db.commit()

        except Exception as e:
            logger.error(f"Error sending deal notification for deal {deal.id}: {e}")
