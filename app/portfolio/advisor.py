from __future__ import annotations

from pydantic import BaseModel


class AssetDecision(BaseModel):
    asset: str
    regime: str
    regime_confidence: float
    suggested_direction: str
    confidence: float
    uncertainty_note: str


def build_uncertainty_note(confidence: float, drawdown: float) -> str:
    if confidence >= 75 and drawdown < 10:
        return "Higher-conviction research signal, still subject to model risk and non-stationarity."
    if confidence >= 55:
        return "Moderate-conviction setup; discretionary confirmation is recommended."
    return "Low-conviction environment. Stand aside or reduce risk until clearer structure emerges."
