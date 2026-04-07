from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

from ..services.scraper_service import ScraperService
from ..scheduler import scheduler

router = APIRouter(prefix="/scraper", tags=["scraper"])

_scraper_service = ScraperService()
_last_willhaben_run: Dict[str, Any] = {}
_last_chrono24_run: Dict[str, Any] = {}


class ScrapeResult(BaseModel):
    status: str
    new_listings: int = 0
    updated_listings: int = 0
    new_deals: int = 0
    errors: int = 0
    started_at: str = ""


class ScraperStatus(BaseModel):
    willhaben: Dict[str, Any]
    chrono24: Dict[str, Any]
    scheduler_running: bool
    next_willhaben_run: str
    next_chrono24_run: str


@router.post("/run-willhaben", response_model=ScrapeResult)
async def run_willhaben():
    global _last_willhaben_run
    started = datetime.utcnow().isoformat()
    try:
        stats = await _scraper_service.run_willhaben_scrape()
        _last_willhaben_run = {**stats, "started_at": started, "status": "success"}
        return ScrapeResult(status="success", started_at=started, **stats)
    except Exception as e:
        _last_willhaben_run = {"status": "error", "started_at": started, "error": str(e)}
        raise HTTPException(status_code=500, detail=f"Scrape failed: {str(e)}")


@router.post("/run-chrono24", response_model=ScrapeResult)
async def run_chrono24():
    global _last_chrono24_run
    started = datetime.utcnow().isoformat()
    try:
        stats = await _scraper_service.run_chrono24_scrape()
        _last_chrono24_run = {**stats, "started_at": started, "status": "success"}
        return ScrapeResult(status="success", started_at=started, **stats)
    except Exception as e:
        _last_chrono24_run = {"status": "error", "started_at": started, "error": str(e)}
        raise HTTPException(status_code=500, detail=f"Scrape failed: {str(e)}")


@router.get("/status", response_model=ScraperStatus)
def get_scraper_status():
    next_willhaben = ""
    next_chrono24 = ""

    if scheduler.running:
        job_w = scheduler.get_job("willhaben_scrape")
        job_c = scheduler.get_job("chrono24_scrape")
        if job_w and job_w.next_run_time:
            next_willhaben = job_w.next_run_time.isoformat()
        if job_c and job_c.next_run_time:
            next_chrono24 = job_c.next_run_time.isoformat()

    return ScraperStatus(
        willhaben=_last_willhaben_run,
        chrono24=_last_chrono24_run,
        scheduler_running=scheduler.running,
        next_willhaben_run=next_willhaben,
        next_chrono24_run=next_chrono24,
    )
