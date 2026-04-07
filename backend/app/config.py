from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://watchdeal:watchdeal@db:5432/watchdeal"
    ANTHROPIC_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    SCRAPE_INTERVAL_WILLHABEN: int = 5
    SCRAPE_INTERVAL_CHRONO24: int = 15
    MIN_DEAL_SCORE: float = 0.6

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
