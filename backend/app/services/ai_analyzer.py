import logging
from typing import Optional, Dict, Any
import anthropic

logger = logging.getLogger(__name__)

MODEL_ID = "claude-haiku-4-5-20251001"


class AIAnalyzer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    async def analyze_deal(
        self,
        listing_data: Dict[str, Any],
        deal_data: Dict[str, Any],
        market_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a watch deal using Claude AI.
        Returns analysis text, recommendation, and confidence.
        """
        prompt = self._build_analysis_prompt(listing_data, deal_data, market_data)

        try:
            message = self.client.messages.create(
                model=MODEL_ID,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            response_text = message.content[0].text
            result = self._parse_analysis_response(response_text)
            return result

        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {
                "analysis": f"Analysis unavailable: {str(e)}",
                "recommendation": "watch",
                "confidence": 0.0,
            }

    def _build_analysis_prompt(
        self,
        listing_data: Dict[str, Any],
        deal_data: Dict[str, Any],
        market_data: Optional[Dict[str, Any]],
    ) -> str:
        """Build a prompt for deal analysis."""
        market_info = ""
        if market_data:
            market_info = f"""
Market Data:
- Average market price: €{market_data.get('average_price', 'N/A')}
- Price range: €{market_data.get('min_price', 'N/A')} - €{market_data.get('max_price', 'N/A')}
- Sample count: {market_data.get('sample_count', 'N/A')} listings
"""

        return f"""You are an expert watch dealer and appraiser. Analyze this watch listing and determine if it's a good deal.

Listing Details:
- Title: {listing_data.get('title', 'N/A')}
- Brand: {listing_data.get('brand', 'N/A')}
- Model: {listing_data.get('model', 'N/A')}
- Reference: {listing_data.get('reference_number', 'N/A')}
- Price: €{listing_data.get('price', 'N/A')}
- Condition: {listing_data.get('condition', 'N/A')}
- Year: {listing_data.get('year', 'N/A')}
- Source: {listing_data.get('source', 'N/A')}
- Location: {listing_data.get('location', 'N/A')}
- Description: {listing_data.get('description', 'N/A')[:500] if listing_data.get('description') else 'N/A'}

Deal Score: {deal_data.get('deal_score', 'N/A')} (0-1 scale)
Price vs Market: {deal_data.get('price_difference_pct', 'N/A')}% {'below' if (deal_data.get('price_difference', 0) or 0) > 0 else 'above'} market average
{market_info}

Please analyze this deal and provide:
1. A brief analysis (2-3 sentences) covering: value assessment, any red flags, and notable positives
2. A recommendation: exactly one of "buy", "watch", or "skip"
   - "buy": Clear good deal, act quickly
   - "watch": Decent deal or needs more info, monitor it
   - "skip": Overpriced or too many concerns
3. Confidence level: 0.0 to 1.0

Format your response exactly as:
ANALYSIS: [your analysis here]
RECOMMENDATION: [buy/watch/skip]
CONFIDENCE: [0.0-1.0]"""

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the structured response from Claude."""
        lines = response_text.strip().split("\n")
        result = {
            "analysis": "",
            "recommendation": "watch",
            "confidence": 0.5,
        }

        for line in lines:
            line = line.strip()
            if line.startswith("ANALYSIS:"):
                result["analysis"] = line[len("ANALYSIS:"):].strip()
            elif line.startswith("RECOMMENDATION:"):
                rec = line[len("RECOMMENDATION:"):].strip().lower()
                if rec in ("buy", "watch", "skip"):
                    result["recommendation"] = rec
                else:
                    result["recommendation"] = "watch"
            elif line.startswith("CONFIDENCE:"):
                try:
                    conf = float(line[len("CONFIDENCE:"):].strip())
                    result["confidence"] = min(max(conf, 0.0), 1.0)
                except ValueError:
                    result["confidence"] = 0.5

        # If parsing failed, use full response as analysis
        if not result["analysis"]:
            result["analysis"] = response_text[:500]

        return result

    async def generate_listing(self, watch_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a professional watch listing for willhaben.at.
        """
        prompt = self._build_listing_prompt(watch_details)

        try:
            message = self.client.messages.create(
                model=MODEL_ID,
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            response_text = message.content[0].text
            return self._parse_listing_response(response_text, watch_details)

        except Exception as e:
            logger.error(f"AI listing generation error: {e}")
            return {
                "title": f"{watch_details.get('brand', '')} {watch_details.get('model', '')}".strip(),
                "description": "Description generation failed. Please add details manually.",
                "suggested_price": watch_details.get("price"),
                "tags": [],
            }

    def _build_listing_prompt(self, watch_details: Dict[str, Any]) -> str:
        """Build prompt for listing generation."""
        features = watch_details.get("special_features", "")

        return f"""You are an expert watch dealer creating a compelling listing for willhaben.at (Austrian classifieds).

Watch Details:
- Brand: {watch_details.get('brand', 'N/A')}
- Model: {watch_details.get('model', 'N/A')}
- Condition: {watch_details.get('condition', 'N/A')}
- Year: {watch_details.get('year', 'N/A')}
- Asking Price: €{watch_details.get('price', 'N/A')}
- Special Features/Notes: {features if features else 'None provided'}

Create a professional, attractive listing for this watch. The listing should:
1. Be written in German (as willhaben.at is Austrian)
2. Highlight the key selling points
3. Be honest about the condition
4. Be concise but comprehensive

Format your response exactly as:
TITLE: [catchy title under 80 chars]
DESCRIPTION: [detailed description, 3-5 paragraphs in German]
SUGGESTED_PRICE: [price in EUR as number only]
TAGS: [comma-separated tags/keywords]"""

    def _parse_listing_response(
        self,
        response_text: str,
        watch_details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse the generated listing response."""
        result = {
            "title": f"{watch_details.get('brand', '')} {watch_details.get('model', '')}".strip(),
            "description": "",
            "suggested_price": watch_details.get("price"),
            "tags": [],
        }

        current_section = None
        description_lines = []

        for line in response_text.strip().split("\n"):
            line_stripped = line.strip()

            if line_stripped.startswith("TITLE:"):
                result["title"] = line_stripped[len("TITLE:"):].strip()
                current_section = "title"
            elif line_stripped.startswith("DESCRIPTION:"):
                current_section = "description"
                first_line = line_stripped[len("DESCRIPTION:"):].strip()
                if first_line:
                    description_lines.append(first_line)
            elif line_stripped.startswith("SUGGESTED_PRICE:"):
                current_section = "price"
                price_str = line_stripped[len("SUGGESTED_PRICE:"):].strip()
                try:
                    result["suggested_price"] = float(price_str.replace(",", "."))
                except ValueError:
                    pass
            elif line_stripped.startswith("TAGS:"):
                current_section = "tags"
                tags_str = line_stripped[len("TAGS:"):].strip()
                result["tags"] = [t.strip() for t in tags_str.split(",") if t.strip()]
            elif current_section == "description" and line_stripped:
                if not any(line_stripped.startswith(k) for k in ["SUGGESTED_PRICE:", "TAGS:"]):
                    description_lines.append(line_stripped)

        if description_lines:
            result["description"] = "\n\n".join(description_lines)

        return result
