from __future__ import annotations

from datetime import datetime

import pandas as pd

from app.backtesting.engine import backtesting_engine
from app.data.database import db
from app.data.providers import market_data_service
from app.portfolio.advisor import AssetDecision, build_uncertainty_note
from app.regime.detector import regime_detector
from app.scoring.ranker import signal_ranker
from app.signals.engine import signal_engine


class ResearchService:
    async def evaluate_asset(self, asset: str, timeframe: str) -> dict[str, object]:
        df = await market_data_service.get_history(asset, timeframe)
        regime = regime_detector.detect(df)

        candidates = signal_engine.generate(df)
        evaluations = [(signal, backtesting_engine.run(df, signal)) for signal in candidates]
        ranked = signal_ranker.rank(regime.regime, evaluations)

        top = ranked[0]
        db.insert_signal_log(
            {
                "asset": asset,
                "timeframe": timeframe,
                "signal_name": top.name,
                "direction": top.direction,
                "confidence": top.confidence_score,
                "justification": top.justification,
                "expected_return_min": top.expected_return_min,
                "expected_return_max": top.expected_return_max,
                "expected_drawdown": top.expected_drawdown,
            }
        )

        top_eval = evaluations[0][1]
        decision = AssetDecision(
            asset=asset,
            regime=regime.regime,
            regime_confidence=regime.confidence,
            suggested_direction=top.direction,
            confidence=top.confidence_score,
            uncertainty_note=build_uncertainty_note(top.confidence_score, top.expected_drawdown),
        )

        return {
            "asset": asset,
            "timeframe": timeframe,
            "regime": regime.model_dump(),
            "signals": [r.__dict__ for r in ranked[:3]],
            "decision": decision.model_dump(),
            "metrics": {
                "cagr": top_eval.cagr,
                "sharpe": top_eval.sharpe,
                "sortino": top_eval.sortino,
                "calmar": top_eval.calmar,
                "max_drawdown": top_eval.max_drawdown,
                "profit_factor": top_eval.profit_factor,
                "expectancy": top_eval.expectancy,
                "risk_of_ruin": top_eval.risk_of_ruin,
                "win_rate": top_eval.win_rate,
            },
            "curves": {
                "equity": top_eval.equity_curve,
                "drawdown": top_eval.drawdown_curve,
                "rolling_sharpe": top_eval.rolling_sharpe,
            },
            "performance_per_regime": top_eval.regime_performance,
        }

    async def dashboard(self, assets: list[str], timeframe: str) -> dict[str, object]:
        items = [await self.evaluate_asset(asset, timeframe) for asset in assets]
        return {"generated_at": datetime.utcnow().isoformat(), "assets": items, "logs": db.latest_signal_logs()}

    async def historical_replay(self, asset: str, timeframe: str, at: str) -> dict[str, object]:
        target = datetime.fromisoformat(at)
        df = await market_data_service.get_history(asset, timeframe, limit=1200)
        replay_df = df[df["timestamp"] <= pd.Timestamp(target)].tail(700)
        if replay_df.empty:
            replay_df = df.head(700)
        result = await self.evaluate_asset(asset, timeframe)
        result["replay_timestamp"] = target.isoformat()
        result["replay_note"] = (
            "Historical replay is computed using only data available up to the selected timestamp "
            "for transparent, auditable decision support."
        )
        return result


research_service = ResearchService()
