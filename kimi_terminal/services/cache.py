from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class Cache:
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_category ON cache(category)"
            )

    def _make_key(self, category: str, params: dict[str, Any]) -> str:
        canonical = json.dumps(params, sort_keys=True, ensure_ascii=True)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return f"{category}:{digest}"

    def get(self, category: str, params: dict[str, Any], ttl_seconds: int) -> Any | None:
        key = self._make_key(category, params)
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT payload, created_at FROM cache WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return None
        payload, created_at = row
        if time.time() - created_at > ttl_seconds:
            return None
        return json.loads(payload)

    def set(self, category: str, params: dict[str, Any], value: Any) -> None:
        key = self._make_key(category, params)
        payload = json.dumps(value, ensure_ascii=False, default=str)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO cache (key, category, payload, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    category=excluded.category,
                    payload=excluded.payload,
                    created_at=excluded.created_at
                """,
                (key, category, payload, int(time.time())),
            )

    def clear_category(self, category: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache WHERE category = ?", (category,))

    def clear_all(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache")
