import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from ..models.listing import Listing
from ..models.deal import Deal
from ..models.market_price import MarketPrice

logger = logging.getLogger(__name__)

CONDITION_SCORES = {
    "mint": 1.0,
    "like new": 1.0,
    "excellent": 0.9,
    "very good": 0.8,
    "good": 0.7,
    "fair": 0.5,
    "poor": 0.3,
    "unpolished": 0.85,
    "unworn": 1.0,
}

SOURCE_RELIABILITY = {
    "chrono24": 1.0,
    "willhaben": 0.85,
}


class DealScorer:
    def __init__(self, min_deal_score: float = 0.6):
        self.min_deal_score = min_deal_score

    def score_deal(
        self,
        listing: Listing,
        market_price: Optional[MarketPrice],
        db: Session,
    ) -> Optional[Deal]:
        """
        Score a deal 0-1 based on multiple factors.
        Returns a Deal record (or updates existing one).
        """
        score = self._calculate_score(listing, market_price)
        price_diff, price_diff_pct = self.calculate_price_difference(
            listing.price,
            market_price.average_price if market_price else None,
        )

        # Check if a deal already exists for this listing
        existing_deal = db.query(Deal).filter(Deal.listing_id == listing.id).first()

        if existing_deal:
            existing_deal.deal_score = score
            existing_deal.market_price = market_price.average_price if market_price else None
            existing_deal.price_difference = price_diff
            existing_deal.price_difference_pct = price_diff_pct
            db.commit()
            db.refresh(existing_deal)
            return existing_deal
        else:
            deal = Deal(
                listing_id=listing.id,
                deal_score=score,
                market_price=market_price.average_price if market_price else None,
                price_difference=price_diff,
                price_difference_pct=price_diff_pct,
            )
            db.add(deal)
            db.commit()
            db.refresh(deal)
            return deal

    def _calculate_score(
        self,
        listing: Listing,
        market_price: Optional[MarketPrice],
    ) -> float:
        """Calculate a composite deal score."""
        # 1. Price vs market (60% weight)
        price_score = self._price_score(listing.price, market_price)

        # 2. Condition (20% weight)
        condition_score = self._condition_score(listing.condition)

        # 3. Listing completeness (10% weight)
        completeness_score = self._completeness_score(listing)

        # 4. Source reliability (10% weight)
        source_score = SOURCE_RELIABILITY.get(listing.source, 0.5)

        total = (
            price_score * 0.60
            + condition_score * 0.20
            + completeness_score * 0.10
            + source_score * 0.10
        )

        return round(min(max(total, 0.0), 1.0), 4)

    def _price_score(
        self,
        listing_price: float,
        market_price: Optional[MarketPrice],
    ) -> float:
        """Score based on how good the price is relative to market."""
        if market_price is None:
            # No market data - give a neutral-ish score
            return 0.5

        avg = market_price.average_price
        if avg <= 0:
            return 0.5

        ratio = listing_price / avg  # < 1 means cheaper than market

        if ratio <= 0.5:
            return 1.0  # Amazing deal (50%+ below market)
        elif ratio <= 0.7:
            return 0.9  # Great deal
        elif ratio <= 0.85:
            return 0.75  # Good deal
        elif ratio <= 0.95:
            return 0.6  # Decent deal
        elif ratio <= 1.05:
            return 0.5  # Fair price
        elif ratio <= 1.20:
            return 0.3  # Slightly overpriced
        else:
            return 0.1  # Overpriced

    def _condition_score(self, condition: Optional[str]) -> float:
        """Score based on condition."""
        if not condition:
            return 0.6  # Unknown condition, assume average

        condition_lower = condition.lower()
        for key, score in CONDITION_SCORES.items():
            if key in condition_lower:
                return score
        return 0.6

    def _completeness_score(self, listing: Listing) -> float:
        """Score based on how complete the listing info is."""
        fields = [
            listing.brand,
            listing.model,
            listing.reference_number,
            listing.condition,
            listing.year,
            listing.description,
            listing.image_urls,
        ]
        filled = sum(1 for f in fields if f is not None and f != "" and f != [])
        return filled / len(fields)

    def calculate_price_difference(
        self,
        listing_price: float,
        market_price_value: Optional[float],
    ) -> Tuple[Optional[float], Optional[float]]:
        """Calculate absolute and percentage price difference."""
        if market_price_value is None or market_price_value <= 0:
            return None, None

        diff = market_price_value - listing_price
        diff_pct = (diff / market_price_value) * 100

        return round(diff, 2), round(diff_pct, 2)

    def find_market_price(
        self, listing: Listing, db: Session
    ) -> Optional[MarketPrice]:
        """Find the best matching market price for a listing."""
        if not listing.brand:
            return None

        query = db.query(MarketPrice).filter(
            MarketPrice.brand.ilike(listing.brand)
        )

        if listing.model:
            query = query.filter(MarketPrice.model.ilike(listing.model))

        if listing.reference_number:
            mp = query.filter(
                MarketPrice.reference_number == listing.reference_number
            ).first()
            if mp:
                return mp

        return query.first()
