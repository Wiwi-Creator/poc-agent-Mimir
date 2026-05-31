import re
from dataclasses import dataclass


EXERCISE_ALIASES = {
    "bench": ["bench", "bench press", "臥推"],
    "squat": ["squat", "深蹲"],
    "deadlift": ["deadlift", "硬舉", "硬拉"],
    "overhead press": ["overhead press", "shoulder press", "ohp", "肩推"],
    "row": ["row", "划船"],
    "pull-up": ["pull-up", "pullup", "引體向上", "引体向上"],
}


@dataclass(frozen=True)
class ParsedWorkout:
    exercise: str
    weight_kg: float | None
    reps: int | None
    sets: int | None


def is_workout_log_request(message: str) -> bool:
    normalized = message.lower()
    log_keywords = {
        "log",
        "record",
        "tracked",
        "記錄",
        "紀錄",
        "登記",
    }
    return any(keyword in normalized for keyword in log_keywords)


def parse_workout_entry(message: str) -> ParsedWorkout | None:
    exercise = _find_exercise(message)
    if not exercise:
        return None

    weight_kg = _find_weight_kg(message)
    reps = _find_reps(message)
    sets = _find_sets(message)

    return ParsedWorkout(
        exercise=exercise,
        weight_kg=weight_kg,
        reps=reps,
        sets=sets,
    )


def extract_exercise_hint(message: str) -> str | None:
    return _find_exercise(message)


def format_workout_entry(entry: ParsedWorkout) -> str:
    parts = [entry.exercise]
    if entry.weight_kg is not None:
        parts.append(f"{entry.weight_kg:g}kg")
    if entry.sets is not None:
        parts.append(f"{entry.sets} sets")
    if entry.reps is not None:
        parts.append(f"{entry.reps} reps")
    return ", ".join(parts)


def _find_exercise(message: str) -> str | None:
    normalized = message.lower()
    for canonical, aliases in EXERCISE_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            return canonical
    return None


def _find_weight_kg(message: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|公斤|公克)", message, re.IGNORECASE)
    if not match:
        return None
    return float(match.group(1))


def _find_reps(message: str) -> int | None:
    patterns = [
        r"(\d+)\s*(?:reps?|次|下)",
        r"for\s+(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _find_sets(message: str) -> int | None:
    patterns = [
        r"(\d+)\s*(?:sets?|組)",
        r"(\d+)\s*x\s*\d+",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None
