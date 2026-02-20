from __future__ import annotations

from dataclasses import dataclass

from app.backtesting.engine import BacktestResult
from app.signals.engine import SignalCandidate


@dataclass(slots=True)
class RankedSignal:
    name: str
    version: str
    strategy_type: str
    direction: str
    confidence_score: float
    expected_return_min: float
    expected_return_max: float
    expected_drawdown: float
    justification: str


class SignalRanker:
    def rank(
        self,
        regime: str,
        evaluations: list[tuple[SignalCandidate, BacktestResult]],
    ) -> list[RankedSignal]:
        ranked: list[RankedSignal] = []
        for signal, result in evaluations:
            regime_bonus = 12 if regime in signal.definition.regime_compatibility else -18
            drawdown_penalty = result.max_drawdown * 90
            overfit_penalty = max(result.parameter_sensitivity - 18, 0)

            score = (
                result.oos_score * 0.35
                + result.stability_score * 0.2
                + (result.sharpe + 2) * 12
                + regime_bonus
                - drawdown_penalty
                - overfit_penalty
            )
            score = max(0.0, min(100.0, score))

            ranked.append(
                RankedSignal(
                    name=signal.definition.name,
                    version=signal.definition.version,
                    strategy_type=signal.definition.strategy_type,
                    direction=signal.direction,
                    confidence_score=round(score, 2),
                    expected_return_min=round(result.expectancy * 200 * 0.75, 3),
                    expected_return_max=round(result.expectancy * 200 * 1.25, 3),
                    expected_drawdown=round(result.max_drawdown * 100, 2),
                    justification=(
                        f"OOS={result.oos_score:.1f}, stability={result.stability_score:.1f}, "
                        f"regime alignment={'yes' if regime in signal.definition.regime_compatibility else 'no'}, "
                        f"sensitivity={result.parameter_sensitivity:.2f}"
                    ),
                )
            )

        return sorted(ranked, key=lambda r: r.confidence_score, reverse=True)


signal_ranker = SignalRanker()
