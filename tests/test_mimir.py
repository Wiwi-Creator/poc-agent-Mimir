import pytest

from app.agents.mimir import MimirAgent
from app.schemas import ChatRequest


class FakeGroqClient:
    def __init__(self):
        self.calls = []

    async def chat(self, messages, temperature=0.4, max_tokens=700):
        self.calls.append(messages)
        if messages[0].content.startswith("You are Hulk"):
            return "Fake Hulk response"
        return "Fake Mimir response"


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
    groq_client = FakeGroqClient()
    mimir = MimirAgent(groq_client=groq_client)
    response = await mimir.respond(ChatRequest(message="hello"))

    assert response.route == "mimir"
    assert response.agent == "Mimir"
    assert response.reply == "Fake Mimir response"
    system_prompt = groq_client.calls[0][0].content
    assert "cat-like personal supervisor agent" in system_prompt
    assert "reply only in Traditional Chinese" in system_prompt
    assert "Do not use Simplified Chinese" in system_prompt
    assert "0-2 per reply" in system_prompt
    assert 'If replying in English, use "Meow" and never use "喵".' in system_prompt
    assert 'If replying in Chinese, use "喵" and never use "Meow".' in system_prompt


@pytest.mark.asyncio
async def test_routes_chinese_workout_message_to_hulk():
    mimir = MimirAgent(groq_client=FakeGroqClient())
    response = await mimir.respond(ChatRequest(message="我今天臥推80公斤做三組"))

    assert response.route == "hulk"
    assert response.agent == "Hulk"
