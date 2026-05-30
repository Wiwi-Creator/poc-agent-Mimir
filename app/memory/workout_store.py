import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class WorkoutEntry:
    user_id: str
    exercise: str
    weight_kg: float | None
    reps: int | None
    sets: int | None
    logged_at: str
    notes: str


class WorkoutStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def add_entry(
        self,
        user_id: str,
        exercise: str,
        weight_kg: float | None,
        reps: int | None,
        sets: int | None,
        notes: str,
    ) -> WorkoutEntry:
        logged_at = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workout_entries
                    (user_id, exercise, weight_kg, reps, sets, logged_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, exercise, weight_kg, reps, sets, logged_at, notes),
            )

        return WorkoutEntry(
            user_id=user_id,
            exercise=exercise,
            weight_kg=weight_kg,
            reps=reps,
            sets=sets,
            logged_at=logged_at,
            notes=notes,
        )

    def recent_entries(
        self,
        user_id: str,
        exercise: str | None = None,
        limit: int = 5,
    ) -> list[WorkoutEntry]:
        params: list[object] = [user_id]
        where = "WHERE user_id = ?"
        if exercise:
            where += " AND lower(exercise) LIKE ?"
            params.append(f"%{exercise.lower()}%")
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT user_id, exercise, weight_kg, reps, sets, logged_at, notes
                FROM workout_entries
                {where}
                ORDER BY logged_at DESC, id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()

        return [
            WorkoutEntry(
                user_id=row["user_id"],
                exercise=row["exercise"],
                weight_kg=row["weight_kg"],
                reps=row["reps"],
                sets=row["sets"],
                logged_at=row["logged_at"],
                notes=row["notes"],
            )
            for row in rows
        ]

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workout_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    exercise TEXT NOT NULL,
                    weight_kg REAL,
                    reps INTEGER,
                    sets INTEGER,
                    logged_at TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT ''
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workout_entries_user_exercise
                ON workout_entries (user_id, exercise, logged_at)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
