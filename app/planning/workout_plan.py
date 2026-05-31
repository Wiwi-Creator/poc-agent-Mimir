from pydantic import BaseModel, Field


class PlannedExercise(BaseModel):
    name: str
    sets: int
    reps: str
    notes: str = ""


class PlannedWorkoutDay(BaseModel):
    day: str
    focus: str
    exercises: list[PlannedExercise] = Field(default_factory=list)


class WorkoutPlan(BaseModel):
    title: str
    goal: str
    days_per_week: int
    days: list[PlannedWorkoutDay] = Field(default_factory=list)


def build_default_plan(message: str) -> WorkoutPlan:
    goal = _infer_goal(message)
    days_per_week = _infer_days_per_week(message)
    days = _default_days(days_per_week)
    return WorkoutPlan(
        title=f"{days_per_week}-Day {goal.title()} Training Plan",
        goal=goal,
        days_per_week=days_per_week,
        days=days,
    )


def is_plan_request(message: str) -> bool:
    normalized = message.lower()
    keywords = {
        "plan",
        "program",
        "routine",
        "schedule",
        "weekly",
        "一週",
        "一周",
        "課表",
        "計畫",
        "安排",
        "菜單",
    }
    training_terms = {
        "workout",
        "training",
        "gym",
        "lift",
        "健身",
        "訓練",
        "重訓",
        "增肌",
        "減脂",
    }
    return any(keyword in normalized for keyword in keywords) and any(
        term in normalized for term in training_terms
    )


def format_plan(plan: WorkoutPlan) -> str:
    lines = [
        "Saved workout plan:",
        f"- Title: {plan.title}",
        f"- Goal: {plan.goal}",
        f"- Days per week: {plan.days_per_week}",
    ]
    for day in plan.days:
        lines.append(f"- {day.day}: {day.focus}")
        for exercise in day.exercises:
            lines.append(
                f"  - {exercise.name}: {exercise.sets} sets x {exercise.reps}"
            )
    return "\n".join(lines)


def _infer_goal(message: str) -> str:
    normalized = message.lower()
    if any(term in normalized for term in {"strength", "力量", "肌力"}):
        return "strength"
    if any(term in normalized for term in {"fat loss", "cut", "減脂"}):
        return "fat loss"
    return "hypertrophy"


def _infer_days_per_week(message: str) -> int:
    normalized = message.lower()
    day_patterns = {
        2: {"2 day", "2-day", "twice", "兩天", "二天", "2天"},
        3: {"3 day", "3-day", "three", "三天", "3天"},
        4: {"4 day", "4-day", "four", "四天", "4天"},
        5: {"5 day", "5-day", "five", "五天", "5天"},
        6: {"6 day", "6-day", "six", "六天", "6天"},
    }
    for days, patterns in day_patterns.items():
        if any(pattern in normalized for pattern in patterns):
            return days
    return 4


def _default_days(days_per_week: int) -> list[PlannedWorkoutDay]:
    templates = [
        PlannedWorkoutDay(
            day="Monday",
            focus="Push / Chest",
            exercises=[
                PlannedExercise(name="Chest press", sets=4, reps="8-10"),
                PlannedExercise(name="Incline dumbbell press", sets=3, reps="8-12"),
                PlannedExercise(name="Cable fly", sets=3, reps="12-15"),
            ],
        ),
        PlannedWorkoutDay(
            day="Tuesday",
            focus="Lower Body",
            exercises=[
                PlannedExercise(name="Squat", sets=4, reps="5-8"),
                PlannedExercise(name="Romanian deadlift", sets=3, reps="8-10"),
                PlannedExercise(name="Leg press", sets=3, reps="10-12"),
            ],
        ),
        PlannedWorkoutDay(
            day="Thursday",
            focus="Pull / Back",
            exercises=[
                PlannedExercise(name="Lat pulldown", sets=4, reps="8-12"),
                PlannedExercise(name="Seated row", sets=3, reps="8-12"),
                PlannedExercise(name="Face pull", sets=3, reps="12-15"),
            ],
        ),
        PlannedWorkoutDay(
            day="Saturday",
            focus="Full Body / Accessories",
            exercises=[
                PlannedExercise(name="Deadlift", sets=3, reps="3-5"),
                PlannedExercise(name="Overhead press", sets=3, reps="6-10"),
                PlannedExercise(name="Lateral raise", sets=3, reps="12-15"),
            ],
        ),
        PlannedWorkoutDay(
            day="Wednesday",
            focus="Arms / Conditioning",
            exercises=[
                PlannedExercise(name="Biceps curl", sets=3, reps="10-12"),
                PlannedExercise(name="Triceps pushdown", sets=3, reps="10-12"),
                PlannedExercise(name="Zone 2 cardio", sets=1, reps="20-30 min"),
            ],
        ),
        PlannedWorkoutDay(
            day="Sunday",
            focus="Mobility / Recovery",
            exercises=[
                PlannedExercise(name="Hip mobility", sets=2, reps="8-10 min"),
                PlannedExercise(name="Thoracic rotation", sets=2, reps="8/side"),
                PlannedExercise(name="Easy walk", sets=1, reps="20-40 min"),
            ],
        ),
    ]
    return templates[:days_per_week]
