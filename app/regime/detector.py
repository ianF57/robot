from __future__ import annotations

import numpy as np
import pandas as pd
from pydantic import BaseModel


class RegimeResult(BaseModel):
    regime: str
    confidence: float
    volatility: float
    adx_proxy: float
    rsi: float
    distribution: dict[str, float]


class RegimeDetector:
    def detect(self, df: pd.DataFrame) -> RegimeResult:
        close = df["close"]
        returns = close.pct_change().dropna()
        rolling_vol = returns.rolling(30).std().iloc[-1] * np.sqrt(252)

        trend_strength = abs(close.pct_change(20).iloc[-1])
        mean_reversion = abs(returns.tail(20).mean()) < returns.tail(20).std() * 0.15

        gains = returns.clip(lower=0).rolling(14).mean().iloc[-1]
        losses = -returns.clip(upper=0).rolling(14).mean().iloc[-1] + 1e-9
        rs = gains / losses
        rsi = 100 - (100 / (1 + rs))

        adx_proxy = min(100.0, trend_strength * 1500)

        if rolling_vol > 0.45:
            regime = "high_volatility"
        elif rolling_vol < 0.18:
            regime = "low_volatility"
        elif adx_proxy > 35 and rsi > 58:
            regime = "momentum_breakout"
        elif mean_reversion and 42 <= rsi <= 58:
            regime = "mean_reversion"
        elif adx_proxy > 22:
            regime = "trending"
        else:
            regime = "ranging"

        confidence = float(np.clip(45 + adx_proxy * 0.7 + (rolling_vol * 40), 0, 100))

        distribution = {
            "trending": float(np.clip(adx_proxy / 100, 0, 1)),
            "ranging": float(np.clip(1 - adx_proxy / 100, 0, 1)),
            "high_volatility": float(np.clip((rolling_vol - 0.25) * 2, 0, 1)),
            "low_volatility": float(np.clip((0.25 - rolling_vol) * 2, 0, 1)),
            "momentum_breakout": float(np.clip((rsi - 50) / 50, 0, 1)),
            "mean_reversion": float(np.clip((55 - abs(rsi - 50)) / 55, 0, 1)),
        }

        return RegimeResult(
            regime=regime,
            confidence=round(confidence, 2),
            volatility=round(float(rolling_vol), 4),
            adx_proxy=round(float(adx_proxy), 2),
            rsi=round(float(rsi), 2),
            distribution=distribution,
        )


regime_detector = RegimeDetector()
