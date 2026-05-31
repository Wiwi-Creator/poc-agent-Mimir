from app.agents.hulk import HulkAgent
from app.llm.groq_client import GroqClient
from app.memory.user_state_store import UserStateStore
from app.memory.workout_store import WorkoutStore
from app.planning.plan_store import WorkoutPlanStore
from app.schemas import ChatRequest, ChatResponse
from app.tools.hulk_tools import HulkToolRegistry


class MimirAgent:
    name = "Mimir"

    def __init__(
        self,
        groq_client: GroqClient,
        workout_store: WorkoutStore | None = None,
        plan_store: WorkoutPlanStore | None = None,
        user_state_store: UserStateStore | None = None,
        hulk_tools: HulkToolRegistry | None = None,
    ) -> None:
        self.groq_client = groq_client
        self.user_state_store = user_state_store
        self._seen_intro_users: set[str] = set()
        self.hulk = HulkAgent(
            groq_client,
            workout_store=workout_store,
            plan_store=plan_store,
            tool_registry=hulk_tools,
        )

    async def respond(self, request: ChatRequest) -> ChatResponse:
        if self._is_closing(request.message):
            return ChatResponse(
                agent=self.name,
                route="mimir",
                reply=self._with_title("🐱 Mimir :", "Have a nice day! Meow ~"),
                metadata={"enabled_agents": ["Hulk"]},
            )

        route = self.route(request.message)
        if route == "hulk":
            reply = await self.hulk.respond(request.message, user_id=request.user_id)
            return ChatResponse(
                agent=self.hulk.name,
                route="hulk",
                reply=self._with_title("🟢💪 Hulk :", reply),
                metadata={"routed_by": self.name},
            )

        reply = self._mimir_reply(request.message, request.user_id)
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

    def _mimir_reply(self, message: str, user_id: str) -> str:
        if self._is_intro_request(message):
            self._mark_seen_intro(user_id)
            return self._intro_reply(message)

        if self._is_greeting(message):
            if not self._has_seen_intro(user_id):
                self._mark_seen_intro(user_id)
                return self._intro_reply(message)
            return self._social_reply(message)

        if self._is_social(message):
            return self._social_reply(message)

        return self._out_of_scope_reply(message)

    def _has_seen_intro(self, user_id: str) -> bool:
        if self.user_state_store:
            return self.user_state_store.has_seen_intro(user_id)
        return user_id in self._seen_intro_users

    def _mark_seen_intro(self, user_id: str) -> None:
        if self.user_state_store:
            self.user_state_store.mark_seen_intro(user_id)
            return
        self._seen_intro_users.add(user_id)

    def _intro_reply(self, message: str) -> str:
        if _contains_chinese(message):
            return (
                "喵。我是 Mimir，Wiwi 的貓型主管代理，也是一個多代理系統的入口。"
                "我負責陪你簡短聊天、理解需求，並把專門任務交給合適的子代理。\n\n"
                "目前的子代理是 Hulk：可以處理訓練課表、健身建議、動作替代、"
                "組數與次數追蹤、訓練紀錄、餐點估算、熱量與巨量營養素、"
                "營養情境、體態與姿勢回饋。"
            )
        return (
            "Meow. I am Mimir, Wiwi's cat-like supervisor agent and the front "
            "door to a multi-agent system. I can socialize briefly, understand "
            "what you need, and route specialist tasks.\n\n"
            "Current sub-agent: Hulk. Hulk handles workout planning, training "
            "advice, exercise alternatives, set/rep tracking, workout logs, "
            "meal estimates, calories/macros, nutrition context, physique/body "
            "composition, and posture feedback."
        )

    def _social_reply(self, message: str) -> str:
        if _contains_chinese(message):
            return "喵，我在。今天想聊一下，還是要我幫你叫 Hulk 處理訓練或飲食？"
        return "Meow, I am here. Want to chat for a moment, or should I route a workout or nutrition question to Hulk?"

    def _out_of_scope_reply(self, message: str) -> str:
        if _contains_chinese(message):
            return (
                "喵，這題超出我目前的職責。我可以陪你簡短聊天，或把健身、訓練、"
                "飲食、熱量、巨量營養素、體態與姿勢問題交給 Hulk。"
            )
        return (
            "Meow, that is outside my current role. I can socialize briefly or "
            "route fitness, training, nutrition, meal, calorie/macro, physique, "
            "and posture questions to Hulk."
        )

    def _is_closing(self, message: str) -> bool:
        normalized = message.strip().lower()
        closing_phrases = {
            "ok",
            "okay",
            "thanks",
            "thank you",
            "bye",
            "goodbye",
            "好",
            "好的",
            "謝謝",
            "掰掰",
        }
        return normalized in closing_phrases

    def _is_greeting(self, message: str) -> bool:
        normalized = message.strip().lower()
        greeting_phrases = {
            "hi",
            "hello",
            "hey",
            "yo",
            "good morning",
            "good afternoon",
            "good evening",
            "你好",
            "嗨",
            "哈囉",
            "早安",
            "午安",
            "晚安",
        }
        return normalized in greeting_phrases

    def _is_intro_request(self, message: str) -> bool:
        normalized = message.lower()
        intro_keywords = {
            "who are you",
            "what can you do",
            "introduce",
            "your capabilities",
            "你是誰",
            "你可以做什麼",
            "介紹",
            "能力",
        }
        return any(keyword in normalized for keyword in intro_keywords)

    def _is_social(self, message: str) -> bool:
        normalized = message.lower()
        social_keywords = {
            "how are you",
            "how is your day",
            "chat",
            "talk with me",
            "陪我聊",
            "你今天如何",
            "心情",
        }
        return any(keyword in normalized for keyword in social_keywords)

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
            "training question",
            "workout question",
            "fitness question",
            "ask hulk",
            "talk to hulk",
            "ask a workout",
            "ask about workout",
            "ask about training",
            "training advice",
            "workout advice",
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
            "重訓",
            "臥推",
            "深蹲",
            "硬舉",
            "硬拉",
            "組",
            "次",
            "蛋白質",
            "碳水",
            "脂肪",
            "熱量",
            "卡路里",
            "飲食",
            "餐",
            "食物",
            "體脂",
            "體態",
            "姿勢",
            "問健身",
            "健身問題",
            "訓練問題",
            "問訓練",
            "問飲食",
            "問熱量",
            "問hulk",
        }
        if any(keyword in normalized for keyword in hulk_keywords):
            return "hulk"
        return "mimir"


def _contains_chinese(message: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in message)
