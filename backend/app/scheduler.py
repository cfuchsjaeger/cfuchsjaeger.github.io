import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .config import settings
from .services.scraper_service import ScraperService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
scraper_service = ScraperService()


async def _run_willhaben_job():
    logger.info("Starting scheduled Willhaben scrape")
    try:
        stats = await scraper_service.run_willhaben_scrape()
        logger.info(f"Willhaben scrape complete: {stats}")
    except Exception as e:
        logger.error(f"Error in scheduled Willhaben scrape: {e}")


async def _run_chrono24_job():
    logger.info("Starting scheduled Chrono24 scrape")
    try:
        stats = await scraper_service.run_chrono24_scrape()
        logger.info(f"Chrono24 scrape complete: {stats}")
    except Exception as e:
        logger.error(f"Error in scheduled Chrono24 scrape: {e}")


def start():
    """Start the scheduler with configured intervals."""
    scheduler.add_job(
        _run_willhaben_job,
        trigger=IntervalTrigger(minutes=settings.SCRAPE_INTERVAL_WILLHABEN),
        id="willhaben_scrape",
        name="Willhaben Watch Scraper",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.add_job(
        _run_chrono24_job,
        trigger=IntervalTrigger(minutes=settings.SCRAPE_INTERVAL_CHRONO24),
        id="chrono24_scrape",
        name="Chrono24 Watch Scraper",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started. "
        f"Willhaben: every {settings.SCRAPE_INTERVAL_WILLHABEN}min, "
        f"Chrono24: every {settings.SCRAPE_INTERVAL_CHRONO24}min"
    )


def stop():
    """Stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
