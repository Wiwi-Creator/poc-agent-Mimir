import sqlite3
from pathlib import Path


class UserStateStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def has_seen_intro(self, user_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT seen_intro FROM user_state WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return bool(row and row["seen_intro"])

    def mark_seen_intro(self, user_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_state (user_id, seen_intro)
                VALUES (?, 1)
                ON CONFLICT(user_id) DO UPDATE SET seen_intro = 1
                """,
                (user_id,),
            )

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_state (
                    user_id TEXT PRIMARY KEY,
                    seen_intro INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

