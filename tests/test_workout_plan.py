from app.planning.plan_store import WorkoutPlanStore
from app.planning.workout_plan import build_default_plan, format_plan, is_plan_request


def test_build_default_plan_from_request():
    plan = build_default_plan("Build me a 4-day workout plan for hypertrophy")

    assert plan.days_per_week == 4
    assert plan.goal == "hypertrophy"
    assert plan.days[0].day == "Monday"
    assert plan.days[0].exercises[0].name == "Chest press"
    assert "Chest press" in format_plan(plan)


def test_detects_chinese_plan_request():
    assert is_plan_request("幫我安排一週四天重訓課表")


def test_plan_store_saves_and_reads_latest_plan(tmp_path):
    store = WorkoutPlanStore(str(tmp_path / "plans.sqlite3"))
    plan = build_default_plan("Build me a 3-day strength plan")

    store.save_plan("user-1", plan)
    latest = store.latest_plan("user-1")

    assert latest is not None
    assert latest.plan.days_per_week == 3
    assert latest.plan.goal == "strength"

