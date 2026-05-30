from app.agents.hulk import HulkAgent
from app.agents.prompts import MIMIR_SYSTEM_PROMPT
from app.llm.groq_client import GroqClient
from app.schemas import ChatRequest, ChatResponse, LLMMessage


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
                reply=self._with_title("🏋️‍♂️ Hulk :", reply),
                metadata={"routed_by": self.name},
            )

        reply = await self.groq_client.chat(
            [
                LLMMessage(role="system", content=MIMIR_SYSTEM_PROMPT),
                LLMMessage(role="user", content=request.message),
            ],
            temperature=0.5,
            max_tokens=500,
        )
        return ChatResponse(
            agent=self.name,
            route="mimir",
            reply=self._with_title("🐱 Mimir :", reply),
            metadata={"enabled_agents": ["Hulk"]},
        )

    def _with_title(self, title: str, reply: str) -> str:
        normalized = reply.lstrip()
        if normalized.startswith(title):
            return normalized
        return f"{title}\n{normalized}"

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
            "健身",
            "訓練",
            "训练",
            "重訓",
            "重训",
            "臥推",
            "卧推",
            "深蹲",
            "硬舉",
            "硬拉",
            "組",
            "组",
            "次",
            "蛋白質",
            "蛋白质",
            "碳水",
            "脂肪",
            "熱量",
            "热量",
            "卡路里",
            "飲食",
            "饮食",
            "餐",
            "食物",
            "體脂",
            "体脂",
            "體態",
            "体态",
            "姿勢",
            "姿势",
        }
        if any(keyword in normalized for keyword in hulk_keywords):
            return "hulk"
        return "mimir"
