from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

import pandas as pd

from app.api.schemas import (
    AssetAnalysisResponse,
    AssetDecisionResponse,
    CurvesResponse,
    DashboardResponse,
    MetricsResponse,
    RankedSignalResponse,
    ReplayResponse,
    SignalLogEntry,
)
from app.backtesting.engine import backtesting_engine
from app.data.database import db
from app.data.providers import market_data_service
from app.portfolio.advisor import AssetDecision, build_uncertainty_note
from app.regime.detector import regime_detector
from app.scoring.ranker import signal_ranker
from app.signals.engine import signal_engine


class ResearchService:
    @staticmethod
    def _normalize_cutoff_timestamp(at: datetime) -> pd.Timestamp:
        """Normalize replay cutoff to UTC-naive to safely compare with local OHLCV timestamps."""
        if at.tzinfo is not None:
            at = at.astimezone(timezone.utc).replace(tzinfo=None)
        return pd.Timestamp(at)

    @staticmethod
    def _normalize_dataframe_timestamps(df: pd.DataFrame) -> pd.Series:
        """Force datetime series to UTC-naive to avoid tz-aware/naive comparison errors."""
        return pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(None)

    def _evaluate_dataframe(self, asset: str, timeframe: str, df: pd.DataFrame) -> AssetAnalysisResponse:
        regime = regime_detector.detect(df)
        candidates = signal_engine.generate(df)
        evaluations = [(signal, backtesting_engine.run(df, signal)) for signal in candidates]
        ranked = signal_ranker.rank(regime.regime, evaluations)

        top_ranked = ranked[0]
        top_eval = next(
            result
            for signal, result in evaluations
            if signal.definition.name == top_ranked.name
            and signal.definition.version == top_ranked.version
        )

        db.insert_signal_log(
            {
                "asset": asset,
                "timeframe": timeframe,
                "signal_name": top_ranked.name,
                "direction": top_ranked.direction,
                "confidence": top_ranked.confidence_score,
                "justification": top_ranked.justification,
                "expected_return_min": top_ranked.expected_return_min,
                "expected_return_max": top_ranked.expected_return_max,
                "expected_drawdown": top_ranked.expected_drawdown,
            }
        )

        decision = AssetDecision(
            asset=asset,
            regime=regime.regime,
            regime_confidence=regime.confidence,
            suggested_direction=top_ranked.direction,
            confidence=top_ranked.confidence_score,
            uncertainty_note=build_uncertainty_note(top_ranked.confidence_score, top_ranked.expected_drawdown),
        )

        return AssetAnalysisResponse(
            asset=asset,
            timeframe=timeframe,
            regime=regime,
            signals=[RankedSignalResponse(**asdict(item)) for item in ranked[:3]],
            decision=AssetDecisionResponse(**decision.model_dump()),
            metrics=MetricsResponse(
                cagr=top_eval.cagr,
                sharpe=top_eval.sharpe,
                sortino=top_eval.sortino,
                calmar=top_eval.calmar,
                max_drawdown=top_eval.max_drawdown,
                profit_factor=top_eval.profit_factor,
                expectancy=top_eval.expectancy,
                risk_of_ruin=top_eval.risk_of_ruin,
                win_rate=top_eval.win_rate,
            ),
            curves=CurvesResponse(
                equity=top_eval.equity_curve,
                drawdown=top_eval.drawdown_curve,
                rolling_sharpe=top_eval.rolling_sharpe,
            ),
            performance_per_regime=top_eval.regime_performance,
        )

    async def evaluate_asset(self, asset: str, timeframe: str) -> AssetAnalysisResponse:
        df = await market_data_service.get_history(asset, timeframe)
        return self._evaluate_dataframe(asset, timeframe, df)

    async def dashboard(self, assets: list[str], timeframe: str) -> DashboardResponse:
        items = [await self.evaluate_asset(asset, timeframe) for asset in assets]
        logs = [SignalLogEntry(**row) for row in db.latest_signal_logs()]
        return DashboardResponse(
            generated_at=datetime.utcnow(),
            assets=items,
            logs=logs,
        )

    async def historical_replay(self, asset: str, timeframe: str, at: datetime) -> ReplayResponse:
        df = await market_data_service.get_history(asset, timeframe, limit=1200)
        cutoff = self._normalize_cutoff_timestamp(at)
        timestamps = self._normalize_dataframe_timestamps(df)

        replay_df = df[timestamps <= cutoff].tail(700)
        if replay_df.empty:
            replay_df = df.head(700)

        result = self._evaluate_dataframe(asset, timeframe, replay_df)
        return ReplayResponse(
            **result.model_dump(),
            replay_timestamp=at,
            replay_note=(
                "Historical replay is computed using only data available up to the selected timestamp "
                "for transparent, auditable decision support."
            ),
        )


research_service = ResearchService()
