from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SignalLogEntry(BaseModel):
    id: int
    created_at: datetime
    asset: str
    timeframe: str
    signal_name: str
    direction: str
    confidence: float
    justification: str
    expected_return_min: float
    expected_return_max: float
    expected_drawdown: float


class MetricsResponse(BaseModel):
    cagr: float
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float
    profit_factor: float
    expectancy: float
    risk_of_ruin: float
    win_rate: float


class CurvesResponse(BaseModel):
    equity: list[float]
    drawdown: list[float]
    rolling_sharpe: list[float]


class RankedSignalResponse(BaseModel):
    name: str
    version: str
    strategy_type: str
    direction: str
    confidence_score: float = Field(ge=0, le=100)
    expected_return_min: float
    expected_return_max: float
    expected_drawdown: float
    justification: str


class AssetDecisionResponse(BaseModel):
    asset: str
    regime: str
    regime_confidence: float
    suggested_direction: str
    confidence: float = Field(ge=0, le=100)
    uncertainty_note: str


class RegimeResponse(BaseModel):
    regime: str
    confidence: float = Field(ge=0, le=100)
    volatility: float
    adx_proxy: float
    rsi: float
    distribution: dict[str, float]


class AssetAnalysisResponse(BaseModel):
    asset: str
    timeframe: str
    regime: RegimeResponse
    signals: list[RankedSignalResponse]
    decision: AssetDecisionResponse
    metrics: MetricsResponse
    curves: CurvesResponse
    performance_per_regime: dict[str, float]


class DashboardResponse(BaseModel):
    generated_at: datetime
    assets: list[AssetAnalysisResponse]
    logs: list[SignalLogEntry]


class ReplayResponse(AssetAnalysisResponse):
    replay_timestamp: datetime
    replay_note: str
