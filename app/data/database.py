from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from config import settings


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _initialize(self) -> None:
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS signal_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    signal_name TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    justification TEXT NOT NULL,
                    expected_return_min REAL NOT NULL,
                    expected_return_max REAL NOT NULL,
                    expected_drawdown REAL NOT NULL
                );
                """
            )

    def insert_signal_log(self, payload: dict[str, object]) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO signal_logs (
                    created_at, asset, timeframe, signal_name, direction, confidence,
                    justification, expected_return_min, expected_return_max, expected_drawdown
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    payload["asset"],
                    payload["timeframe"],
                    payload["signal_name"],
                    payload["direction"],
                    payload["confidence"],
                    payload["justification"],
                    payload["expected_return_min"],
                    payload["expected_return_max"],
                    payload["expected_drawdown"],
                ),
            )

    def latest_signal_logs(self, limit: int = 15) -> list[dict[str, object]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM signal_logs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]


db = Database(settings.database_path)
