from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .database import engine, Base
from . import models  # noqa: F401 - ensure models are imported for table creation
from .routers import (
    listings,
    deals,
    market_prices,
    search_configs,
    alerts,
    price_history,
    ai_listing,
    scraper,
)
from . import scheduler as sched

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting WatchDeal Vienna API...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

    try:
        sched.start()
        logger.info("Scheduler started")
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")

    yield

    # Shutdown
    logger.info("Shutting down WatchDeal Vienna API...")
    try:
        sched.stop()
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


app = FastAPI(
    title="WatchDeal Vienna API",
    description="Watch deal finder for willhaben.at and Chrono24",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(listings.router, prefix="/api")
app.include_router(deals.router, prefix="/api")
app.include_router(market_prices.router, prefix="/api")
app.include_router(search_configs.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(price_history.router, prefix="/api")
app.include_router(ai_listing.router, prefix="/api")
app.include_router(scraper.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "WatchDeal Vienna API"}


@app.get("/api/stats")
def get_stats(db=None):
    from .database import SessionLocal
    from .models.listing import Listing
    from .models.deal import Deal
    from .models.alert import Alert
    from sqlalchemy import func

    db = SessionLocal()
    try:
        total_listings = db.query(Listing).filter(Listing.is_active == True).count()
        active_deals = db.query(Deal).count()
        avg_score_result = db.query(func.avg(Deal.deal_score)).scalar()
        avg_deal_score = round(float(avg_score_result), 4) if avg_score_result else 0.0
        alerts_sent = db.query(Alert).filter(Alert.success == True).count()

        return {
            "total_listings": total_listings,
            "active_deals": active_deals,
            "avg_deal_score": avg_deal_score,
            "alerts_sent": alerts_sent,
        }
    finally:
        db.close()
