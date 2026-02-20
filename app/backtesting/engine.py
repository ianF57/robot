from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import settings
from app.signals.engine import SignalCandidate


@dataclass(slots=True)
class BacktestResult:
    cagr: float
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float
    profit_factor: float
    expectancy: float
    risk_of_ruin: float
    win_rate: float
    equity_curve: list[float]
    drawdown_curve: list[float]
    rolling_sharpe: list[float]
    regime_performance: dict[str, float]
    oos_score: float
    stability_score: float
    parameter_sensitivity: float


class BacktestingEngine:
    def run(self, df: pd.DataFrame, signal: SignalCandidate) -> BacktestResult:
        returns = df["close"].pct_change().fillna(0)
        direction = 1 if signal.direction == "Long" else -1 if signal.direction == "Short" else 0
        strat_returns = returns * direction

        friction = (settings.transaction_cost_bps + settings.slippage_bps) / 10_000
        strat_returns = strat_returns - abs(strat_returns) * friction

        split = int(len(strat_returns) * 0.7)
        in_sample = strat_returns.iloc[:split]
        out_of_sample = strat_returns.iloc[split:]

        equity = (1 + strat_returns).cumprod()
        peak = equity.cummax()
        dd = (equity - peak) / peak

        ann_factor = 252
        mean = strat_returns.mean()
        std = strat_returns.std() + 1e-9
        downside = strat_returns[strat_returns < 0].std() + 1e-9

        cagr = (equity.iloc[-1] ** (ann_factor / max(len(strat_returns), 1))) - 1
        sharpe = (mean / std) * np.sqrt(ann_factor)
        sortino = (mean / downside) * np.sqrt(ann_factor)
        max_drawdown = abs(dd.min())
        calmar = cagr / (max_drawdown + 1e-9)

        wins = strat_returns[strat_returns > 0]
        losses = strat_returns[strat_returns < 0]
        profit_factor = abs(wins.sum() / (losses.sum() + 1e-9))
        win_rate = len(wins) / max(len(strat_returns), 1)
        expectancy = float(strat_returns.mean())
        risk_of_ruin = float(np.clip((1 - win_rate) ** 2 * (1 + max_drawdown), 0, 1))

        rolling_sharpe = (
            strat_returns.rolling(60).mean() / (strat_returns.rolling(60).std() + 1e-9)
        ).fillna(0) * np.sqrt(ann_factor)

        oos_score = float(np.clip(out_of_sample.mean() / (out_of_sample.std() + 1e-9) * 40 + 50, 0, 100))
        stability_score = float(np.clip((out_of_sample.mean() - in_sample.std()) * 5000 + 50, 0, 100))

        shocked_returns = []
        for _ in range(100):
            sample = np.random.choice(strat_returns, size=len(strat_returns), replace=True)
            shocked_returns.append(float(np.mean(sample)))
        parameter_sensitivity = float(np.std(shocked_returns) * 10000)

        regime_performance = {
            "trending": float(in_sample.mean() * 100),
            "ranging": float(out_of_sample.mean() * 100),
            "high_volatility": float(strat_returns.std() * 100),
            "low_volatility": float((1 - strat_returns.std()) * 100),
        }

        return BacktestResult(
            cagr=float(cagr),
            sharpe=float(sharpe),
            sortino=float(sortino),
            calmar=float(calmar),
            max_drawdown=float(max_drawdown),
            profit_factor=float(profit_factor),
            expectancy=expectancy,
            risk_of_ruin=risk_of_ruin,
            win_rate=float(win_rate),
            equity_curve=[float(x) for x in equity.tail(250).tolist()],
            drawdown_curve=[float(x) for x in dd.tail(250).tolist()],
            rolling_sharpe=[float(x) for x in rolling_sharpe.tail(250).tolist()],
            regime_performance=regime_performance,
            oos_score=oos_score,
            stability_score=stability_score,
            parameter_sensitivity=parameter_sensitivity,
        )


backtesting_engine = BacktestingEngine()
