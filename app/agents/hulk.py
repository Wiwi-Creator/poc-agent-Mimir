from app.agents.prompts import HULK_SYSTEM_PROMPT
from app.llm.groq_client import GroqClient
from app.memory.workout_store import WorkoutEntry, WorkoutStore
from app.planning.plan_store import WorkoutPlanStore
from app.planning.workout_plan import build_default_plan, format_plan, is_plan_request
from app.schemas import LLMMessage
from app.tools.hulk_tools import HulkToolRegistry
from app.tools.models import ToolResult
from app.tools.workout_parser import (
    extract_exercise_hint,
    is_workout_log_request,
    parse_workout_entry,
)


class HulkAgent:
    name = "Hulk"

    def __init__(
        self,
        groq_client: GroqClient,
        workout_store: WorkoutStore | None = None,
        plan_store: WorkoutPlanStore | None = None,
        tool_registry: HulkToolRegistry | None = None,
    ) -> None:
        self.groq_client = groq_client
        self.workout_store = workout_store
        self.plan_store = plan_store
        self.tool_registry = tool_registry or HulkToolRegistry()

    async def respond(self, message: str, user_id: str = "local-user") -> str:
        context_blocks = []

        if self.plan_store and is_plan_request(message):
            plan = build_default_plan(message)
            self.plan_store.save_plan(user_id=user_id, plan=plan)
            context_blocks.append(format_plan(plan))
        elif self.plan_store:
            latest_plan = self.plan_store.latest_plan(user_id)
            if latest_plan:
                context_blocks.append(
                    "Latest saved workout plan:\n" + format_plan(latest_plan.plan)
                )

        if self.workout_store and is_workout_log_request(message):
            parsed_workout = parse_workout_entry(message)
            if parsed_workout:
                saved_entry = self.workout_store.add_entry(
                    user_id=user_id,
                    exercise=parsed_workout.exercise,
                    weight_kg=parsed_workout.weight_kg,
                    reps=parsed_workout.reps,
                    sets=parsed_workout.sets,
                    notes=message,
                )
                context_blocks.append(_format_saved_workout_context(saved_entry))

        if self.workout_store:
            exercise_hint = extract_exercise_hint(message)
            recent_entries = self.workout_store.recent_entries(
                user_id=user_id,
                exercise=exercise_hint,
                limit=5,
            )
            if recent_entries:
                context_blocks.append(_format_recent_workouts_context(recent_entries))

        tool_results = await self._gather_tool_context(message)
        for result in tool_results:
            context_blocks.append(_format_tool_result(result))

        user_content = message
        if context_blocks:
            user_content = (
                f"{message}\n\n"
                "Use this private Hulk context when useful. Do not invent facts "
                "that are not supported by the context.\n\n"
                + "\n\n".join(context_blocks)
            )

        return await self.groq_client.chat(
            [
                LLMMessage(role="system", content=HULK_SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_content),
            ],
            temperature=0.35,
        )

    async def _gather_tool_context(self, message: str) -> list[ToolResult]:
        results = []
        if _should_lookup_food(message):
            results.append(await self.tool_registry.get_taiwan_food_info(message))
        if _should_lookup_research(message):
            results.append(
                await self.tool_registry.get_scientific_workout_research(message)
            )
        return results


def _should_lookup_food(message: str) -> bool:
    normalized = message.lower()
    keywords = {
        "7-11",
        "familymart",
        "全家",
        "便利商店",
        "restaurant",
        "餐廳",
        "便當",
        "雞肉飯",
        "牛肉麵",
        "hotpot",
        "火鍋",
    }
    nutrition_terms = {"calorie", "calories", "macro", "macros", "熱量", "卡路里"}
    return any(keyword in normalized for keyword in keywords) and any(
        term in normalized for term in nutrition_terms
    )


def _should_lookup_research(message: str) -> bool:
    normalized = message.lower()
    return any(
        keyword in normalized
        for keyword in {
            "research",
            "study",
            "science",
            "evidence",
            "pubmed",
            "研究",
            "科學",
            "證據",
        }
    )


def _format_saved_workout_context(entry: WorkoutEntry) -> str:
    return (
        "Saved workout log:\n"
        f"- Exercise: {entry.exercise}\n"
        f"- Weight: {_format_optional(entry.weight_kg, 'kg')}\n"
        f"- Sets: {_format_optional(entry.sets)}\n"
        f"- Reps: {_format_optional(entry.reps)}"
    )


def _format_recent_workouts_context(entries: list[WorkoutEntry]) -> str:
    lines = ["Recent workout history:"]
    for entry in entries:
        parts = [entry.exercise]
        if entry.weight_kg is not None:
            parts.append(f"{entry.weight_kg:g}kg")
        if entry.sets is not None:
            parts.append(f"{entry.sets} sets")
        if entry.reps is not None:
            parts.append(f"{entry.reps} reps")
        lines.append("- " + ", ".join(parts))
    return "\n".join(lines)


def _format_tool_result(result: ToolResult) -> str:
    return (
        f"Tool result from {result.name}\n"
        f"Query: {result.query}\n"
        f"{result.content}"
    )


def _format_optional(value: object, suffix: str = "") -> str:
    if value is None:
        return "unknown"
    return f"{value:g}{suffix}" if isinstance(value, float) else f"{value}{suffix}"
