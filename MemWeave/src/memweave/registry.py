"""Local SQLite registry for completed MemWeave experiment runs.

The registry stores provenance pointers and compact summaries, not benchmark data
or per-question predictions. It is safe to recreate from run manifests if needed.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('completed')),
    output_dir TEXT NOT NULL,
    input_sha256 TEXT,
    manifest_sha256 TEXT NOT NULL,
    config_json TEXT NOT NULL,
    summary_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at DESC);
"""


class RunRegistry:
    """Append-only index of completed runs stored in a local SQLite database."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            connection.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def record(
        self,
        *,
        run_id: str,
        output_dir: str | Path,
        manifest_sha256: str,
        config: dict[str, Any],
        summary: dict[str, Any],
        input_sha256: str | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        """Insert a completed run. Duplicate run IDs are rejected, never overwritten."""
        if not run_id or not manifest_sha256:
            raise ValueError("run_id and manifest_sha256 must be non-empty")
        timestamp = created_at or datetime.now(timezone.utc).isoformat()
        record = {
            "run_id": run_id,
            "created_at": timestamp,
            "status": "completed",
            "output_dir": str(Path(output_dir).expanduser().resolve()),
            "input_sha256": input_sha256,
            "manifest_sha256": manifest_sha256,
            "config_json": json.dumps(config, sort_keys=True, default=str),
            "summary_json": json.dumps(summary, sort_keys=True, default=str),
        }
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO runs
                (run_id, created_at, status, output_dir, input_sha256,
                 manifest_sha256, config_json, summary_json)
                VALUES (:run_id, :created_at, :status, :output_dir, :input_sha256,
                        :manifest_sha256, :config_json, :summary_json)""",
                record,
            )
        return self.get(run_id)

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        if not isinstance(limit, int) or limit < 1 or limit > 1000:
            raise ValueError("limit must be an integer between 1 and 1000")
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM runs ORDER BY created_at DESC, run_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._decode(row) for row in rows]

    def get(self, run_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"Run not found: {run_id}")
        return self._decode(row)

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["config"] = json.loads(item.pop("config_json"))
        item["summary"] = json.loads(item.pop("summary_json"))
        return item
