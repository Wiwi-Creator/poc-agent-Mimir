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
    assert response.reply == "🟢💪 Hulk :\nFake Hulk response"


@pytest.mark.asyncio
async def test_non_fitness_message_stays_with_mimir():
    groq_client = FakeGroqClient()
    mimir = MimirAgent(groq_client=groq_client)
    response = await mimir.respond(ChatRequest(message="hello"))

    assert response.route == "mimir"
    assert response.agent == "Mimir"
    assert response.reply == "🐱 Mimir :\nFake Mimir response"
    system_prompt = groq_client.calls[0][0].content
    assert "cat-like personal supervisor agent" in system_prompt
    assert "multi-agent system" in system_prompt
    assert "Master is Wiwi" in system_prompt
    assert "Currently the only sub-agent is Hulk" in system_prompt
    assert "reply only in Traditional Chinese" in system_prompt
    assert "Do not use Simplified Chinese" in system_prompt
    assert "0-2 per reply" in system_prompt
    assert 'If replying in English, use "Meow" and never use "喵".' in system_prompt
    assert 'If replying in Chinese, use "喵" and never use "Meow".' in system_prompt
    assert 'the app will add "🐱 Mimir" automatically' in system_prompt


@pytest.mark.asyncio
async def test_routes_chinese_workout_message_to_hulk():
    mimir = MimirAgent(groq_client=FakeGroqClient())
    response = await mimir.respond(ChatRequest(message="我今天臥推80公斤做三組"))

    assert response.route == "hulk"
    assert response.agent == "Hulk"


@pytest.mark.asyncio
async def test_routes_workout_meta_intent_to_hulk_without_confirmation():
    mimir = MimirAgent(groq_client=FakeGroqClient())
    response = await mimir.respond(ChatRequest(message="I need to ask a workout question"))

    assert response.route == "hulk"
    assert response.agent == "Hulk"


@pytest.mark.asyncio
async def test_routes_chinese_workout_meta_intent_to_hulk_without_confirmation():
    mimir = MimirAgent(groq_client=FakeGroqClient())
    response = await mimir.respond(ChatRequest(message="我想問健身問題"))

    assert response.route == "hulk"
    assert response.agent == "Hulk"


@pytest.mark.asyncio
async def test_hulk_prompt_stays_in_scope():
    groq_client = FakeGroqClient()
    mimir = MimirAgent(groq_client=groq_client)

    await mimir.respond(ChatRequest(message="How many calories in chicken rice?"))

    system_prompt = groq_client.calls[0][0].content
    assert "Only answer questions related to workouts" in system_prompt
    assert "outside those areas" in system_prompt
    assert 'the app will add "🟢💪 Hulk" automatically' in system_prompt


@pytest.mark.asyncio
async def test_mimir_intro_prompt_mentions_hulk_capabilities():
    groq_client = FakeGroqClient()
    mimir = MimirAgent(groq_client=groq_client)

    await mimir.respond(ChatRequest(message="What can you do?"))

    system_prompt = groq_client.calls[0][0].content
    assert "Mimir is a multi-agent supervisor system" in system_prompt
    assert "workout planning" in system_prompt
    assert "exercise alternatives" in system_prompt
    assert "meal estimates" in system_prompt
    assert "posture feedback" in system_prompt
