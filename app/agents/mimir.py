from app.agents.hulk import HulkAgent
from app.llm.groq_client import GroqClient
from app.schemas import ChatRequest, ChatResponse


class MimirAgent:
    name = "Mimir"

    def __init__(self, groq_client: GroqClient) -> None:
        self.groq_client = groq_client
        self.hulk = HulkAgent(groq_client)

    async def respond(self, request: ChatRequest) -> ChatResponse:
        route = self.route(request.message)
        if route == "hulk":
            reply = await self.hulk.respond(request.message)
            return ChatResponse(
                agent=self.hulk.name,
                route="hulk",
                reply=reply,
                metadata={"routed_by": self.name},
            )

        return ChatResponse(
            agent=self.name,
            route="mimir",
            reply=(
                "Mimir here. Local prototype is running. Hulk is enabled for "
                "workout, meal, calorie, macro, and physique questions."
            ),
            metadata={"enabled_agents": ["Hulk"]},
        )

    def route(self, message: str) -> str:
        normalized = message.lower()
        hulk_keywords = {
            "bench",
            "squat",
            "deadlift",
            "press",
            "row",
            "pullup",
            "pull-up",
            "workout",
            "routine",
            "program",
            "sets",
            "reps",
            "kg",
            "lb",
            "protein",
            "carb",
            "carbs",
            "fat",
            "macro",
            "macros",
            "calorie",
            "calories",
            "meal",
            "food",
            "diet",
            "bulk",
            "body fat",
            "physique",
            "posture",
            "progress photo",
        }
        if any(keyword in normalized for keyword in hulk_keywords):
            return "hulk"
        return "mimir"
