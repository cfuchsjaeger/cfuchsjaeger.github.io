from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from ..services.ai_analyzer import AIAnalyzer
from ..config import settings

router = APIRouter(prefix="/ai-listing", tags=["ai_listing"])


class GenerateListingRequest(BaseModel):
    brand: str
    model: str
    condition: str
    year: Optional[int] = None
    price: float
    special_features: Optional[str] = None


class GenerateListingResponse(BaseModel):
    title: str
    description: str
    suggested_price: Optional[float] = None
    tags: List[str] = []


@router.post("/generate", response_model=GenerateListingResponse)
async def generate_listing(request: GenerateListingRequest):
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI service not configured. Please set ANTHROPIC_API_KEY.",
        )

    analyzer = AIAnalyzer(api_key=settings.ANTHROPIC_API_KEY)

    try:
        result = await analyzer.generate_listing(request.model_dump())
        return GenerateListingResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Listing generation failed: {str(e)}")
