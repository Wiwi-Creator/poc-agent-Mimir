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
    mimir = MimirAgent(groq_client=FakeGroqClient())
    response = await mimir.respond(ChatRequest(message="How are you?"))

    assert response.route == "mimir"
    assert response.agent == "Mimir"
    assert response.reply.startswith("🐱 Mimir :\nMeow")


@pytest.mark.asyncio
async def test_mimir_intro_only_on_first_greeting():
    mimir = MimirAgent(groq_client=FakeGroqClient())

    first = await mimir.respond(ChatRequest(message="hello", user_id="user-1"))
    second = await mimir.respond(ChatRequest(message="hello", user_id="user-1"))

    assert "multi-agent system" in first.reply
    assert "Current sub-agent: Hulk" in first.reply
    assert "multi-agent system" not in second.reply


@pytest.mark.asyncio
async def test_mimir_closing_reply():
    mimir = MimirAgent(groq_client=FakeGroqClient())

    response = await mimir.respond(ChatRequest(message="okay"))

    assert response.reply == "🐱 Mimir :\nHave a nice day! Meow ~"


@pytest.mark.asyncio
async def test_mimir_refuses_out_of_scope_question():
    mimir = MimirAgent(groq_client=FakeGroqClient())

    response = await mimir.respond(ChatRequest(message="How do I learn Python?"))

    assert response.route == "mimir"
    assert "outside my current role" in response.reply


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
async def test_call_hulk_routes_to_hulk_handoff_without_refusal():
    mimir = MimirAgent(groq_client=FakeGroqClient())
    response = await mimir.respond(ChatRequest(message="Call Hulk"))

    assert response.route == "hulk"
    assert response.agent == "Hulk"
    assert response.reply.startswith("🟢💪 Hulk :")
    assert "Hulk is here" in response.reply


@pytest.mark.asyncio
async def test_call_huk_typo_routes_to_hulk_handoff_without_refusal():
    mimir = MimirAgent(groq_client=FakeGroqClient())
    response = await mimir.respond(ChatRequest(message="Call Huk"))

    assert response.route == "hulk"
    assert response.agent == "Hulk"
    assert "Hulk is here" in response.reply


@pytest.mark.asyncio
async def test_need_sub_agent_routes_to_hulk_handoff_without_refusal():
    mimir = MimirAgent(groq_client=FakeGroqClient())
    response = await mimir.respond(ChatRequest(message="need $sub agent"))

    assert response.route == "hulk"
    assert response.agent == "Hulk"
    assert "Hulk is here" in response.reply


@pytest.mark.asyncio
async def test_muscle_question_routes_to_hulk():
    mimir = MimirAgent(groq_client=FakeGroqClient())
    response = await mimir.respond(ChatRequest(message="How do I build more muscle?"))

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
    mimir = MimirAgent(groq_client=FakeGroqClient())

    response = await mimir.respond(ChatRequest(message="What can you do?"))

    assert "multi-agent system" in response.reply
    assert "workout planning" in response.reply
    assert "exercise alternatives" in response.reply
    assert "meal estimates" in response.reply
    assert "posture feedback" in response.reply
