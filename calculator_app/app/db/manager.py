"""
app/db/manager.py
-----------------
SQLite persistence layer for API requests and user sessions.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import uuid
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages the SQLite database for request logging and session storage."""

    def __init__(self, db_path: str = None) -> None:
        if db_path:
            self.db_path = db_path
        else:
            env_path = os.environ.get("DB_PATH")
            if env_path:
                self.db_path = env_path
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                data_dir = os.path.join(base_dir, "..", "..", "data")
                os.makedirs(data_dir, exist_ok=True)
                self.db_path = os.path.join(data_dir, "calculator_api.db")

        self._init_database()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_database(self) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_requests (
                    id           TEXT PRIMARY KEY,
                    operation_type TEXT NOT NULL,
                    input_value  TEXT NOT NULL,
                    result       TEXT,
                    status       TEXT NOT NULL,
                    error_message TEXT,
                    timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address   TEXT,
                    user_agent   TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id  TEXT PRIMARY KEY,
                    last_choice INTEGER DEFAULT 0,
                    last_input  TEXT    DEFAULT '',
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        logger.info("Database initialised at %s", self.db_path)

    # ------------------------------------------------------------------
    # Connection helper
    # ------------------------------------------------------------------

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception as exc:
            conn.rollback()
            logger.error("Database error: %s", exc)
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Request logging
    # ------------------------------------------------------------------

    def log_request(
        self,
        operation_type: str,
        input_value: str,
        result: str = None,
        status: str = "success",
        error_message: str = None,
        ip_address: str = None,
        user_agent: str = None,
    ) -> str:
        request_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO api_requests
                    (id, operation_type, input_value, result, status, error_message, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (request_id, operation_type, input_value, result, status,
                 error_message, ip_address, user_agent),
            )
            conn.commit()
        return request_id

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def get_session(self, session_id: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM user_sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        return dict(row) if row else None

    def update_session(
        self,
        session_id: str,
        last_choice: int = None,
        last_input: str = None,
    ) -> None:
        with self.get_connection() as conn:
            exists = conn.execute(
                "SELECT 1 FROM user_sessions WHERE session_id = ?", (session_id,)
            ).fetchone()

            if exists:
                fields, values = [], []
                if last_choice is not None:
                    fields.append("last_choice = ?")
                    values.append(last_choice)
                if last_input is not None:
                    fields.append("last_input = ?")
                    values.append(last_input)
                if fields:
                    fields.append("updated_at = CURRENT_TIMESTAMP")
                    values.append(session_id)
                    conn.execute(
                        f"UPDATE user_sessions SET {', '.join(fields)} WHERE session_id = ?",
                        values,
                    )
            else:
                conn.execute(
                    "INSERT INTO user_sessions (session_id, last_choice, last_input) VALUES (?, ?, ?)",
                    (session_id, last_choice or 0, last_input or ""),
                )
            conn.commit()

    # ------------------------------------------------------------------
    # History & analytics
    # ------------------------------------------------------------------

    def get_request_history(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM api_requests ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_analytics(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) AS n FROM api_requests").fetchone()["n"]

            op_rows = conn.execute(
                "SELECT operation_type, COUNT(*) AS c FROM api_requests GROUP BY operation_type"
            ).fetchall()

            status_rows = conn.execute(
                "SELECT status, COUNT(*) AS c FROM api_requests GROUP BY status"
            ).fetchall()

        return {
            "total_requests": total,
            "operation_stats": {r["operation_type"]: r["c"] for r in op_rows},
            "status_stats":    {r["status"]: r["c"]          for r in status_rows},
        }