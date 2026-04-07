import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    async def send_deal_alert(
        self,
        deal_data: dict,
        listing_data: dict,
    ) -> bool:
        """Format and send a deal alert via Telegram."""
        try:
            score = deal_data.get("deal_score", 0)
            score_pct = int(score * 100)
            recommendation = deal_data.get("ai_recommendation", "watch")

            # Score emoji
            if score >= 0.8:
                score_emoji = "🟢"
            elif score >= 0.6:
                score_emoji = "🟡"
            else:
                score_emoji = "🔴"

            # Recommendation emoji
            rec_emojis = {"buy": "✅ BUY", "watch": "👀 WATCH", "skip": "❌ SKIP"}
            rec_text = rec_emojis.get(recommendation, "👀 WATCH")

            # Build message
            brand = listing_data.get("brand") or ""
            model = listing_data.get("model") or ""
            watch_name = f"{brand} {model}".strip() or listing_data.get("title", "Watch")

            price = listing_data.get("price", 0)
            market_price = deal_data.get("market_price")
            price_diff_pct = deal_data.get("price_difference_pct")

            price_line = f"💶 Price: €{price:,.0f}"
            if market_price and price_diff_pct is not None:
                direction = "below" if price_diff_pct > 0 else "above"
                price_line += f" ({abs(price_diff_pct):.1f}% {direction} market avg of €{market_price:,.0f})"

            ai_analysis = deal_data.get("ai_analysis", "")
            analysis_line = f"\n📊 Analysis: {ai_analysis}" if ai_analysis else ""

            url = listing_data.get("url", "")
            source = listing_data.get("source", "").title()
            condition = listing_data.get("condition") or "N/A"
            location = listing_data.get("location") or "N/A"

            message = (
                f"⌚ *WatchDeal Vienna Alert*\n\n"
                f"{score_emoji} Deal Score: {score_pct}% | {rec_text}\n\n"
                f"*{watch_name}*\n"
                f"{price_line}\n"
                f"📍 Location: {location}\n"
                f"🔧 Condition: {condition}\n"
                f"🏪 Source: {source}"
                f"{analysis_line}\n\n"
                f"🔗 [View Listing]({url})"
            )

            return await self.send_message(message, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error formatting deal alert: {e}")
            return False

    async def send_message(
        self,
        text: str,
        parse_mode: str = "Markdown",
    ) -> bool:
        """Send a message via Telegram Bot API."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram not configured - skipping notification")
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": False,
                    },
                )
                data = response.json()

                if data.get("ok"):
                    logger.info("Telegram message sent successfully")
                    return True
                else:
                    logger.error(f"Telegram API error: {data.get('description', 'Unknown error')}")
                    return False

        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False

    async def send_scrape_summary(
        self,
        source: str,
        new_listings: int,
        new_deals: int,
        top_score: Optional[float] = None,
    ) -> bool:
        """Send a summary message after a scrape run."""
        score_text = f" (top score: {int(top_score * 100)}%)" if top_score else ""
        message = (
            f"🔍 *Scrape Complete: {source.title()}*\n"
            f"New listings: {new_listings}\n"
            f"New deals found: {new_deals}{score_text}"
        )
        return await self.send_message(message)
