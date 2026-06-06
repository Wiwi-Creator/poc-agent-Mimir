from app.agents.hulk import HulkAgent
from app.agents.catalog import (
    DRAGONITE_PROFILE,
    HULK_PROFILE,
    MEWTWO_PROFILE,
    MIMIR_PROFILE,
    PORYGON_PROFILE,
    ROTOM_PROFILE,
    SAGE_PROFILE,
)
from app.agents.prompts import (
    DRAGONITE_SYSTEM_PROMPT,
    MEWTWO_SYSTEM_PROMPT,
    PORYGON_SYSTEM_PROMPT,
    ROTOM_SYSTEM_PROMPT,
    SAGE_SYSTEM_PROMPT,
)
from app.agents.registry import AgentRegistry
from app.agents.specialist import PromptSpecialistAgent
from app.llm.groq_client import GroqClient
from app.memory.user_state_store import UserStateStore
from app.memory.workout_store import WorkoutStore
from app.media.models import MediaAttachment
from app.planning.plan_store import WorkoutPlanStore
from app.schemas import ChatRequest, ChatResponse
from app.tools.hulk_tools import HulkToolRegistry
from app.vision.analyzer import HulkImageAnalyzer, PhysiqueVisionAnalyzer


class MimirAgent:
    name = "Mimir"

    def __init__(
        self,
        groq_client: GroqClient,
        workout_store: WorkoutStore | None = None,
        plan_store: WorkoutPlanStore | None = None,
        user_state_store: UserStateStore | None = None,
        hulk_tools: HulkToolRegistry | None = None,
        physique_analyzer: PhysiqueVisionAnalyzer | None = None,
        image_analyzer: HulkImageAnalyzer | None = None,
    ) -> None:
        self.groq_client = groq_client
        self.user_state_store = user_state_store
        self._seen_intro_users: set[str] = set()
        self.hulk = HulkAgent(
            groq_client,
            workout_store=workout_store,
            plan_store=plan_store,
            tool_registry=hulk_tools,
            physique_analyzer=physique_analyzer,
            image_analyzer=image_analyzer,
        )
        self.registry = AgentRegistry()
        self.registry.register(HULK_PROFILE, self.hulk)
        self.registry.extend(
            (
                (
                    DRAGONITE_PROFILE,
                    PromptSpecialistAgent(
                        groq_client,
                        DRAGONITE_PROFILE,
                        DRAGONITE_SYSTEM_PROMPT,
                    ),
                ),
                (
                    PORYGON_PROFILE,
                    PromptSpecialistAgent(
                        groq_client,
                        PORYGON_PROFILE,
                        PORYGON_SYSTEM_PROMPT,
                    ),
                ),
                (
                    SAGE_PROFILE,
                    PromptSpecialistAgent(
                        groq_client,
                        SAGE_PROFILE,
                        SAGE_SYSTEM_PROMPT,
                    ),
                ),
                (
                    MEWTWO_PROFILE,
                    PromptSpecialistAgent(
                        groq_client,
                        MEWTWO_PROFILE,
                        MEWTWO_SYSTEM_PROMPT,
                    ),
                ),
                (
                    ROTOM_PROFILE,
                    PromptSpecialistAgent(
                        groq_client,
                        ROTOM_PROFILE,
                        ROTOM_SYSTEM_PROMPT,
                    ),
                ),
            )
        )

    async def respond(self, request: ChatRequest) -> ChatResponse:
        if self._is_closing(request.message):
            return ChatResponse(
                agent=self.name,
                route="mimir",
                reply=self._with_title("🐱 Mimir :", "Have a nice day! Meow ~"),
                metadata={"enabled_agents": self.registry.enabled_agent_names()},
            )

        route = self.route(request.message)
        specialist = self.registry.get(route)
        profile = self.registry.profile(route)
        if specialist and profile:
            if self._is_specialist_handoff_only(request.message, profile.name):
                reply = self._specialist_handoff_reply(profile.name, request.message)
            else:
                reply = await specialist.respond(
                    request.message,
                    user_id=request.user_id,
                )
            return ChatResponse(
                agent=profile.name,
                route=profile.id,
                reply=self._with_title(
                    f"{profile.icon} {profile.name} :",
                    reply,
                ),
                metadata={"routed_by": self.name, "role": profile.role},
            )

        reply = self._mimir_reply(request.message, request.user_id)
        return ChatResponse(
            agent=self.name,
            route="mimir",
            reply=self._with_title("🐱 Mimir :", reply),
            metadata={"enabled_agents": self.registry.enabled_agent_names()},
        )

    def agent_profiles(self):
        return (MIMIR_PROFILE, *self.registry.profiles())

    async def respond_to_physique_image(
        self,
        attachment: MediaAttachment,
        user_id: str,
        context: str = "",
    ) -> ChatResponse:
        reply = await self.hulk.analyze_physique_photo(
            attachment=attachment,
            context=context,
        )
        return ChatResponse(
            agent=self.hulk.name,
            route="hulk",
            reply=self._with_title("🟢💪 Hulk :", reply),
            metadata={"routed_by": self.name, "media_type": "physique_image"},
        )

    async def respond_to_image(
        self,
        attachment: MediaAttachment,
        user_id: str,
        context: str = "",
    ) -> ChatResponse:
        reply = await self.hulk.analyze_image(
            attachment=attachment,
            context=context,
        )
        return ChatResponse(
            agent=self.hulk.name,
            route="hulk",
            reply=self._with_title("🟢💪 Hulk :", reply),
            metadata={"routed_by": self.name, "media_type": "image"},
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
                "目前的專家團隊有 Hulk（健身與營養）、Dragonite（旅行）、"
                "Porygon（財務）、Sage（職涯）、Mewtwo（科技資訊）與 "
                "Rotom（會議支援）。直接告訴我目標，我會交給合適的專家。"
            )
        return (
            "Meow. I am Mimir, Wiwi's cat-like supervisor agent and the front "
            "door to a multi-agent system. I can socialize briefly, understand "
            "what you need, and route specialist tasks.\n\n"
            "Current sub-agent team: Hulk for workout planning, training advice, "
            "exercise alternatives, workout logs, meal estimates, and posture "
            "feedback; Dragonite "
            "for travel, Porygon for finance, Sage for career, Mewtwo for "
            "technology information, and Rotom for meeting support. Tell me the "
            "goal and I will route it."
        )

    def _social_reply(self, message: str) -> str:
        if _contains_chinese(message):
            return "喵，我在。告訴我你想完成什麼，我會找合適的專家一起處理。"
        return "Meow, I am here. Tell me what you need and I will bring in the right specialist."

    def _out_of_scope_reply(self, message: str) -> str:
        if _contains_chinese(message):
            return (
                "喵，這題目前沒有對應的專家。我可以處理健身、旅行、財務、"
                "職涯、科技資訊與會議支援，也可以陪你簡短聊天。"
            )
        return (
            "Meow, that is outside my current role. I can socialize briefly or "
            "route workout, travel, finance, career, technology, or meeting work "
            "to a specialist."
        )

    def _specialist_handoff_reply(self, name: str, message: str) -> str:
        if _contains_chinese(message):
            return f"{name} 已上線。請直接告訴我你想完成的目標。"
        return f"{name} is here. Tell me the outcome you want."

    def _is_specialist_handoff_only(self, message: str, name: str) -> bool:
        normalized = message.strip().lower()
        agent_name = name.lower()
        return normalized in {
            agent_name,
            f"call {agent_name}",
            f"need {agent_name}",
            f"ask {agent_name}",
            f"talk to {agent_name}",
            f"叫{agent_name}",
            f"叫 {agent_name}",
            f"找{agent_name}",
            f"找 {agent_name}",
            f"需要{agent_name}",
            f"需要 {agent_name}",
        } or (agent_name == "hulk" and self._is_hulk_handoff_only(message))

    def _hulk_handoff_reply(self, message: str) -> str:
        if _contains_chinese(message):
            return (
                "Hulk 已上線。直接丟給我你的訓練、課表、動作、飲食、熱量、"
                "巨量營養素、體態或姿勢問題。💪"
            )
        return (
            "Hulk is here. Send me your workout, routine, exercise, nutrition, "
            "calorie, macro, physique, or posture question. 💪"
        )

    def _is_hulk_handoff_only(self, message: str) -> bool:
        normalized = message.strip().lower()
        handoff_phrases = {
            "hulk",
            "huk",
            "call hulk",
            "call huk",
            "need hulk",
            "need huk",
            "i need hulk",
            "i need huk",
            "ask hulk",
            "ask huk",
            "talk to hulk",
            "talk to huk",
            "call sub agent",
            "call sub-agent",
            "need sub agent",
            "need sub-agent",
            "need $sub agent",
            "need $sub-agent",
            "$sub agent",
            "$sub-agent",
            "sub agent",
            "sub-agent",
            "叫 hulk",
            "叫hulk",
            "叫 huk",
            "叫huk",
            "找 hulk",
            "找hulk",
            "找 huk",
            "找huk",
            "需要 hulk",
            "需要hulk",
            "需要 huk",
            "需要huk",
            "子代理",
            "叫子代理",
            "需要子代理",
        }
        return normalized in handoff_phrases

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
        return self.registry.match(message) or "mimir"


def _contains_chinese(message: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in message)
