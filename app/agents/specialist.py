from app.agents.base import AgentProfile
from app.llm.groq_client import GroqClient
from app.schemas import LLMMessage


class PromptSpecialistAgent:
    def __init__(
        self,
        groq_client: GroqClient,
        profile: AgentProfile,
        system_prompt: str,
    ) -> None:
        self.groq_client = groq_client
        self.profile = profile
        self.name = profile.name
        self.system_prompt = system_prompt

    async def respond(self, message: str, user_id: str = "local-user") -> str:
        return await self.groq_client.chat(
            [
                LLMMessage(role="system", content=self.system_prompt),
                LLMMessage(role="user", content=message),
            ],
            temperature=0.35,
        )
