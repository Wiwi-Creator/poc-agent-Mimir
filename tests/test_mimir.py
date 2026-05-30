import pytest

from app.agents.mimir import MimirAgent
from app.schemas import ChatRequest


class FakeGroqClient:
    async def chat(self, messages, temperature=0.4, max_tokens=700):
        return "Fake Hulk response"


@pytest.mark.asyncio
async def test_routes_workout_message_to_hulk():
    mimir = MimirAgent(groq_client=FakeGroqClient())
    response = await mimir.respond(
        ChatRequest(message="I benched 80kg for 5, 5, 4. What now?")
    )

    assert response.route == "hulk"
    assert response.agent == "Hulk"
    assert response.reply == "Fake Hulk response"


@pytest.mark.asyncio
async def test_non_fitness_message_stays_with_mimir():
    mimir = MimirAgent(groq_client=FakeGroqClient())
    response = await mimir.respond(ChatRequest(message="hello"))

    assert response.route == "mimir"
    assert response.agent == "Mimir"
