from pathlib import Path
from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = "Market Signal Intelligence & Research Platform"
    host: str = "127.0.0.1"
    port: int = 8000
    auto_open_browser: bool = True

    database_path: Path = Path("app/data/market_research.db")
    cache_path: Path = Path("app/data/cache")
    log_path: Path = Path("app/data/platform.log")

    default_assets: list[str] = Field(default_factory=lambda: ["BTCUSDT", "EURUSD", "ES1!"])
    default_timeframe: str = "1h"

    transaction_cost_bps: float = 2.5
    slippage_bps: float = 1.5


settings = Settings()
