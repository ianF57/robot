from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(slots=True)
class SignalDefinition:
    name: str
    version: str
    strategy_type: str
    timeframe_compatibility: list[str]
    regime_compatibility: list[str]
    parameters: dict[str, float]


@dataclass(slots=True)
class SignalCandidate:
    definition: SignalDefinition
    direction: str
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float


class SignalEngine:
    def __init__(self) -> None:
        self.definitions = [
            SignalDefinition(
                name="EMA Trend Following",
                version="1.0.0",
                strategy_type="trend",
                timeframe_compatibility=["5m", "1h", "1d"],
                regime_compatibility=["trending", "momentum_breakout"],
                parameters={"fast": 20, "slow": 50},
            ),
            SignalDefinition(
                name="Bollinger Mean Reversion",
                version="1.0.0",
                strategy_type="mean_reversion",
                timeframe_compatibility=["1m", "5m", "1h"],
                regime_compatibility=["ranging", "mean_reversion", "low_volatility"],
                parameters={"window": 20, "std": 2},
            ),
            SignalDefinition(
                name="Donchian Breakout",
                version="1.1.0",
                strategy_type="breakout",
                timeframe_compatibility=["1h", "1d", "1w"],
                regime_compatibility=["high_volatility", "momentum_breakout"],
                parameters={"window": 30},
            ),
        ]

    def generate(self, df: pd.DataFrame) -> list[SignalCandidate]:
        close = df["close"]
        latest = float(close.iloc[-1])
        candidates: list[SignalCandidate] = []

        fast = close.ewm(span=20).mean().iloc[-1]
        slow = close.ewm(span=50).mean().iloc[-1]
        direction = "Long" if fast > slow else "Short"
        stop = latest * (0.985 if direction == "Long" else 1.015)
        tp = latest * (1.03 if direction == "Long" else 0.97)
        candidates.append(
            SignalCandidate(self.definitions[0], direction, latest, stop, tp, 2.0)
        )

        ma = close.rolling(20).mean().iloc[-1]
        sd = close.rolling(20).std().iloc[-1]
        upper = ma + 2 * sd
        lower = ma - 2 * sd
        if latest > upper:
            mr_direction = "Short"
        elif latest < lower:
            mr_direction = "Long"
        else:
            mr_direction = "Neutral"
        mr_stop = latest * (0.99 if mr_direction == "Long" else 1.01)
        mr_tp = latest * (1.015 if mr_direction == "Long" else 0.985)
        candidates.append(
            SignalCandidate(self.definitions[1], mr_direction, latest, mr_stop, mr_tp, 1.5)
        )

        high = df["high"].rolling(30).max().iloc[-1]
        low = df["low"].rolling(30).min().iloc[-1]
        bo_direction = "Long" if latest >= high * 0.995 else ("Short" if latest <= low * 1.005 else "Neutral")
        bo_stop = latest * (0.98 if bo_direction == "Long" else 1.02)
        bo_tp = latest * (1.04 if bo_direction == "Long" else 0.96)
        candidates.append(
            SignalCandidate(self.definitions[2], bo_direction, latest, bo_stop, bo_tp, 2.2)
        )

        return candidates


signal_engine = SignalEngine()
