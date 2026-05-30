from app.agents.prompts import HULK_SYSTEM_PROMPT
from app.llm.groq_client import GroqClient
from app.schemas import LLMMessage


class HulkAgent:
    name = "Hulk"

    def __init__(self, groq_client: GroqClient) -> None:
        self.groq_client = groq_client

    async def respond(self, message: str) -> str:
        return await self.groq_client.chat(
            [
                LLMMessage(role="system", content=HULK_SYSTEM_PROMPT),
                LLMMessage(role="user", content=message),
            ],
            temperature=0.35,
        )
