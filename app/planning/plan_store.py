import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.planning.workout_plan import WorkoutPlan


@dataclass(frozen=True)
class StoredWorkoutPlan:
    user_id: str
    plan: WorkoutPlan
    created_at: str


class WorkoutPlanStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def save_plan(self, user_id: str, plan: WorkoutPlan) -> StoredWorkoutPlan:
        created_at = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workout_plans (user_id, plan_json, created_at)
                VALUES (?, ?, ?)
                """,
                (user_id, plan.model_dump_json(), created_at),
            )
        return StoredWorkoutPlan(user_id=user_id, plan=plan, created_at=created_at)

    def latest_plan(self, user_id: str) -> StoredWorkoutPlan | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT user_id, plan_json, created_at
                FROM workout_plans
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        if not row:
            return None
        return StoredWorkoutPlan(
            user_id=row["user_id"],
            plan=WorkoutPlan.model_validate(json.loads(row["plan_json"])),
            created_at=row["created_at"],
        )

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workout_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    plan_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workout_plans_user_created
                ON workout_plans (user_id, created_at)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

