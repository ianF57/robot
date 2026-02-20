# Market Signal Intelligence & Research Platform

Professional-grade **decision-support** quant research system for crypto, forex, and futures.

> Safety first: this repository **does not execute trades**, does **not connect to brokerage accounts**, and provides only transparent research signals for discretionary decision-making.

## Quickstart

```bash
pip install -r requirements.txt
python main.py
```

`python main.py` starts FastAPI and automatically opens the dashboard in your default browser.

## Architecture

```
/app
    /data          # SQLite logging + unified data service (async)
    /features      # orchestration services (dashboard, replay)
    /regime        # market regime detector
    /signals       # modular, versioned signal definitions and generator
    /backtesting   # walk-forward style evaluation + metrics + Monte Carlo proxy
    /scoring       # robustness ranker + confidence scoring
    /portfolio     # decision-support summaries and uncertainty notes
    /api           # FastAPI routes/server
    /ui            # institutional dashboard templates/static assets
main.py
config.py
requirements.txt
README.md
```

## Core features

- Unified market data interface with async fetching and timeframe validation (`1m`, `5m`, `1h`, `1d`, `1w`).
- Regime detection: trending/ranging/high-vol/low-vol/momentum-breakout/mean-reversion + confidence.
- Signal engine: modular, parameterized, versioned signals with entry/exit/stop/risk-reward metadata.
- Institutional-style backtesting metrics: CAGR, Sharpe, Sortino, Calmar, max drawdown, profit factor, expectancy, risk of ruin, win rate.
- Robustness checks: out-of-sample scoring, Monte Carlo proxy, parameter sensitivity penalty.
- Signal ranking + confidence (0-100) with explicit penalties for overfitting and drawdown.
- Historical replay mode for auditable “what was known then” analysis.
- SQLite logging of recommendations + justification trail.

## API endpoints

- `GET /api/dashboard?timeframe=1h`
- `GET /api/replay?asset=BTCUSDT&timeframe=1h&at=2025-01-01T00:00:00`

## Transparency and risk policy

- No guaranteed returns.
- Drawdown and uncertainty are shown prominently.
- Outputs are recommendations for discretionary review, not automated execution instructions.

## Future extensibility

The modular structure supports:
- machine-learning regime classifiers,
- reinforcement learning for signal ideas,
- portfolio optimization,
- cloud/SaaS deployment,
- external REST consumers.
