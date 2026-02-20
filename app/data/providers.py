from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Protocol

import numpy as np
import pandas as pd


class MarketDataProvider(Protocol):
    async def fetch_ohlcv(
        self,
        asset: str,
        timeframe: str,
        interval_seconds: int,
        limit: int = 700,
    ) -> pd.DataFrame: ...


class SyntheticProvider:
    """Local deterministic market generator used for offline research bootstrap."""

    async def fetch_ohlcv(
        self,
        asset: str,
        timeframe: str,
        interval_seconds: int,
        limit: int = 700,
    ) -> pd.DataFrame:
        await asyncio.sleep(0.01)
        seed = abs(hash((asset, timeframe))) % (2**32)
        rng = np.random.default_rng(seed)
        base_price = 100 + rng.random() * 100
        returns = rng.normal(loc=0.0004, scale=0.015, size=limit)
        price = base_price * np.exp(np.cumsum(returns))
        high = price * (1 + rng.uniform(0.0005, 0.01, limit))
        low = price * (1 - rng.uniform(0.0005, 0.01, limit))
        open_ = np.concatenate(([price[0]], price[:-1]))
        volume = rng.integers(1_000, 20_000, limit)
        now = datetime.utcnow()
        timestamps = [
            now - timedelta(seconds=interval_seconds * (limit - i))
            for i in range(limit)
        ]
        return pd.DataFrame(
            {
                "timestamp": timestamps,
                "open": open_,
                "high": high,
                "low": low,
                "close": price,
                "volume": volume,
            }
        )


class UnifiedMarketDataService:
    def __init__(self) -> None:
        self.provider = SyntheticProvider()
        self.timeframe_map = {
            "1m": 60,
            "5m": 300,
            "1h": 3600,
            "1d": 86400,
            "1w": 604800,
        }

    async def get_history(self, asset: str, timeframe: str, limit: int = 700) -> pd.DataFrame:
        if timeframe not in self.timeframe_map:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        return await self.provider.fetch_ohlcv(
            asset,
            timeframe,
            self.timeframe_map[timeframe],
            limit,
        )


market_data_service = UnifiedMarketDataService()
